import 'dart:async';
import 'dart:isolate';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_events/tideglass_events.dart';
import 'package:tideglass_progression/tideglass_progression.dart';
import 'story_state.dart';

class ReplayedSession {
  const ReplayedSession(this.main, this.story, this.settledThrough);
  final GameState main;
  final StoryProgress story;
  final DateTime settledThrough;
}

class ReplayProgress {
  const ReplayProgress(this.completed, this.total);
  final Duration completed, total;
  double get fraction => total.inMicroseconds == 0
      ? 1
      : (completed.inMicroseconds / total.inMicroseconds).clamp(0, 1);
}

/// Run pure settlement away from the rendering isolate. The caller commits the
/// final session atomically; interruption leaves the entire prior snapshot
/// recoverable. Chunk boundaries retain the original absence's offline offset.
Future<ReplayedSession> replayOfflineSession({
  required GameState main,
  required StoryProgress story,
  required StoryCatalogue catalogue,
  required DateTime settledThrough,
  required DateTime now,
  void Function(ReplayProgress)? onProgress,
  Duration chunk = const Duration(hours: 4),
}) async {
  if (chunk <= Duration.zero) {
    throw ArgumentError('Replay chunks must be positive.');
  }
  final receive = ReceivePort();
  final result = Completer<ReplayedSession>();
  final subscription = receive.listen((Object? message) {
    if (message is ReplayProgress) {
      onProgress?.call(message);
    } else if (message is ReplayedSession) {
      if (!result.isCompleted) result.complete(message);
    } else if (message is List) {
      if (!result.isCompleted) {
        result.completeError(
          StateError('Saved progress could not be replayed: ${message.first}'),
        );
      }
    } else if (message == null && !result.isCompleted) {
      result.completeError(
        StateError(
          'Settlement worker stopped before completion. Saved progress is unchanged.',
        ),
      );
    }
  });
  Isolate? worker;
  try {
    worker = await Isolate.spawn(
      _replayWorker,
      _ReplayRequest(
        receive.sendPort,
        main,
        story,
        catalogue,
        settledThrough.toUtc(),
        now.toUtc(),
        chunk,
      ),
      onError: receive.sendPort,
      onExit: receive.sendPort,
      errorsAreFatal: true,
    );
    return await result.future;
  } finally {
    worker?.kill(priority: Isolate.immediate);
    await subscription.cancel();
    receive.close();
  }
}

class _ReplayRequest {
  const _ReplayRequest(
    this.port,
    this.main,
    this.story,
    this.catalogue,
    this.from,
    this.through,
    this.chunk,
  );
  final SendPort port;
  final GameState main;
  final StoryProgress story;
  final StoryCatalogue catalogue;
  final DateTime from, through;
  final Duration chunk;
}

void _replayWorker(_ReplayRequest input) {
  const engine = TideglassEngine();
  var main = input.main, story = input.story, cursor = input.from;
  final end = input.through.isBefore(cursor) ? cursor : input.through;
  final total = end.difference(cursor);
  final watch = Stopwatch()..start();
  var lastUpdate = -100;
  void progress() {
    if (watch.elapsedMilliseconds - lastUpdate >= 25 || cursor == end) {
      input.port.send(ReplayProgress(cursor.difference(input.from), total));
      lastUpdate = watch.elapsedMilliseconds;
    }
  }

  if (main.support.receiptCursorMigrationRequired) {
    final migrated = engine.initializeReceiptCursor(main, cursor);
    if (!migrated.accepted) {
      throw StateError(migrated.reason ?? 'Settlement rejected.');
    }
    main = migrated.state;
  }

  void advancePartitions(Duration duration, Duration offset, DateTime through) {
    final active = story.dossiers.active;
    if (active != null) {
      final definition = input.catalogue.dossier(active.dossierId);
      final run = ChallengeEconomy(definition).advanceRun(
        active,
        duration,
        offline: true,
        offlineElapsedBefore: offset,
      );
      final firstCompletion =
          run.complete && !story.dossiers.completed.contains(run.dossierId);
      story = story.copyWith(dossiers: story.dossiers.withRun(run, definition));
      if (firstCompletion) {
        final discovered = engine.recordDiscovery(
          main,
          'challenge',
          operationSequence: main.nextDiscoverySequence,
          contentId: run.dossierId,
        );
        if (!discovered.accepted) {
          throw StateError(discovered.reason ?? 'Settlement rejected.');
        }
        main = discovered.state;
      }
    }
    if (story.season != null && through.isAfter(cursor)) {
      final advanced = SeasonEngine(input.catalogue.seasonDefinition).advanceTo(
        story.season!,
        through,
        offline: true,
        offlineElapsedBefore: offset,
      );
      if (!advanced.accepted) {
        throw StateError(advanced.reason ?? 'Settlement rejected.');
      }
      story = story.copyWith(season: advanced.state);
    }
  }

  progress();
  if (main.support.hasLegacyPendingSettlement) {
    final offset = Duration(
      microseconds: main.support.nextOffsetMicros.toInt(),
    );
    final elapsed = end.difference(cursor);
    final advanced = engine.finishLegacyOfflineSettlement(
      main,
      elapsed,
      frozenSettlementId: main.support.activeSettlementId!,
      offlineElapsedBefore: offset,
      throughUtc: end,
    );
    if (!advanced.accepted) {
      throw StateError(advanced.reason ?? 'Settlement rejected.');
    }
    main = advanced.state;
    advancePartitions(elapsed, offset, end);
    cursor = end;
  }
  while (cursor.isBefore(end) || main.support.activeSettlementRequest != null) {
    final existing = main.support.activeSettlementRequest;
    final request =
        existing ??
        OfflineSettlementRequest(
          sequence: main.nextSettlementSequence,
          fromUtc: cursor,
          throughUtc: end,
        );
    final requestEnd = DateTime.fromMicrosecondsSinceEpoch(
      request.throughUtcMicros.toInt(),
      isUtc: true,
    );
    if (requestEnd.isAfter(end)) {
      throw StateError(
        'An unfinished settlement ends after the current clock.',
      );
    }
    var offset = Duration(microseconds: main.support.nextOffsetMicros.toInt());
    // A new request starts at zero; finalized caches retain no active offset.
    if (existing == null) offset = Duration.zero;
    while (cursor.isBefore(requestEnd)) {
      final remaining = requestEnd.difference(cursor);
      // Beyond the 72-hour envelope, one final capped step avoids iterating
      // thousands of empty hourly chunks after a long absence.
      final step =
          offset >= const Duration(hours: 72) || remaining <= input.chunk
          ? remaining
          : input.chunk;
      final nextCursor = cursor.add(step);
      final advanced = engine.advance(
        main,
        step,
        offline: true,
        offlineElapsedBefore: offset,
        offlineSettlement: request,
        finalizeOfflineSettlement: nextCursor == requestEnd,
      );
      if (!advanced.accepted) {
        throw StateError(advanced.reason ?? 'Settlement rejected.');
      }
      main = advanced.state;
      advancePartitions(step, offset, nextCursor);
      cursor = nextCursor;
      offset += step;
      progress();
    }
    if (main.support.activeSettlementRequest != null) {
      // A persisted zero-length final chunk is legal and must close once.
      final closed = engine.advance(
        main,
        Duration.zero,
        offline: true,
        offlineElapsedBefore: offset,
        offlineSettlement: request,
      );
      if (!closed.accepted) {
        throw StateError(closed.reason ?? 'Settlement rejected.');
      }
      main = closed.state;
    }
  }
  final facts = ProgressFacts(
    main: main,
    recharts: main.rechartCount,
    surveysCollected: main.surveysCollectedTotal > BigInt.from(1 << 30)
        ? 1 << 30
        : main.surveysCollectedTotal.toInt(),
    calibrations: main.completedCalibrationIds,
    completedChallenges: story.dossiers.completed,
  );
  story = story.copyWith(
    campaign: input.catalogue.campaign.evaluate(story.campaign, facts),
  );
  if (main.daily.initialized) {
    main = engine
        .refreshContracts(
          main,
          cursor,
          availableDiscoveryKinds: [
            'archive',
            if (story.campaign.restoredHarbor >= 3) 'challenge',
            if (main.focusCharges > 0 ||
                main.completedCalibrationIds.isNotEmpty)
              'calibration',
          ],
        )
        .state;
  }
  if (story.pass != null) {
    story = story.copyWith(
      pass: PassEngine([
        input.catalogue.seasonDefinition,
      ]).pruneAlternatives(main, story.pass!).pass,
    );
  }
  progress();
  input.port.send(ReplayedSession(main, story, cursor));
}

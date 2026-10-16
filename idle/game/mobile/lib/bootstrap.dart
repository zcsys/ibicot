import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:path_provider/path_provider.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_persistence/tideglass_persistence.dart';
import 'package:tideglass_events/tideglass_events.dart';
import 'package:tideglass_progression/tideglass_progression.dart';

import 'app.dart';
import 'game_controller.dart';
import 'palette.dart';
import 'story_state.dart';
import 'audio_bus.dart';
import 'bundled_content.dart';
import 'offline_replay.dart';

const bundledEconomyDigest = bundledEconomicDigest;

/// The client envelope is separate from the strict, portable economy state.
/// Preferences never influence the economic configuration or output.
void validateClientPayload(
  Map<String, dynamic> payload, {
  StoryCatalogue? catalogue,
}) {
  final version = payload['client_schema_version'];
  if (version != 1 && version != 2) {
    throw const IncompatibleSaveException('Unsupported client version.');
  }
  if ((version != 1 && version != 2) ||
      payload.length != (version == 1 ? 3 : 4) ||
      payload['core'] is! Map ||
      payload['client_preferences'] is! Map) {
    throw const FormatException('Unsupported client save payload.');
  }
  final core = Map<String, dynamic>.from(payload['core'] as Map);
  if (!{1, 2, 3, stateSchemaVersion}.contains(core['schema_version']) ||
      core['economic_version'] != economyVersion ||
      core['event_order_version'] != core['schema_version']) {
    throw const IncompatibleSaveException(
      'Unsupported economic state or event ordering.',
    );
  }
  final main = GameState.fromJson(core);
  if (version == 2) {
    if (payload['story'] is! Map) {
      throw const FormatException('Missing story state.');
    }
    final story = Map<String, dynamic>.from(payload['story'] as Map);
    if (!{1, 2, 3, 4}.contains(story['schema_version']) ||
        (story['content_digest'] != null &&
            story['content_digest'] != bundledManifestDigest)) {
      throw const IncompatibleSaveException(
        'This story requires its pinned content version.',
      );
    }
    final season = story['season'];
    final definition = (catalogue ?? StoryCatalogue.loaded)?.seasonDefinition;
    if (season is Map &&
        definition != null &&
        (season['rules_digest'] != definition.digest ||
            season['rules_version'] != definition.rulesVersion)) {
      throw const IncompatibleSaveException(
        'This season requires its pinned rules.',
      );
    }
    final progress = StoryProgress.fromJson(
      story,
      seasonDefinition: catalogue?.seasonDefinition,
    );
    final pinned = catalogue ?? StoryCatalogue.loaded;
    final active = progress.dossiers.active;
    if (active != null) {
      if (pinned == null) {
        throw const IncompatibleSaveException(
          'The pinned challenge catalogue is required.',
        );
      }
      ChallengeEconomy(pinned.dossier(active.dossierId)).validateRun(active);
    }
    if (progress.season != null) {
      if (pinned == null) {
        throw const IncompatibleSaveException(
          'The pinned seasonal catalogue is required.',
        );
      }
      SeasonEngine(pinned.seasonDefinition).validate(progress.season!);
      PassEngine([
        pinned.seasonDefinition,
      ]).validate(progress.pass!, main: main);
    }
  }
  final preferences = payload['client_preferences'] as Map;
  const fields = {
    'reduce_motion',
    'large_text',
    'scientific',
    'onboarding_dismissed',
  };
  if (preferences.length != fields.length ||
      !preferences.keys.every(fields.contains) ||
      preferences.values.any((value) => value is! bool)) {
    throw const FormatException('Unsupported saved preferences.');
  }
}

/// The save envelope's cursor is part of the simulation contract. Reject a
/// mismatched partition before selecting or replacing a persisted branch.
void validateClientSnapshot(
  Map<String, dynamic> payload,
  DateTime settledThrough, {
  StoryCatalogue? catalogue,
}) {
  final main = GameState.fromJson(Map<String, dynamic>.from(payload['core']));
  final cursor = BigInt.from(settledThrough.toUtc().microsecondsSinceEpoch);
  if (main.daily.initialized &&
      main.daily.utcAnchorMicros! + main.elapsedMicros != cursor) {
    throw const FormatException('Saved calendar and production cursor differ.');
  }
  final pending = main.support.activeSettlementRequest;
  if (pending != null &&
      (pending.fromUtcMicros + main.support.nextOffsetMicros != cursor ||
          cursor > pending.throughUtcMicros)) {
    throw const FormatException('Pending replay and save cursor differ.');
  }
  if (main.support.lastSettlementThroughUtcMicros != null &&
      main.support.lastSettlementThroughUtcMicros! > cursor) {
    throw const FormatException('A receipt extends beyond saved production.');
  }
  if (payload['client_schema_version'] == 2) {
    final story = StoryProgress.fromJson(
      Map<String, dynamic>.from(payload['story']),
      seasonDefinition: catalogue?.seasonDefinition,
    );
    if (story.season != null && story.season!.settledThroughMicros != cursor) {
      throw const FormatException('Main and seasonal save cursors differ.');
    }
  }
}

class TideglassBootstrap extends StatefulWidget {
  const TideglassBootstrap({
    super.key,
    this.directory,
    this.enableAudio = true,
  });

  /// Injected only for host integration tests. Production uses app support.
  final Directory? directory;
  final bool enableAudio;
  @override
  State<TideglassBootstrap> createState() => _TideglassBootstrapState();
}

class _TideglassBootstrapState extends State<TideglassBootstrap> {
  SaveRepository? repository;
  GameController? controller;
  TideAudioBus? audio;
  ClientPreferences preferences = const ClientPreferences();
  String? failure, recoveryNotice;
  bool loading = true;
  ReplayProgress? replayProgress;
  int generation = 0;

  @override
  void initState() {
    super.initState();
    unawaited(_open());
  }

  Future<void> _open() async {
    if (mounted) {
      setState(() {
        loading = true;
        failure = null;
        replayProgress = null;
      });
    }
    try {
      final directory =
          widget.directory ??
          Directory(
            '${(await getApplicationSupportDirectory()).path}/tideglass',
          );
      final catalogue = await StoryCatalogue.load();
      final store = SaveRepository(
        directory,
        economicVersion: economyVersion,
        economicDigest: bundledEconomyDigest,
        validatePayload: (payload) =>
            validateClientPayload(payload, catalogue: catalogue),
        validateSnapshot: (payload, cursor) =>
            validateClientSnapshot(payload, cursor, catalogue: catalogue),
      );
      repository = store;
      final loaded = await store.load();
      final snapshot = loaded.snapshot;
      final payload = snapshot?.payload;
      preferences = payload == null
          ? const ClientPreferences()
          : ClientPreferences.fromJson(
              Map<String, dynamic>.from(payload['client_preferences'] as Map),
            );
      var main = payload == null
          ? GameState.initial()
          : GameState.fromJson(Map<String, dynamic>.from(payload['core']));
      var story = payload?['client_schema_version'] == 2
          ? StoryProgress.fromJson(
              Map<String, dynamic>.from(payload!['story']),
              seasonDefinition: catalogue.seasonDefinition,
            )
          : StoryProgress();
      var cursor = snapshot?.settledThrough;
      final originalMain = main;
      final target = DateTime.now().toUtc();
      if (cursor != null) {
        final replayed = await replayOfflineSession(
          main: main,
          story: story,
          catalogue: catalogue,
          settledThrough: cursor,
          now: target,
          onProgress: (value) {
            if (mounted) setState(() => replayProgress = value);
          },
        );
        main = replayed.main;
        story = replayed.story;
        cursor = replayed.settledThrough;
      }
      if (!mounted) return;
      if (widget.enableAudio && audio == null) {
        audio = TideAudioBus(
          driver: NativeTideAudioDriver(),
          store: FileAudioPreferenceStore(
            File('${directory.path}/audio-preferences.json'),
          ),
        );
        // Sound failures never prevent loading a saved harbor.
        unawaited(audio!.initialize());
      }
      final game = GameController(
        audio: audio,
        catalogue: catalogue,
        initialStory: story,
        initialState: main,
        settledThrough: cursor,
        onSessionPersist: (state, story, cursor) => store.save({
          'client_schema_version': 2,
          'story': story.toJson(),
          'core': state.toJson(),
          'client_preferences': preferences.toJson(),
        }, settledThrough: cursor),
      );
      if (snapshot != null &&
          target.difference(snapshot.settledThrough) >=
              const Duration(minutes: 1)) {
        game.returnReport = ReturnReport(
          absence: target.difference(snapshot.settledThrough),
          earnedMicros: main.lifetimeMicros - originalMain.lifetimeMicros,
          automated: originalMain.autoBuyEnabled,
        );
      }
      // Persist replay before exposing its return report. A write failure stays
      // visible; reopening replays only from the last committed snapshot.
      await game.save();
      if (audio != null) {
        unawaited(
          audio!.startMusic(
            game.story.campaign.hasEnding ? TideMusic.dawn : TideMusic.harbor,
          ),
        );
      }
      if (!mounted) {
        game.dispose();
        return;
      }
      controller?.dispose();
      setState(() {
        controller = game;
        generation++;
        recoveryNotice = loaded.recoveredFromBackup
            ? 'The latest copy could not be read. Your previous saved harbor was recovered; its time away has been settled.'
            : null;
        loading = false;
      });
    } catch (error) {
      if (!mounted) return;
      setState(() {
        loading = false;
        failure = switch (error) {
          IncompatibleSaveException() =>
            'This harbor needs a compatible game version. Its saved files have been preserved.',
          SaveConflictException() =>
            'Two different saved harbors need to be reconciled. Both copies have been preserved.',
          CorruptSaveException() =>
            'Neither saved copy could be opened. Your files have been preserved. You can recover from a previously exported copy.',
          _ =>
            'Your harbor could not be opened (${error.runtimeType}). Its saved files have been preserved.',
        };
      });
    }
  }

  Future<String> _export() async {
    await controller!.save();
    if (controller!.saveError != null) {
      throw const SaveException('Save the latest progress before exporting.');
    }
    return repository!.exportSave();
  }

  Future<void> _recover(String source) async {
    final store = repository;
    if (store == null) throw const SaveException('Storage is not available.');
    await store.importSave(source, recoverCorrupt: true);
    await _open();
  }

  Future<void> _import(String source) async {
    final game = controller!;
    game.suspend();
    await game.save();
    if (game.saveError != null) {
      game.resume();
      throw const SaveException('Save current progress before replacing it.');
    }
    try {
      await repository!.importSave(source);
    } catch (_) {
      game.resume();
      rethrow;
    }
    game.dispose();
    controller = null;
    await _open();
  }

  @override
  void dispose() {
    controller?.dispose();
    audio?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (!loading && controller != null && failure == null) {
      return TideglassApp(
        key: ValueKey(generation),
        controller: controller!,
        initialPreferences: preferences,
        onPreferencesChanged: (value) async {
          preferences = value;
          await controller!.save();
        },
        onExport: _export,
        onImport: _import,
        recoveryNotice: recoveryNotice,
      );
    }
    return MaterialApp(
      title: 'Tideglass',
      debugShowCheckedModeBanner: false,
      theme: tideglassTheme(),
      home: Scaffold(
        body: SafeArea(
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 560),
              child: Padding(
                padding: const EdgeInsets.all(28),
                child: loading
                    ? Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          CircularProgressIndicator(
                            value: replayProgress?.fraction,
                          ),
                          const SizedBox(height: 24),
                          Text(
                            replayProgress == null
                                ? 'Opening your harbor…'
                                : 'Gathering your time away… ${(replayProgress!.fraction * 100).floor()}%',
                          ),
                          if (replayProgress != null)
                            const Padding(
                              padding: EdgeInsets.only(top: 12),
                              child: Text(
                                'Your previous save stays safe until all progress is ready.',
                                textAlign: TextAlign.center,
                              ),
                            ),
                        ],
                      )
                    : _RecoveryPanel(
                        message: failure!,
                        retry: _open,
                        recover: _recover,
                      ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _RecoveryPanel extends StatefulWidget {
  const _RecoveryPanel({
    required this.message,
    required this.retry,
    required this.recover,
  });
  final String message;
  final Future<void> Function() retry;
  final Future<void> Function(String) recover;
  @override
  State<_RecoveryPanel> createState() => _RecoveryPanelState();
}

class _RecoveryPanelState extends State<_RecoveryPanel> {
  final source = TextEditingController();
  bool busy = false;
  String? error;
  @override
  void dispose() {
    source.dispose();
    super.dispose();
  }

  Future<void> restore() async {
    setState(() {
      busy = true;
      error = null;
    });
    try {
      await widget.recover(source.text.trim());
    } catch (issue) {
      if (mounted) {
        setState(
          () => error =
              'This recovery copy could not be used (${issue.runtimeType}). Your current files have been kept.',
        );
      }
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => SingleChildScrollView(
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const Icon(Icons.anchor, color: TideColors.amber, size: 48),
        const SizedBox(height: 24),
        Text(
          'Keep your harbor safe',
          style: Theme.of(context).textTheme.headlineMedium,
        ),
        const SizedBox(height: 16),
        Text(widget.message),
        const SizedBox(height: 24),
        OutlinedButton(
          onPressed: busy ? null : widget.retry,
          child: const Text('Try opening again'),
        ),
        const SizedBox(height: 24),
        TextField(
          controller: source,
          minLines: 3,
          maxLines: 6,
          maxLength: SaveRepository.maxImportBytes,
          decoration: const InputDecoration(
            labelText: 'Previously exported harbor',
            hintText: 'Paste your complete recovery copy here',
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 8),
        const Text(
          'Recovery selects the exported progress. Existing readable progress is archived; damaged files are retained for recovery. Purchases require separate verified restoration.',
        ),
        const SizedBox(height: 16),
        if (error != null) ...[
          Text(error!, style: const TextStyle(color: TideColors.warning)),
          const SizedBox(height: 16),
        ],
        FilledButton(
          onPressed: busy ? null : restore,
          child: Text(busy ? 'Recovering…' : 'Use this recovery copy'),
        ),
      ],
    ),
  );
}

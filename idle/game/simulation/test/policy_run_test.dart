import 'dart:convert';
import 'dart:io';
import 'package:test/test.dart';
import 'package:tideglass_simulation/policy_run.dart';

void main() {
  final content = SimulationContent('../content', '../events/content');
  PolicyRun policy(
    BonusPolicy bonus, {
    int chunk = 4,
    ContractPolicy contracts = ContractPolicy.allReady,
  }) => PolicyRun(
    content,
    visitsPerDay: 3,
    bonus: bonus,
    resetPolicy: ResetPolicy.atVisits,
    offlineChunkHours: chunk,
    contractPolicy: contracts,
  );

  test('experiment content is byte-identical to shipped mobile content', () {
    for (final section in ['challenges', 'progression']) {
      for (final file in Directory(
        '../content/$section',
      ).listSync().whereType<File>()) {
        if (!file.path.endsWith('.json')) continue;
        final name = file.uri.pathSegments.last;
        if (section == 'progression' && name != 'campaign.json') continue;
        expect(
          File('../mobile/assets/$section/$name').readAsBytesSync(),
          file.readAsBytesSync(),
        );
      }
    }
    expect(
      File('../mobile/assets/events/season.01.json').readAsBytesSync(),
      File('../events/content/season.01.json').readAsBytesSync(),
    );
  });

  test(
    'successful ad fixtures and free Support have equal compounded outcomes',
    () {
      final free = policy(BonusPolicy.focusAndFreeSupport);
      final ad = policy(BonusPolicy.focusAndAdSupportFixture);
      final a = free.run(days: 2), b = ad.run(days: 2);
      for (final key in [
        'lifetime_r_micros',
        'charts',
        'counts',
        'recharts',
        'notes_earned',
        'chapters_completed',
        'pass_level',
        'season_lifetime_micros',
        'focus_charges_used',
        'free_support_tokens_used',
      ]) {
        expect(b[key], a[key], reason: key);
      }
      expect(free.supportUsed, 12);
      expect(
        ad.main.support.tokens.every((token) => token.route == 'ad'),
        isTrue,
      );
      expect(
        free.main.support.tokens.every((token) => token.route == 'briefing'),
        isTrue,
      );
    },
    timeout: const Timeout(Duration(minutes: 2)),
  );

  test(
    'changing offline chunk size preserves economics and Note accounting',
    () {
      final coarse = policy(BonusPolicy.requiredCalibrationsOnly);
      final fine = policy(BonusPolicy.requiredCalibrationsOnly, chunk: 1);
      coarse.run(days: 2);
      fine.run(days: 2);
      expect(fine.main.walletMicros, coarse.main.walletMicros);
      expect(fine.main.lifetimeMicros, coarse.main.lifetimeMicros);
      expect(fine.main.counts, coarse.main.counts);
      expect(fine.main.charts, coarse.main.charts);
      expect(fine.main.support.toJson(), coarse.main.support.toJson());
      expect(fine.season.fleet.walletMicros, coarse.season.fleet.walletMicros);
      expect(
        coarse.notesSpent + coarse.main.surveyNotes,
        coarse.surveyNotesEarned + coarse.contractNotesEarned,
      );
      expect(coarse.elapsed, const Duration(days: 2));
      expect(coarse.visits, 6);
    },
    timeout: const Timeout(Duration(minutes: 2)),
  );

  test(
    'no-bonus surveys-only policy grants neither bonuses nor contract income',
    () {
      final run = policy(
        BonusPolicy.none,
        contracts: ContractPolicy.surveysOnly,
      );
      run.run(days: 2);
      expect(run.focusUsed, 0);
      expect(run.supportUsed, 0);
      expect(run.contractsClaimed, 0);
      expect(run.contractNotesEarned, BigInt.zero);
      expect(run.main.surveyNotes, run.surveyNotesEarned);
      expect(run.campaign.restoredHarbor, lessThan(3));
      expect(run.main.focusCharges, greaterThan(0));
    },
    timeout: const Timeout(Duration(minutes: 2)),
  );

  test('recorded summaries do not change when later chapters are unlocked', () {
    final run = policy(BonusPolicy.none);
    final captured = run.summary();
    final before = jsonEncode(captured);
    run.chapterAt['chapter.01'] = 1234;
    run.challengeAt['challenge.01'] = 2345;
    expect(jsonEncode(captured), before);
  });
}

import 'dart:convert';
import 'dart:io';
import 'package:test/test.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_events/tideglass_events.dart';
import 'package:tideglass_persistence/tideglass_persistence.dart';

void main() {
  final definition = SeasonDefinition.fromJson(
      jsonDecode(File('content/season.01.json').readAsStringSync())
          as Map<String, dynamic>);
  final seasonEngine = SeasonEngine(definition),
      passEngine = PassEngine([definition]);
  const core = TideglassEngine();
  final start = DateTime.utc(2026, 10, 16, 12);
  late Directory directory;
  SaveRepository repository({CommitProbe? probe}) => SaveRepository(directory,
      economicVersion: economyVersion,
      economicDigest:
          '9e5b9bcfcfc7a68d4eaeebc97e8d40cd42d04532fa59f514c7483efee885d2b6',
      commitProbe: probe,
      now: () => start,
      validatePayload: (payload) {
        final main =
            GameState.fromJson(Map<String, dynamic>.from(payload['core']));
        final pass = PassState.fromJson(
            Map<String, dynamic>.from(payload['pass']), [definition]);
        passEngine.validate(pass, main: main);
        SeasonState.fromJson(
            Map<String, dynamic>.from(payload['season']), definition);
      });
  Map<String, dynamic> payload(
          GameState main, PassState pass, SeasonState season) =>
      {'core': main.toJson(), 'pass': pass.toJson(), 'season': season.toJson()};
  setUp(() async => directory =
      await Directory.systemTemp.createTemp('season-pass-receipt-'));
  tearDown(() async => directory.delete(recursive: true));
  test(
      'bound objective, sharedXP, cosmeticreceipt andeventcursor commitandreload together',
      () async {
    var main = core
        .refreshContracts(GameState.initial(), start, accountSeed: 'persistent')
        .state;
    main = main.copyWith(
        daily: main.daily.copyWith(passXpById: {'pass.01': BigInt.from(250)}));
    var season = SeasonState.initial(definition, SeasonSchedule(start), start,
        runId: 'save-run');
    var pass = PassState.initial([definition]);
    final id = main.dailyContracts.first.id;
    pass = passEngine.bindEventAlternative(main, pass, id, season).pass;
    final repo = repository();
    await repo.load();
    await repo.save(payload(main, pass, season), settledThrough: start);
    final restored = (await repository().load()).snapshot!.payload;
    pass = PassState.fromJson(
        Map<String, dynamic>.from(restored['pass']), [definition]);
    season = SeasonState.fromJson(
        Map<String, dynamic>.from(restored['season']), definition);
    final end = start.add(const Duration(minutes: 10));
    season = seasonEngine.advanceTo(season, end, offline: true).state;
    final claim =
        passEngine.claimDaily(main, pass, id, alternativeSeason: season);
    expect(claim.accepted, isTrue);
    main = claim.main;
    pass = claim.pass;
    final reward =
        passEngine.claimFreeReward(main, pass, 'pass.01', 'pass.01.free.01');
    expect(reward.accepted, isTrue);
    pass = reward.pass;
    await repo.save(payload(main, pass, season), settledThrough: end);
    final saved = (await repository().load()).snapshot!;
    expect(saved.payload, payload(main, pass, season));
    final loadedMain =
        GameState.fromJson(Map<String, dynamic>.from(saved.payload['core']));
    final loadedPass = PassState.fromJson(
        Map<String, dynamic>.from(saved.payload['pass']), [definition]);
    final loadedSeason = SeasonState.fromJson(
        Map<String, dynamic>.from(saved.payload['season']), definition);
    expect(core.claimContract(loadedMain, id).accepted, isFalse);
    expect(
        passEngine
            .claimFreeReward(
                loadedMain, loadedPass, 'pass.01', 'pass.01.free.01')
            .accepted,
        isFalse);
    expect(seasonEngine.advanceTo(loadedSeason, end, offline: true).accepted,
        isFalse);
  });
  test('after-rename interruption cannot repeatdailyXPor eventinterval',
      () async {
    var main = core
        .refreshContracts(GameState.initial(), start, accountSeed: 'interrupt')
        .state;
    var season = SeasonState.initial(definition, SeasonSchedule(start), start,
        runId: 'interrupt-run');
    var pass = PassState.initial([definition]);
    final id = main.dailyContracts.first.id;
    pass = passEngine.bindEventAlternative(main, pass, id, season).pass;
    final repo = repository();
    await repo.load();
    await repo.save(payload(main, pass, season), settledThrough: start);
    final end = start.add(const Duration(minutes: 10));
    season = seasonEngine.advanceTo(season, end).state;
    final claim =
        passEngine.claimDaily(main, pass, id, alternativeSeason: season);
    main = claim.main;
    pass = claim.pass;
    final interrupted = repository(probe: (stage) async {
      if (stage == CommitStage.afterRename)
        throw const FileSystemException('test interruption');
    });
    await interrupted.load();
    await expectLater(
        interrupted.save(payload(main, pass, season), settledThrough: end),
        throwsA(isA<FileSystemException>()));
    final loaded = (await repository().load()).snapshot!;
    expect(loaded.payload, payload(main, pass, season));
    expect(loaded.settledThrough, end);
    final loadedMain =
        GameState.fromJson(Map<String, dynamic>.from(loaded.payload['core']));
    expect(loadedMain.passXp, BigInt.from(250));
    expect(core.claimContract(loadedMain, id).accepted, isFalse);
  });
  test('unknownXPcopy orpaidflag cannot be imported intoPassState', () {
    final pass = PassState.initial([definition]).toJson();
    for (final key in ['xp', 'premium_owned', 'paid_xp_multiplier']) {
      expect(() => PassState.fromJson({...pass, key: 1}, [definition]),
          throwsFormatException);
    }
  });
}

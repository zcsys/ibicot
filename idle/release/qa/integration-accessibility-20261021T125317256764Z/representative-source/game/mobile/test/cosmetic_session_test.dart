import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/game_controller.dart';
import 'package:tideglass/story_state.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_progression/tideglass_progression.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late StoryCatalogue catalogue;
  final epoch = DateTime.utc(2026, 10, 16, 12);
  setUpAll(() async {
    catalogue = await StoryCatalogue.load();
  });

  test(
    'earned chapter and Note decoration coexist and selection survives reload',
    () {
      final game = GameController(
        catalogue: catalogue,
        startTicker: false,
        clock: () => epoch,
        initialStory: StoryProgress(
          campaign: CampaignProgress(completed: {'chapter.01'}),
        ),
        initialState: GameState.initial().copyWith(
          surveyNotes: BigInt.from(50),
        ),
      );
      addTearDown(game.dispose);
      final earnings = game.state.lifetimeMicros,
          wallet = game.state.walletMicros;
      expect(game.equipCosmetic('cosmetic.core.chapter.01'), isTrue);
      expect(game.equipCosmetic('cosmetic.core.chapter.02'), isFalse);
      expect(game.buyDecoration('cosmetic.core.decoration.02'), isTrue);
      expect(game.visibleAppearance, 'cosmetic.core.chapter.01');
      expect(game.story.equippedDecoration, 'cosmetic.core.decoration.02');
      expect(game.state.walletMicros, wallet);
      expect(game.state.lifetimeMicros, earnings);
      final reloaded = GameController(
        catalogue: catalogue,
        startTicker: false,
        clock: () => epoch,
        settledThrough: game.settledThrough,
        initialState: GameState.fromJson(game.state.toJson()),
        initialStory: StoryProgress.fromJson(
          game.story.toJson(),
          seasonDefinition: catalogue.seasonDefinition,
        ),
      );
      addTearDown(reloaded.dispose);
      expect(reloaded.visibleAppearance, 'cosmetic.core.chapter.01');
      expect(reloaded.story.equippedDecoration, 'cosmetic.core.decoration.02');
      expect(reloaded.equipCosmetic(null), isTrue);
      expect(reloaded.visibleAppearance, isNull);
      expect(reloaded.story.equippedDecoration, 'cosmetic.core.decoration.02');
    },
  );

  test(
    'imported paid appearance is only a preference and cannot grant ownership',
    () {
      final game = GameController(
        catalogue: catalogue,
        startTicker: false,
        clock: () => epoch,
        initialStory: StoryProgress(
          equippedAppearance: 'cosmetic.premium_pass.10',
        ),
      );
      addTearDown(game.dispose);
      expect(game.story.equippedAppearance, 'cosmetic.premium_pass.10');
      expect(game.visibleAppearance, isNull);
      expect(game.ownedCosmetics, isEmpty);
      expect(game.equipCosmetic('cosmetic.premium_pass.10'), isFalse);
      expect(game.equipCosmetic('cosmetic.shop.01'), isFalse);
    },
  );

  test(
    'earned free pass cosmetic becomes equippable without any paid verifier',
    () {
      final game = GameController(
        catalogue: catalogue,
        startTicker: false,
        clock: () => epoch,
      );
      addTearDown(game.dispose);
      game.state = game.state.copyWith(
        daily: game.state.daily.copyWith(
          passXpById: {catalogue.seasonDefinition.passId: BigInt.from(1500)},
        ),
      );
      final reward = catalogue.seasonDefinition.rewards.firstWhere(
        (r) => r.contentId == 'cosmetic.free_pass.01',
      );
      expect(game.equipCosmetic(reward.contentId), isFalse);
      final wallet = game.state.walletMicros;
      expect(game.claimFreePassReward(reward.id), isTrue);
      expect(game.equipCosmetic(reward.contentId), isTrue);
      expect(game.visibleAppearance, reward.contentId);
      expect(game.state.walletMicros, wallet);
      expect(
        game.ownedCosmetics.where((id) => id.contains('premium')),
        isEmpty,
      );
    },
  );

  test('story schema3 migrates with no invented selected appearance', () {
    final old = StoryProgress().toJson()
      ..['schema_version'] = 3
      ..remove('equipped_appearance');
    final restored = StoryProgress.fromJson(old);
    expect(restored.equippedAppearance, isNull);
    expect(restored.toJson()['schema_version'], 4);
  });

  test('paid authority is a revocable projection and never enters a save', () {
    var independentlyVerified = <String>{
      'cosmetic.shop.01',
      'cosmetic.core.chapter.06',
      'unknown-item',
    };
    final game = GameController(
      catalogue: catalogue,
      startTicker: false,
      clock: () => epoch,
      verifiedPaidCosmetics: () => independentlyVerified,
    );
    addTearDown(game.dispose);
    final economicBefore = game.state.toJson();
    expect(game.ownedCosmetics, {'cosmetic.shop.01'});
    expect(game.equipCosmetic('cosmetic.shop.01'), isTrue);
    expect(game.visibleAppearance, 'cosmetic.shop.01');
    final selectedStory = game.story.toJson();
    independentlyVerified = {};
    expect(game.visibleAppearance, isNull);
    expect(game.ownedCosmetics, isEmpty);
    expect(game.equipCosmetic('cosmetic.shop.01'), isFalse);
    expect(game.story.toJson(), selectedStory);
    expect(game.state.toJson(), economicBefore);
  });
}

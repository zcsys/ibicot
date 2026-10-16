import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/app.dart';
import 'package:tideglass/calibration_screen.dart';
import 'package:tideglass/cosmetics.dart';
import 'package:tideglass/cosmetics_screen.dart';
import 'package:tideglass/daily_panel.dart';
import 'package:tideglass/game_controller.dart';
import 'package:tideglass/native_services.dart';
import 'package:tideglass/notification_copy.dart';
import 'package:tideglass/notification_service.dart';
import 'package:tideglass/notification_settings.dart';
import 'package:tideglass/palette.dart';
import 'package:tideglass/presentation.dart';
import 'package:tideglass/season_screen.dart';
import 'package:tideglass/service_settings.dart';
import 'package:tideglass/story_screen.dart';
import 'package:tideglass/story_state.dart';
import 'package:tideglass/strings.dart';
import 'package:tideglass/support_screen.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_progression/tideglass_progression.dart';
import 'calibration_test.dart' show allPatterns;
import 'notification_service_test.dart'
    show FixtureNotificationGateway, MemoryReminderStore;
import 'service_settings_test.dart' show FixtureClient, MemoryCredentials;

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late StoryCatalogue catalogue;
  final now = DateTime.utc(2026, 10, 16, 12);
  setUpAll(() async {
    catalogue = await StoryCatalogue.load();
  });
  setUp(() {});
  GameController game({GameState? state, StoryProgress? story}) =>
      GameController(
        catalogue: catalogue,
        initialState: state,
        initialStory: story,
        clock: () => now,
        startTicker: false,
      );
  void viewport(WidgetTester tester) {
    tester.view.physicalSize = const Size(320, 720);
    tester.view.devicePixelRatio = 1;
    tester.platformDispatcher.textScaleFactorTestValue = 2;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
  }

  Future<void> show(
    WidgetTester tester,
    Widget child, {
    bool app = false,
  }) async {
    viewport(tester);
    await tester.pumpWidget(
      app ? child : MaterialApp(theme: tideglassTheme(), home: child),
    );
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
  }

  Future<void> tap(WidgetTester tester, Finder finder) async {
    if (find.byType(SnackBar).evaluate().isNotEmpty) {
      await tester.pump(const Duration(seconds: 5));
      await tester.pumpAndSettle();
    }
    await tester.ensureVisible(finder);
    await tester.tap(finder);
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
  }

  Finder key(String value) => find.byKey(ValueKey(value));
  Finder label(String english) => find.text(Presentation.text(english));

  test(
    'template expansion preserves exact prices, codes, identifiers and values',
    () {
      const price = 'USD 9.99 / ₺123,45';
      const secret = 'MiXeD-secret-1A2b';
      final english = Presentation.template(
        'Buy for {price}. Code {code}; {count} Charts.',
        {'price': price, 'code': secret, 'count': 10},
        pseudo: false,
      );
      expect(english, 'Buy for $price. Code $secret; 10 Charts.');
      final expanded = Presentation.template(
        'Buy for {price}. Code {code}; {count} Charts.',
        {'price': price, 'code': secret, 'count': 10},
        pseudo: true,
      );
      expect(expanded, startsWith('⟦'));
      expect(expanded, contains(price));
      expect(expanded, contains(secret));
      expect(expanded, contains('10'));
      expect(expanded, isNot(contains('{price}')));
      expect(Presentation.text(expanded, pseudo: true), expanded);
      expect(Presentation.text('42.5K / 10', pseudo: true), '42.5K / 10');
      expect(const NotificationCopy().pseudo, Presentation.pseudoEnabled);
    },
  );

  testWidgets(
    'actual first purchase and primary navigation fit expanded 200% text',
    (tester) async {
      final subject = game(
        state: const TideglassEngine()
            .advance(GameState.initial(), const Duration(seconds: 60))
            .state,
      );
      addTearDown(subject.dispose);
      await show(
        tester,
        TideglassApp(
          controller: subject,
          initialPreferences: const ClientPreferences(
            reduceMotion: true,
            onboardingDismissed: true,
          ),
        ),
        app: true,
      );
      expect(label(Copy.subtitle), findsOneWidget);
      await tap(tester, key('buy-0'));
      expect(subject.state.counts[0], 2);
      await tap(tester, find.byType(NavigationDestination).at(1));
      await tap(tester, find.byType(NavigationDestination).at(2));
      await tap(tester, key('open-season'));
      expect(find.byType(SeasonScreen), findsOneWidget);
      await tester.pageBack();
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'Rechart preview cancellation and confirmation preserve exact core meaning',
    (tester) async {
      final initial = GameState(
        counts: [40, 12, 0, 0, 0],
        walletMicros: BigInt.from(1000000000),
        lifetimeMicros: TideglassEngine.firstPrestigeMicros,
      );
      final subject = game(state: initial);
      addTearDown(subject.dispose);
      await show(
        tester,
        TideglassApp(
          controller: subject,
          initialPreferences: const ClientPreferences(
            reduceMotion: true,
            onboardingDismissed: true,
          ),
        ),
        app: true,
      );
      await tap(tester, find.byType(NavigationDestination).at(1));
      await tap(tester, key('preview-rechart'));
      await tap(tester, label(UiCopy.keepBuilding));
      expect(subject.state.charts, BigInt.zero);
      await tap(tester, key('preview-rechart'));
      await tap(tester, key('confirm-rechart'));
      expect(subject.state.charts, BigInt.from(10));
      expect(subject.state.lifetimeMicros, initial.lifetimeMicros);
      expect(subject.state.counts, [1, 0, 0, 0, 0]);
    },
  );

  testWidgets(
    'offline return acknowledgement and actual settings stay reachable',
    (tester) async {
      final subject = GameController(
        startTicker: false,
        settledThrough: now.subtract(const Duration(hours: 48)),
        clock: () => now,
      );
      addTearDown(subject.dispose);
      await show(
        tester,
        TideglassApp(
          controller: subject,
          initialPreferences: const ClientPreferences(
            reduceMotion: true,
            onboardingDismissed: true,
          ),
        ),
        app: true,
      );
      final before = subject.state.lifetimeMicros;
      await tap(tester, label(Copy.returnAcknowledge));
      expect(subject.returnReport, isNull);
      expect(subject.state.lifetimeMicros, before);
      await tap(tester, find.byTooltip(Presentation.text(Copy.settings)));
      await tap(tester, label(UiCopy.returnToTheHarbor));
    },
  );

  testWidgets(
    'authored calibration prose expands and accessible completion works once',
    (tester) async {
      final pattern = allPatterns().first;
      final before = pattern.title;
      final claims = <String>[];
      await show(
        tester,
        CalibrationScreen(
          patterns: [pattern],
          focusCharges: () => 1,
          collectedIds: () => {},
          onComplete: (id) {
            claims.add(id);
            return true;
          },
        ),
      );
      expect(label(pattern.title), findsOneWidget);
      await tap(tester, key('claim-accessible-calibration'));
      expect(claims, [pattern.id]);
      expect(pattern.title, before);
    },
  );

  testWidgets('campaign chapter prose and dossier opening remain navigable', (
    tester,
  ) async {
    final subject = game(
      state: GameState(surveyNotes: BigInt.from(150)),
      story: StoryProgress(
        campaign: CampaignProgress(
          completed: {'chapter.01', 'chapter.02', 'chapter.03'},
        ),
      ),
    );
    addTearDown(subject.dispose);
    final contentBefore = jsonEncode(catalogue.campaign.chapters);
    await show(tester, StoryScreen(game: subject));
    await tap(tester, key('story-tab-1'));
    await tap(tester, key('open-challenge.01'));
    await tap(tester, label(UiEnglish.storyOpenDossier));
    expect(subject.state.surveyNotes, BigInt.from(50));
    expect(subject.story.dossiers.owned, contains('challenge.01'));
    expect(jsonEncode(catalogue.campaign.chapters), contentBefore);
  });

  testWidgets(
    'season isolated fleet and free pass reward use expanded real templates',
    (tester) async {
      final subject = game(
        state: GameState(
          daily: DailyState(passXpById: {'pass.01': BigInt.from(30000)}),
        ),
      );
      addTearDown(subject.dispose);
      await show(tester, SeasonScreen(game: subject));
      await tap(tester, key('season-automatic'));
      expect(subject.story.season!.automatic, isTrue);
      await tap(tester, key('season-tab-1'));
      final reward = catalogue.seasonDefinition.rewards.firstWhere(
        (r) => r.track == 'free',
      );
      await tap(tester, key('claim-${reward.id}'));
      expect(subject.story.pass!.claims, contains(reward.id));
      expect(subject.state.charts, BigInt.zero);
    },
  );

  testWidgets(
    'cloud consent and retained recovery code use unmodified secret data',
    (tester) async {
      final client = FixtureClient();
      final manager = NativeServicesManager(
        client: client,
        credentials: MemoryCredentials(),
      );
      addTearDown(manager.dispose);
      await manager.initialize();
      await show(
        tester,
        ServiceSettings(
          manager: manager,
          onExportHarbor: () async => 'opaque-harbor-export',
          onImportHarbor: (_) async {},
        ),
      );
      await tap(tester, key('create-account'));
      expect(
        tester.widget<FilledButton>(key('create-account-confirm')).onPressed,
        isNull,
      );
      await tap(tester, key('cloud-consent'));
      await tap(tester, key('create-account-confirm'));
      expect(
        tester.widget<SelectableText>(key('new-recovery-code')).data,
        client.currentCode,
      );
      expect(manager.recoveryAcknowledged, isFalse);
      await tap(tester, key('recovery-retained'));
      await tap(tester, key('recovery-retained-confirm'));
      expect(manager.recoveryAcknowledged, isTrue);
      expect(client.calls, isNot(contains('upload')));
    },
  );

  testWidgets(
    'real store price stays exact inside expanded cosmetic purchase label',
    (tester) async {
      const price = 'USD 9.99 / ₺123,45';
      var purchases = 0;
      await show(
        tester,
        CosmeticsScreen(
          ownedIds: {},
          equippedId: null,
          onEquip: (_) {},
          offers: [
            CosmeticStoreOffer(
              productId: 'fixture',
              productTitle: 'Store title',
              localizedPrice: price,
              cosmeticIds: {'cosmetic.shop.01'},
            ),
          ],
          onPurchase: (_) async {
            purchases++;
          },
        ),
      );
      await tap(tester, key('cosmetic-filter-5'));
      final offer = key('purchase-cosmetic.shop.01-fixture');
      expect(find.textContaining(price), findsOneWidget);
      await tap(tester, offer);
      expect(purchases, 1);
    },
  );

  testWidgets(
    'Support briefing and automation save remain available at expanded size',
    (tester) async {
      final subject = game(
        state: GameState(
          charts: BigInt.from(100),
          lifetimeMicros: BigInt.from(10).pow(20),
        ),
      );
      addTearDown(subject.dispose);
      await show(tester, SupportScreen(game: subject));
      await tap(tester, key('open-briefing'));
      await tap(tester, key('complete-briefing'));
      expect(subject.state.support.tokens.length, 1);
      await tester.pumpWidget(
        MaterialApp(
          theme: tideglassTheme(),
          home: AutomationScreen(game: subject),
        ),
      );
      await tester.pumpAndSettle();
      await tap(tester, label(UiEnglish.dailySaveAndSelectPlan));
      expect(subject.state.automationPlans.length, 1);
    },
  );

  testWidgets(
    'notification default copy follows build mode without implicit permission',
    (tester) async {
      final gateway = FixtureNotificationGateway();
      final service = NotificationService(
        gateway: gateway,
        store: MemoryReminderStore(),
      );
      addTearDown(service.dispose);
      await service.initialize();
      await show(
        tester,
        Scaffold(
          body: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: NotificationSettings(service: service),
          ),
        ),
      );
      expect(
        find.text(const NotificationCopy().text('heading')),
        findsOneWidget,
      );
      expect(gateway.requests, 0);
      await tap(tester, key('reminder-enable'));
      expect(gateway.requests, 1);
      await tap(tester, key('reminder-quiet-start'));
      await tester.enterText(key('reminder-hour-input'), '21');
      await tap(tester, key('reminder-save-time'));
      expect(service.preferences.quietStart, 1260);
    },
  );
}

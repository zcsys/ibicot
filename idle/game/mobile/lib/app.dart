import 'dart:async';
import 'package:flutter/material.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'game_controller.dart';
import 'harbor_art.dart';
import 'number_format.dart';
import 'palette.dart';
import 'strings.dart';
import 'daily_panel.dart';
import 'story_screen.dart';
import 'support_screen.dart';
import 'season_screen.dart';
import 'audio_bus.dart';
import 'audio_settings.dart';
import 'producer_art.dart';
import 'cosmetic_art.dart';
import 'cosmetics_screen.dart';

class ClientPreferences {
  const ClientPreferences({
    this.reduceMotion = false,
    this.largeText = false,
    this.scientific = false,
    this.onboardingDismissed = false,
  });
  final bool reduceMotion, largeText, scientific, onboardingDismissed;
  ClientPreferences copyWith({
    bool? reduceMotion,
    bool? largeText,
    bool? scientific,
    bool? onboardingDismissed,
  }) => ClientPreferences(
    reduceMotion: reduceMotion ?? this.reduceMotion,
    largeText: largeText ?? this.largeText,
    scientific: scientific ?? this.scientific,
    onboardingDismissed: onboardingDismissed ?? this.onboardingDismissed,
  );
  Map<String, dynamic> toJson() => {
    'reduce_motion': reduceMotion,
    'large_text': largeText,
    'scientific': scientific,
    'onboarding_dismissed': onboardingDismissed,
  };
  factory ClientPreferences.fromJson(Map<String, dynamic> v) =>
      ClientPreferences(
        reduceMotion: v['reduce_motion'] == true,
        largeText: v['large_text'] == true,
        scientific: v['scientific'] == true,
        onboardingDismissed: v['onboarding_dismissed'] == true,
      );
}

class TideglassApp extends StatefulWidget {
  const TideglassApp({
    super.key,
    required this.controller,
    this.initialPreferences = const ClientPreferences(),
    this.onPreferencesChanged,
    this.onExport,
    this.onImport,
    this.recoveryNotice,
  });
  final GameController controller;
  final ClientPreferences initialPreferences;
  final Future<void> Function(ClientPreferences)? onPreferencesChanged;
  final Future<String> Function()? onExport;
  final Future<void> Function(String)? onImport;
  final String? recoveryNotice;
  @override
  State<TideglassApp> createState() => _TideglassAppState();
}

class _TideglassAppState extends State<TideglassApp>
    with WidgetsBindingObserver, SingleTickerProviderStateMixin {
  late ClientPreferences prefs;
  late AnimationController animation;
  int tab = 0;
  final fleetKey = GlobalKey();
  bool returnVisible = false, recoveryDismissed = false;
  GameController get game => widget.controller;
  @override
  void initState() {
    super.initState();
    prefs = widget.initialPreferences;
    animation = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 8),
    )..repeat();
    WidgetsBinding.instance.addObserver(this);
    game.addListener(_changed);
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      unawaited(game.resumeWithProgress());
    } else if (state == AppLifecycleState.inactive ||
        state == AppLifecycleState.paused ||
        state == AppLifecycleState.detached) {
      game.suspend();
    }
  }

  void _changed() {
    if (mounted) setState(() {});
  }

  @override
  void dispose() {
    game.removeListener(_changed);
    animation.dispose();
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  void updatePrefs(ClientPreferences value) {
    setState(() => prefs = value);
    if (widget.onPreferencesChanged != null) {
      unawaited(widget.onPreferencesChanged!(value));
    }
  }

  void begin() {
    updatePrefs(prefs.copyWith(onboardingDismissed: true));
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final target = fleetKey.currentContext;
      if (target != null) {
        Scrollable.ensureVisible(
          target,
          alignment: 0,
          duration: prefs.reduceMotion
              ? Duration.zero
              : const Duration(milliseconds: 350),
        );
      }
    });
  }

  String number(BigInt n) => compactMicros(n, scientific: prefs.scientific);
  String rate(Fixed n) => compactFixed(n, scientific: prefs.scientific);
  @override
  Widget build(BuildContext context) => MaterialApp(
    title: Copy.title,
    debugShowCheckedModeBanner: false,
    theme: tideglassTheme(),
    builder: (context, child) {
      final media = MediaQuery.of(context);
      return MediaQuery(
        data: media.copyWith(
          disableAnimations: media.disableAnimations || prefs.reduceMotion,
          textScaler: TextScaler.linear(
            media.textScaler.scale(1) * (prefs.largeText ? 1.2 : 1),
          ),
        ),
        child: Stack(
          children: [
            child!,
            if (game.replaying || game.replayError != null) ...[
              const ModalBarrier(dismissible: false, color: Color(0xE80A1A24)),
              Center(
                child: Material(
                  color: Colors.transparent,
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 420),
                    child: Padding(
                      padding: const EdgeInsets.all(28),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          if (game.replaying)
                            CircularProgressIndicator(
                              value: game.replayProgress?.fraction,
                            ),
                          const SizedBox(height: 20),
                          Text(
                            game.replayError ?? 'Gathering your time away…',
                            textAlign: TextAlign.center,
                          ),
                          if (game.replayProgress != null &&
                              game.replayError == null)
                            Text(
                              '${(game.replayProgress!.fraction * 100).floor()}%',
                            ),
                          if (game.replayError != null)
                            Padding(
                              padding: const EdgeInsets.only(top: 16),
                              child: FilledButton(
                                onPressed: game.resumeWithProgress,
                                child: const Text('Try again'),
                              ),
                            ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ],
        ),
      );
    },
    home: Builder(
      builder: (context) {
        final returned = game.returnReport;
        if (returned != null && !returnVisible) {
          returnVisible = true;
          WidgetsBinding.instance.addPostFrameCallback((_) async {
            if (!mounted) return;
            await showDialog<void>(
              context: context,
              builder: (dialog) => _returnDialog(dialog, returned),
            );
            if (!mounted) return;
            game.acknowledgeReturn();
            returnVisible = false;
          });
        }
        final reduced =
            prefs.reduceMotion || MediaQuery.disableAnimationsOf(context);
        if (reduced && animation.isAnimating) animation.stop();
        if (!reduced && !animation.isAnimating) animation.repeat();
        return Scaffold(
          appBar: AppBar(
            backgroundColor: TideColors.deep,
            surfaceTintColor: Colors.transparent,
            toolbarHeight: 80,
            titleSpacing: 24,
            title: Row(
              children: [
                const Icon(
                  Icons.auto_awesome_outlined,
                  color: TideColors.amber,
                  size: 26,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        Copy.title,
                        style: Theme.of(
                          context,
                        ).textTheme.titleLarge?.copyWith(letterSpacing: 2),
                      ),
                      const Text(
                        Copy.subtitle,
                        style: TextStyle(color: TideColors.muted, fontSize: 11),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            actions: [
              IconButton(
                tooltip: Copy.settings,
                onPressed: () => _settings(context),
                icon: const Icon(Icons.tune_rounded),
              ),
              const SizedBox(width: 12),
            ],
          ),
          body: SafeArea(
            top: false,
            child: Column(
              children: [
                if (game.saveError != null) _saveWarning(),
                if (widget.recoveryNotice != null && !recoveryDismissed)
                  _notice(
                    widget.recoveryNotice!,
                    () => setState(() => recoveryDismissed = true),
                  ),
                Expanded(
                  child: IndexedStack(
                    index: tab,
                    children: [
                      _harbor(context),
                      _atlas(context),
                      _journal(context),
                    ],
                  ),
                ),
              ],
            ),
          ),
          bottomNavigationBar: NavigationBar(
            selectedIndex: tab,
            onDestinationSelected: (v) => setState(() => tab = v),
            destinations: const [
              NavigationDestination(
                icon: Icon(Icons.water_outlined),
                selectedIcon: Icon(Icons.water),
                label: Copy.harbor,
              ),
              NavigationDestination(
                icon: Icon(Icons.explore_outlined),
                selectedIcon: Icon(Icons.explore),
                label: Copy.atlas,
              ),
              NavigationDestination(
                icon: Icon(Icons.menu_book_outlined),
                selectedIcon: Icon(Icons.menu_book),
                label: Copy.journal,
              ),
            ],
          ),
        );
      },
    ),
  );

  Widget _harbor(BuildContext context) => LayoutBuilder(
    builder: (context, constraints) {
      final illustration = Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _stats(context),
          const SizedBox(height: 20),
          AnimatedBuilder(
            animation: animation,
            builder: (context, _) => ClipRRect(
              borderRadius: BorderRadius.circular(22),
              child: Stack(
                children: [
                  HarborArt(
                    counts: game.state.counts,
                    phase: animation.value,
                    restoration: game.story.campaign.restoredHarbor,
                    decoration: game.story.equippedDecoration,
                  ),
                  if (game.visibleAppearance != null)
                    Positioned.fill(
                      child: CosmeticOverlay(
                        id: game.visibleAppearance!,
                        phase: animation.value,
                      ),
                    ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),
          Wrap(
            alignment: WrapAlignment.spaceBetween,
            spacing: 12,
            runSpacing: 4,
            children: [
              Text(
                game.state.charts == BigInt.zero
                    ? UiCopy.theFirstLight
                    : UiCopy.aWiderSky,
                style: Theme.of(
                  context,
                ).textTheme.labelSmall?.copyWith(color: TideColors.amber),
              ),
              Text(
                UiCopy.lightkeeperCount(
                  game.state.counts.fold<int>(0, (a, b) => a + b),
                ),
                style: const TextStyle(color: TideColors.muted, fontSize: 12),
              ),
            ],
          ),
          const SizedBox(height: 22),
          if (!prefs.onboardingDismissed)
            _panel(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    Copy.introduction,
                    style: Theme.of(
                      context,
                    ).textTheme.titleMedium?.copyWith(color: TideColors.amber),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    Copy.introductionBody,
                    style: TextStyle(color: TideColors.muted),
                  ),
                  const SizedBox(height: 12),
                  TextButton(
                    onPressed: begin,
                    child: const Text(Copy.introductionDismiss),
                  ),
                ],
              ),
            ),
          if (game.state.charts >= BigInt.from(10))
            _panel(
              child: SwitchListTile.adaptive(
                contentPadding: EdgeInsets.zero,
                title: const Text(UiCopy.letTheFleetBuild),
                subtitle: const Text(UiCopy.bestPaybackIncludingWhileYouAre),
                value: game.state.autoBuyEnabled,
                onChanged: game.setAutoBuy,
              ),
            ),
        ],
      );
      final fleet = Column(
        key: fleetKey,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(Copy.fleet, style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 4),
          const Text(
            Copy.fleetHint,
            style: TextStyle(color: TideColors.muted, fontSize: 13),
          ),
          const SizedBox(height: 18),
          SegmentedButton<PurchaseMode>(
            showSelectedIcon: false,
            segments: const [
              ButtonSegment(
                value: PurchaseMode.single,
                label: Text(UiCopy.buy),
              ),
              ButtonSegment(
                value: PurchaseMode.milestone,
                label: Text('Milestone'),
              ),
              ButtonSegment(
                value: PurchaseMode.maximum,
                label: Text(UiCopy.buyMax),
              ),
            ],
            selected: {game.purchaseMode},
            onSelectionChanged: (v) => game.selectPurchaseMode(v.first),
          ),
          const SizedBox(height: 16),
          for (var i = 0; i < 5; i++)
            Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: _producer(context, i),
            ),
          const SizedBox(height: 8),
          const Text(
            UiCopy.forecastsAssumeAFixedFleetAnd,
            style: TextStyle(color: TideColors.muted, fontSize: 12),
          ),
          const SizedBox(height: 24),
        ],
      );
      return SingleChildScrollView(
        key: const PageStorageKey('harbor-scroll'),
        padding: const EdgeInsets.fromLTRB(24, 8, 24, 24),
        child: Center(
          child: ConstrainedBox(
            constraints: BoxConstraints(
              maxWidth: constraints.maxWidth >= 900 ? 1260 : 640,
            ),
            child: constraints.maxWidth >= 900
                ? Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(child: illustration),
                      const SizedBox(width: 32),
                      Expanded(child: fleet),
                    ],
                  )
                : Column(children: [illustration, fleet]),
          ),
        ),
      );
    },
  );
  Widget _stats(BuildContext context) => _panel(
    child: LayoutBuilder(
      builder: (context, box) {
        final first = Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              Copy.radiance,
              style: Theme.of(
                context,
              ).textTheme.labelSmall?.copyWith(color: TideColors.muted),
            ),
            const SizedBox(height: 6),
            Text(
              number(game.state.walletMicros),
              key: const ValueKey('wallet'),
              style: Theme.of(
                context,
              ).textTheme.headlineMedium?.copyWith(color: TideColors.amber),
            ),
          ],
        );
        final second = Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              Copy.rate,
              style: Theme.of(
                context,
              ).textTheme.labelSmall?.copyWith(color: TideColors.muted),
            ),
            const SizedBox(height: 6),
            Text(
              '+${rate(game.engine.activeOutputPerSecond(game.state))}',
              style: Theme.of(
                context,
              ).textTheme.titleLarge?.copyWith(color: TideColors.teal),
            ),
          ],
        );
        return MediaQuery.textScalerOf(context).scale(1) > 1.5
            ? Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [first, const SizedBox(height: 16), second],
              )
            : Row(
                children: [
                  Expanded(child: first),
                  Container(width: 1, height: 44, color: TideColors.line),
                  const SizedBox(width: 18),
                  Expanded(child: second),
                ],
              );
      },
    ),
  );
  Widget _producer(BuildContext context, int tier) {
    final s = game.state,
        unlocked = game.engine.isUnlocked(game.state, tier),
        quantity = game.quantityFor(tier),
        canBuy = game.canBuy(tier);
    final forecast = game.engine.waitForPurchase(
          s,
          tier,
          quantity: quantity > 0 ? quantity : 1,
        ),
        nextMilestone = ((s.counts[tier] ~/ 25) + 1) * 25;
    return Container(
      key: ValueKey('producer-$tier'),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: TideColors.panel,
        border: Border.all(color: TideColors.line),
        borderRadius: BorderRadius.circular(18),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              StagedProducerArt(
                tier: tier,
                count: s.counts[tier],
                locked: !unlocked,
                size: 58,
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      TideglassEngine.producerNames[tier],
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        color: unlocked ? TideColors.text : TideColors.muted,
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      unlocked
                          ? '${s.counts[tier]} at work · ${rate(game.engine.producerOutputPerSecond(s, tier))} R/s'
                          : UiCopy.undiscoveredLightkeeper,
                      style: const TextStyle(
                        color: TideColors.muted,
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
              ),
              if (!unlocked)
                const Icon(
                  Icons.lock_outline,
                  size: 18,
                  color: TideColors.muted,
                ),
            ],
          ),
          if (unlocked) ...[
            const SizedBox(height: 12),
            if (s.counts[tier] < 100) ...[
              ClipRRect(
                borderRadius: BorderRadius.circular(2),
                child: LinearProgressIndicator(
                  minHeight: 3,
                  value: (s.counts[tier] % 25) / 25,
                  backgroundColor: TideColors.line,
                  color: TideColors.teal.withValues(alpha: .65),
                ),
              ),
              const SizedBox(height: 7),
              Text(
                '$nextMilestone lightkeepers → double this tier',
                style: const TextStyle(color: TideColors.muted, fontSize: 11),
              ),
            ] else
              const Text(
                UiCopy.allFourMilestonesIlluminated,
                style: TextStyle(color: TideColors.amber, fontSize: 11),
              ),
            const SizedBox(height: 14),
            Wrap(
              alignment: WrapAlignment.spaceBetween,
              crossAxisAlignment: WrapCrossAlignment.center,
              spacing: 12,
              runSpacing: 10,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '${number(game.priceFor(tier))} R',
                      style: const TextStyle(
                        color: TideColors.amber,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    Text(
                      canBuy
                          ? '+${rate(game.engine.marginalOutputPerSecond(s, tier, quantity: quantity))} network R/s'
                          : forecast == null
                          ? UiCopy.aDistantHorizon
                          : 'Ready in ${durationLabel(forecast)}',
                      style: const TextStyle(
                        color: TideColors.muted,
                        fontSize: 11,
                      ),
                    ),
                  ],
                ),
                SizedBox(
                  width: 134,
                  child: FilledButton(
                    key: ValueKey('buy-$tier'),
                    onPressed: canBuy ? () => _buy(context, tier) : null,
                    style: FilledButton.styleFrom(
                      backgroundColor: TideColors.teal.withValues(alpha: .14),
                      foregroundColor: TideColors.teal,
                      disabledBackgroundColor: TideColors.raised,
                      disabledForegroundColor: TideColors.muted,
                    ),
                    child: Text(
                      canBuy ? 'Build $quantity' : UiCopy.gathering,
                      textAlign: TextAlign.center,
                    ),
                  ),
                ),
              ],
            ),
          ] else ...[
            const SizedBox(height: 12),
            Text(
              'Needs 10 ${TideglassEngine.producerNames[tier - 1]}',
              style: const TextStyle(color: TideColors.muted, fontSize: 12),
            ),
          ],
        ],
      ),
    );
  }

  void _buy(BuildContext context, int tier) {
    if (game.buy(tier)) {
      ScaffoldMessenger.of(context)
        ..hideCurrentSnackBar()
        ..showSnackBar(
          SnackBar(
            duration: const Duration(seconds: 2),
            content: Text(game.lastAction!),
          ),
        );
    }
  }

  Widget _atlas(BuildContext context) {
    final claim = game.engine.prestigeAward(game.state),
        eligible = game.engine.prestigeAward(game.state) > BigInt.zero;
    return _page(
      children: [
        const SizedBox(height: 12),
        const Icon(Icons.explore_outlined, size: 48, color: TideColors.amber),
        const SizedBox(height: 18),
        Text(Copy.rechart, style: Theme.of(context).textTheme.headlineMedium),
        const SizedBox(height: 8),
        const Text(Copy.rechartBody, style: TextStyle(color: TideColors.muted)),
        const SizedBox(height: 28),
        _panel(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Text(
                UiCopy.yourPermanentAtlas,
                style: TextStyle(
                  color: TideColors.muted,
                  fontSize: 11,
                  letterSpacing: 1.5,
                ),
              ),
              const SizedBox(height: 12),
              Text(
                '${game.state.charts} Charts',
                style: Theme.of(
                  context,
                ).textTheme.headlineLarge?.copyWith(color: TideColors.amber),
              ),
              const SizedBox(height: 12),
              const Text(Copy.rechartHint),
              const SizedBox(height: 20),
              const Divider(),
              const SizedBox(height: 20),
              _dataRow(
                UiCopy.permanentPower,
                '${game.engine.prestigeMultiplier(game.state.charts).toDecimalString(decimals: 2)}×',
              ),
              const SizedBox(height: 12),
              _dataRow(
                UiCopy.lifetimeRadiance,
                '${number(game.state.lifetimeMicros)} R',
              ),
              const SizedBox(height: 12),
              _dataRow(
                UiCopy.newChartsAvailable,
                eligible ? '+$claim' : UiCopy.notYet,
              ),
              const SizedBox(height: 20),
              FilledButton(
                key: const ValueKey('preview-rechart'),
                onPressed: eligible
                    ? () => _confirmRechart(context, claim)
                    : null,
                child: Text(
                  eligible
                      ? 'Preview Rechart · +$claim Charts'
                      : UiCopy.gatherTheFirstBillion,
                ),
              ),
              const SizedBox(height: 12),
              Text(
                eligible ? Copy.noPerfectReset : Copy.firstRechartHint,
                style: const TextStyle(color: TideColors.muted, fontSize: 12),
              ),
            ],
          ),
        ),
        const SizedBox(height: 22),
        Text(
          UiCopy.anAtlasThatGrowsWithYou,
          style: Theme.of(context).textTheme.titleLarge,
        ),
        const SizedBox(height: 16),
        _unlock(
          UiCopy.charts,
          UiCopy.aSelfBuildingFleet,
          UiCopy.freeAutomaticBuyingForEveryProducer,
          BigInt.from(10),
        ),
        _unlock(
          UiCopy.chartsText,
          UiCopy.aConnectedOcean,
          UiCopy.skiffsAndNurseriesStrengthenLoomsAnd,
          BigInt.from(25),
        ),
      ],
    );
  }

  Widget _unlock(
    String threshold,
    String title,
    String description,
    BigInt charts,
  ) => Padding(
    padding: const EdgeInsets.only(bottom: 18),
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(
          game.state.charts >= charts
              ? Icons.check_circle_outline
              : Icons.radio_button_unchecked,
          color: game.state.charts >= charts
              ? TideColors.teal
              : TideColors.muted,
          size: 22,
        ),
        const SizedBox(width: 14),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                threshold,
                style: const TextStyle(color: TideColors.amber, fontSize: 11),
              ),
              const SizedBox(height: 3),
              Text(title, style: const TextStyle(fontWeight: FontWeight.w600)),
              const SizedBox(height: 4),
              Text(
                description,
                style: const TextStyle(color: TideColors.muted, fontSize: 13),
              ),
            ],
          ),
        ),
      ],
    ),
  );
  Future<void> _confirmRechart(
    BuildContext context,
    BigInt claim,
  ) => showDialog<void>(
    context: context,
    builder: (dialog) => AlertDialog(
      title: const Text(UiCopy.chartABrighterOcean),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Claim $claim new Charts',
              style: const TextStyle(color: TideColors.amber, fontSize: 23),
            ),
            const SizedBox(height: 12),
            Text(
              'Permanent power: ${game.engine.prestigeMultiplier(game.state.charts).toDecimalString(decimals: 2)}× → ${game.engine.prestigeMultiplier(game.state.charts + claim).toDecimalString(decimals: 2)}×',
            ),
            const SizedBox(height: 18),
            const Text(Copy.rechartLost),
            const SizedBox(height: 12),
            const Text(Copy.rechartKept),
            const SizedBox(height: 12),
            const Text(
              UiCopy.yourCurrentFleetStopsEarningAs,
              style: TextStyle(color: TideColors.muted),
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(dialog),
          child: const Text(UiCopy.keepBuilding),
        ),
        FilledButton(
          key: const ValueKey('confirm-rechart'),
          onPressed: () {
            game.rechart();
            Navigator.pop(dialog);
            setState(() => tab = 0);
          },
          child: const Text(UiCopy.rechart),
        ),
      ],
    ),
  );
  Widget _journal(BuildContext context) => _page(
    children: [
      Text(
        UiCopy.theKeeperSLogbook,
        style: Theme.of(context).textTheme.headlineMedium,
      ),
      const SizedBox(height: 10),
      const Text(
        UiCopy.smallDiscoveriesKeptForTheNext,
        style: TextStyle(color: TideColors.muted),
      ),
      const SizedBox(height: 28),
      if (game.catalogue != null)
        Padding(
          padding: const EdgeInsets.only(bottom: 18),
          child: FilledButton.icon(
            key: const ValueKey('open-story'),
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute<void>(builder: (_) => StoryScreen(game: game)),
            ),
            icon: const Icon(Icons.auto_awesome_outlined),
            label: Text(
              'Restoration · ${game.story.campaign.restoredHarbor} / 6',
            ),
          ),
        ),
      Padding(
        padding: const EdgeInsets.only(bottom: 18),
        child: OutlinedButton.icon(
          onPressed: () => Navigator.of(context).push(
            MaterialPageRoute<void>(builder: (_) => SupportScreen(game: game)),
          ),
          icon: const Icon(Icons.handshake_outlined),
          label: const Text('Crew support'),
        ),
      ),
      if (game.story.season != null)
        Padding(
          padding: const EdgeInsets.only(bottom: 18),
          child: OutlinedButton.icon(
            key: const ValueKey('open-season'),
            onPressed: () => _openSeason(context),
            icon: const Icon(Icons.nights_stay_outlined),
            label: Text(game.catalogue!.seasonDefinition.title),
          ),
        ),
      Padding(
        padding: const EdgeInsets.only(bottom: 18),
        child: OutlinedButton.icon(
          key: const ValueKey('open-cosmetics'),
          onPressed: () => _openCosmetics(context),
          icon: const Icon(Icons.palette_outlined),
          label: const Text('Harbor appearances'),
        ),
      ),
      _daily(context),
      _panel(child: ContractPanel(game: game)),
      if (game.state.charts >= BigInt.from(10))
        Padding(
          padding: const EdgeInsets.only(bottom: 20),
          child: OutlinedButton.icon(
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute<void>(
                builder: (_) => AutomationScreen(game: game),
              ),
            ),
            icon: const Icon(Icons.route_outlined),
            label: const Text('Edit the crew’s automation plan'),
          ),
        ),
      _panel(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              UiCopy.aLightLeftOn,
              style: TextStyle(
                color: TideColors.amber,
                fontSize: 11,
                letterSpacing: 1.5,
              ),
            ),
            const SizedBox(height: 16),
            const Text(UiCopy.theOceanDidNotForgetIts),
            const SizedBox(height: 12),
            const Text(
              UiCopy.oneSkiffOneLanternEnoughTo,
              style: TextStyle(color: TideColors.muted),
            ),
            const SizedBox(height: 12),
            TextButton(
              onPressed: () {
                game.readArchive('archive.intro');
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text(
                      'An archive interaction recorded for your crew contracts.',
                    ),
                  ),
                );
              },
              child: const Text('Reflect on this entry'),
            ),
          ],
        ),
      ),
      const SizedBox(height: 24),
      Text(Copy.help, style: Theme.of(context).textTheme.titleLarge),
      const SizedBox(height: 16),
      _help(UiCopy.whileYouAreAway, Copy.offlineHelp, Icons.bedtime_outlined),
      _help(
        UiCopy.aGrowingFleet,
        Copy.milestoneHelp,
        Icons.auto_awesome_outlined,
      ),
      _help(UiCopy.aPermanentAtlas, Copy.rechartKept, Icons.explore_outlined),
      const SizedBox(height: 18),
      Text(
        game.hasPersistence
            ? UiCopy.yourHarborIsSavedOnThis
            : UiCopy.sessionPreviewLocalSavingIsNot,
        style: const TextStyle(color: TideColors.muted, fontSize: 12),
      ),
      if (widget.onExport != null) ...[
        const SizedBox(height: 12),
        OutlinedButton.icon(
          onPressed: () => _export(context),
          icon: const Icon(Icons.file_upload_outlined),
          label: const Text(UiCopy.exportMyHarbor),
        ),
      ],
      if (widget.onImport != null) ...[
        const SizedBox(height: 12),
        OutlinedButton.icon(
          onPressed: () => _import(context),
          icon: const Icon(Icons.file_download_outlined),
          label: const Text(UiCopy.importASavedHarbor),
        ),
      ],
      const SizedBox(height: 12),
      TextButton(
        onPressed: () => showLicensePage(
          context: context,
          applicationName: Copy.title,
          applicationVersion: '0.1.0',
        ),
        child: const Text(UiCopy.openSourceLicenses),
      ),
    ],
  );
  Widget _daily(BuildContext context) => _panel(
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          UiCopy.theHarborSRhythm,
          style: Theme.of(context).textTheme.titleLarge,
        ),
        const SizedBox(height: 14),
        _dataRow(UiCopy.focusStored, '${game.state.focusCharges} / 12'),
        const SizedBox(height: 8),
        const Text(
          UiCopy.oneChargeEveryTwoHoursEach,
          style: TextStyle(color: TideColors.muted, fontSize: 12),
        ),
        if (game.state.focusRemainingMicros > BigInt.zero) ...[
          const SizedBox(height: 8),
          Text(
            'Focused for ${durationLabel(Duration(microseconds: game.state.focusRemainingMicros.toInt()))}',
            style: const TextStyle(color: TideColors.teal),
          ),
        ],
        const SizedBox(height: 12),
        OutlinedButton(
          key: const ValueKey('activate-focus'),
          onPressed: () => openCalibration(context, game),
          child: const Text(UiCopy.focusTheConstellation),
        ),
        const SizedBox(height: 22),
        _dataRow(UiCopy.surveysComplete, '${game.state.completedSurveys} / 3'),
        const SizedBox(height: 8),
        const Text(
          UiCopy.oneSurveyEveryEightHoursUp,
          style: TextStyle(color: TideColors.muted, fontSize: 12),
        ),
        const SizedBox(height: 12),
        OutlinedButton(
          key: const ValueKey('collect-surveys'),
          onPressed: game.state.completedSurveys > 0
              ? game.collectSurveys
              : null,
          child: Text('Collect ${game.state.completedSurveys * 10} Notes'),
        ),
        const SizedBox(height: 12),
        _dataRow(UiCopy.surveyNotes, game.state.surveyNotes.toString()),
      ],
    ),
  );
  Future<void> _openSeason(BuildContext context) async {
    final audio = game.audio;
    if (audio != null) unawaited(audio.startMusic(TideMusic.current));
    await Navigator.of(
      context,
    ).push(MaterialPageRoute<void>(builder: (_) => SeasonScreen(game: game)));
    if (mounted && audio != null) {
      unawaited(
        audio.startMusic(
          game.story.campaign.hasEnding ? TideMusic.dawn : TideMusic.harbor,
        ),
      );
    }
  }

  Future<void> _openCosmetics(BuildContext context) =>
      Navigator.of(context).push(
        MaterialPageRoute<void>(
          builder: (_) => ListenableBuilder(
            listenable: game,
            builder: (context, _) => CosmeticsScreen(
              ownedIds: game.ownedCosmetics,
              equippedId: game.visibleAppearance,
              equippedDecorationId: game.story.equippedDecoration,
              onEquip: game.equipCosmetic,
              onUnequipDecoration: game.unequipDecoration,
              onBuyDecoration: game.buyDecoration,
              notes: game.state.surveyNotes > BigInt.from(1000000000)
                  ? 1000000000
                  : game.state.surveyNotes.toInt(),
              previewCounts: game.state.counts,
              restoration: game.story.campaign.restoredHarbor,
            ),
          ),
        ),
      );

  Widget _help(String title, String body, IconData icon) => Padding(
    padding: const EdgeInsets.only(bottom: 22),
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, color: TideColors.teal, size: 22),
        const SizedBox(width: 14),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title, style: const TextStyle(fontWeight: FontWeight.w600)),
              const SizedBox(height: 6),
              Text(
                body,
                style: const TextStyle(color: TideColors.muted, fontSize: 13),
              ),
            ],
          ),
        ),
      ],
    ),
  );
  Widget _returnDialog(
    BuildContext context,
    ReturnReport report,
  ) => AlertDialog(
    title: const Text(Copy.returnTitle),
    content: SingleChildScrollView(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(Copy.returnBody),
          const SizedBox(height: 20),
          Text(
            '+${number(report.earnedMicros)} R',
            style: const TextStyle(color: TideColors.amber, fontSize: 30),
          ),
          const SizedBox(height: 20),
          _dataRow(UiCopy.timeAway, durationLabel(report.absence)),
          const SizedBox(height: 12),
          _dataRow(UiCopy.atFullRate, durationLabel(report.fullRate)),
          if (report.quarterRate > Duration.zero) ...[
            const SizedBox(height: 12),
            _dataRow(UiCopy.atQuarterRate, durationLabel(report.quarterRate)),
          ],
          if (report.uncredited > Duration.zero) ...[
            const SizedBox(height: 12),
            _dataRow(UiCopy.beyondStorage, durationLabel(report.uncredited)),
          ],
          const SizedBox(height: 16),
          Text(
            report.automated
                ? UiCopy.yourSavedAutomaticBuyingPolicyWas
                : UiCopy.yourFleetCompositionRemainedUnchanged,
            style: const TextStyle(color: TideColors.muted, fontSize: 12),
          ),
          const SizedBox(height: 12),
          const Text(
            UiCopy.alreadyAddedToYourHarbor,
            style: TextStyle(color: TideColors.teal, fontSize: 12),
          ),
        ],
      ),
    ),
    actions: [
      FilledButton(
        onPressed: () => Navigator.pop(context),
        child: const Text(Copy.returnAcknowledge),
      ),
    ],
  );
  Future<void> _settings(BuildContext context) => showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    showDragHandle: true,
    builder: (context) => StatefulBuilder(
      builder: (context, refresh) => SafeArea(
        child: SingleChildScrollView(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(24, 0, 24, 24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text(
                  Copy.settings,
                  style: Theme.of(context).textTheme.headlineMedium,
                ),
                const SizedBox(height: 16),
                SwitchListTile.adaptive(
                  contentPadding: EdgeInsets.zero,
                  title: const Text(Copy.reducedMotion),
                  subtitle: const Text(Copy.reducedMotionHint),
                  value: prefs.reduceMotion,
                  onChanged: (v) {
                    updatePrefs(prefs.copyWith(reduceMotion: v));
                    refresh(() {});
                  },
                ),
                SwitchListTile.adaptive(
                  contentPadding: EdgeInsets.zero,
                  title: const Text(Copy.largerText),
                  subtitle: const Text(Copy.largerTextHint),
                  value: prefs.largeText,
                  onChanged: (v) {
                    updatePrefs(prefs.copyWith(largeText: v));
                    refresh(() {});
                  },
                ),
                SwitchListTile.adaptive(
                  contentPadding: EdgeInsets.zero,
                  title: const Text(Copy.scientific),
                  subtitle: const Text(Copy.scientificHint),
                  value: prefs.scientific,
                  onChanged: (v) {
                    updatePrefs(prefs.copyWith(scientific: v));
                    refresh(() {});
                  },
                ),
                const SizedBox(height: 16),
                const Text(
                  UiCopy.yourDeviceSReducedMotionAnd,
                  style: TextStyle(color: TideColors.muted, fontSize: 12),
                ),
                const SizedBox(height: 24),
                if (game.audio != null) ...[
                  AudioSettings(audio: game.audio!),
                  const SizedBox(height: 24),
                ],
                FilledButton(
                  onPressed: () => Navigator.pop(context),
                  child: const Text(UiCopy.returnToTheHarbor),
                ),
              ],
            ),
          ),
        ),
      ),
    ),
  );
  Future<void> _import(BuildContext context) async {
    final text = TextEditingController();
    final backup = await showDialog<String>(
      context: context,
      builder: (dialog) => AlertDialog(
        title: const Text(UiCopy.chooseASavedHarbor),
        content: SizedBox(
          width: 500,
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(UiCopy.importReplacesThisDeviceSCurrent),
                const SizedBox(height: 18),
                TextField(
                  key: const ValueKey('import-save-text'),
                  controller: text,
                  minLines: 5,
                  maxLines: 10,
                  decoration: const InputDecoration(
                    labelText: UiCopy.pasteYourExportedHarbor,
                    border: OutlineInputBorder(),
                  ),
                ),
              ],
            ),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialog),
            child: const Text(UiCopy.keepThisHarbor),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(dialog, text.text.trim()),
            child: const Text(UiCopy.replaceLocalHarbor),
          ),
        ],
      ),
    );
    text.dispose();
    if (backup == null || backup.isEmpty) return;
    try {
      await widget.onImport!(backup);
    } catch (_) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text(UiCopy.thisHarborCouldNotBeImported)),
        );
      }
    }
  }

  Future<void> _export(BuildContext context) async {
    try {
      final value = await widget.onExport!();
      if (!context.mounted) return;
      await showDialog<void>(
        context: context,
        builder: (dialog) => AlertDialog(
          title: const Text(UiCopy.yourHarborBackup),
          content: SizedBox(
            width: 500,
            child: SingleChildScrollView(child: SelectableText(value)),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialog),
              child: const Text(UiCopy.done),
            ),
          ],
        ),
      );
    } catch (_) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text(UiCopy.theBackupCouldNotBeExported)),
        );
      }
    }
  }

  Widget _saveWarning() => Material(
    color: TideColors.warning.withValues(alpha: .14),
    child: Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Row(
        children: [
          const Icon(Icons.warning_amber_rounded, color: TideColors.warning),
          const SizedBox(width: 12),
          const Expanded(child: Text(Copy.saveFailed)),
          TextButton(onPressed: game.save, child: const Text('Retry')),
        ],
      ),
    ),
  );
  Widget _notice(String text, VoidCallback dismiss) => Material(
    color: TideColors.raised,
    child: Padding(
      padding: const EdgeInsets.only(left: 16),
      child: Row(
        children: [
          Expanded(child: Text(text)),
          IconButton(
            onPressed: dismiss,
            tooltip: UiCopy.dismissRecoveryNotice,
            icon: const Icon(Icons.close),
          ),
        ],
      ),
    ),
  );
  Widget _page({required List<Widget> children}) => SingleChildScrollView(
    padding: const EdgeInsets.fromLTRB(24, 12, 24, 32),
    child: Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 680),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: children,
        ),
      ),
    ),
  );
  Widget _panel({required Widget child}) => Container(
    width: double.infinity,
    margin: const EdgeInsets.only(bottom: 16),
    padding: const EdgeInsets.all(20),
    decoration: BoxDecoration(
      color: TideColors.panel,
      border: Border.all(color: TideColors.line),
      borderRadius: BorderRadius.circular(18),
    ),
    child: Material(color: Colors.transparent, child: child),
  );
  Widget _dataRow(String label, String value) => Wrap(
    alignment: WrapAlignment.spaceBetween,
    spacing: 20,
    runSpacing: 4,
    children: [
      Text(label, style: const TextStyle(color: TideColors.muted)),
      Text(value, style: const TextStyle(fontWeight: FontWeight.w600)),
    ],
  );
}

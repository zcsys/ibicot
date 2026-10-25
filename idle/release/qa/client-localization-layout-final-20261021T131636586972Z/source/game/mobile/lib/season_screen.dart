import 'presentation.dart';
import 'strings.dart';
import 'package:flutter/material.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_events/tideglass_events.dart';
import 'game_controller.dart';
import 'harbor_art.dart';
import 'number_format.dart';
import 'palette.dart';
import 'cosmetic_art.dart';
import 'producer_art.dart';
import 'native_services.dart';
import 'service_cosmetics.dart';

/// Seasonal presentation has no local award or entitlement state.
class SeasonScreen extends StatefulWidget {
  const SeasonScreen({
    super.key,
    required this.game,
    this.initialTab = 0,
    this.services,
  });
  final GameController game;
  final int initialTab;
  final NativeServicesManager? services;
  @override
  State<SeasonScreen> createState() => _SeasonScreenState();
}

class _SeasonScreenState extends State<SeasonScreen> {
  GameController get game => widget.game;
  SeasonState get season => game.story.season!;
  SeasonDefinition get definition => game.catalogue!.seasonDefinition;
  late int tab = widget.initialTab;
  final scroll = ScrollController();
  @override
  void dispose() {
    scroll.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    // Keep the complete heading readable without taking the action viewport
    // away from large-text controls, matching the calibration screen pattern.
    final scrollHeading = MediaQuery.textScalerOf(context).scale(16) > 24;
    return ListenableBuilder(
      listenable: Listenable.merge([
        game,
        if (widget.services != null) widget.services!,
      ]),
      builder: (context, _) => Scaffold(
        appBar: scrollHeading
            ? AppBar()
            : readingAppBar(context, title: UiEnglish.seasonReturningStars),
        body: SafeArea(
          child: SingleChildScrollView(
            controller: scroll,
            padding: const EdgeInsets.fromLTRB(24, 8, 24, 32),
            child: Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 760),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    if (scrollHeading) ...[
                      Semantics(
                        header: true,
                        namesRoute: true,
                        child: LocalizedText(
                          UiEnglish.seasonReturningStars,
                          style: Theme.of(context).textTheme.headlineMedium,
                        ),
                      ),
                      const SizedBox(height: 20),
                    ],
                    if (game.story.season == null || game.story.pass == null)
                      const LocalizedText(
                        UiEnglish.seasonThisSeasonalCatalogueIsNotAvailable,
                      )
                    else ...[
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: [
                          for (var i = 0; i < 3; i++)
                            ChoiceChip(
                              key: ValueKey('season-tab-$i'),
                              label: LocalizedText(
                                [
                                  UiEnglish.seasonFleet,
                                  UiEnglish.seasonPass,
                                  UiEnglish.seasonContracts,
                                ][i],
                              ),
                              selected: tab == i,
                              onSelected: (_) {
                                setState(() => tab = i);
                                scroll.jumpTo(0);
                              },
                            ),
                        ],
                      ),
                      const SizedBox(height: 24),
                      LocalizedText(
                        definition.title,
                        style: Theme.of(context).textTheme.headlineMedium,
                      ),
                      const SizedBox(height: 12),
                      ...switch (tab) {
                        0 => _fleet(),
                        1 => _pass(),
                        _ => _contracts(),
                      },
                    ],
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  List<Widget> _fleet() => [
    LocalizedText(
      _phaseLabel(),
      style: const TextStyle(color: TideColors.amber),
    ),
    const SizedBox(height: 8),
    LocalizedText(
      UiEnglish.seasonUtcDateSeasonStartsAtMicrosUtcDateSeasonEndsAtMicrosUTC(
        _utcDate(season.startsAtMicros),
        _utcDate(season.endsAtMicros),
        game.catalogue!.seasonRolloutMode == 'local_development'
            ? UiEnglish.seasonLocalPreviewSchedule
            : '',
      ),
      style: _muted,
    ),
    const SizedBox(height: 12),
    LocalizedText(definition.copy[season.phase.name]!, style: _muted),
    if (season.phase == SeasonPhase.archived) ...[
      const SizedBox(height: 12),
      LocalizedText(definition.copy['ended']!, style: _muted),
      const SizedBox(height: 12),
      LocalizedText(definition.copy['archive_resume']!, style: _muted),
      const SizedBox(height: 12),
      FilledButton(
        key: const ValueKey('season-archive-toggle'),
        onPressed: () =>
            _perform(() => game.setSeasonArchiveActive(!season.archiveActive)),
        child: LocalizedText(
          season.archiveActive
              ? UiEnglish.seasonPauseArchivedFleet
              : UiEnglish.seasonResumeArchivedFleetFree,
        ),
      ),
    ],
    const SizedBox(height: 20),
    HarborArt(
      counts: season.fleet.counts,
      phase: 0,
      restoration: season.claimedMilestones.length,
    ),
    const SizedBox(height: 18),
    _card(
      Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const LocalizedText(
            UiEnglish.seasonSEASONALRADIANCE,
            style: TextStyle(
              color: TideColors.amber,
              fontSize: 11,
              letterSpacing: 1.4,
            ),
          ),
          const SizedBox(height: 8),
          LocalizedText(
            UiEnglish.seasonCompactMicrosSeasonFleetWalletMicrosR(
              compactMicros(season.fleet.walletMicros),
            ),
            key: const ValueKey('season-wallet'),
            style: Theme.of(context).textTheme.headlineLarge,
          ),
          LocalizedText(
            UiEnglish.seasonSeasonCanPlayPausedPotentialCompactFixedGameSeasonEngine(
              season.canPlay ? '+' : UiEnglish.seasonPausedPotential,
              compactFixed(game.seasonEngine!.outputPerSecond(season)),
            ),
            style: const TextStyle(color: TideColors.teal),
          ),
          const SizedBox(height: 14),
          const LocalizedText(
            UiEnglish.seasonThisFleetKeepsItsOwnRadianceAnd,
            style: _muted,
          ),
        ],
      ),
    ),
    _card(
      Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const LocalizedText(
            UiEnglish.seasonFreeAutomationForThisSeparateFleet,
          ),
          const SizedBox(height: 8),
          SwitchListTile.adaptive(
            key: const ValueKey('season-automatic'),
            contentPadding: EdgeInsets.zero,
            title: const LocalizedText(UiEnglish.seasonLetTheCrewBuild),
            value: season.automatic,
            onChanged: (value) =>
                _perform(() => game.setSeasonPlan(automatic: value)),
          ),
          if (season.automatic) ...[
            const SizedBox(height: 12),
            DropdownButtonFormField<SeasonPolicy>(
              key: ValueKey('season-policy-${season.policy.name}'),
              initialValue: season.policy,
              isExpanded: true,
              decoration: InputDecoration(
                labelText: Presentation.text(UiEnglish.seasonPurchaseApproach),
                border: OutlineInputBorder(),
              ),
              items: const [
                DropdownMenuItem(
                  value: SeasonPolicy.bestPayback,
                  child: LocalizedText(UiEnglish.seasonBestPayback),
                ),
                DropdownMenuItem(
                  value: SeasonPolicy.tierPriority,
                  child: LocalizedText(UiEnglish.seasonTierPriority),
                ),
              ],
              onChanged: (value) {
                if (value != null) {
                  _perform(() => game.setSeasonPlan(policy: value));
                }
              },
            ),
            const SizedBox(height: 10),
            const LocalizedText(
              UiEnglish.seasonBestPaybackWaitsForTheMostEfficient,
              style: _muted,
            ),
            if (season.policy == SeasonPolicy.tierPriority)
              for (var i = 0; i < 5; i++)
                Row(
                  children: [
                    Expanded(
                      child: LocalizedText(
                        '${i + 1}. ${UiEnglish.producerNames[season.priority[i]]}',
                      ),
                    ),
                    IconButton(
                      key: ValueKey('season-priority-up-$i'),
                      tooltip: Presentation.text(
                        UiEnglish.seasonMoveTideglassEngineProducerNamesSeasonPriorityIEarlier(
                          Presentation.authored(
                            (UiEnglish.producerNames[season.priority[i]])
                                .toString(),
                          ),
                        ),
                      ),
                      onPressed: i == 0 ? null : () => _move(i, -1),
                      icon: const Icon(Icons.arrow_upward),
                    ),
                    IconButton(
                      tooltip: Presentation.text(
                        UiEnglish.seasonMoveTideglassEngineProducerNamesSeasonPriorityILater(
                          Presentation.authored(
                            (UiEnglish.producerNames[season.priority[i]])
                                .toString(),
                          ),
                        ),
                      ),
                      onPressed: i == 4 ? null : () => _move(i, 1),
                      icon: const Icon(Icons.arrow_downward),
                    ),
                  ],
                ),
          ],
        ],
      ),
    ),
    for (var tier = 0; tier < 5; tier++) _producer(tier),
    _card(
      ExpansionTile(
        tilePadding: EdgeInsets.zero,
        title: const LocalizedText(UiEnglish.seasonTheReturningStarNetwork),
        children: [
          const LocalizedText(
            UiEnglish.seasonConnectionsWorkFromTheFirstSkiffEach,
            style: _muted,
          ),
          const SizedBox(height: 14),
          Table(
            border: TableBorder.all(color: TideColors.line),
            children: [
              const TableRow(
                children: [
                  _Cell(UiEnglish.seasonSource),
                  _Cell(UiEnglish.seasonLoom),
                  _Cell(UiEnglish.seasonDawn),
                ],
              ),
              for (var row = 0; row < 2; row++)
                TableRow(
                  children: [
                    _Cell(
                      row == 0
                          ? UiEnglish.seasonSkiffs
                          : UiEnglish.seasonNurseries,
                    ),
                    _Cell('${definition.matrix[row][0]}%'),
                    _Cell('${definition.matrix[row][1]}%'),
                  ],
                ),
            ],
          ),
          const SizedBox(height: 12),
          LocalizedText(
            UiEnglish.seasonCurrentLoomLinkGameSeasonEngineSynergyMultiplierSeason(
              game.seasonEngine!
                  .synergyMultiplier(season, 3)
                  .toDecimalString(decimals: 3),
              game.seasonEngine!
                  .synergyMultiplier(season, 4)
                  .toDecimalString(decimals: 3),
            ),
            style: _muted,
          ),
        ],
      ),
    ),
    LocalizedText(
      UiEnglish.seasonPersonalBearings,
      style: Theme.of(context).textTheme.titleLarge,
    ),
    const SizedBox(height: 14),
    for (final milestone in definition.milestones) _milestone(milestone),
  ];

  Widget _producer(int tier) {
    final engine = game.seasonEngine!;
    final unlocked = engine.isUnlocked(season, tier);
    final price = engine.priceMicros(season, tier);
    final max = unlocked && season.canPlay
        ? engine.maximumAffordable(season, tier)
        : 0;
    return _card(
      Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              StagedProducerArt(
                tier: tier,
                count: season.fleet.counts[tier],
                locked: !unlocked,
                size: 58,
              ),
              const SizedBox(width: 12),
              Expanded(
                child: LocalizedText(
                  UiEnglish.seasonTideglassEngineProducerNamesTierNSeasonFleetCounts(
                    Presentation.authored(
                      (UiEnglish.producerNames[tier]).toString(),
                    ),
                    season.fleet.counts[tier],
                  ),
                  style: Theme.of(context).textTheme.titleMedium,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          if (!unlocked)
            LocalizedText(
              UiEnglish.seasonNeedsTideglassEngineProducerNamesTier(
                Presentation.authored(
                  (UiEnglish.producerNames[tier - 1]).toString(),
                ),
              ),
              style: _muted,
            )
          else
            Wrap(
              spacing: 10,
              runSpacing: 8,
              children: [
                OutlinedButton(
                  key: ValueKey('season-buy-$tier'),
                  onPressed: max > 0
                      ? () => _perform(() => game.buyInSeason(tier))
                      : null,
                  child: LocalizedText(
                    UiEnglish.seasonBuildCompactMicrosPriceR(
                      compactMicros(price),
                    ),
                  ),
                ),
                OutlinedButton(
                  key: ValueKey('season-max-$tier'),
                  onPressed: max > 0
                      ? () => _perform(
                          () => game.buyInSeason(tier, maximum: true),
                        )
                      : null,
                  child: LocalizedText(UiEnglish.seasonBuildMaxMax(max)),
                ),
              ],
            ),
        ],
      ),
    );
  }

  Widget _milestone(SeasonMilestone value) {
    final claimed = season.claimedMilestones.contains(value.id);
    final ready = season.fleet.lifetimeMicros >= value.lifetimeMicros;
    return _card(
      Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          LocalizedText(
            value.title,
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 8),
          LocalizedText(value.body, style: _muted),
          const SizedBox(height: 10),
          LocalizedText(
            UiEnglish.seasonCompactMicrosSeasonFleetLifetimeMicrosCompactMicrosValueLifetime(
              compactMicros(season.fleet.lifetimeMicros),
              compactMicros(value.lifetimeMicros),
            ),
            style: _muted,
          ),
          const SizedBox(height: 12),
          OutlinedButton(
            key: ValueKey('season-badge-${value.id}'),
            onPressed: ready && !claimed
                ? () => _perform(() => game.claimSeasonMilestone(value.id))
                : null,
            child: LocalizedText(
              claimed
                  ? UiEnglish.seasonBadgeKept
                  : UiEnglish.seasonKeepPersonalBadge,
            ),
          ),
          const LocalizedText(
            UiEnglish.seasonAPersonalKeepsakeNoEconomicReward,
            style: _muted,
          ),
        ],
      ),
    );
  }

  List<Widget> _pass() {
    final level = game.passEngine!.level(game.state, definition.passId);
    final xp = game.state.daily.passXpById[definition.passId] ?? BigInt.zero;
    final selected = game.state.daily.selectedPassId == definition.passId;
    return [
      LocalizedText(definition.copy['pass']!, style: _muted),
      const SizedBox(height: 16),
      _card(
        Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            LocalizedText(
              UiEnglish.seasonLevelLevel(level),
              key: const ValueKey('pass-level'),
              style: Theme.of(context).textTheme.headlineMedium,
            ),
            const SizedBox(height: 8),
            LocalizedText(UiEnglish.seasonXpXPXPPerLevel(xp)),
            const SizedBox(height: 12),
            LinearProgressIndicator(
              value: level == 30 ? 1 : (xp % BigInt.from(500)).toInt() / 500,
              minHeight: 6,
            ),
            const SizedBox(height: 16),
            if (selected)
              const Row(
                children: [
                  Icon(Icons.check_circle_outline, color: TideColors.teal),
                  SizedBox(width: 12),
                  Expanded(
                    child: LocalizedText(
                      UiEnglish.seasonSelectedForFutureContractXP,
                      style: TextStyle(color: TideColors.teal),
                    ),
                  ),
                ],
              )
            else
              FilledButton(
                key: const ValueKey('select-season-pass'),
                onPressed: season.phase != SeasonPhase.upcoming
                    ? () => _perform(game.selectSeasonPass)
                    : null,
                child: const LocalizedText(UiEnglish.seasonSelectThisPass),
              ),
            const SizedBox(height: 10),
            const LocalizedText(
              UiEnglish.seasonMainAndSeasonalObjectivesShareTheSame,
              style: _muted,
            ),
          ],
        ),
      ),
      const LocalizedText(
        UiEnglish.seasonFREETRACKLEVELS,
        style: TextStyle(
          color: TideColors.amber,
          letterSpacing: 1.2,
          fontSize: 12,
        ),
      ),
      const SizedBox(height: 12),
      const LocalizedText(
        UiEnglish.seasonTenFreeAppearancesAndTwentyReadableAccounts,
        style: _muted,
      ),
      const SizedBox(height: 18),
      if (widget.services != null) ...[
        OutlinedButton(
          key: const ValueKey('season-commerce'),
          onPressed: () => Navigator.of(context).push(
            MaterialPageRoute<void>(
              builder: (_) =>
                  CommerceScreen(game: game, manager: widget.services!),
            ),
          ),
          child: const LocalizedText(UiEnglish.seasonCollectionAndStoreStatus),
        ),
        const SizedBox(height: 18),
      ],
      for (var value = 1; value <= 30; value++) _rewardLevel(value, level),
    ];
  }

  Widget _rewardLevel(int value, int unlockedLevel) {
    final free = definition.rewards.firstWhere(
      (reward) => reward.track == 'free' && reward.level == value,
    );
    final premium = definition.rewards
        .where((reward) => reward.track == 'premium' && reward.level == value)
        .firstOrNull;
    final claimed = game.story.pass!.claims.containsKey(free.id);
    return _card(
      ExpansionTile(
        key: PageStorageKey('level-$value'),
        tilePadding: EdgeInsets.zero,
        initiallyExpanded: value == (unlockedLevel + 1).clamp(1, 30),
        leading: Icon(
          claimed
              ? Icons.check_circle_outline
              : free.kind == 'cosmetic'
              ? Icons.palette_outlined
              : Icons.menu_book_outlined,
          color: claimed ? TideColors.teal : TideColors.amber,
        ),
        title: LocalizedText(
          UiEnglish.seasonLevelValueFreeTitle(
            value,
            Presentation.authored((free.title).toString()),
          ),
        ),
        subtitle: LocalizedText(
          claimed
              ? UiEnglish.seasonKeptInYourCollection
              : value <= unlockedLevel
              ? UiEnglish.seasonReadyToCollect
              : UiEnglish.seasonValueXP(value * 500),
          style: _muted,
        ),
        children: [
          Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              if (free.kind == 'cosmetic') _appearancePreview(free),
              if (free.kind != 'archive_fragment' || claimed)
                LocalizedText(
                  free.body,
                  key: ValueKey('reward-copy-${free.id}'),
                )
              else
                LocalizedText(
                  UiEnglish.seasonCollectThisAccountAtLevelValueTo(value),
                  style: _muted,
                ),
              const SizedBox(height: 12),
              OutlinedButton(
                key: ValueKey('claim-${free.id}'),
                onPressed: !claimed && value <= unlockedLevel
                    ? () => _perform(() => game.claimFreePassReward(free.id))
                    : null,
                child: LocalizedText(
                  claimed
                      ? UiEnglish.seasonCollectedFree
                      : UiEnglish.seasonKeepFreeFreeKindCosmeticAppearanceAccount(
                          free.kind == 'cosmetic'
                              ? UiEnglish.appearanceNoun
                              : UiEnglish.accountNoun,
                        ),
                ),
              ),
              if (premium != null) ...[
                const Divider(height: 32),
                LocalizedText(
                  widget.services != null &&
                          verifiedPaidCosmetics(
                            widget.services!,
                            game,
                          ).contains(premium.contentId)
                      ? UiEnglish.seasonPREMIUMAPPEARANCEAVAILABLE
                      : UiEnglish.seasonPREMIUMAPPEARANCEPREVIEW,
                  style: const TextStyle(
                    color: TideColors.amber,
                    fontSize: 11,
                    letterSpacing: 1,
                  ),
                ),
                const SizedBox(height: 10),
                LocalizedText(
                  premium.title,
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                _appearancePreview(premium),
                LocalizedText(premium.body, style: _muted),
                const SizedBox(height: 10),
                if (widget.services == null || !widget.services!.configured)
                  const LocalizedText(
                    UiEnglish
                        .seasonPurchasingAndPremiumDeliveryAreUnavailableIn,
                    key: ValueKey('premium-unavailable'),
                    style: _muted,
                  )
                else
                  LocalizedText(
                    verifiedPaidCosmetics(
                          widget.services!,
                          game,
                        ).contains(premium.contentId)
                        ? UiEnglish
                              .seasonAvailableInYourHarborCollectionThisLevel
                        : widget.services!.ownedEntitlementIds.contains(
                            definition.passId,
                          )
                        ? UiEnglish.seasonPremiumOwnershipIsVerifiedEarnLevelValue(
                            value,
                          )
                        : UiEnglish
                              .seasonPremiumOwnershipIsNotCurrentlyVerifiedReview,
                    key: ValueKey('premium-status-${premium.contentId}'),
                    style: _muted,
                  ),
              ],
            ],
          ),
        ],
      ),
    );
  }

  Widget _appearancePreview(PassReward reward) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 12),
    child: CosmeticPreview(
      key: ValueKey(reward.contentId),
      id: reward.contentId,
      counts: game.state.counts,
      restoration: game.story.campaign.restoredHarbor,
    ),
  );

  List<Widget> _contracts() => [
    LocalizedText(definition.copy['alternative']!, style: _muted),
    const SizedBox(height: 12),
    const LocalizedText(
      UiEnglish.seasonNewSeasonalProductionCountsOnlyAfterAssignment,
      style: _muted,
    ),
    const SizedBox(height: 20),
    for (final contract in game.state.dailyContracts.reversed)
      _contract(contract),
  ];

  Widget _contract(DailyContract contract) {
    final binding = game.story.pass!.alternatives[contract.id];
    final progress = game.seasonContractProgress(contract.id);
    final qualified = binding != null && progress >= binding.targetMicros;
    final mainProgress = game.engine.contractProgress(game.state, contract);
    final age = game.state.daily.dayHighWater - contract.accountDay;
    final dayLabel = age == 0
        ? UiEnglish.seasonToday
        : age == 1
        ? UiEnglish.seasonYesterday
        : UiEnglish.seasonAgeDaysAgo(age);
    final labels = {
      'restore': UiEnglish.seasonRestoreRadiance,
      'build': UiEnglish.seasonBuildYourHarbor,
      'discover': switch (contract.discoveryKind) {
        'calibration' => UiEnglish.seasonStudyAConstellation,
        'challenge' => UiEnglish.seasonChartAPassage,
        _ => UiEnglish.seasonReadAnArchiveAccount,
      },
    };
    return _card(
      Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          LocalizedText(
            '$dayLabel · ${labels[contract.kind]}',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 10),
          LocalizedText(
            contract.claimed
                ? UiEnglish.seasonThisSharedSlotIsComplete
                : UiEnglish.seasonNotesXPToTheSelectedPass,
            style: const TextStyle(color: TideColors.amber),
          ),
          const SizedBox(height: 10),
          LocalizedText(
            UiEnglish.seasonHarborRouteContractKindRestoreCompactMicrosMainProgress(
              contract.kind == 'restore'
                  ? compactMicros(mainProgress)
                  : mainProgress,
              contract.kind == 'restore'
                  ? compactMicros(contract.target)
                  : contract.target,
              contract.kind == 'restore' ? UiEnglish.seasonR : '',
            ),
            style: _muted,
          ),
          if (!contract.claimed) ...[
            const SizedBox(height: 14),
            if (binding == null)
              OutlinedButton(
                key: ValueKey('bind-${contract.id}'),
                onPressed: season.canPlay
                    ? () => _perform(() => game.bindSeasonContract(contract.id))
                    : null,
                child: const LocalizedText(UiEnglish.seasonAddSeasonalRoute),
              )
            else ...[
              LocalizedText(
                UiEnglish.seasonSeasonalRouteCompactMicrosProgressCompactMicrosBindingTargetMicr(
                  compactMicros(progress),
                  compactMicros(binding.targetMicros),
                ),
                style: _muted,
              ),
              const SizedBox(height: 10),
              FilledButton(
                key: ValueKey('season-claim-${contract.id}'),
                onPressed: qualified
                    ? () =>
                          _perform(() => game.claimSeasonContract(contract.id))
                    : null,
                child: const LocalizedText(UiEnglish.seasonClaimThisSharedSlot),
              ),
            ],
          ],
        ],
      ),
    );
  }

  String _phaseLabel() => switch (season.phase) {
    SeasonPhase.upcoming =>
      UiEnglish.seasonBeginsInTimeUntilSeasonStartsAtMicros(
        _timeUntil(season.startsAtMicros),
      ),
    SeasonPhase.live =>
      UiEnglish.seasonLiveWindowTimeUntilSeasonEndsAtMicrosRemaining(
        _timeUntil(season.endsAtMicros),
      ),
    SeasonPhase.archived =>
      season.archiveActive
          ? UiEnglish.seasonArchivedFleetContinuing
          : UiEnglish.seasonArchivedFleetPaused,
  };
  String _timeUntil(BigInt target) => durationLabel(
    Duration(microseconds: (target - season.settledThroughMicros).toInt()),
  );
  String _utcDate(BigInt value) {
    final date = DateTime.fromMicrosecondsSinceEpoch(
      value.toInt(),
      isUtc: true,
    );
    return '${date.day} ${[UiEnglish.seasonJan, UiEnglish.seasonFeb, UiEnglish.seasonMar, UiEnglish.seasonApr, UiEnglish.seasonMay, UiEnglish.seasonJun, UiEnglish.seasonJul, UiEnglish.seasonAug, UiEnglish.seasonSep, UiEnglish.seasonOct, UiEnglish.seasonNov, UiEnglish.seasonDec][date.month - 1]} ${date.year}';
  }

  void _move(int index, int delta) {
    final priority = season.priority.toList();
    priority.insert(index + delta, priority.removeAt(index));
    _perform(() => game.setSeasonPlan(priority: priority));
  }

  void _perform(bool Function() command) {
    final accepted = command();
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(
        SnackBar(
          content: LocalizedText(
            accepted
                ? game.lastAction ?? UiEnglish.seasonYourProgressIsSaved
                : UiEnglish.seasonThisActionIsNotAvailableYet,
          ),
        ),
      );
  }

  Widget _card(Widget child) => Container(
    margin: const EdgeInsets.only(bottom: 18),
    padding: const EdgeInsets.all(18),
    decoration: BoxDecoration(
      color: TideColors.panel,
      borderRadius: BorderRadius.circular(18),
      border: Border.all(color: TideColors.line),
    ),
    child: Material(color: Colors.transparent, child: child),
  );
  static const _muted = TextStyle(
    color: TideColors.muted,
    fontSize: 13,
    height: 1.45,
  );
}

class _Cell extends StatelessWidget {
  const _Cell(this.text);
  final String text;
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.all(8),
    child: LocalizedText(text, style: const TextStyle(fontSize: 12)),
  );
}

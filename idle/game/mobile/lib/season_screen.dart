import 'package:flutter/material.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_events/tideglass_events.dart';
import 'game_controller.dart';
import 'harbor_art.dart';
import 'number_format.dart';
import 'palette.dart';
import 'cosmetic_art.dart';
import 'producer_art.dart';

/// Seasonal presentation has no local award or entitlement state.
class SeasonScreen extends StatefulWidget {
  const SeasonScreen({super.key, required this.game, this.initialTab = 0});
  final GameController game;
  final int initialTab;
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
  Widget build(BuildContext context) => ListenableBuilder(
    listenable: game,
    builder: (context, _) => Scaffold(
      appBar: AppBar(title: const Text('Returning stars')),
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
                  if (game.story.season == null || game.story.pass == null)
                    const Text('This seasonal catalogue is not available.')
                  else ...[
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: [
                        for (var i = 0; i < 3; i++)
                          ChoiceChip(
                            key: ValueKey('season-tab-$i'),
                            label: Text(['Fleet', 'Pass', 'Contracts'][i]),
                            selected: tab == i,
                            onSelected: (_) {
                              setState(() => tab = i);
                              scroll.jumpTo(0);
                            },
                          ),
                      ],
                    ),
                    const SizedBox(height: 24),
                    Text(
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

  List<Widget> _fleet() => [
    Text(_phaseLabel(), style: const TextStyle(color: TideColors.amber)),
    const SizedBox(height: 8),
    Text(
      '${_utcDate(season.startsAtMicros)} — ${_utcDate(season.endsAtMicros)} UTC\n28 days${game.catalogue!.seasonRolloutMode == 'local_development' ? ' · local preview schedule' : ''}',
      style: _muted,
    ),
    const SizedBox(height: 12),
    Text(definition.copy[season.phase.name]!, style: _muted),
    if (season.phase == SeasonPhase.archived) ...[
      const SizedBox(height: 12),
      Text(definition.copy['ended']!, style: _muted),
      const SizedBox(height: 12),
      Text(definition.copy['archive_resume']!, style: _muted),
      const SizedBox(height: 12),
      FilledButton(
        key: const ValueKey('season-archive-toggle'),
        onPressed: () =>
            _perform(() => game.setSeasonArchiveActive(!season.archiveActive)),
        child: Text(
          season.archiveActive
              ? 'Pause archived fleet'
              : 'Resume archived fleet · free',
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
          const Text(
            'SEASONAL RADIANCE',
            style: TextStyle(
              color: TideColors.amber,
              fontSize: 11,
              letterSpacing: 1.4,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            '${compactMicros(season.fleet.walletMicros)} R',
            key: const ValueKey('season-wallet'),
            style: Theme.of(context).textTheme.headlineLarge,
          ),
          Text(
            '${season.canPlay ? '+' : 'Paused · potential '}${compactFixed(game.seasonEngine!.outputPerSecond(season))} R/s',
            style: const TextStyle(color: TideColors.teal),
          ),
          const SizedBox(height: 14),
          const Text(
            'This fleet keeps its own Radiance and production. Your main harbor continues independently. No Charts, Focus, Support or purchases increase its power.',
            style: _muted,
          ),
        ],
      ),
    ),
    _card(
      Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          SwitchListTile.adaptive(
            key: const ValueKey('season-automatic'),
            contentPadding: EdgeInsets.zero,
            title: const Text('Let the crew build'),
            subtitle: const Text('Free automation for this separate fleet.'),
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
              decoration: const InputDecoration(
                labelText: 'Purchase approach',
                border: OutlineInputBorder(),
              ),
              items: const [
                DropdownMenuItem(
                  value: SeasonPolicy.bestPayback,
                  child: Text('Best payback'),
                ),
                DropdownMenuItem(
                  value: SeasonPolicy.tierPriority,
                  child: Text('Tier priority'),
                ),
              ],
              onChanged: (value) {
                if (value != null) {
                  _perform(() => game.setSeasonPlan(policy: value));
                }
              },
            ),
            const SizedBox(height: 10),
            const Text(
              'Best payback waits for the most efficient purchase. Tier priority waits for the first unlocked tier in your order.',
              style: _muted,
            ),
            if (season.policy == SeasonPolicy.tierPriority)
              for (var i = 0; i < 5; i++)
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        '${i + 1}. ${TideglassEngine.producerNames[season.priority[i]]}',
                      ),
                    ),
                    IconButton(
                      key: ValueKey('season-priority-up-$i'),
                      tooltip:
                          'Move ${TideglassEngine.producerNames[season.priority[i]]} earlier',
                      onPressed: i == 0 ? null : () => _move(i, -1),
                      icon: const Icon(Icons.arrow_upward),
                    ),
                    IconButton(
                      tooltip:
                          'Move ${TideglassEngine.producerNames[season.priority[i]]} later',
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
        title: const Text('The returning-star network'),
        children: [
          const Text(
            'Connections work from the first Skiff. Each column adds both source effects: coefficient × log₂(1 + source count / 25).',
            style: _muted,
          ),
          const SizedBox(height: 14),
          Table(
            border: TableBorder.all(color: TideColors.line),
            children: [
              const TableRow(
                children: [_Cell('Source'), _Cell('Loom'), _Cell('Dawn')],
              ),
              for (var row = 0; row < 2; row++)
                TableRow(
                  children: [
                    _Cell(row == 0 ? 'Skiffs' : 'Nurseries'),
                    _Cell('${definition.matrix[row][0]}%'),
                    _Cell('${definition.matrix[row][1]}%'),
                  ],
                ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            'Current Loom link: ${game.seasonEngine!.synergyMultiplier(season, 3).toDecimalString(decimals: 3)}×\nCurrent Dawn link: ${game.seasonEngine!.synergyMultiplier(season, 4).toDecimalString(decimals: 3)}×',
            style: _muted,
          ),
        ],
      ),
    ),
    Text('Personal bearings', style: Theme.of(context).textTheme.titleLarge),
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
                child: Text(
                  '${TideglassEngine.producerNames[tier]}\n${season.fleet.counts[tier]} at work',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          if (!unlocked)
            Text(
              'Needs 10 ${TideglassEngine.producerNames[tier - 1]}',
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
                  child: Text('Build 1 · ${compactMicros(price)} R'),
                ),
                OutlinedButton(
                  key: ValueKey('season-max-$tier'),
                  onPressed: max > 0
                      ? () => _perform(
                          () => game.buyInSeason(tier, maximum: true),
                        )
                      : null,
                  child: Text('Build max · $max'),
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
          Text(value.title, style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          Text(value.body, style: _muted),
          const SizedBox(height: 10),
          Text(
            '${compactMicros(season.fleet.lifetimeMicros)} / ${compactMicros(value.lifetimeMicros)} lifetime seasonal R',
            style: _muted,
          ),
          const SizedBox(height: 12),
          OutlinedButton(
            key: ValueKey('season-badge-${value.id}'),
            onPressed: ready && !claimed
                ? () => _perform(() => game.claimSeasonMilestone(value.id))
                : null,
            child: Text(claimed ? 'Badge kept' : 'Keep personal badge'),
          ),
          const Text('A personal keepsake. No economic reward.', style: _muted),
        ],
      ),
    );
  }

  List<Widget> _pass() {
    final level = game.passEngine!.level(game.state, definition.passId);
    final xp = game.state.daily.passXpById[definition.passId] ?? BigInt.zero;
    final selected = game.state.daily.selectedPassId == definition.passId;
    return [
      Text(definition.copy['pass']!, style: _muted),
      const SizedBox(height: 16),
      _card(
        Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              'Level $level / 30',
              key: const ValueKey('pass-level'),
              style: Theme.of(context).textTheme.headlineMedium,
            ),
            const SizedBox(height: 8),
            Text('$xp XP · 500 XP per level'),
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
                    child: Text(
                      'Selected for future contract XP',
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
                child: const Text('Select this pass'),
              ),
            const SizedBox(height: 10),
            const Text(
              'Main and seasonal objectives share the same daily slots: 250 XP and 10 Notes once per completed slot. This pass stays available after the season ends.',
              style: _muted,
            ),
          ],
        ),
      ),
      const Text(
        'FREE TRACK · 30 LEVELS',
        style: TextStyle(
          color: TideColors.amber,
          letterSpacing: 1.2,
          fontSize: 12,
        ),
      ),
      const SizedBox(height: 12),
      const Text(
        'Ten free appearances and twenty readable accounts. Ten premium appearances are previewed at every third level.',
        style: _muted,
      ),
      const SizedBox(height: 18),
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
        title: Text('Level $value · ${free.title}'),
        subtitle: Text(
          claimed
              ? 'Kept in your collection'
              : value <= unlockedLevel
              ? 'Ready to collect'
              : '${value * 500} XP',
          style: _muted,
        ),
        children: [
          Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              if (free.kind == 'cosmetic') _appearancePreview(free),
              if (free.kind != 'archive_fragment' || claimed)
                Text(free.body, key: ValueKey('reward-copy-${free.id}'))
              else
                Text(
                  'Collect this account at level $value to read the next part of the watchkeeper’s record.',
                  style: _muted,
                ),
              const SizedBox(height: 12),
              OutlinedButton(
                key: ValueKey('claim-${free.id}'),
                onPressed: !claimed && value <= unlockedLevel
                    ? () => _perform(() => game.claimFreePassReward(free.id))
                    : null,
                child: Text(
                  claimed
                      ? 'Collected · free'
                      : 'Keep free ${free.kind == 'cosmetic' ? 'appearance' : 'account'}',
                ),
              ),
              if (premium != null) ...[
                const Divider(height: 32),
                const Text(
                  'PREMIUM APPEARANCE · PREVIEW',
                  style: TextStyle(
                    color: TideColors.amber,
                    fontSize: 11,
                    letterSpacing: 1,
                  ),
                ),
                const SizedBox(height: 10),
                Text(
                  premium.title,
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                _appearancePreview(premium),
                Text(premium.body, style: _muted),
                const SizedBox(height: 10),
                const Text(
                  'Purchasing and premium delivery are unavailable in this build. This preview grants no ownership or game power.',
                  key: ValueKey('premium-unavailable'),
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
    Text(definition.copy['alternative']!, style: _muted),
    const SizedBox(height: 12),
    const Text(
      'New seasonal production counts only after assignment. The original harbor objective stays available; claiming either route completes this same slot once.',
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
        ? 'Today'
        : age == 1
        ? 'Yesterday'
        : '$age days ago';
    final labels = {
      'restore': 'Restore Radiance',
      'build': 'Build your harbor',
      'discover': switch (contract.discoveryKind) {
        'calibration' => 'Study a constellation',
        'challenge' => 'Chart a passage',
        _ => 'Read an archive account',
      },
    };
    return _card(
      Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            '$dayLabel · ${labels[contract.kind]}',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 10),
          Text(
            contract.claimed
                ? 'This shared slot is complete.'
                : '10 Notes + 250 XP to the selected pass',
            style: const TextStyle(color: TideColors.amber),
          ),
          const SizedBox(height: 10),
          Text(
            'Harbor route: ${contract.kind == 'restore' ? compactMicros(mainProgress) : mainProgress} / ${contract.kind == 'restore' ? compactMicros(contract.target) : contract.target}${contract.kind == 'restore' ? ' R' : ''}',
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
                child: const Text('Add seasonal route'),
              )
            else ...[
              Text(
                'Seasonal route: ${compactMicros(progress)} / ${compactMicros(binding.targetMicros)} new R',
                style: _muted,
              ),
              const SizedBox(height: 10),
              FilledButton(
                key: ValueKey('season-claim-${contract.id}'),
                onPressed: qualified
                    ? () =>
                          _perform(() => game.claimSeasonContract(contract.id))
                    : null,
                child: const Text('Claim this shared slot'),
              ),
            ],
          ],
        ],
      ),
    );
  }

  String _phaseLabel() => switch (season.phase) {
    SeasonPhase.upcoming => 'Begins in ${_timeUntil(season.startsAtMicros)}',
    SeasonPhase.live =>
      'Live window · ${_timeUntil(season.endsAtMicros)} remaining',
    SeasonPhase.archived =>
      season.archiveActive
          ? 'Archived fleet · continuing'
          : 'Archived fleet · paused',
  };
  String _timeUntil(BigInt target) => durationLabel(
    Duration(microseconds: (target - season.settledThroughMicros).toInt()),
  );
  String _utcDate(BigInt value) {
    final date = DateTime.fromMicrosecondsSinceEpoch(
      value.toInt(),
      isUtc: true,
    );
    return '${date.day} ${['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][date.month - 1]} ${date.year}';
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
          content: Text(
            accepted
                ? game.lastAction ?? 'Your progress is saved.'
                : 'This action is not available yet.',
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
    child: Text(text, style: const TextStyle(fontSize: 12)),
  );
}

import 'package:flutter/material.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_progression/tideglass_progression.dart';
import 'game_controller.dart';
import 'harbor_art.dart';
import 'number_format.dart';
import 'palette.dart';

/// Campaign and passage presentation. All economic mutations go through the
/// shared controller so main progress and a separate fleet save atomically.
class StoryScreen extends StatefulWidget {
  const StoryScreen({super.key, required this.game, this.initialTab = 0});
  final GameController game;
  final int initialTab;
  @override
  State<StoryScreen> createState() => _StoryScreenState();
}

class _StoryScreenState extends State<StoryScreen> {
  late int tab = widget.initialTab;
  final activeKey = GlobalKey();
  final scroll = ScrollController();
  GameController get game => widget.game;
  static const familyLabels = {
    'constrained_fleets': 'A smaller fleet',
    'synergy_priorities': 'Different connections',
    'automation_planning': 'Plans for the tide',
  };
  @override
  void dispose() {
    scroll.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => ListenableBuilder(
    listenable: game,
    builder: (context, _) => Scaffold(
      appBar: AppBar(title: const Text('The restoration')),
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
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      for (var i = 0; i < 4; i++)
                        ChoiceChip(
                          key: ValueKey('story-tab-$i'),
                          label: Text(
                            [
                              'Chapters',
                              'Passages',
                              'Archive',
                              'Decorations',
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
                  if (game.catalogue == null)
                    const Text('The restoration catalogue could not be loaded.')
                  else
                    ...switch (tab) {
                      0 => _chapters(context),
                      1 => _dossiers(context),
                      2 => _archive(context),
                      _ => _decorations(context),
                    },
                ],
              ),
            ),
          ),
        ),
      ),
    ),
  );
  List<Widget> _chapters(BuildContext context) {
    final campaign = game.story.campaign;
    return [
      Text(
        '${campaign.restoredHarbor} of 6 constellations restored',
        style: Theme.of(context).textTheme.headlineMedium,
      ),
      const SizedBox(height: 10),
      const Text(
        'A permanent record of what you discover. Recharting never darkens a restored constellation.',
        style: TextStyle(color: TideColors.muted),
      ),
      const SizedBox(height: 24),
      if (campaign.hasEnding)
        _card(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Icon(Icons.auto_awesome, color: TideColors.amber, size: 36),
              const SizedBox(height: 12),
              Text(
                'The Harbor Remembers',
                key: const ValueKey('campaign-ending'),
                style: Theme.of(context).textTheme.headlineMedium,
              ),
              const SizedBox(height: 12),
              Text(
                game.catalogue!.campaign.chapters.last['completion'] as String,
              ),
              const SizedBox(height: 18),
              FilledButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('Keep charting'),
              ),
            ],
          ),
        ),
      for (var i = 0; i < 6; i++) _chapter(context, i),
    ];
  }

  Widget _chapter(BuildContext context, int index) {
    final chapter = game.catalogue!.campaign.chapters[index];
    final id = chapter['id'] as String;
    final complete = game.story.campaign.completed.contains(id);
    final unlocked =
        index == 0 ||
        game.story.campaign.completed.contains(
          'chapter.${index.toString().padLeft(2, '0')}',
        );
    return _card(
      child: ExpansionTile(
        key: PageStorageKey('chapter-$id'),
        initiallyExpanded: unlocked && !complete,
        tilePadding: EdgeInsets.zero,
        childrenPadding: const EdgeInsets.only(bottom: 8),
        leading: Icon(
          complete
              ? Icons.check_circle_outline
              : unlocked
              ? Icons.auto_awesome_outlined
              : Icons.lock_outline,
          color: complete
              ? TideColors.teal
              : unlocked
              ? TideColors.amber
              : TideColors.muted,
        ),
        title: Text('${index + 1}. ${chapter['title']}'),
        subtitle: Text(
          complete
              ? 'Restored'
              : unlocked
              ? 'Your current chapter'
              : 'Complete chapter $index first',
          style: const TextStyle(color: TideColors.muted),
        ),
        children: [
          Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(chapter['intro'] as String),
              const SizedBox(height: 18),
              for (final raw in chapter['objectives'] as List)
                _objective(Map<String, dynamic>.from(raw), recorded: complete),
              const SizedBox(height: 10),
              for (final hint in chapter['hints'] as List)
                Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Text(
                    '• $hint',
                    style: const TextStyle(
                      color: TideColors.muted,
                      fontSize: 13,
                    ),
                  ),
                ),
              if (complete) ...[
                const SizedBox(height: 10),
                Text(
                  chapter['completion'] as String,
                  style: const TextStyle(color: TideColors.teal),
                ),
              ],
              const SizedBox(height: 12),
              const Text(
                'Keepsake: a restored sky, three archive entries and a permanent chapter badge. No production boost.',
                style: TextStyle(color: TideColors.muted, fontSize: 12),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _objective(Map<String, dynamic> goal, {bool recorded = false}) {
    final facts = game.progressFacts;
    final met = recorded || game.catalogue!.campaign.objectiveMet(goal, facts);
    final target = goal['value'] as int;
    String label, value;
    switch (goal['kind']) {
      case 'owned_min':
        final tier = (goal['tier'] as int) - 1;
        label = '${TideglassEngine.producerNames[tier]} in your current fleet';
        value = '${facts.main.counts[tier]}';
      case 'challenge_family_min':
        label = 'Passages: ${familyLabels[goal['family']]}';
        value =
            '${facts.completedChallenges.where((id) => game.catalogue!.campaign.families[id] == goal['family']).length}';
      default:
        switch (goal['stat']) {
          case 'recharts':
            label = 'Recharts completed';
            value = '${facts.recharts}';
          case 'charts_awarded':
            label = 'Permanent Charts';
            value = '${facts.main.charts}';
          case 'surveys_collected':
            label = 'Surveys collected';
            value = '${facts.surveysCollected}';
          default:
            label = 'Distinct calibration patterns';
            value = '${facts.calibrations.length}';
        }
    }
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            met ? Icons.check_circle : Icons.radio_button_unchecked,
            color: met ? TideColors.teal : TideColors.muted,
            size: 20,
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              recorded
                  ? '$label · $target · achieved'
                  : '$label · $value / $target',
            ),
          ),
        ],
      ),
    );
  }

  List<Widget> _archive(BuildContext context) => [
    Text(
      'The keeper’s archive',
      style: Theme.of(context).textTheme.headlineMedium,
    ),
    const SizedBox(height: 10),
    Text(
      '${game.story.campaign.archiveIds.length} of 18 accounts recovered',
      style: const TextStyle(color: TideColors.muted),
    ),
    const SizedBox(height: 24),
    for (final entry in game.catalogue!.archive)
      _card(
        child: game.story.campaign.archiveIds.contains(entry['id'])
            ? ExpansionTile(
                key: PageStorageKey(entry['id']),
                tilePadding: EdgeInsets.zero,
                title: Text(entry['title'] as String),
                leading: const Icon(
                  Icons.menu_book_outlined,
                  color: TideColors.amber,
                ),
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text(entry['text'] as String),
                      const SizedBox(height: 14),
                      OutlinedButton(
                        key: ValueKey('read-${entry['id']}'),
                        onPressed: () => _perform(
                          context,
                          () => game.readArchive(entry['id'] as String),
                        ),
                        child: const Text('Reflect on this account'),
                      ),
                    ],
                  ),
                ],
              )
            : ListTile(
                contentPadding: EdgeInsets.zero,
                leading: const Icon(
                  Icons.lock_outline,
                  color: TideColors.muted,
                ),
                title: Text(entry['title'] as String),
                subtitle: Text(
                  'Restores with chapter ${int.parse((entry['chapter_id'] as String).split('.').last)}',
                ),
              ),
      ),
  ];
  List<Widget> _dossiers(BuildContext context) {
    final collection = game.story.dossiers;
    return [
      Text(
        'Passages beyond the harbor',
        style: Theme.of(context).textTheme.headlineMedium,
      ),
      const SizedBox(height: 10),
      Text(
        '${game.state.surveyNotes} Survey Notes · ${collection.completed.length} / 12 charted',
        style: const TextStyle(color: TideColors.amber),
      ),
      const SizedBox(height: 12),
      const Text(
        'Each dossier opens a separate fleet. Your main harbor keeps earning. Main Radiance, Charts and boosts stay at home; passage progress returns as discoveries, never money.',
        style: TextStyle(color: TideColors.muted),
      ),
      const SizedBox(height: 20),
      if (collection.active != null)
        KeyedSubtree(
          key: activeKey,
          child: _active(context, collection.active!),
        ),
      if (game.story.campaign.restoredHarbor < 3)
        _card(
          child: const Text(
            'Finish The Quiet Watch, chapter 3, to open passages. Each dossier then costs 100 Survey Notes once. Replays are free.',
          ),
        ),
      for (final family in familyLabels.entries) ...[
        const SizedBox(height: 12),
        Text(family.value, style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: 12),
        for (final dossier in game.catalogue!.dossiers.where(
          (d) => d.family == family.key,
        ))
          _dossierCard(context, dossier),
      ],
    ];
  }

  Widget _dossierCard(BuildContext context, ChallengeDefinition definition) {
    final owned = game.story.dossiers.owned.contains(definition.id),
        completed = game.story.dossiers.completed.contains(definition.id),
        active = game.story.dossiers.active?.dossierId == definition.id;
    final canOpen =
        game.story.campaign.restoredHarbor >= 3 &&
        (owned || game.state.surveyNotes >= BigInt.from(100));
    return _card(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Icon(
                completed ? Icons.check_circle_outline : Icons.sailing_outlined,
                color: completed ? TideColors.teal : TideColors.amber,
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  definition.title,
                  style: Theme.of(context).textTheme.titleMedium,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            definition.intro,
            style: const TextStyle(color: TideColors.muted),
          ),
          const SizedBox(height: 10),
          Text(
            'Goal: ${compactMicros(definition.goalMicros)} lifetime passage Radiance',
            style: const TextStyle(fontSize: 12),
          ),
          const SizedBox(height: 14),
          OutlinedButton(
            key: ValueKey('open-${definition.id}'),
            onPressed: !active && canOpen
                ? () => _open(context, definition)
                : null,
            child: Text(
              active
                  ? 'Your active passage'
                  : owned
                  ? 'Open owned dossier · free'
                  : 'Open dossier · 100 Notes',
            ),
          ),
          if (completed)
            const Padding(
              padding: EdgeInsets.only(top: 8),
              child: Text(
                'Charted · replay whenever you like',
                style: TextStyle(color: TideColors.teal, fontSize: 12),
              ),
            ),
        ],
      ),
    );
  }

  Future<void> _open(
    BuildContext context,
    ChallengeDefinition definition,
  ) async {
    final replacing = game.story.dossiers.active != null;
    final owned = game.story.dossiers.owned.contains(definition.id);
    final accepted = await _confirm(
      context,
      replacing ? 'Replace the active passage?' : 'Open ${definition.title}?',
      '${owned ? 'This dossier is already yours. Opening it is free.' : 'Spend 100 Survey Notes to keep this dossier permanently. Replays are free.'}${replacing ? ' Your current passage fleet and its unfinished progress will be replaced; its ownership and recorded completion remain.' : ''} Your main harbor is unchanged.',
      replacing ? 'Replace and open' : 'Open dossier',
    );
    if (accepted && context.mounted) {
      final opened = _perform(
        context,
        () => game.openDossier(definition.id, replaceActive: replacing),
      );
      if (opened) {
        WidgetsBinding.instance.addPostFrameCallback((_) {
          final target = activeKey.currentContext;
          if (target != null) {
            Scrollable.ensureVisible(
              target,
              alignment: 0,
              duration: MediaQuery.disableAnimationsOf(target)
                  ? Duration.zero
                  : const Duration(milliseconds: 250),
            );
          }
        });
      }
    }
  }

  Widget _active(BuildContext context, ChallengeRun run) {
    final definition = game.catalogue!.dossier(run.dossierId),
        economy = ChallengeEconomy(game.catalogue!.dossier(run.dossierId));
    final fraction =
        (run.fleet.lifetimeMicros >= definition.goalMicros
            ? 10000
            : ((run.fleet.lifetimeMicros * BigInt.from(10000)) ~/
                      definition.goalMicros)
                  .toInt()) /
        10000;
    return _card(
      key: const ValueKey('active-challenge'),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Text(
            'PASSAGE FLEET',
            style: TextStyle(
              color: TideColors.amber,
              fontSize: 11,
              letterSpacing: 1.5,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            definition.title,
            style: Theme.of(context).textTheme.headlineMedium,
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 24,
            runSpacing: 8,
            children: [
              Text(
                '${compactMicros(run.fleet.walletMicros)} R',
                key: const ValueKey('challenge-wallet'),
                style: Theme.of(context).textTheme.titleLarge,
              ),
              Text(
                '+${compactFixed(economy.outputPerSecond(run.fleet))} R/s',
                style: const TextStyle(color: TideColors.teal),
              ),
            ],
          ),
          const SizedBox(height: 16),
          LinearProgressIndicator(value: fraction, minHeight: 6),
          const SizedBox(height: 8),
          Text(
            '${compactMicros(run.fleet.lifetimeMicros)} / ${compactMicros(definition.goalMicros)} lifetime Radiance',
            style: const TextStyle(color: TideColors.muted, fontSize: 12),
          ),
          if (run.complete) ...[
            const SizedBox(height: 14),
            Text(
              definition.completion,
              style: const TextStyle(color: TideColors.teal),
            ),
            const SizedBox(height: 8),
            const Text(
              'Passage charted. Its discovery is kept in your restoration.',
              key: ValueKey('challenge-complete'),
            ),
          ],
          const SizedBox(height: 18),
          const Text(
            'You can return to the harbor without closing this passage. Both fleets continue working.',
            style: TextStyle(color: TideColors.muted, fontSize: 12),
          ),
          const SizedBox(height: 18),
          if (definition.automaticOnly)
            const ListTile(
              contentPadding: EdgeInsets.zero,
              title: Text('The passage crew builds automatically'),
              subtitle: Text('Choose the plan they follow below.'),
              trailing: Icon(
                Icons.check_circle_outline,
                color: TideColors.teal,
              ),
            )
          else
            SwitchListTile.adaptive(
              contentPadding: EdgeInsets.zero,
              title: const Text('Let the passage crew build'),
              subtitle: const Text(
                'Pause the plan to make purchases yourself.',
              ),
              value: run.automatic,
              onChanged: (value) => game.setDossierPlan(automatic: value),
            ),
          if (run.automatic || definition.automaticOnly) ...[
            const SizedBox(height: 8),
            DropdownButtonFormField<ChallengePolicy>(
              key: ValueKey('challenge-policy-${run.policy.name}'),
              initialValue: run.policy,
              isExpanded: true,
              decoration: const InputDecoration(
                labelText: 'Purchase approach',
                border: OutlineInputBorder(),
              ),
              items: const [
                DropdownMenuItem(
                  value: ChallengePolicy.bestPayback,
                  child: Text('Best payback'),
                ),
                DropdownMenuItem(
                  value: ChallengePolicy.tierPriority,
                  child: Text('Tier priority'),
                ),
              ],
              onChanged: (value) {
                if (value != null) {
                  game.setDossierPlan(policy: value);
                }
              },
            ),
            const SizedBox(height: 10),
            const Text(
              'Best payback waits for the most efficient purchase. Tier priority waits for the first unlocked tier in your order.',
              style: TextStyle(color: TideColors.muted, fontSize: 12),
            ),
            if (run.policy == ChallengePolicy.tierPriority) ...[
              const SizedBox(height: 14),
              for (var i = 0; i < 5; i++)
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        '${i + 1}. ${TideglassEngine.producerNames[run.priority[i]]}',
                      ),
                    ),
                    IconButton(
                      key: ValueKey('priority-up-$i'),
                      tooltip:
                          'Move ${TideglassEngine.producerNames[run.priority[i]]} earlier',
                      onPressed: i == 0
                          ? null
                          : () => _movePriority(run, i, -1),
                      icon: const Icon(Icons.arrow_upward),
                    ),
                    IconButton(
                      tooltip:
                          'Move ${TideglassEngine.producerNames[run.priority[i]]} later',
                      onPressed: i == 4 ? null : () => _movePriority(run, i, 1),
                      icon: const Icon(Icons.arrow_downward),
                    ),
                  ],
                ),
            ],
          ],
          const SizedBox(height: 20),
          for (var tier = 0; tier < 5; tier++)
            _challengeProducer(context, economy, run, tier),
          ExpansionTile(
            tilePadding: EdgeInsets.zero,
            title: const Text('Passage network rules'),
            children: [
              Text(
                definition.synergyImmediate
                    ? 'These cross-tier links apply from the start. Each coefficient multiplies log₂(1 + source count / 25).'
                    : 'This passage has no cross-tier multipliers. Its berth limits shape the fleet.',
                style: const TextStyle(color: TideColors.muted, fontSize: 12),
              ),
              if (definition.synergyImmediate) ...[
                const SizedBox(height: 12),
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
              ],
            ],
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 12,
            runSpacing: 8,
            children: [
              OutlinedButton(
                onPressed: () => _restart(context),
                child: const Text('Restart fleet · free'),
              ),
              TextButton(
                onPressed: () => _leave(context),
                child: const Text('Close this passage'),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _challengeProducer(
    BuildContext context,
    ChallengeEconomy economy,
    ChallengeRun run,
    int tier,
  ) {
    final cap = economy.definition.tierCaps[tier];
    final unlocked = economy.isUnlocked(run.fleet, tier);
    final affordable =
        run.fleet.walletMicros >=
        economy.priceMicros(tier, run.fleet.counts[tier]);
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              ProducerArt(
                tier: tier,
                active: run.fleet.counts[tier] > 0,
                size: 44,
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  '${TideglassEngine.producerNames[tier]}\n${run.fleet.counts[tier]}${cap == null ? '' : ' / $cap'} at work',
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          if (cap != null && run.fleet.counts[tier] >= cap)
            const Text(
              'Berth limit reached',
              style: TextStyle(color: TideColors.muted, fontSize: 12),
            )
          else if (!unlocked)
            Text(
              'Needs 10 ${TideglassEngine.producerNames[tier - 1]}',
              style: const TextStyle(color: TideColors.muted, fontSize: 12),
            )
          else
            OutlinedButton(
              key: ValueKey('challenge-buy-$tier'),
              onPressed: affordable && !economy.definition.automaticOnly
                  ? () => _perform(context, () => game.buyInDossier(tier))
                  : null,
              child: Text(
                '${economy.definition.automaticOnly ? 'Crew purchase' : 'Build 1'} · ${compactMicros(economy.priceMicros(tier, run.fleet.counts[tier]))} R',
              ),
            ),
        ],
      ),
    );
  }

  void _movePriority(ChallengeRun run, int index, int delta) {
    final order = run.priority.toList();
    final tier = order.removeAt(index);
    order.insert(index + delta, tier);
    game.setDossierPlan(priority: order);
  }

  Future<void> _restart(BuildContext context) async {
    if (await _confirm(
          context,
          'Restart this passage fleet?',
          'The current passage Radiance and fleet will be rebuilt. Ownership, recorded completion and your main harbor remain. Replaying costs no Notes.',
          'Restart fleet',
        ) &&
        context.mounted) {
      _perform(context, game.restartDossier);
    }
  }

  Future<void> _leave(BuildContext context) async {
    if (await _confirm(
          context,
          'Close this passage?',
          'The current passage fleet and unfinished progress will be discarded. Dossier ownership and recorded completion remain. You can use Back to visit your harbor while keeping this passage active.',
          'Close passage',
        ) &&
        context.mounted) {
      _perform(context, game.leaveDossier);
    }
  }

  List<Widget> _decorations(BuildContext context) => [
    Text(
      'Make the harbor yours',
      style: Theme.of(context).textTheme.headlineMedium,
    ),
    const SizedBox(height: 10),
    const Text(
      'Six optional decorations, 50 Survey Notes each. Purely visual: they never change production, prestige or storage.',
      style: TextStyle(color: TideColors.muted),
    ),
    const SizedBox(height: 18),
    if (game.story.equippedDecoration != null)
      Padding(
        padding: const EdgeInsets.only(bottom: 18),
        child: OutlinedButton(
          key: const ValueKey('unequip-decoration'),
          onPressed: () => _perform(context, game.unequipDecoration),
          child: const Text('Show the undecorated harbor'),
        ),
      ),
    for (var i = 1; i <= 6; i++) _decoration(context, i),
  ];
  Widget _decoration(BuildContext context, int index) {
    final id = 'cosmetic.core.decoration.${index.toString().padLeft(2, '0')}';
    final owned = game.story.decorations.contains(id),
        equipped = game.story.equippedDecoration == id;
    const names = [
      'Beacon pennants',
      'Glass buoys',
      'Aurora kite',
      'Tide rings',
      'Shore garden',
      'Returning comets',
    ];
    return _card(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          HarborArt(
            counts: game.state.counts,
            phase: 0,
            restoration: game.story.campaign.restoredHarbor,
            decoration: id,
          ),
          const SizedBox(height: 14),
          Text(
            names[index - 1],
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 12),
          OutlinedButton(
            key: ValueKey('decoration-$index'),
            onPressed: equipped
                ? null
                : owned
                ? () => _perform(context, () => game.equipDecoration(id))
                : game.state.surveyNotes >= BigInt.from(50)
                ? () => _perform(context, () => game.buyDecoration(id))
                : null,
            child: Text(
              equipped
                  ? 'Equipped'
                  : owned
                  ? 'Equip decoration'
                  : 'Keep decoration · 50 Notes',
            ),
          ),
        ],
      ),
    );
  }

  bool _perform(BuildContext context, bool Function() command) {
    final result = command();
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(
        SnackBar(
          content: Text(
            game.lastAction ??
                (result
                    ? 'Your harbor has been updated.'
                    : 'This action is not available yet.'),
          ),
        ),
      );
    return result;
  }

  Future<bool> _confirm(
    BuildContext context,
    String title,
    String body,
    String confirm,
  ) async =>
      await showDialog<bool>(
        context: context,
        builder: (dialog) => AlertDialog(
          title: Text(title),
          content: SingleChildScrollView(child: Text(body)),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialog, false),
              child: const Text('Keep current progress'),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(dialog, true),
              child: Text(confirm),
            ),
          ],
        ),
      ) ??
      false;
  Widget _card({Key? key, required Widget child}) => Container(
    key: key,
    margin: const EdgeInsets.only(bottom: 18),
    decoration: BoxDecoration(
      color: TideColors.panel,
      borderRadius: BorderRadius.circular(18),
      border: Border.all(color: TideColors.line),
    ),
    padding: const EdgeInsets.all(18),
    child: Material(color: Colors.transparent, child: child),
  );
}

class _Cell extends StatelessWidget {
  const _Cell(this.text);
  final String text;
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.all(10),
    child: Text(text, style: const TextStyle(fontSize: 12)),
  );
}

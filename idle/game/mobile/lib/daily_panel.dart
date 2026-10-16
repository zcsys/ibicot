import 'package:flutter/material.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'calibration_pattern.dart';
import 'calibration_screen.dart';
import 'game_controller.dart';
import 'number_format.dart';
import 'palette.dart';

Future<void> openCalibration(BuildContext context, GameController game) async {
  try {
    final patterns = await loadCalibrationPatterns();
    if (!context.mounted) return;
    await Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => ListenableBuilder(
          listenable: game,
          builder: (_, _) => CalibrationScreen(
            patterns: patterns,
            focusCharges: () => game.state.focusCharges,
            collectedIds: () => game.state.completedCalibrationIds,
            onComplete: game.completeCalibration,
          ),
        ),
      ),
    );
  } catch (_) {
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'The constellation charts could not be opened. Your Focus has been kept.',
          ),
        ),
      );
    }
  }
}

class ContractPanel extends StatelessWidget {
  const ContractPanel({super.key, required this.game});
  final GameController game;
  @override
  Widget build(BuildContext context) {
    final pending = game.state.dailyContracts.where((c) => !c.claimed).toList();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text('Crew contracts', style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: 8),
        const Text(
          'Three each account day, kept for seven days. Targets stay fixed. Each completed contract grants 10 Notes and 250 pass XP.',
          style: TextStyle(color: TideColors.muted),
        ),
        const SizedBox(height: 12),
        Text(
          '${game.state.dailyContracts.where((c) => c.claimed).length} claimed · ${game.state.passXp} XP toward the selected pass',
          style: const TextStyle(color: TideColors.amber),
        ),
        const SizedBox(height: 12),
        if (pending.isEmpty)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 16),
            child: Text(
              'All retained contracts are complete. The harbor has no streak to protect.',
            ),
          ),
        for (final contract in pending)
          _ContractCard(game: game, contract: contract),
        const SizedBox(height: 12),
        Text(
          'Account day uses a fixed UTC${game.state.daily.utcOffsetMinutes >= 0 ? '+' : ''}${game.state.daily.utcOffsetMinutes / 60} offset. Traveling will not reset the allowance.',
          style: const TextStyle(color: TideColors.muted, fontSize: 12),
        ),
      ],
    );
  }
}

class _ContractCard extends StatelessWidget {
  const _ContractCard({required this.game, required this.contract});
  final GameController game;
  final DailyContract contract;
  @override
  Widget build(BuildContext context) {
    final progress = game.engine.contractProgress(game.state, contract);
    final ready = progress >= contract.target;
    final title = switch (contract.kind) {
      'restore' => 'Gather ${compactMicros(contract.target)} Radiance',
      'build' => 'Build ${contract.target} lightkeepers',
      _ =>
        'Explore one ${switch (contract.discoveryKind) {
          'calibration' => 'constellation',
          'challenge' => 'challenge',
          _ => 'archive entry',
        }}',
    };
    final shown = contract.kind == 'restore'
        ? '${compactMicros(progress)} / ${compactMicros(contract.target)} R'
        : '$progress / ${contract.target}';
    final age = game.state.daily.dayHighWater - contract.accountDay;
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(title, style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            Text(
              '$shown · ${age == 0 ? 'Today' : '${age}d in the backlog'}',
              style: const TextStyle(color: TideColors.muted),
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 12,
              runSpacing: 8,
              children: [
                FilledButton(
                  key: ValueKey('claim-${contract.id}'),
                  onPressed: ready
                      ? () => game.claimContract(contract.id)
                      : null,
                  child: const Text('Claim 10 Notes + 250 XP'),
                ),
                if (!contract.rerolled && !ready)
                  TextButton(
                    onPressed: () => game.rerollContract(contract.id),
                    child: const Text('Reroll once'),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class AutomationScreen extends StatefulWidget {
  const AutomationScreen({super.key, required this.game});
  final GameController game;
  @override
  State<AutomationScreen> createState() => _AutomationScreenState();
}

class _AutomationScreenState extends State<AutomationScreen> {
  late TextEditingController name, charts, seconds;
  late String id, policy;
  late List<int> priority;
  late bool reset;
  String? notice;
  GameController get game => widget.game;
  @override
  void initState() {
    super.initState();
    name = TextEditingController();
    charts = TextEditingController();
    seconds = TextEditingController();
    load(game.state.selectedAutomationPlan);
  }

  void load(AutomationPlan plan) {
    id = plan.id;
    name.text = plan.name;
    charts.text = plan.minimumAdditionalCharts.toString();
    seconds.text = plan.minimumRunSeconds.toString();
    policy = plan.purchasePolicy;
    priority = plan.tierPriority.toList();
    reset = plan.autoResetEnabled;
  }

  @override
  void dispose() {
    name.dispose();
    charts.dispose();
    seconds.dispose();
    super.dispose();
  }

  void save() {
    final amount = BigInt.tryParse(charts.text),
        duration = int.tryParse(seconds.text);
    if (name.text.trim().isEmpty ||
        amount == null ||
        amount <= BigInt.zero ||
        duration == null ||
        duration < 1) {
      setState(
        () => notice =
            'Choose a name, at least one new Chart, and a run of at least one second.',
      );
      return;
    }
    final plan = AutomationPlan(
      id: id,
      name: name.text.trim(),
      purchasePolicy: policy,
      tierPriority: priority,
      autoResetEnabled: reset,
      minimumAdditionalCharts: amount,
      minimumRunSeconds: duration,
    );
    if (game.savePlan(plan)) {
      game.selectPlan(id);
      setState(
        () => notice =
            'Plan saved and selected. Automatic rebuilding remains your separate choice in the harbor.',
      );
    } else {
      setState(
        () => notice =
            'This plan could not be saved. Check the Chart unlock and available plan slots.',
      );
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('The crew’s plan')),
    body: ListenableBuilder(
      listenable: game,
      builder: (_, _) => SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 640),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const Text(
                  'One free plan. Extra saved plans cost 50 Notes each, up to five. Plans work while you are away.',
                ),
                const SizedBox(height: 20),
                DropdownButtonFormField<String>(
                  key: ValueKey('saved-plan-$id'),
                  isExpanded: true,
                  isDense: false,
                  itemHeight: null,
                  initialValue:
                      game.state.automationPlans.any((p) => p.id == id)
                      ? id
                      : null,
                  decoration: const InputDecoration(labelText: 'Saved plan'),
                  items: game.state.automationPlans
                      .map(
                        (p) =>
                            DropdownMenuItem(value: p.id, child: Text(p.name)),
                      )
                      .toList(),
                  onChanged: (value) {
                    if (value != null) {
                      setState(
                        () => load(
                          game.state.automationPlans.firstWhere(
                            (p) => p.id == value,
                          ),
                        ),
                      );
                    }
                  },
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: name,
                  maxLength: 120,
                  decoration: const InputDecoration(labelText: 'Plan name'),
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  key: ValueKey('policy-$policy'),
                  isExpanded: true,
                  isDense: false,
                  itemHeight: null,
                  initialValue: policy,
                  decoration: const InputDecoration(labelText: 'Buying policy'),
                  items: const [
                    DropdownMenuItem(
                      value: 'greedy',
                      child: Text('Best marginal payback'),
                    ),
                    DropdownMenuItem(
                      value: 'priority',
                      child: Text('Tier priority'),
                    ),
                  ],
                  onChanged: (value) => setState(() => policy = value!),
                ),
                const SizedBox(height: 12),
                const Text(
                  'Best payback waits for the most efficient next purchase. Tier priority waits for the first unlocked tier in your list; it can favor a longer-term route.',
                  style: TextStyle(color: TideColors.muted),
                ),
                if (policy == 'priority') ...[
                  const SizedBox(height: 12),
                  for (var i = 0; i < priority.length; i++)
                    ListTile(
                      contentPadding: EdgeInsets.zero,
                      title: Text(
                        '${i + 1}. ${TideglassEngine.producerNames[priority[i]]}',
                      ),
                      trailing: Wrap(
                        children: [
                          IconButton(
                            tooltip: 'Move earlier',
                            onPressed: i == 0
                                ? null
                                : () => setState(() {
                                    final n = priority.removeAt(i);
                                    priority.insert(i - 1, n);
                                  }),
                            icon: const Icon(Icons.arrow_upward),
                          ),
                          IconButton(
                            tooltip: 'Move later',
                            onPressed: i == 4
                                ? null
                                : () => setState(() {
                                    final n = priority.removeAt(i);
                                    priority.insert(i + 1, n);
                                  }),
                            icon: const Icon(Icons.arrow_downward),
                          ),
                        ],
                      ),
                    ),
                ],
                const SizedBox(height: 20),
                SwitchListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Automatically Rechart'),
                  subtitle: Text(
                    game.state.charts < BigInt.from(100)
                        ? 'Unlocks at 100 Charts.'
                        : 'Rebuild only when both limits below are met. Existing fleet and wallet are spent at every reset.',
                  ),
                  value: reset,
                  onChanged: game.state.charts < BigInt.from(100)
                      ? null
                      : (v) => setState(() => reset = v),
                ),
                TextField(
                  controller: charts,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                    labelText: 'Minimum new Charts per Rechart',
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: seconds,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                    labelText: 'Minimum run length in seconds',
                  ),
                ),
                const SizedBox(height: 12),
                const Text(
                  'These are your chosen conditions, not a prediction of the best possible reset time.',
                  style: TextStyle(color: TideColors.muted),
                ),
                if (notice != null) ...[
                  const SizedBox(height: 16),
                  Text(
                    notice!,
                    style: const TextStyle(color: TideColors.amber),
                  ),
                ],
                const SizedBox(height: 20),
                FilledButton(
                  onPressed: save,
                  child: const Text('Save and select plan'),
                ),
                const SizedBox(height: 12),
                OutlinedButton(
                  onPressed:
                      game.state.extraPlanSlots >= 5 ||
                          game.state.surveyNotes < BigInt.from(50)
                      ? null
                      : () {
                          if (game.buyPlanSlot()) {
                            setState(
                              () => notice = 'A new plan slot is available.',
                            );
                          }
                        },
                  child: Text(
                    'Buy a plan slot · 50 Notes (${1 + game.state.extraPlanSlots}/6 owned)',
                  ),
                ),
                if (game.state.automationPlans.length <
                    1 + game.state.extraPlanSlots)
                  TextButton(
                    onPressed: () => setState(() {
                      load(
                        AutomationPlan(
                          id: 'plan.extra.${game.state.automationPlans.length}',
                          name: 'New plan',
                        ),
                      );
                    }),
                    child: const Text('Create a plan in an empty slot'),
                  ),
              ],
            ),
          ),
        ),
      ),
    ),
  );
}

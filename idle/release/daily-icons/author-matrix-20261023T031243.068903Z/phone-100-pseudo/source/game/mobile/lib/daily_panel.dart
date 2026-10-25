import 'presentation.dart';
import 'daily_icon_label.dart';
import 'strings.dart';
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
          content: LocalizedText(
            UiEnglish.dailyTheConstellationChartsCouldNotBeOpened,
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
        DailyIconLabel(
          icon: Icons.assignment_outlined,
          label: UiEnglish.dailyCrewContracts,
          style: Theme.of(context).textTheme.titleLarge,
        ),
        const SizedBox(height: 8),
        const LocalizedText(
          UiEnglish.dailyThreeEachAccountDayKeptForSeven,
          style: TextStyle(color: TideColors.muted),
        ),
        const SizedBox(height: 12),
        LocalizedText(
          UiEnglish.dailyGameStateDailyContractsWhereCCClaimed(
            game.state.dailyContracts.where((c) => c.claimed).length,
            game.state.passXp,
          ),
          style: const TextStyle(color: TideColors.amber),
        ),
        const SizedBox(height: 12),
        if (pending.isEmpty)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 16),
            child: LocalizedText(
              UiEnglish.dailyAllRetainedContractsAreCompleteTheHarbor,
            ),
          ),
        for (final contract in pending)
          _ContractCard(game: game, contract: contract),
        const SizedBox(height: 12),
        LocalizedText(
          UiEnglish.dailyAccountDayUsesAFixedUTCGame(
            game.state.daily.utcOffsetMinutes >= 0 ? '+' : '',
            game.state.daily.utcOffsetMinutes / 60,
          ),
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
      'restore' => UiEnglish.dailyGatherCompactMicrosContractTargetRadiance(
        compactMicros(contract.target),
      ),
      'build' => UiEnglish.dailyBuildContractTargetLightkeepers(
        contract.target,
      ),
      _ =>
        UiEnglish.dailyExploreOneSwitchContractDiscoveryKindCalibrationConstellation(
          switch (contract.discoveryKind) {
            'calibration' => UiEnglish.constellationNoun,
            'challenge' => UiEnglish.challengeNoun,
            _ => UiEnglish.dailyArchiveEntry,
          },
        ),
    };
    final shown = contract.kind == 'restore'
        ? UiEnglish.dailyCompactMicrosProgressCompactMicrosContractTargetR(
            compactMicros(progress),
            compactMicros(contract.target),
          )
        : '$progress / ${contract.target}';
    final age = game.state.daily.dayHighWater - contract.accountDay;
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            LocalizedText(
              title,
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 8),
            LocalizedText(
              '$shown · ${age == 0 ? UiEnglish.dailyToday : UiEnglish.dailyAgeDInTheBacklog(age)}',
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
                  child: const LocalizedText(UiEnglish.dailyClaimNotesXP),
                ),
                if (!contract.rerolled && !ready)
                  TextButton(
                    onPressed: () => game.rerollContract(contract.id),
                    child: const LocalizedText(UiEnglish.dailyRerollOnce),
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
      setState(() => notice = UiEnglish.dailyChooseANameAtLeastOneNew);
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
            UiEnglish.dailyPlanSavedAndSelectedAutomaticRebuildingRemains,
      );
    } else {
      setState(() => notice = UiEnglish.dailyThisPlanCouldNotBeSavedCheck);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: readingAppBar(context, title: UiEnglish.dailyTheCrewSPlan),
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
                const LocalizedText(
                  UiEnglish.dailyOneFreePlanExtraSavedPlansCost,
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
                  decoration: InputDecoration(
                    labelText: Presentation.text(UiEnglish.dailySavedPlan),
                  ),
                  items: game.state.automationPlans
                      .map(
                        (p) => DropdownMenuItem(
                          value: p.id,
                          child: LocalizedText(p.name),
                        ),
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
                  decoration: InputDecoration(
                    labelText: Presentation.text(UiEnglish.dailyPlanName),
                  ),
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  key: ValueKey('policy-$policy'),
                  isExpanded: true,
                  isDense: false,
                  itemHeight: null,
                  initialValue: policy,
                  decoration: InputDecoration(
                    labelText: Presentation.text(UiEnglish.dailyBuyingPolicy),
                  ),
                  items: const [
                    DropdownMenuItem(
                      value: 'greedy',
                      child: LocalizedText(UiEnglish.dailyBestMarginalPayback),
                    ),
                    DropdownMenuItem(
                      value: 'priority',
                      child: LocalizedText(UiEnglish.dailyTierPriority),
                    ),
                  ],
                  onChanged: (value) => setState(() => policy = value!),
                ),
                const SizedBox(height: 12),
                const LocalizedText(
                  UiEnglish.dailyBestPaybackWaitsForTheMostEfficient,
                  style: TextStyle(color: TideColors.muted),
                ),
                if (policy == 'priority') ...[
                  const SizedBox(height: 12),
                  for (var i = 0; i < priority.length; i++)
                    ListTile(
                      contentPadding: EdgeInsets.zero,
                      title: LocalizedText(
                        '${i + 1}. ${UiEnglish.producerNames[priority[i]]}',
                      ),
                      trailing: Wrap(
                        children: [
                          IconButton(
                            tooltip: Presentation.text(
                              UiEnglish.dailyMoveEarlier,
                            ),
                            onPressed: i == 0
                                ? null
                                : () => setState(() {
                                    final n = priority.removeAt(i);
                                    priority.insert(i - 1, n);
                                  }),
                            icon: const Icon(Icons.arrow_upward),
                          ),
                          IconButton(
                            tooltip: Presentation.text(
                              UiEnglish.dailyMoveLater,
                            ),
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
                  title: const LocalizedText(
                    UiEnglish.dailyAutomaticallyRechart,
                  ),
                  subtitle: LocalizedText(
                    game.state.charts < BigInt.from(100)
                        ? UiEnglish.dailyUnlocksAtCharts
                        : UiEnglish.dailyRebuildOnlyWhenBothLimitsBelowAre,
                  ),
                  value: reset,
                  onChanged: game.state.charts < BigInt.from(100)
                      ? null
                      : (v) => setState(() => reset = v),
                ),
                TextField(
                  controller: charts,
                  keyboardType: TextInputType.number,
                  decoration: InputDecoration(
                    labelText: Presentation.text(
                      UiEnglish.dailyMinimumNewChartsPerRechart,
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: seconds,
                  keyboardType: TextInputType.number,
                  decoration: InputDecoration(
                    labelText: Presentation.text(
                      UiEnglish.dailyMinimumRunLengthInSeconds,
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                const LocalizedText(
                  UiEnglish.dailyTheseAreYourChosenConditionsNotA,
                  style: TextStyle(color: TideColors.muted),
                ),
                if (notice != null) ...[
                  const SizedBox(height: 16),
                  LocalizedText(
                    notice!,
                    style: const TextStyle(color: TideColors.amber),
                  ),
                ],
                const SizedBox(height: 20),
                FilledButton(
                  onPressed: save,
                  child: const LocalizedText(UiEnglish.dailySaveAndSelectPlan),
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
                              () => notice =
                                  UiEnglish.dailyANewPlanSlotIsAvailable,
                            );
                          }
                        },
                  child: LocalizedText(
                    UiEnglish.dailyBuyAPlanSlotNotesGameState(
                      1 + game.state.extraPlanSlots,
                    ),
                  ),
                ),
                if (game.state.automationPlans.length <
                    1 + game.state.extraPlanSlots)
                  TextButton(
                    onPressed: () => setState(() {
                      load(
                        AutomationPlan(
                          id: 'plan.extra.${game.state.automationPlans.length}',
                          name: UiEnglish.dailyNewPlan,
                        ),
                      );
                    }),
                    child: const LocalizedText(
                      UiEnglish.dailyCreateAPlanInAnEmptySlot,
                    ),
                  ),
              ],
            ),
          ),
        ),
      ),
    ),
  );
}

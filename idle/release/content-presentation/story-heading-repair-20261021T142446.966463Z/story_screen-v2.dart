import 'presentation.dart';
import 'strings.dart';
import 'package:flutter/material.dart';
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
    'constrained_fleets': UiEnglish.storyASmallerFleet,
    'synergy_priorities': UiEnglish.storyDifferentConnections,
    'automation_planning': UiEnglish.storyPlansForTheTide,
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
      appBar: MediaQuery.textScalerOf(context).scale(16) > 24
          ? AppBar()
          : readingAppBar(context, title: UiEnglish.storyTheRestoration),
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
                  if (MediaQuery.textScalerOf(context).scale(16) > 24) ...[
                    Semantics(
                      header: true,
                      namesRoute: true,
                      child: LocalizedText(
                        UiEnglish.storyTheRestoration,
                        style: Theme.of(context).textTheme.headlineMedium,
                      ),
                    ),
                    const SizedBox(height: 20),
                  ],
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      for (var i = 0; i < 4; i++)
                        ChoiceChip(
                          key: ValueKey('story-tab-$i'),
                          label: LocalizedText(
                            [
                              UiEnglish.storyChapters,
                              UiEnglish.storyPassages,
                              UiEnglish.storyArchive,
                              UiEnglish.storyDecorations,
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
                    const LocalizedText(
                      UiEnglish.storyTheRestorationCatalogueCouldNotBeLoaded,
                    )
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
      LocalizedText(
        UiEnglish.storyCampaignRestoredHarborOfConstellationsRestored(
          campaign.restoredHarbor,
        ),
        style: Theme.of(context).textTheme.headlineMedium,
      ),
      const SizedBox(height: 10),
      const LocalizedText(
        UiEnglish.storyAPermanentRecordOfWhatYouDiscover,
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
              LocalizedText(
                UiEnglish.storyTheHarborRemembers,
                key: const ValueKey('campaign-ending'),
                style: Theme.of(context).textTheme.headlineMedium,
              ),
              const SizedBox(height: 12),
              LocalizedText(
                game.catalogue!.campaign.chapters.last['completion'] as String,
              ),
              const SizedBox(height: 18),
              FilledButton(
                onPressed: () => Navigator.pop(context),
                child: const LocalizedText(UiEnglish.storyKeepCharting),
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
        // The status words carry the same meaning when large text needs the
        // full header width. Keep the disclosure control and all copy intact.
        leading: MediaQuery.textScalerOf(context).scale(16) > 24
            ? null
            : Icon(
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
        title: LocalizedText('${index + 1}. ${chapter['title']}'),
        subtitle: LocalizedText(
          complete
              ? UiEnglish.storyRestored
              : unlocked
              ? UiEnglish.storyYourCurrentChapter
              : UiEnglish.storyCompleteChapterIndexFirst(index),
          style: const TextStyle(color: TideColors.muted),
        ),
        children: [
          Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              LocalizedText(chapter['intro'] as String),
              const SizedBox(height: 18),
              for (final raw in chapter['objectives'] as List)
                _objective(Map<String, dynamic>.from(raw), recorded: complete),
              const SizedBox(height: 10),
              for (final hint in chapter['hints'] as List)
                Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: LocalizedText(
                    '• $hint',
                    style: const TextStyle(
                      color: TideColors.muted,
                      fontSize: 13,
                    ),
                  ),
                ),
              if (complete) ...[
                const SizedBox(height: 10),
                LocalizedText(
                  chapter['completion'] as String,
                  style: const TextStyle(color: TideColors.teal),
                ),
              ],
              const SizedBox(height: 12),
              const LocalizedText(
                UiEnglish.storyKeepsakeARestoredSkyThreeArchiveEntries,
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
        label =
            UiEnglish.storyTideglassEngineProducerNamesTierInYourCurrentFleet(
              Presentation.authored((UiEnglish.producerNames[tier]).toString()),
            );
        value = '${facts.main.counts[tier]}';
      case 'challenge_family_min':
        label = UiEnglish.storyPassagesFamilyLabelsGoalFamily(
          familyLabels[goal['family']],
        );
        value =
            '${facts.completedChallenges.where((id) => game.catalogue!.campaign.families[id] == goal['family']).length}';
      default:
        switch (goal['stat']) {
          case 'recharts':
            label = UiEnglish.storyRechartsCompleted;
            value = '${facts.recharts}';
          case 'charts_awarded':
            label = UiEnglish.storyPermanentCharts;
            value = '${facts.main.charts}';
          case 'surveys_collected':
            label = UiEnglish.storySurveysCollected;
            value = '${facts.surveysCollected}';
          default:
            label = UiEnglish.storyDistinctCalibrationPatterns;
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
            child: LocalizedText(
              recorded
                  ? UiEnglish.storyLabelTargetAchieved(label, target)
                  : '$label · $value / $target',
            ),
          ),
        ],
      ),
    );
  }

  List<Widget> _archive(BuildContext context) => [
    LocalizedText(
      UiEnglish.storyTheKeeperSArchive,
      style: Theme.of(context).textTheme.headlineMedium,
    ),
    const SizedBox(height: 10),
    LocalizedText(
      UiEnglish.storyGameStoryCampaignArchiveIdsLengthOfAccounts(
        game.story.campaign.archiveIds.length,
      ),
      style: const TextStyle(color: TideColors.muted),
    ),
    const SizedBox(height: 24),
    for (final entry in game.catalogue!.archive)
      _card(
        child: game.story.campaign.archiveIds.contains(entry['id'])
            ? ExpansionTile(
                key: PageStorageKey(entry['id']),
                tilePadding: EdgeInsets.zero,
                title: LocalizedText(entry['title'] as String),
                leading: const Icon(
                  Icons.menu_book_outlined,
                  color: TideColors.amber,
                ),
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      LocalizedText(entry['text'] as String),
                      const SizedBox(height: 14),
                      OutlinedButton(
                        key: ValueKey('read-${entry['id']}'),
                        onPressed: () => _perform(
                          context,
                          () => game.readArchive(entry['id'] as String),
                        ),
                        child: const LocalizedText(
                          UiEnglish.storyReflectOnThisAccount,
                        ),
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
                title: LocalizedText(entry['title'] as String),
                subtitle: LocalizedText(
                  UiEnglish.storyRestoresWithChapterIntParseEntryChapter(
                    int.parse((entry['chapter_id'] as String).split('.').last),
                  ),
                ),
              ),
      ),
  ];
  List<Widget> _dossiers(BuildContext context) {
    final collection = game.story.dossiers;
    return [
      LocalizedText(
        UiEnglish.storyPassagesBeyondTheHarbor,
        style: Theme.of(context).textTheme.headlineMedium,
      ),
      const SizedBox(height: 10),
      LocalizedText(
        UiEnglish.storyGameStateSurveyNotesSurveyNotesCollectionCompleted(
          game.state.surveyNotes,
          collection.completed.length,
        ),
        style: const TextStyle(color: TideColors.amber),
      ),
      const SizedBox(height: 12),
      const LocalizedText(
        UiEnglish.storyEachDossierOpensASeparateFleetYour,
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
          child: const LocalizedText(
            UiEnglish.storyFinishTheQuietWatchChapterToOpen,
          ),
        ),
      for (final family in familyLabels.entries) ...[
        const SizedBox(height: 12),
        LocalizedText(
          family.value,
          style: Theme.of(context).textTheme.titleLarge,
        ),
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
                child: LocalizedText(
                  definition.title,
                  style: Theme.of(context).textTheme.titleMedium,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          LocalizedText(
            definition.intro,
            style: const TextStyle(color: TideColors.muted),
          ),
          const SizedBox(height: 10),
          LocalizedText(
            UiEnglish.storyGoalCompactMicrosDefinitionGoalMicrosLifetimePassageRadiance(
              compactMicros(definition.goalMicros),
            ),
            style: const TextStyle(fontSize: 12),
          ),
          const SizedBox(height: 14),
          OutlinedButton(
            key: ValueKey('open-${definition.id}'),
            onPressed: !active && canOpen
                ? () => _open(context, definition)
                : null,
            child: LocalizedText(
              active
                  ? UiEnglish.storyYourActivePassage
                  : owned
                  ? UiEnglish.storyOpenOwnedDossierFree
                  : UiEnglish.storyOpenDossierNotes,
            ),
          ),
          if (completed)
            const Padding(
              padding: EdgeInsets.only(top: 8),
              child: LocalizedText(
                UiEnglish.storyChartedReplayWheneverYouLike,
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
      replacing
          ? UiEnglish.storyReplaceTheActivePassage
          : UiEnglish.storyOpenDefinitionTitle(
              Presentation.authored((definition.title).toString()),
            ),
      UiEnglish.storyOwnedThisDossierIsAlreadyYoursOpening(
        owned
            ? UiEnglish.storyThisDossierIsAlreadyYoursOpeningIt
            : UiEnglish.storySpendSurveyNotesToKeepThisDossier,
        replacing ? UiEnglish.storyYourCurrentPassageFleetAndItsUnfinished : '',
      ),
      replacing ? UiEnglish.storyReplaceAndOpen : UiEnglish.storyOpenDossier,
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
          const LocalizedText(
            UiEnglish.storyPASSAGEFLEET,
            style: TextStyle(
              color: TideColors.amber,
              fontSize: 11,
              letterSpacing: 1.5,
            ),
          ),
          const SizedBox(height: 8),
          LocalizedText(
            definition.title,
            style: Theme.of(context).textTheme.headlineMedium,
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 24,
            runSpacing: 8,
            children: [
              LocalizedText(
                UiEnglish.storyCompactMicrosRunFleetWalletMicrosR(
                  compactMicros(run.fleet.walletMicros),
                ),
                key: const ValueKey('challenge-wallet'),
                style: Theme.of(context).textTheme.titleLarge,
              ),
              LocalizedText(
                UiEnglish.storyCompactFixedEconomyOutputPerSecondRunFleetRS(
                  compactFixed(economy.outputPerSecond(run.fleet)),
                ),
                style: const TextStyle(color: TideColors.teal),
              ),
            ],
          ),
          const SizedBox(height: 16),
          LinearProgressIndicator(value: fraction, minHeight: 6),
          const SizedBox(height: 8),
          LocalizedText(
            UiEnglish.storyCompactMicrosRunFleetLifetimeMicrosCompactMicrosDefinitionGoalMic(
              compactMicros(run.fleet.lifetimeMicros),
              compactMicros(definition.goalMicros),
            ),
            style: const TextStyle(color: TideColors.muted, fontSize: 12),
          ),
          if (run.complete) ...[
            const SizedBox(height: 14),
            LocalizedText(
              definition.completion,
              style: const TextStyle(color: TideColors.teal),
            ),
            const SizedBox(height: 8),
            const LocalizedText(
              UiEnglish.storyPassageChartedItsDiscoveryIsKeptIn,
              key: ValueKey('challenge-complete'),
            ),
          ],
          const SizedBox(height: 18),
          const LocalizedText(
            UiEnglish.storyYouCanReturnToTheHarborWithout,
            style: TextStyle(color: TideColors.muted, fontSize: 12),
          ),
          const SizedBox(height: 18),
          if (definition.automaticOnly)
            const ListTile(
              contentPadding: EdgeInsets.zero,
              title: LocalizedText(
                UiEnglish.storyThePassageCrewBuildsAutomatically,
              ),
              subtitle: LocalizedText(
                UiEnglish.storyChooseThePlanTheyFollowBelow,
              ),
              trailing: Icon(
                Icons.check_circle_outline,
                color: TideColors.teal,
              ),
            )
          else
            SwitchListTile.adaptive(
              contentPadding: EdgeInsets.zero,
              title: const LocalizedText(UiEnglish.storyLetThePassageCrewBuild),
              subtitle: const LocalizedText(
                UiEnglish.storyPauseThePlanToMakePurchasesYourself,
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
              decoration: InputDecoration(
                labelText: Presentation.text(UiEnglish.storyPurchaseApproach),
                border: OutlineInputBorder(),
              ),
              items: const [
                DropdownMenuItem(
                  value: ChallengePolicy.bestPayback,
                  child: LocalizedText(UiEnglish.storyBestPayback),
                ),
                DropdownMenuItem(
                  value: ChallengePolicy.tierPriority,
                  child: LocalizedText(UiEnglish.storyTierPriority),
                ),
              ],
              onChanged: (value) {
                if (value != null) {
                  game.setDossierPlan(policy: value);
                }
              },
            ),
            const SizedBox(height: 10),
            const LocalizedText(
              UiEnglish.storyBestPaybackWaitsForTheMostEfficient,
              style: TextStyle(color: TideColors.muted, fontSize: 12),
            ),
            if (run.policy == ChallengePolicy.tierPriority) ...[
              const SizedBox(height: 14),
              for (var i = 0; i < 5; i++)
                Row(
                  children: [
                    Expanded(
                      child: LocalizedText(
                        '${i + 1}. ${UiEnglish.producerNames[run.priority[i]]}',
                      ),
                    ),
                    IconButton(
                      key: ValueKey('priority-up-$i'),
                      tooltip: Presentation.text(
                        UiEnglish.storyMoveTideglassEngineProducerNamesRunPriorityIEarlier(
                          Presentation.authored(
                            (UiEnglish.producerNames[run.priority[i]])
                                .toString(),
                          ),
                        ),
                      ),
                      onPressed: i == 0
                          ? null
                          : () => _movePriority(run, i, -1),
                      icon: const Icon(Icons.arrow_upward),
                    ),
                    IconButton(
                      tooltip: Presentation.text(
                        UiEnglish.storyMoveTideglassEngineProducerNamesRunPriorityILater(
                          Presentation.authored(
                            (UiEnglish.producerNames[run.priority[i]])
                                .toString(),
                          ),
                        ),
                      ),
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
            title: const LocalizedText(UiEnglish.storyPassageNetworkRules),
            children: [
              LocalizedText(
                definition.synergyImmediate
                    ? UiEnglish.storyTheseCrossTierLinksApplyFromThe
                    : UiEnglish.storyThisPassageHasNoCrossTierMultipliers,
                style: const TextStyle(color: TideColors.muted, fontSize: 12),
              ),
              if (definition.synergyImmediate) ...[
                const SizedBox(height: 12),
                Table(
                  border: TableBorder.all(color: TideColors.line),
                  children: [
                    const TableRow(
                      children: [
                        _Cell(UiEnglish.storySource),
                        _Cell(UiEnglish.storyLoom),
                        _Cell(UiEnglish.storyDawn),
                      ],
                    ),
                    for (var row = 0; row < 2; row++)
                      TableRow(
                        children: [
                          _Cell(
                            row == 0
                                ? UiEnglish.storySkiffs
                                : UiEnglish.storyNurseries,
                          ),
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
                child: const LocalizedText(UiEnglish.storyRestartFleetFree),
              ),
              TextButton(
                onPressed: () => _leave(context),
                child: const LocalizedText(UiEnglish.storyCloseThisPassage),
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
                child: LocalizedText(
                  UiEnglish.storyTideglassEngineProducerNamesTierNRunFleetCounts(
                    Presentation.authored(
                      (UiEnglish.producerNames[tier]).toString(),
                    ),
                    run.fleet.counts[tier],
                    cap == null ? '' : ' / $cap',
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          if (cap != null && run.fleet.counts[tier] >= cap)
            const LocalizedText(
              UiEnglish.storyBerthLimitReached,
              style: TextStyle(color: TideColors.muted, fontSize: 12),
            )
          else if (!unlocked)
            LocalizedText(
              UiEnglish.storyNeedsTideglassEngineProducerNamesTier(
                Presentation.authored(
                  (UiEnglish.producerNames[tier - 1]).toString(),
                ),
              ),
              style: const TextStyle(color: TideColors.muted, fontSize: 12),
            )
          else
            OutlinedButton(
              key: ValueKey('challenge-buy-$tier'),
              onPressed: affordable && !economy.definition.automaticOnly
                  ? () => _perform(context, () => game.buyInDossier(tier))
                  : null,
              child: LocalizedText(
                UiEnglish.storyEconomyDefinitionAutomaticOnlyCrewPurchaseBuildCompactMicros(
                  economy.definition.automaticOnly
                      ? UiEnglish.storyCrewPurchase
                      : UiEnglish.storyBuild,
                  compactMicros(
                    economy.priceMicros(tier, run.fleet.counts[tier]),
                  ),
                ),
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
          UiEnglish.storyRestartThisPassageFleet,
          UiEnglish.storyTheCurrentPassageRadianceAndFleetWill,
          UiEnglish.storyRestartFleet,
        ) &&
        context.mounted) {
      _perform(context, game.restartDossier);
    }
  }

  Future<void> _leave(BuildContext context) async {
    if (await _confirm(
          context,
          UiEnglish.storyCloseThisPassage2,
          UiEnglish.storyTheCurrentPassageFleetAndUnfinishedProgress,
          UiEnglish.storyClosePassage,
        ) &&
        context.mounted) {
      _perform(context, game.leaveDossier);
    }
  }

  List<Widget> _decorations(BuildContext context) => [
    LocalizedText(
      UiEnglish.storyMakeTheHarborYours,
      style: Theme.of(context).textTheme.headlineMedium,
    ),
    const SizedBox(height: 10),
    const LocalizedText(
      UiEnglish.storySixOptionalDecorationsSurveyNotesEachPurely,
      style: TextStyle(color: TideColors.muted),
    ),
    const SizedBox(height: 18),
    if (game.story.equippedDecoration != null)
      Padding(
        padding: const EdgeInsets.only(bottom: 18),
        child: OutlinedButton(
          key: const ValueKey('unequip-decoration'),
          onPressed: () => _perform(context, game.unequipDecoration),
          child: const LocalizedText(UiEnglish.storyShowTheUndecoratedHarbor),
        ),
      ),
    for (var i = 1; i <= 6; i++) _decoration(context, i),
  ];
  Widget _decoration(BuildContext context, int index) {
    final id = 'cosmetic.core.decoration.${index.toString().padLeft(2, '0')}';
    final owned = game.story.decorations.contains(id),
        equipped = game.story.equippedDecoration == id;
    const names = [
      UiEnglish.storyBeaconPennants,
      UiEnglish.storyGlassBuoys,
      UiEnglish.storyAuroraKite,
      UiEnglish.storyTideRings,
      UiEnglish.storyShoreGarden,
      UiEnglish.storyReturningComets,
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
          LocalizedText(
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
            child: LocalizedText(
              equipped
                  ? UiEnglish.storyEquipped
                  : owned
                  ? UiEnglish.storyEquipDecoration
                  : UiEnglish.storyKeepDecorationNotes,
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
          content: LocalizedText(
            game.lastAction ??
                (result
                    ? UiEnglish.storyYourHarborHasBeenUpdated
                    : UiEnglish.storyThisActionIsNotAvailableYet),
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
        builder: (dialog) => ReadingDialog(
          title: LocalizedText(title),
          content: SingleChildScrollView(child: LocalizedText(body)),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialog, false),
              child: const LocalizedText(UiEnglish.storyKeepCurrentProgress),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(dialog, true),
              child: LocalizedText(confirm),
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
    child: LocalizedText(text, style: const TextStyle(fontSize: 12)),
  );
}

import 'presentation.dart';
import 'strings.dart';
import 'package:flutter/material.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'game_controller.dart';
import 'number_format.dart';
import 'palette.dart';

/// Both a briefing and a verified ad use the same core allowance. This screen
/// offers the complete free route; it never manufactures ad-completion proof.
class SupportScreen extends StatelessWidget {
  const SupportScreen({
    super.key,
    required this.game,
    this.onCompletedBriefing,
    this.onRewardedAd,
    this.servicePanel,
    this.serviceBusy = false,
  });
  final GameController game;
  final Future<void> Function(int)? onCompletedBriefing, onRewardedAd;
  final Widget? servicePanel;
  final bool serviceBusy;
  static const briefings = [
    (
      UiEnglish.supportAPatientHarbor,
      UiEnglish.supportYourFleetWorksWhileYouAreAway,
    ),
    (
      UiEnglish.supportTheOldCraftMatter,
      UiEnglish.supportAtChartsSkiffsAndNurseriesStrengthenYour,
    ),
    (
      UiEnglish.supportAChartRemembers,
      UiEnglish.supportRechartRebuildsYourFleetAndKeepsLifetime,
    ),
    (
      UiEnglish.supportAPlanYouCanChange,
      UiEnglish.supportTheCrewCanBuyForTheBest,
    ),
    (
      UiEnglish.supportADifferentPassage,
      UiEnglish.supportChallengeDossiersUseTheirOwnFleetsYour,
    ),
    (
      UiEnglish.supportKeepTheWatchGentle,
      UiEnglish.supportSupportIsOptionalItsAllowanceHasNo,
    ),
  ];

  Future<void> _briefing(BuildContext context, int slot) async {
    final copy = briefings[slot];
    final accepted = await showDialog<bool>(
      context: context,
      builder: (dialog) => ReadingDialog(
        title: LocalizedText(copy.$1),
        content: SingleChildScrollView(
          child: LocalizedText(
            UiEnglish.supportCopyNNCompletingThisBriefingUsesOne(copy.$2),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialog, false),
            child: const LocalizedText(UiEnglish.supportLater),
          ),
          FilledButton(
            key: const ValueKey('complete-briefing'),
            onPressed: () => Navigator.pop(dialog, true),
            child: const LocalizedText(UiEnglish.supportCompleteBriefing),
          ),
        ],
      ),
    );
    if (accepted == true) {
      if (onCompletedBriefing != null) {
        await onCompletedBriefing!(slot);
      } else {
        game.completeCrewBriefing(slot);
      }
    }
  }

  @override
  Widget build(BuildContext context) => ListenableBuilder(
    listenable: game,
    builder: (context, _) {
      final support = game.state.support;
      final tokens = support.tokens.where((token) => !token.spent).toList();
      final currentDay = game.state.daily.dayHighWater;
      final slots = support.tokenDay == currentDay
          ? support.tokens.map((token) => token.slot).toSet()
          : <int>{};
      final nextSlot = List.generate(
        6,
        (i) => i,
      ).where((i) => !slots.contains(i)).firstOrNull;
      final availableToken = support.tokenDay == currentDay
          ? tokens.firstOrNull
          : null;
      final caches = support.caches
          .where(
            (cache) =>
                !support.claimedSliceIds.contains(cache.id) &&
                game.engine.salvageBonusMicros(cache) > BigInt.zero,
          )
          .toList();
      return Scaffold(
        appBar: readingAppBar(context, title: UiEnglish.supportCrewSupport),
        body: SafeArea(
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 760),
              child: ListView(
                padding: const EdgeInsets.all(24),
                children: [
                  LocalizedText(
                    UiEnglish.supportALittleHelpFreelyAvailable,
                    style: Theme.of(context).textTheme.headlineSmall,
                  ),
                  const SizedBox(height: 12),
                  const LocalizedText(
                    UiEnglish.supportSixSharedSlotsEachAccountDayA,
                  ),
                  const SizedBox(height: 16),
                  LocalizedText(
                    UiEnglish.supportSlotsLengthOfSlotsUsedAvailableTokenNull(
                      slots.length,
                      availableToken == null ? 0 : tokens.length,
                    ),
                    key: const ValueKey('support-allowance'),
                  ),
                  const SizedBox(height: 12),
                  FilledButton.icon(
                    key: const ValueKey('open-briefing'),
                    onPressed: nextSlot == null || serviceBusy
                        ? null
                        : () => _briefing(context, nextSlot),
                    icon: const Icon(Icons.menu_book_outlined),
                    label: LocalizedText(
                      nextSlot == null
                          ? UiEnglish.supportAllSixSlotsUsedToday
                          : UiEnglish.supportReadACrewBriefing,
                    ),
                  ),
                  if (onRewardedAd != null) ...[
                    const SizedBox(height: 12),
                    OutlinedButton.icon(
                      key: const ValueKey('watch-support-ad'),
                      onPressed: nextSlot == null || serviceBusy
                          ? null
                          : () => onRewardedAd!(nextSlot),
                      icon: const Icon(Icons.ondemand_video_outlined),
                      label: const LocalizedText(
                        UiEnglish.supportOptionalAdTheSameToken,
                      ),
                    ),
                  ],
                  if (servicePanel != null) ...[
                    const SizedBox(height: 12),
                    servicePanel!,
                  ],
                  const SizedBox(height: 12),
                  const LocalizedText(
                    UiEnglish.supportUnusedTokensExpireAtYourFixedAccount,
                    style: TextStyle(color: TideColors.muted),
                  ),
                  const SizedBox(height: 28),
                  LocalizedText(
                    UiEnglish.supportSteadyTheLight,
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 8),
                  const LocalizedText(
                    UiEnglish
                        .supportProductionForMinutesPerTokenRepeatingQueues,
                  ),
                  if (support.remainingMicros > BigInt.zero)
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      child: LocalizedText(
                        UiEnglish.supportSupportRemainingMicrosBigIntFromToStringSecondsOf(
                          (support.remainingMicros ~/ BigInt.from(1000000))
                              .toString(),
                        ),
                      ),
                    ),
                  const SizedBox(height: 12),
                  OutlinedButton(
                    key: const ValueKey('use-support-boost'),
                    onPressed: availableToken == null
                        ? null
                        : () => game.useSupportBoost(availableToken.id),
                    child: const LocalizedText(
                      UiEnglish.supportUseTokenForMinutes,
                    ),
                  ),
                  const SizedBox(height: 28),
                  LocalizedText(
                    UiEnglish.supportSalvageCache,
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 8),
                  const LocalizedText(
                    UiEnglish.supportYourSixLatestCompleteFiveMinuteSlices,
                  ),
                  const SizedBox(height: 12),
                  if (caches.isEmpty)
                    const LocalizedText(
                      UiEnglish.supportNoUnclaimedSliceIsAvailableReturnAfter,
                      style: TextStyle(color: TideColors.muted),
                    ),
                  for (var i = 0; i < caches.length; i++)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: Card(
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.stretch,
                            children: [
                              LocalizedText(
                                UiEnglish.supportSliceICompactMicrosGameEngineSalvageBonusMicrosCaches(
                                  i + 1,
                                  compactMicros(
                                    game.engine.salvageBonusMicros(caches[i]),
                                  ),
                                ),
                              ),
                              const SizedBox(height: 8),
                              OutlinedButton(
                                key: ValueKey('salvage-${caches[i].id}'),
                                onPressed: availableToken == null
                                    ? null
                                    : () => game.claimSalvage(
                                        availableToken.id,
                                        caches[i].id,
                                      ),
                                child: const LocalizedText(
                                  UiEnglish.supportUseTokenMatchThisSlice,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  const SizedBox(height: 16),
                  const LocalizedText(
                    UiEnglish
                        .supportSupportChangesMainHarborProductionOnlyChallenges,
                    style: TextStyle(color: TideColors.muted),
                  ),
                ],
              ),
            ),
          ),
        ),
      );
    },
  );
}

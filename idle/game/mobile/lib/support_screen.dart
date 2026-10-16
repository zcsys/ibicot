import 'package:flutter/material.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'game_controller.dart';
import 'number_format.dart';
import 'palette.dart';

/// Both a briefing and a verified ad use the same core allowance. This screen
/// offers the complete free route; it never manufactures ad-completion proof.
class SupportScreen extends StatelessWidget {
  const SupportScreen({super.key, required this.game});
  final GameController game;
  static const briefings = [
    (
      'A patient harbor',
      'Your fleet works while you are away. The first 24 hours keep full production, followed by 48 hours at one quarter. A longer break does not erase your harbor.',
    ),
    (
      'The old craft matter',
      'At 25 Charts, Skiffs and Nurseries strengthen your Looms and Observatories. The smallest craft can still be worth building.',
    ),
    (
      'A chart remembers',
      'Rechart rebuilds your fleet and keeps lifetime earnings, Charts, Notes and your discoveries. Preview the gain before choosing to start again.',
    ),
    (
      'A plan you can change',
      'The crew can buy for the best payback or follow your tier priorities. A saved plan does no work until you choose it and enable automatic building.',
    ),
    (
      'A different passage',
      'Challenge dossiers use their own fleets. Your main harbor keeps working. Notes open a dossier once; replaying it is free.',
    ),
    (
      'Keep the watch gentle',
      'Support is optional. Its allowance has no streak, paid refill or catch-up penalty. Focus and Support add together: +20% and +25% give +45%.',
    ),
  ];

  Future<void> _briefing(BuildContext context, int slot) async {
    final copy = briefings[slot];
    final accepted = await showDialog<bool>(
      context: context,
      builder: (dialog) => AlertDialog(
        title: Text(copy.$1),
        content: SingleChildScrollView(
          child: Text(
            '${copy.$2}\n\nCompleting this briefing uses one of today’s six shared Support slots. The token expires at your account-day boundary.',
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialog, false),
            child: const Text('Later'),
          ),
          FilledButton(
            key: const ValueKey('complete-briefing'),
            onPressed: () => Navigator.pop(dialog, true),
            child: const Text('Complete briefing'),
          ),
        ],
      ),
    );
    if (accepted == true) game.completeCrewBriefing(slot);
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
        appBar: AppBar(title: const Text('Crew Support')),
        body: SafeArea(
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 760),
              child: ListView(
                padding: const EdgeInsets.all(24),
                children: [
                  Text(
                    'A little help, freely available',
                    style: Theme.of(context).textTheme.headlineSmall,
                  ),
                  const SizedBox(height: 12),
                  const Text(
                    'Six shared slots each account day. A crew briefing grants one token. Spend it on a short boost or a genuine salvage slice. Neither is needed to finish the restoration.',
                  ),
                  const SizedBox(height: 16),
                  Text(
                    '${slots.length} of 6 slots used · ${availableToken == null ? 0 : tokens.length} unspent tokens',
                    key: const ValueKey('support-allowance'),
                  ),
                  const SizedBox(height: 12),
                  FilledButton.icon(
                    key: const ValueKey('open-briefing'),
                    onPressed: nextSlot == null
                        ? null
                        : () => _briefing(context, nextSlot),
                    icon: const Icon(Icons.menu_book_outlined),
                    label: Text(
                      nextSlot == null
                          ? 'All six slots used today'
                          : 'Read a crew briefing',
                    ),
                  ),
                  const SizedBox(height: 12),
                  const Text(
                    'Unused tokens expire at your fixed account-day boundary. A boost already queued keeps its remaining real time, including through Rechart.',
                    style: TextStyle(color: TideColors.muted),
                  ),
                  const SizedBox(height: 28),
                  Text(
                    'Steady the light',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    '+25% production for 20 minutes per token. Repeating queues time. With Focus, the combined bonus is +45%.',
                  ),
                  if (support.remainingMicros > BigInt.zero)
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      child: Text(
                        '${(support.remainingMicros ~/ BigInt.from(1000000)).toString()} seconds of Support remaining',
                      ),
                    ),
                  const SizedBox(height: 12),
                  OutlinedButton(
                    key: const ValueKey('use-support-boost'),
                    onPressed: availableToken == null
                        ? null
                        : () => game.useSupportBoost(availableToken.id),
                    child: const Text('Use 1 token · +25% for 20 minutes'),
                  ),
                  const SizedBox(height: 28),
                  Text(
                    'Salvage cache',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Your six latest complete five-minute slices of credited time away are retained. A token matches a slice’s unboosted earnings, capped at five minutes of the unboosted rate when that return was settled. Later building cannot enlarge the reward. Partial slices are not kept.',
                  ),
                  const SizedBox(height: 12),
                  if (caches.isEmpty)
                    const Text(
                      'No unclaimed slice is available. Return after at least five minutes away to form a cache.',
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
                              Text(
                                'Slice ${i + 1} · ${compactMicros(game.engine.salvageBonusMicros(caches[i]))} R',
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
                                child: const Text(
                                  'Use 1 token · match this slice',
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  const SizedBox(height: 16),
                  const Text(
                    'Support changes main-harbor production only. Challenges and seasonal fleets keep their own rules.',
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

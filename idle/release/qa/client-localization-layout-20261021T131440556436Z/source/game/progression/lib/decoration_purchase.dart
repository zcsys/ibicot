import 'package:tideglass_core/tideglass_core.dart';

class DecorationPurchase {
  DecorationPurchase(this.accepted, this.main, Set<String> owned)
    : owned = Set.unmodifiable(owned);
  final bool accepted;
  final GameState main;
  final Set<String> owned;
}

/// The shared main-world Note transaction. Equipping is a client preference;
/// this transaction has no effect on wallets, production or earned Charts.
DecorationPurchase buyDecoration(GameState main, Set<String> owned, String id) {
  if (!RegExp(r'^cosmetic\.core\.decoration\.0[1-6]$').hasMatch(id) ||
      owned.contains(id) ||
      main.surveyNotes < BigInt.from(50)) {
    return DecorationPurchase(false, main, owned);
  }
  return DecorationPurchase(
    true,
    main.copyWith(
      surveyNotes: main.surveyNotes - BigInt.from(50),
      revision: main.revision + 1,
    ),
    {...owned, id},
  );
}

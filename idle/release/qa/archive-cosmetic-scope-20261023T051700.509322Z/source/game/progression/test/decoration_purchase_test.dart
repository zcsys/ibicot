import 'package:test/test.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_progression/decoration_purchase.dart';

void main() {
  test('six cosmetic purchases spend only300 Notes and cannot repeat', () {
    var main = GameState.initial().copyWith(surveyNotes: BigInt.from(350));
    final initial = main.toJson();
    var owned = <String>{};
    for (var i = 1; i <= 6; i++) {
      final id = 'cosmetic.core.decoration.0$i';
      final purchase = buyDecoration(main, owned, id);
      expect(purchase.accepted, isTrue);
      main = purchase.main;
      owned = purchase.owned;
      final repeat = buyDecoration(main, owned, id);
      expect(repeat.accepted, isFalse);
      expect(identical(repeat.main, main), isTrue);
    }
    final actual = main.toJson();
    initial['survey_notes'] = actual['survey_notes'];
    initial['revision'] = actual['revision'];
    expect(actual, initial);
    expect(main.surveyNotes, BigInt.from(50));
    expect(owned.length, 6);
  });
  test(
    'invalid IDs and insufficient Notes leave exact source state unchanged',
    () {
      final main = GameState.initial().copyWith(surveyNotes: BigInt.from(49));
      for (final id in [
        'cosmetic.core.decoration.01',
        'cosmetic.shop.01',
        'cosmetic.core.decoration.07',
      ]) {
        final purchase = buyDecoration(main, {}, id);
        expect(purchase.accepted, isFalse);
        expect(identical(purchase.main, main), isTrue);
        expect(purchase.owned, isEmpty);
      }
    },
  );
}

import 'dart:convert';
import 'package:tideglass_core/tideglass_core.dart';

// Deliberately reads state omitted from the base engine's numeric cache key.
class WalletRule extends TideglassEngine {
  const WalletRule();
  @override
  Fixed producerOutputPerSecond(GameState state, int tierIndex) => Fixed.raw(
    super.producerOutputPerSecond(state, tierIndex).raw + state.walletMicros * Fixed.scale,
  );
}
// Same runtime type, different immutable rules; runtime type alone is not a key.
class ParameterRule extends TideglassEngine {
  const ParameterRule(this.factor);
  final int factor;
  @override
  int milestoneMultiplier(int owned) => super.milestoneMultiplier(owned) * factor;
}
void main() {
  const base = TideglassEngine(), walletRule = WalletRule();
  var assertions = 0;
  void equal(BigInt actual, BigInt expected, String label) {
    assertions++;
    if (actual != expected) throw StateError('$label: $actual != $expected');
  }
  final state = GameState(counts: [25, 25, 25, 25, 25], charts: BigInt.from(25));
  final baseline = base.outputPerSecond(state).raw;
  for (var round = 0; round < 2; round++) {
    for (var n = 1; n <= 64; n++) {
      final i = round == 0 ? n : 65 - n;
      final modified = state.copyWith(walletMicros: BigInt.from(i));
      equal(walletRule.outputPerSecond(modified).raw,
        baseline + BigInt.from(i * 5) * Fixed.scale, 'wallet state $i');
      equal(ParameterRule(i).outputPerSecond(state).raw,
        List.generate(5, (t) => ParameterRule(i).producerOutputPerSecond(state, t).raw)
          .fold(BigInt.zero, (a, b) => a + b), 'same class parameter $i');
      equal(base.outputPerSecond(modified).raw, baseline, 'base unchanged $i');
      equal(ParameterRule(i).priceMicros(i % 5, i), base.priceMicros(i % 5, i), 'shared fixed price $i');
    }
  }
  print(jsonEncode({'status': 'passed', 'assertions': assertions,
    'extra_state_values': 64, 'same_runtime_type_rule_instances': 64,
    'orders': ['forward', 'reverse'], 'limits': 'Deliberate subclass fixtures; no content or physical-device qualification'}));
}

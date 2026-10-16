import 'dart:convert';
import 'dart:io';
import 'dart:math' as math;
import 'package:tideglass_core/tideglass_core.dart';

void main() {
  const engine = TideglassEngine();
  final beyondDoubleInteger = BigInt.from(2).pow(53);
  final beyondNativeInteger = BigInt.from(2).pow(63);
  final huge = BigInt.from(10).pow(3000);
  final price = engine.priceMicros(4, 500);
  final state = GameState(counts: [10,10,10,10,500],walletMicros: price-BigInt.one,lifetimeMicros: price-BigInt.one);
  final below = engine.buy(state,4,1);
  final exact = engine.buy(state.copyWith(walletMicros:price,lifetimeMicros:price),4,1);
  final observations = <String,Object?>{
    'double_adjacent_2pow53_collapses': beyondDoubleInteger.toDouble()==(beyondDoubleInteger+BigInt.one).toDouble(),
    'native_int_max_plus_one': (int.parse('9223372036854775807')+1).toString(),
    'bigint_2pow63': beyondNativeInteger.toString(),
    'bigint_3001_digit_neighbors_distinct': huge != huge-BigInt.one,
    'double_1e3000_is_infinite': huge.toDouble().isInfinite,
    'log10_neighbor_collapses_at_1e30': math.log(1e30)/math.ln10==math.log(1e30+1)/math.ln10,
    'tier5_count500_price_micros': price.toString(),
    'double_price_minus_one_collapses': price.toDouble()==(price-BigInt.one).toDouble(),
    'production_one_micro_below_rejected': !below.accepted,
    'production_exact_price_accepted': exact.accepted,
  };
  if (below.accepted || !exact.accepted || !(observations['bigint_3001_digit_neighbors_distinct'] as bool)) {
    throw StateError('Selected representation failed a discrete boundary.');
  }
  final measurements = <Map<String,Object?>>[];
  for (final count in [100,500,1000]) {
    final watch = Stopwatch()..start();
    var checksum=BigInt.zero;
    for(var i=0;i<100;i++) { checksum += engine.bulkPriceMicros(4,count,25); }
    watch.stop();
    measurements.add({'ownership_count':count,'repetitions':100,'elapsed_microseconds':watch.elapsedMicroseconds,'checksum_digits':checksum.toString().length});
  }
  stdout.writeln(const JsonEncoder.withIndent('  ').convert({
    'scope':'host representation comparison, not physical mobile performance',
    'sdk':Platform.version,'observed_utc':DateTime.now().toUtc().toIso8601String(),
    'observations':observations,'measurements':measurements,
  }));
}

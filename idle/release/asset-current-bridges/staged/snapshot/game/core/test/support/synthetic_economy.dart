// Qualification only. This implementation is never registered by the shipped
// client and is not a proposed rebalance or a historical production release.
import 'package:tideglass_core/tideglass_core.dart';

const syntheticOldVersion = 'tideglass-economy-0.0.1';
const syntheticOldDigest =
    '9ecd3addb659b78144ecf733239b8003ab3af516897f7e7f7ee2c810955295c6';

class SyntheticOldEconomy extends TideglassEngine {
  const SyntheticOldEconomy();
  @override
  String get rulesVersion => syntheticOldVersion;
  @override
  Fixed producerOutputPerSecond(GameState state, int tierIndex) =>
      Fixed.raw(super.producerOutputPerSecond(state, tierIndex).raw *
          BigInt.from(3) ~/
          BigInt.two);
}

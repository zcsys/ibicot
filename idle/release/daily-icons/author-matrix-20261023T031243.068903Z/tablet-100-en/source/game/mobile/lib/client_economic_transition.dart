import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_persistence/tideglass_persistence.dart';

/// A predecessor is executable, reviewed code bundled with this application.
/// Neither save data nor remote configuration can supply an implementation.
/// The shipped v1 has no predecessors; tests explicitly supply synthetic rules.
class ClientEconomicPredecessor {
  const ClientEconomicPredecessor({required this.engine, required this.digest});

  final TideglassEngine engine;
  final String digest;

  CompatibleEconomicPredecessor registration({
    required PayloadValidator validatePayload,
    required SnapshotValidator validateSnapshot,
    TideglassEngine destination = const TideglassEngine(),
  }) => CompatibleEconomicPredecessor(
    configuration: EconomicConfiguration(
      version: engine.rulesVersion,
      digest: digest,
      validatePayload: validatePayload,
      validateSnapshot: validateSnapshot,
    ),
    migratePayload: (payload) {
      final old = GameState.fromJson(
        Map<String, dynamic>.from(payload['core'] as Map),
        expectedEconomicVersion: engine.rulesVersion,
      );
      final adopted = destination.adoptCompatibleState(
        old,
        sourceRulesVersion: engine.rulesVersion,
      );
      if (!adopted.accepted) {
        throw IncompatibleSaveException(
          adopted.reason ?? 'Economic transition was not completed.',
        );
      }
      return {...payload, 'core': adopted.state.toJson()};
    },
  );
}

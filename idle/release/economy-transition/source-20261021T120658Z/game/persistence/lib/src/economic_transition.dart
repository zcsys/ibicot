part of '../tideglass_persistence.dart';

/// Trusted compiled configuration plus its version-specific validators.
/// Registration is code-owned: a save or remote manifest cannot add a registry
/// entry, nominate a callback, or authenticate its own economic configuration.
class EconomicConfiguration {
  EconomicConfiguration({
    required this.version,
    required this.digest,
    required this.validatePayload,
    this.validateSnapshot,
  }) {
    if (!RegExp(r'^tideglass-economy-\d+\.\d+\.\d+$').hasMatch(version) ||
        !RegExp(r'^[a-f0-9]{64}$').hasMatch(digest)) {
      throw ArgumentError('Invalid compiled economic configuration identity.');
    }
  }
  final String version, digest;
  final PayloadValidator validatePayload;
  final SnapshotValidator? validateSnapshot;
}

/// An explicit compatible edge from [configuration] to this repository's
/// destination. The source validator must remain available while either saved
/// generation uses it. migratePayload must preserve the compatible currency
/// basis and change the rules identity only after old-rule settlement.
class CompatibleEconomicPredecessor {
  const CompatibleEconomicPredecessor({
    required this.configuration,
    required this.migratePayload,
  });
  final EconomicConfiguration configuration;
  final Map<String, dynamic> Function(Map<String, dynamic> settledOldPayload)
  migratePayload;
}

typedef OldEconomySettlement =
    Future<Map<String, dynamic>> Function(
      SaveSnapshot source,
      DateTime boundary,
    );

extension EconomicTransitions on SaveRepository {
  EconomicConfiguration _configurationFor(Object? version, Object? digest) {
    if (version == economicVersion && digest == economicDigest) {
      return EconomicConfiguration(
        version: economicVersion,
        digest: economicDigest,
        validatePayload: validatePayload,
        validateSnapshot: validateSnapshot,
      );
    }
    for (final predecessor in _compatiblePredecessors) {
      final configuration = predecessor.configuration;
      if (version == configuration.version && digest == configuration.digest) {
        return configuration;
      }
    }
    throw const IncompatibleSaveException(
      'Pinned economic configuration is unavailable; do not settle with different rules.',
    );
  }

  CompatibleEconomicPredecessor _predecessor(SaveSnapshot source) {
    for (final predecessor in _compatiblePredecessors) {
      if (source.economicVersion == predecessor.configuration.version &&
          source.economicDigest == predecessor.configuration.digest) {
        return predecessor;
      }
    }
    throw const IncompatibleSaveException(
      'No compiled compatible economic transition exists for this source.',
    );
  }

  bool needsEconomicTransition(SaveSnapshot source) {
    if (source.economicVersion == economicVersion &&
        source.economicDigest == economicDigest)
      return false;
    _predecessor(source); // Unknown means failure, never an implicit migration.
    return true;
  }

  /// Captured source and boundary are the immutable retry request. The caller
  /// separately authorizes a latest UTC endpoint. All callbacks run under the
  /// writer lock and cannot reenter a repository for the same directory.
  ///
  /// settleOld uses the source's compiled rules and returns OLD-version payload
  /// settled exactly through boundary, including any other timeline partitions.
  /// It must not emit UI rewards or perform external side effects. A failed
  /// pre-commit attempt may recompute it; only the single committed result is
  /// authoritative. A post-rename retry recognizes the durable receipt without
  /// evaluating the old rules again. Explicit imports clear this local receipt.
  Future<SaveSnapshot> transitionEconomy({
    required SaveSnapshot source,
    required DateTime boundary,
    required DateTime authorizedThrough,
    required OldEconomySettlement settleOld,
  }) {
    final end = boundary.toUtc(), authorized = authorizedThrough.toUtc();
    return _exclusive(() async {
      if (!_loaded)
        throw StateError('Load the repository before transitioning.');
      final predecessor = _predecessor(source);
      if (end.isBefore(source.settledThrough) || end.isAfter(authorized)) {
        throw const SaveConflictException(
          'Economic transition boundary is outside the authorized interval.',
        );
      }
      final receipt = _transitionReceipt(source, end);
      final current = (await _read()).snapshot;
      if (current != null &&
          current.economicVersion == economicVersion &&
          current.economicDigest == economicDigest &&
          current.branchId == source.branchId &&
          current.revision > source.revision &&
          !current.settledThrough.isBefore(end) &&
          (current.envelope['applied_operation_ids'] as List).contains(
            receipt,
          )) {
        _remember(current);
        return current;
      }
      _checkRevision(current);
      if (current == null ||
          current.saveId != source.saveId ||
          current.branchId != source.branchId ||
          current.revision != source.revision ||
          _digest(current._envelope) != _digest(source._envelope)) {
        throw const SaveConflictException(
          'Economic transition source changed; reload the retained snapshot.',
        );
      }
      final oldPayload = _copy(
        await runZoned(
          () => settleOld(current, end),
          zoneValues: {
            SaveRepository._transitionZoneKey: await directory
                .resolveSymbolicLinks(),
          },
        ),
      );
      predecessor.configuration.validatePayload(_copy(oldPayload));
      predecessor.configuration.validateSnapshot?.call(_copy(oldPayload), end);
      final migrated = _copy(
        runZoned(
          () => predecessor.migratePayload(_copy(oldPayload)),
          zoneValues: {
            SaveRepository._transitionZoneKey: await directory
                .resolveSymbolicLinks(),
          },
        ),
      );
      validatePayload(_copy(migrated));
      validateSnapshot?.call(_copy(migrated), end);
      final envelope = _makeEnvelope(
        migrated,
        end,
        current,
        appliedOperationIds: [receipt],
      );
      // The complete result must be reloadable, including the size ceiling,
      // before the durable file is touched.
      _decode(_encode(envelope));
      final saved = await _commit(envelope);
      _remember(saved);
      return saved;
    });
  }

  String _transitionReceipt(SaveSnapshot source, DateTime boundary) {
    final hash = _digest({
      'kind': 'compatible_economic_transition_v1',
      'source_save_id': source.saveId,
      'source_branch_id': source.branchId,
      'source_revision': source.revision,
      'from_version': source.economicVersion,
      'from_digest': source.economicDigest,
      'to_version': economicVersion,
      'to_digest': economicDigest,
      'from_utc': _utc(source.settledThrough),
      'through_utc': _utc(boundary),
    });
    // Opaque deterministic UUID-shaped local operation identity; not a server
    // receipt, an ownership proof, or a UUID namespace-based authentication.
    return '${hash.substring(0, 8)}-${hash.substring(8, 12)}-'
        '${hash.substring(12, 16)}-${hash.substring(16, 20)}-'
        '${hash.substring(20, 32)}';
  }
}

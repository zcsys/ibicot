/// Bounded, consented process observation. It is not a crash or launch report.
library;

class StudyProcessObservation {
  StudyProcessObservation.available({
    required int nativePid,
    required String platform,
    required String applicationId,
    required String applicationVersion,
    required String applicationBuild,
    required int observedStartUtcMs,
  }) : nativePid = nativePid,
       platform = platform,
       applicationId = applicationId,
       applicationVersion = applicationVersion,
       applicationBuild = applicationBuild,
       observedStartUtcMs = observedStartUtcMs,
       unavailableReason = null {
    _check(nativePid > 1 && nativePid <= 2147483647);
    _check({'ios', 'android'}.contains(platform));
    _check(_package.hasMatch(applicationId));
    _check(_value.hasMatch(applicationVersion));
    _check(_value.hasMatch(applicationBuild));
    _check(_time(observedStartUtcMs));
  }

  const StudyProcessObservation.unavailable(String reason)
    : unavailableReason = reason,
      nativePid = null,
      platform = null,
      applicationId = null,
      applicationVersion = null,
      applicationBuild = null,
      observedStartUtcMs = null;

  final int? nativePid, observedStartUtcMs;
  final String? platform, applicationId, applicationVersion, applicationBuild;
  final String? unavailableReason;
  bool get available => unavailableReason == null;
  static final _package = RegExp(r'^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$');
  static final _value = RegExp(r'^[A-Za-z0-9][A-Za-z0-9_.+-]{0,79}$');
  static const reasons = {
    'unsupported_platform',
    'native_unavailable',
    'invalid_native_context',
    'not_requested',
    'consent_not_granted',
  };
  static bool _time(int? value) =>
      value != null && value >= 0 && value < 9007199254740992;
  static void _check(bool valid) {
    if (!valid)
      throw const FormatException('Invalid bounded native process observation');
  }

  Map<String, Object?> toJson() {
    if (!available) {
      _check(reasons.contains(unavailableReason));
      return {
        'version': 1,
        'status': 'unavailable',
        'reason': unavailableReason,
      };
    }
    return {
      'version': 1,
      'status': 'available',
      'source': 'native_process_observation_v1',
      'native_pid': nativePid,
      'platform': platform,
      'application_id': applicationId,
      'application_version': applicationVersion,
      'application_build': applicationBuild,
      'observed_start_utc_ms': observedStartUtcMs,
    };
  }

  factory StudyProcessObservation.fromJson(Map<String, dynamic> value) {
    _check(value['version'] is int && value['version'] == 1);
    if (value['status'] == 'unavailable') {
      _check(
        value.length == 3 &&
            value.keys.toSet().containsAll({'version', 'status', 'reason'}),
      );
      _check(reasons.contains(value['reason']));
      return StudyProcessObservation.unavailable(value['reason'] as String);
    }
    _check(
      value['status'] == 'available' &&
          value.length == 9 &&
          value.keys.toSet().containsAll({
            'version',
            'status',
            'source',
            'native_pid',
            'platform',
            'application_id',
            'application_version',
            'application_build',
            'observed_start_utc_ms',
          }),
    );
    _check(value['source'] == 'native_process_observation_v1');
    return StudyProcessObservation.available(
      nativePid: value['native_pid'] as int,
      platform: value['platform'] as String,
      applicationId: value['application_id'] as String,
      applicationVersion: value['application_version'] as String,
      applicationBuild: value['application_build'] as String,
      observedStartUtcMs: value['observed_start_utc_ms'] as int,
    );
  }
}

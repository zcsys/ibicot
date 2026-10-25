import 'dart:io';

import 'package:flutter/services.dart';
import 'package:tideglass_platform/study_native_context.dart';

/// No channel call or identity read occurs until explicitly requested by the
/// consented StudyGate path. This never captures logs or installs crash handlers.
class NativeStudyProcessContext {
  static const channel = MethodChannel('dev.tideglass/study_process');
  static Future<StudyProcessObservation> sample() async {
    if (!Platform.isIOS && !Platform.isAndroid) {
      return const StudyProcessObservation.unavailable('unsupported_platform');
    }
    try {
      final raw = await channel
          .invokeMapMethod<String, dynamic>('observe')
          .timeout(const Duration(seconds: 2));
      if (raw == null) {
        return const StudyProcessObservation.unavailable('native_unavailable');
      }
      final value = StudyProcessObservation.fromJson(raw);
      if (!value.available ||
          value.platform != Platform.operatingSystem ||
          value.nativePid != pid) {
        return const StudyProcessObservation.unavailable(
          'invalid_native_context',
        );
      }
      return value;
    } on FormatException {
      return const StudyProcessObservation.unavailable(
        'invalid_native_context',
      );
    } on TypeError {
      return const StudyProcessObservation.unavailable(
        'invalid_native_context',
      );
    } catch (_) {
      return const StudyProcessObservation.unavailable('native_unavailable');
    }
  }
}

import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter_timezone/flutter_timezone.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:timezone/data/latest.dart' as tzdata;
import 'package:timezone/timezone.dart' as tz;
import 'notification_copy.dart';

tz.Location reminderLocation(String name) =>
    {'UTC', 'Etc/UTC', 'GMT', 'Etc/GMT'}.contains(name)
    ? tz.UTC
    : tz.getLocation(name);

@immutable
class ReminderPreferences {
  const ReminderPreferences({
    this.enabled = false,
    this.focus = true,
    this.survey = true,
    this.storage = true,
    this.quiet = true,
    this.quietStart = 1320,
    this.quietEnd = 480,
  });
  final bool enabled, focus, survey, storage, quiet;
  final int quietStart, quietEnd;
  void validate() {
    if (quietStart < 0 ||
        quietStart >= 1440 ||
        quietEnd < 0 ||
        quietEnd >= 1440 ||
        (quiet && quietStart == quietEnd)) {
      throw const FormatException('Invalid quiet hours.');
    }
  }

  ReminderPreferences copyWith({
    bool? enabled,
    bool? focus,
    bool? survey,
    bool? storage,
    bool? quiet,
    int? quietStart,
    int? quietEnd,
  }) => ReminderPreferences(
    enabled: enabled ?? this.enabled,
    focus: focus ?? this.focus,
    survey: survey ?? this.survey,
    storage: storage ?? this.storage,
    quiet: quiet ?? this.quiet,
    quietStart: quietStart ?? this.quietStart,
    quietEnd: quietEnd ?? this.quietEnd,
  );
  Map<String, dynamic> toJson() => {
    'version': 1,
    'enabled': enabled,
    'focus': focus,
    'survey': survey,
    'storage': storage,
    'quiet': quiet,
    'quiet_start': quietStart,
    'quiet_end': quietEnd,
  };
  factory ReminderPreferences.fromJson(Map<String, dynamic> json) {
    const keys = {
      'version',
      'enabled',
      'focus',
      'survey',
      'storage',
      'quiet',
      'quiet_start',
      'quiet_end',
    };
    if (json.keys.toSet().difference(keys).isNotEmpty ||
        !json.keys.toSet().containsAll(keys) ||
        json['version'] != 1 ||
        ![
          'enabled',
          'focus',
          'survey',
          'storage',
          'quiet',
        ].every((key) => json[key] is bool) ||
        json['quiet_start'] is! int ||
        json['quiet_end'] is! int) {
      throw const FormatException('Invalid reminder preferences.');
    }
    final value = ReminderPreferences(
      enabled: json['enabled'],
      focus: json['focus'],
      survey: json['survey'],
      storage: json['storage'],
      quiet: json['quiet'],
      quietStart: json['quiet_start'],
      quietEnd: json['quiet_end'],
    );
    value.validate();
    return value;
  }
}

enum ReminderKind { focus, survey, storage }

enum ReminderPermission { unknown, allowed, denied, unsupported }

@immutable
class PlannedReminder {
  PlannedReminder({
    required this.id,
    required this.dueUtc,
    required this.zoneName,
    required Iterable<ReminderKind> kinds,
  }) : kinds = List.unmodifiable(kinds);
  final int id;
  final DateTime dueUtc;
  final String zoneName;
  final List<ReminderKind> kinds;
  String title(NotificationCopy copy) => copy.text('title');
  String body(NotificationCopy copy) =>
      kinds.map((kind) => copy.text('${kind.name}Body')).join('\n');
}

/// A pure forecast. It never advances the core, awards currency or changes a
/// daily boundary. Only future transitions from this settled snapshot qualify.
class ReminderPlanner {
  static const ids = [77101, 77102, 77103];
  const ReminderPlanner();
  List<PlannedReminder> plan({
    required GameState state,
    required DateTime settledThrough,
    required DateTime nowUtc,
    required ReminderPreferences preferences,
    required tz.Location location,
  }) {
    preferences.validate();
    final now = nowUtc.toUtc(), boundary = settledThrough.toUtc();
    if (!preferences.enabled || now.isBefore(boundary)) return const [];
    final candidates = <(ReminderKind, DateTime)>[];
    if (preferences.focus && state.focusCharges < 12) {
      candidates.add((
        ReminderKind.focus,
        boundary.add(
          Duration(
            microseconds:
                (TideglassEngine.focusCycleMicros - state.focusPhaseMicros)
                    .toInt(),
          ),
        ),
      ));
    }
    if (preferences.survey && state.completedSurveys < 3) {
      candidates.add((
        ReminderKind.survey,
        boundary.add(
          Duration(
            microseconds:
                (TideglassEngine.surveyCycleMicros - state.surveyPhaseMicros)
                    .toInt(),
          ),
        ),
      ));
    }
    if (preferences.storage) {
      candidates.add((
        ReminderKind.storage,
        boundary.add(const Duration(hours: 24)),
      ));
    }
    final groups = <int, List<ReminderKind>>{};
    for (final (kind, ready) in candidates) {
      if (!ready.isAfter(now)) continue;
      // Do not post immediately after leaving or round readiness backwards.
      var due = ready.isBefore(now.add(const Duration(minutes: 5)))
          ? now.add(const Duration(minutes: 5))
          : ready;
      due = DateTime.fromMicrosecondsSinceEpoch(
        ((due.microsecondsSinceEpoch + 59999999) ~/ 60000000) * 60000000,
        isUtc: true,
      );
      due = afterQuietHours(due, preferences, location);
      // The 24-hour message is time-specific: discard it after a pathological
      // deferral, never claim quarter-rate production beyond its 72-hour limit.
      if (!due.isBefore(boundary.add(const Duration(hours: 72)))) continue;
      groups.putIfAbsent(due.microsecondsSinceEpoch, () => []).add(kind);
    }
    final result = [
      for (final entry in groups.entries)
        PlannedReminder(
          id: ids[entry.value.first.index],
          dueUtc: DateTime.fromMicrosecondsSinceEpoch(entry.key, isUtc: true),
          zoneName: location.name,
          kinds: entry.value,
        ),
    ]..sort((a, b) => a.dueUtc.compareTo(b.dueUtc));
    return List.unmodifiable(result);
  }

  DateTime afterQuietHours(
    DateTime instant,
    ReminderPreferences prefs,
    tz.Location location,
  ) {
    if (!prefs.quiet) return instant.toUtc();
    // Scan elapsed minutes, including repeated/skipped DST minutes. At most one
    // local day is quiet, plus a DST transition; 26h bounds the search.
    var cursor = instant.toUtc();
    for (var i = 0; i <= 1560; i++) {
      final local = tz.TZDateTime.from(cursor, location);
      final minute = local.hour * 60 + local.minute;
      final inside = prefs.quietStart < prefs.quietEnd
          ? minute >= prefs.quietStart && minute < prefs.quietEnd
          : minute >= prefs.quietStart || minute < prefs.quietEnd;
      if (!inside) return cursor;
      cursor = cursor.add(const Duration(minutes: 1));
    }
    throw const FormatException('Quiet-hour window could not be resolved.');
  }
}

abstract interface class NotificationPreferenceStore {
  Future<ReminderPreferences> load();
  Future<void> save(ReminderPreferences value);
}

class FileNotificationPreferences implements NotificationPreferenceStore {
  FileNotificationPreferences(this.file);
  final File file;
  @override
  Future<ReminderPreferences> load() async {
    if (!await file.exists()) return const ReminderPreferences();
    if (await file.length() > 4096) {
      throw const FormatException('Reminder preferences exceed bound.');
    }
    return ReminderPreferences.fromJson(
      (jsonDecode(await file.readAsString()) as Map).cast<String, dynamic>(),
    );
  }

  @override
  Future<void> save(ReminderPreferences value) async {
    value.validate();
    await file.parent.create(recursive: true);
    final temporary = File('${file.path}.new');
    await temporary.writeAsString(jsonEncode(value.toJson()), flush: true);
    await temporary.rename(file.path);
  }
}

abstract interface class NotificationGateway {
  Future<void> initialize();
  Future<ReminderPermission> permission();
  Future<ReminderPermission> requestPermission();
  Future<void> cancelReminders();
  Future<void> schedule(PlannedReminder reminder);
  Future<String> timeZone();
  Future<void> openSettings();
}

class NativeNotificationGateway implements NotificationGateway {
  NativeNotificationGateway({
    FlutterLocalNotificationsPlugin? plugin,
    this.copy = const NotificationCopy(),
    TargetPlatform? platform,
  }) : plugin = plugin ?? FlutterLocalNotificationsPlugin(),
       platform = platform ?? defaultTargetPlatform;
  final FlutterLocalNotificationsPlugin plugin;
  final NotificationCopy copy;
  final TargetPlatform platform;
  bool get supported =>
      !kIsWeb &&
      (platform == TargetPlatform.android || platform == TargetPlatform.iOS);
  @override
  Future<void> initialize() async {
    tzdata.initializeTimeZones();
    if (!supported) return;
    await plugin.initialize(
      settings: const InitializationSettings(
        android: AndroidInitializationSettings('ic_tideglass_notification'),
        iOS: DarwinInitializationSettings(
          requestAlertPermission: false,
          requestBadgePermission: false,
          requestSoundPermission: false,
          defaultPresentAlert: false,
          defaultPresentSound: false,
          defaultPresentBadge: false,
          defaultPresentBanner: false,
          defaultPresentList: false,
        ),
      ),
    );
    // Tapping simply opens the app. No payload grants anything or invokes core.
  }

  @override
  Future<ReminderPermission> permission() async {
    if (!supported) return ReminderPermission.unsupported;
    if (platform == TargetPlatform.android) {
      return await plugin
                  .resolvePlatformSpecificImplementation<
                    AndroidFlutterLocalNotificationsPlugin
                  >()!
                  .areNotificationsEnabled() ==
              true
          ? ReminderPermission.allowed
          : ReminderPermission.denied;
    }
    final value = await plugin
        .resolvePlatformSpecificImplementation<
          IOSFlutterLocalNotificationsPlugin
        >()!
        .checkPermissions();
    return value?.isEnabled == true && value?.isAlertEnabled == true
        ? ReminderPermission.allowed
        : ReminderPermission.denied;
  }

  @override
  Future<ReminderPermission> requestPermission() async {
    if (!supported) return ReminderPermission.unsupported;
    if (platform == TargetPlatform.android) {
      await plugin
          .resolvePlatformSpecificImplementation<
            AndroidFlutterLocalNotificationsPlugin
          >()!
          .requestNotificationsPermission();
    } else {
      await plugin
          .resolvePlatformSpecificImplementation<
            IOSFlutterLocalNotificationsPlugin
          >()!
          .requestPermissions(alert: true, badge: false, sound: false);
    }
    return permission();
  }

  @override
  Future<void> cancelReminders() async {
    if (!supported) return;
    for (final id in ReminderPlanner.ids) {
      await plugin.cancel(id: id);
    }
  }

  @override
  Future<void> schedule(PlannedReminder reminder) async {
    if (!supported) return;
    await plugin.zonedSchedule(
      id: reminder.id,
      title: reminder.title(copy),
      body: reminder.body(copy),
      scheduledDate: tz.TZDateTime.from(
        reminder.dueUtc,
        reminderLocation(reminder.zoneName),
      ),
      androidScheduleMode: AndroidScheduleMode.inexactAllowWhileIdle,
      notificationDetails: NotificationDetails(
        android: AndroidNotificationDetails(
          'tideglass.quiet.v1',
          copy.text('channelName'),
          channelDescription: copy.text('channelDescription'),
          importance: Importance.low,
          priority: Priority.low,
          playSound: false,
          enableVibration: false,
          channelShowBadge: false,
          onlyAlertOnce: true,
          visibility: NotificationVisibility.private,
        ),
        iOS: const DarwinNotificationDetails(
          presentAlert: true,
          presentBanner: true,
          presentList: true,
          presentSound: false,
          presentBadge: false,
        ),
      ),
    );
  }

  @override
  Future<String> timeZone() async =>
      (await FlutterTimezone.getLocalTimezone()).identifier;
  @override
  Future<void> openSettings() async {
    if (!supported) return;
    if (platform == TargetPlatform.android) {
      await plugin
          .resolvePlatformSpecificImplementation<
            AndroidFlutterLocalNotificationsPlugin
          >()!
          .openAppNotificationSettings();
    } else {
      await plugin
          .resolvePlatformSpecificImplementation<
            IOSFlutterLocalNotificationsPlugin
          >()!
          .openAppNotificationSettings();
    }
  }
}

/// All operations are serialized and failures stay outside the gameplay save.
/// The host calls onReturn before settling/playing, and scheduleForAbsence only
/// with the newest saved snapshot when leaving. No permissions are requested by
/// initialization, lifecycle events, settings edits, or scheduling.
class NotificationService extends ChangeNotifier {
  NotificationService({
    required this.gateway,
    required this.store,
    DateTime Function()? clock,
    this.planner = const ReminderPlanner(),
  }) : clock = clock ?? DateTime.now;
  factory NotificationService.native(Directory directory) =>
      NotificationService(
        gateway: NativeNotificationGateway(),
        store: FileNotificationPreferences(
          File('${directory.path}/notification_preferences.json'),
        ),
      );
  final NotificationGateway gateway;
  final NotificationPreferenceStore store;
  final DateTime Function() clock;
  final ReminderPlanner planner;
  ReminderPreferences preferences = const ReminderPreferences();
  ReminderPermission permission = ReminderPermission.unknown;
  String? warningKey, zoneName;
  List<PlannedReminder> planned = const [];
  bool busy = false, _disposed = false, _initialized = false;
  (GameState, DateTime)? _absence;
  Future<void> _tail = Future.value();
  void _notify() {
    if (!_disposed) notifyListeners();
  }

  Future<void> _serial(Future<void> Function() action) {
    _tail = _tail.then((_) async {
      busy = true;
      _notify();
      try {
        await action();
      } catch (_) {
        warningKey ??= 'serviceUnavailable';
      } finally {
        busy = false;
        _notify();
      }
    });
    return _tail;
  }

  Future<void> initialize() => _serial(() async {
    if (_initialized) return;
    _initialized = true;
    try {
      preferences = await store.load();
    } catch (_) {
      preferences = const ReminderPreferences();
      warningKey = 'preferencesUnreadable';
    }
    await gateway.initialize();
    await gateway.cancelReminders();
    permission = await gateway.permission();
  });
  Future<void> enableByPlayer() => _serial(() async {
    warningKey = null;
    permission = await gateway.requestPermission();
    final next = preferences.copyWith(
      enabled: permission == ReminderPermission.allowed,
    );
    await _save(next);
    await _replan();
  });
  Future<void> updatePreferences(ReminderPreferences next) => _serial(() async {
    next.validate();
    if (next.enabled && !preferences.enabled) {
      throw StateError('Explicit opt-in is required.');
    }
    warningKey = null;
    await _save(next);
    await _replan();
  });
  Future<void> _save(ReminderPreferences next) async {
    try {
      await store.save(next);
      preferences = next;
    } catch (_) {
      preferences = preferences.copyWith(enabled: false);
      warningKey = 'preferencesUnsaved';
      await gateway.cancelReminders();
      planned = const [];
      rethrow;
    }
  }

  Future<void> onReturn() => _serial(() async {
    _absence = null;
    planned = const [];
    await gateway.cancelReminders();
    permission = await gateway.permission();
    try {
      zoneName = await gateway.timeZone();
    } catch (_) {
      zoneName = null;
    }
  });
  Future<void> onClockChanged() => _serial(() async {
    _absence = null;
    planned = const [];
    warningKey = 'clockChanged';
    await gateway.cancelReminders();
  });
  Future<void> scheduleForAbsence({
    required GameState state,
    required DateTime settledThrough,
  }) => _serial(() async {
    _absence = (state, settledThrough.toUtc());
    await _replan();
  });
  Future<void> _replan() async {
    planned = const [];
    await gateway.cancelReminders();
    final snapshot = _absence;
    if (!preferences.enabled || snapshot == null) return;
    permission = await gateway.permission();
    if (permission != ReminderPermission.allowed) return;
    tz.Location location;
    try {
      zoneName = await gateway.timeZone();
      location = reminderLocation(zoneName!);
    } catch (_) {
      warningKey = 'zoneUnavailable';
      return;
    }
    if (clock().toUtc().isBefore(snapshot.$2)) {
      warningKey = 'clockChanged';
      return;
    }
    final candidate = planner.plan(
      state: snapshot.$1,
      settledThrough: snapshot.$2,
      nowUtc: clock().toUtc(),
      preferences: preferences,
      location: location,
    );
    try {
      for (final reminder in candidate) {
        await gateway.schedule(reminder);
      }
      planned = candidate;
      if ({
        'zoneUnavailable',
        'clockChanged',
        'serviceUnavailable',
      }.contains(warningKey)) {
        warningKey = null;
      }
    } catch (_) {
      await gateway.cancelReminders();
      rethrow;
    }
  }

  Future<void> openDeviceSettings() => _serial(gateway.openSettings);
  @override
  void dispose() {
    _disposed = true;
    super.dispose();
  }
}

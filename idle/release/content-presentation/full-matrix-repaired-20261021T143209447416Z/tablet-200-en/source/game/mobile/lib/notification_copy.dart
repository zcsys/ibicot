import 'presentation.dart';

/// Notification and settings copy is separate from timing and economic rules.
/// Pseudo mode expands labels for layout verification without changing keys.
class NotificationCopy {
  const NotificationCopy({this.pseudo = Presentation.pseudoEnabled});
  final bool pseudo;
  static const english = <String, String>{
    'heading': 'Quiet harbor reminders',
    'intro':
        'Optional, silent reminders when Focus, a Survey, or a full-rate day of harbor light is ready. No streaks, rewards for opening, or repeated daily prompts.',
    'enabled': 'Allow local reminders',
    'permissionHint':
        'Turning this on asks your device for permission. Reminders start off and never affect play.',
    'focus': 'Focus readiness',
    'survey': 'Survey readiness',
    'storage': 'A full-rate day collected',
    'quiet': 'Use quiet hours',
    'quietStart': 'Quiet hours begin',
    'quietStartAt': 'Quiet hours begin: {time}',
    'quietEndAt': 'Quiet hours end: {time}',
    'quietEnd': 'Quiet hours end',
    'timeHelp':
        'Enter a 24-hour time. For example, 22:00 means 10 in the evening.',
    'hour': 'Hour (0–23)',
    'minute': 'Minute (0–59)',
    'invalidHour': 'Enter an hour from 0 to 23.',
    'invalidMinute': 'Enter a minute from 0 to 59.',
    'saveTime': 'Save time',
    'cancelTime': 'Cancel',
    'quietHint':
        'Reminders that fall in quiet hours wait until quiet hours end. Overlapping reminders are combined.',
    'quietEqual':
        'Choose different start and end times, or turn quiet hours off.',
    'deviceSettings': 'Open device notification settings',
    'checkPermission': 'Check device permission',
    'allowed': 'Device permission is allowed.',
    'denied':
        'Device permission is not allowed. Your harbor still works normally.',
    'unknown': 'Device permission has not been checked.',
    'unsupported':
        'Local reminders are unavailable on this platform. Your harbor is unaffected.',
    'off': 'Local reminders are off.',
    'bounded':
        'At most three one-time reminders are planned each time you leave. Returning cancels the old plan. Your device may delay or suppress delivery.',
    'zone': 'Quiet-hours time zone: {zone}',
    'zoneHint':
        'The plan uses your device’s time zone when you leave. It is refreshed when you return or change these settings.',
    'planned': '{count} reminders currently planned.',
    'preferencesUnreadable':
        'Reminder preferences could not be read. Reminders are off; your harbor save is unaffected.',
    'preferencesUnsaved':
        'Reminder preferences could not be saved. Reminders have been stopped for this session.',
    'serviceUnavailable':
        'The device could not confirm reminder changes. Check device notification settings; your harbor is unaffected.',
    'clockChanged':
        'The device clock changed. The old reminder plan was cleared; a fresh plan can be made when you next leave.',
    'zoneUnavailable':
        'The device time zone could not be confirmed, so no new reminders were scheduled.',
    'title': 'A light in the harbor',
    'focusBody':
        'Focus is available for your next constellation. Return whenever you like.',
    'surveyBody':
        'A Survey is ready to collect. Its Notes will wait in your harbor.',
    'storageBody':
        'A full-rate day of harbor light is ready. Offline production continues at one-quarter rate until 72 hours away.',
    'channelName': 'Quiet harbor reminders',
    'channelDescription':
        'Optional silent reminders chosen in Tideglass settings',
  };
  String text(String key, [Map<String, Object> values = const {}]) {
    final value = english[key];
    if (value == null) throw ArgumentError('Unknown notification copy key.');
    return Presentation.template(value, values, pseudo: pseudo);
  }
}

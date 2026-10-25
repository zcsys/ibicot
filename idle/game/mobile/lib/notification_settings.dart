import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'notification_copy.dart';
import 'notification_service.dart';

/// Drop into the host's existing settings scroll view. Permission is requested
/// only by the player's enable switch, never by building this widget.
class NotificationSettings extends StatefulWidget {
  const NotificationSettings({
    super.key,
    required this.service,
    this.copy = const NotificationCopy(),
  });
  final NotificationService service;
  final NotificationCopy copy;
  @override
  State<NotificationSettings> createState() => _NotificationSettingsState();
}

class _NotificationSettingsState extends State<NotificationSettings> {
  String? localWarning;
  NotificationService get service => widget.service;
  NotificationCopy get copy => widget.copy;
  Future<void> _pick(bool start) async {
    final prefs = service.preferences;
    final minute = start ? prefs.quietStart : prefs.quietEnd;
    final selected = await showDialog<int>(
      context: context,
      builder: (_) => _QuietTimeEditor(
        minute: minute,
        title: copy.text(start ? 'quietStart' : 'quietEnd'),
        copy: copy,
      ),
    );
    if (!mounted || selected == null) return;
    final next = start
        ? prefs.copyWith(quietStart: selected)
        : prefs.copyWith(quietEnd: selected);
    if (next.quiet && next.quietStart == next.quietEnd) {
      setState(() => localWarning = 'quietEqual');
      return;
    }
    setState(() => localWarning = null);
    await service.updatePreferences(next);
  }

  @override
  Widget build(BuildContext context) => ListenableBuilder(
    listenable: service,
    builder: (context, _) {
      final prefs = service.preferences;
      String time(int value) =>
          TimeOfDay(hour: value ~/ 60, minute: value % 60).format(context);
      return Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            copy.text('heading'),
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const SizedBox(height: 12),
          Text(copy.text('intro')),
          const SizedBox(height: 12),
          Text(copy.text('permissionHint')),
          const SizedBox(height: 8),
          SwitchListTile(
            key: const ValueKey('reminder-enable'),
            contentPadding: EdgeInsets.zero,
            title: Text(copy.text('enabled')),
            value: prefs.enabled,
            onChanged: service.busy
                ? null
                : (enabled) => enabled
                      ? service.enableByPlayer()
                      : service.updatePreferences(
                          prefs.copyWith(enabled: false),
                        ),
          ),
          Text(copy.text(prefs.enabled ? service.permission.name : 'off')),
          if (service.permission == ReminderPermission.denied)
            Text(copy.text('denied')),
          if (localWarning != null || service.warningKey != null)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 12),
              child: Semantics(
                liveRegion: true,
                child: Text(
                  copy.text(localWarning ?? service.warningKey!),
                  key: const ValueKey('reminder-warning'),
                ),
              ),
            ),
          for (final kind in ReminderKind.values)
            SwitchListTile(
              key: ValueKey('reminder-${kind.name}'),
              contentPadding: EdgeInsets.zero,
              title: Text(copy.text(kind.name)),
              value: switch (kind) {
                ReminderKind.focus => prefs.focus,
                ReminderKind.survey => prefs.survey,
                ReminderKind.storage => prefs.storage,
              },
              onChanged: service.busy
                  ? null
                  : (value) => service.updatePreferences(switch (kind) {
                      ReminderKind.focus => prefs.copyWith(focus: value),
                      ReminderKind.survey => prefs.copyWith(survey: value),
                      ReminderKind.storage => prefs.copyWith(storage: value),
                    }),
            ),
          SwitchListTile(
            key: const ValueKey('reminder-quiet'),
            contentPadding: EdgeInsets.zero,
            title: Text(copy.text('quiet')),
            subtitle: Text(copy.text('quietHint')),
            value: prefs.quiet,
            onChanged: service.busy
                ? null
                : (value) {
                    if (value && prefs.quietStart == prefs.quietEnd) {
                      setState(() => localWarning = 'quietEqual');
                      return;
                    }
                    setState(() => localWarning = null);
                    service.updatePreferences(prefs.copyWith(quiet: value));
                  },
          ),
          OutlinedButton(
            key: const ValueKey('reminder-quiet-start'),
            onPressed: service.busy ? null : () => _pick(true),
            child: Text(
              copy.text('quietStartAt', {'time': time(prefs.quietStart)}),
            ),
          ),
          const SizedBox(height: 8),
          OutlinedButton(
            key: const ValueKey('reminder-quiet-end'),
            onPressed: service.busy ? null : () => _pick(false),
            child: Text(
              copy.text('quietEndAt', {'time': time(prefs.quietEnd)}),
            ),
          ),
          const SizedBox(height: 12),
          if (service.zoneName != null)
            Text(copy.text('zone', {'zone': service.zoneName!})),
          Text(copy.text('zoneHint')),
          const SizedBox(height: 12),
          Text(copy.text('bounded')),
          Text(copy.text('planned', {'count': service.planned.length})),
          const SizedBox(height: 12),
          OutlinedButton(
            key: const ValueKey('reminder-check-permission'),
            onPressed: service.busy ? null : service.onReturn,
            child: Text(copy.text('checkPermission')),
          ),
          if (service.permission != ReminderPermission.unsupported)
            OutlinedButton(
              key: const ValueKey('reminder-device-settings'),
              onPressed: service.busy ? null : service.openDeviceSettings,
              child: Text(copy.text('deviceSettings')),
            ),
        ],
      );
    },
  );
}

/// A scrollable 24-hour form preserves the user's text size and remains usable
/// with the keyboard open, including narrow phones and expanded translations.
class _QuietTimeEditor extends StatefulWidget {
  const _QuietTimeEditor({
    required this.minute,
    required this.title,
    required this.copy,
  });
  final int minute;
  final String title;
  final NotificationCopy copy;

  @override
  State<_QuietTimeEditor> createState() => _QuietTimeEditorState();
}

class _QuietTimeEditorState extends State<_QuietTimeEditor> {
  final _form = GlobalKey<FormState>();
  late String hour = (widget.minute ~/ 60).toString().padLeft(2, '0');
  late String minute = (widget.minute % 60).toString().padLeft(2, '0');

  Widget _input({required bool isHour}) => TextFormField(
    key: ValueKey(isHour ? 'reminder-hour-input' : 'reminder-minute-input'),
    initialValue: isHour ? hour : minute,
    keyboardType: TextInputType.number,
    inputFormatters: [
      FilteringTextInputFormatter.digitsOnly,
      LengthLimitingTextInputFormatter(2),
    ],
    decoration: InputDecoration(
      border: const OutlineInputBorder(),
      errorMaxLines: 4,
      semanticCounterText: '',
    ),
    validator: (value) {
      final number = int.tryParse(value ?? '');
      if (number == null || number < 0 || number > (isHour ? 23 : 59)) {
        return widget.copy.text(isHour ? 'invalidHour' : 'invalidMinute');
      }
      return null;
    },
    onChanged: (value) => isHour ? hour = value : minute = value,
  );

  @override
  Widget build(BuildContext context) => Dialog.fullscreen(
    child: SafeArea(
      child: Form(
        key: _form,
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Semantics(
                header: true,
                child: Text(
                  widget.title,
                  style: Theme.of(context).textTheme.headlineSmall,
                ),
              ),
              const SizedBox(height: 16),
              Text(widget.copy.text('timeHelp')),
              const SizedBox(height: 24),
              Text(widget.copy.text('hour')),
              const SizedBox(height: 8),
              Semantics(
                label: widget.copy.text('hour'),
                child: _input(isHour: true),
              ),
              const SizedBox(height: 16),
              Text(widget.copy.text('minute')),
              const SizedBox(height: 8),
              Semantics(
                label: widget.copy.text('minute'),
                child: _input(isHour: false),
              ),
              const SizedBox(height: 24),
              FilledButton(
                key: const ValueKey('reminder-save-time'),
                style: FilledButton.styleFrom(minimumSize: const Size(48, 48)),
                onPressed: () {
                  if (_form.currentState!.validate()) {
                    Navigator.of(
                      context,
                    ).pop(int.parse(hour) * 60 + int.parse(minute));
                  }
                },
                child: Text(widget.copy.text('saveTime')),
              ),
              const SizedBox(height: 12),
              OutlinedButton(
                key: const ValueKey('reminder-cancel-time'),
                style: OutlinedButton.styleFrom(
                  minimumSize: const Size(48, 48),
                ),
                onPressed: () => Navigator.of(context).pop(),
                child: Text(widget.copy.text('cancelTime')),
              ),
            ],
          ),
        ),
      ),
    ),
  );
}

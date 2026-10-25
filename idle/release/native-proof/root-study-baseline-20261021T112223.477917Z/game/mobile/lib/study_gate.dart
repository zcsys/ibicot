import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/semantics.dart';
import 'package:flutter/services.dart';
import 'package:path_provider/path_provider.dart';
import 'package:tideglass_platform/study_recorder.dart';
import 'bundled_content.dart';
import 'presentation.dart';

/// Only explicitly provisioned study builds display enrollment. A provision is
/// preparation, not evidence of ethics approval, valid recruitment or consent.
class StudyProvision {
  StudyProvision.fromJson(Map<String, dynamic> value)
    : data = Map.unmodifiable(value) {
    const keys = {
      'study_id',
      'protocol_sha256',
      'candidate_sha256',
      'config',
      'consent_version',
      'information',
      'contact',
      'retention',
      'synthetic',
      'device_group',
      'acquisition',
    };
    if (data.length != keys.length ||
        !data.keys.every(keys.contains) ||
        data['synthetic'] is! bool ||
        !keys
            .where((k) => k != 'synthetic')
            .every(
              (k) =>
                  data[k] is String &&
                  (data[k] as String).isNotEmpty &&
                  (data[k] as String).length <= 12000,
            )) {
      throw const FormatException('Invalid study provision.');
    }
    final contact = Uri.tryParse(data['contact']);
    if (contact == null ||
        contact.scheme != 'https' ||
        contact.host.isEmpty ||
        contact.userInfo.isNotEmpty) {
      throw const FormatException(
        'An approved public study contact is required.',
      );
    }
    currentConfig; // Validate hashes and categorical config before any I/O.
  }
  final Map<String, dynamic> data;
  StudyConfig get currentConfig => StudyConfig(
    candidateSha256: data['candidate_sha256'],
    economySha256: bundledEconomicDigest,
    contentSha256: bundledManifestDigest,
    config: data['config'],
  );
  String get information =>
      '${data['information']}\n\nStudy contact: ${data['contact']}\n\nRetention and deletion: ${data['retention']}';
  StudyEnrollment enrollment(String evidence) => StudyEnrollment(
    studyId: data['study_id'],
    protocolSha256: data['protocol_sha256'],
    informationSha256: studyDigest(information),
    consentVersion: data['consent_version'],
    eligibilityEvidenceSha256: evidence,
    synthetic: data['synthetic'],
    platform: Platform.isIOS
        ? 'ios'
        : Platform.isAndroid
        ? 'android'
        : 'test',
    deviceGroup: data['device_group'],
    acquisition: data['acquisition'],
  );
}

class StudySession extends ChangeNotifier {
  StudySession(this.recorder, this.provision, this.eligibilityFile);
  final StudyRecorder recorder;
  final StudyProvision provision;
  final File eligibilityFile;
  bool _disposed = false;
  bool failed = false;
  bool get active => recorder.enrolled && !recorder.exhausted && !failed;
  Future<void> capture(Future<void> Function() work) async {
    if (!active) return;
    try {
      await work();
    } catch (_) {
      failed = true;
    }
    if (!active && !_disposed) notifyListeners();
  }

  Future<void> withdraw() async {
    failed = true; // Disable new captures before waiting for durable erasure.
    if (!_disposed) notifyListeners();
    try {
      await recorder.withdraw();
      if (await eligibilityFile.exists()) await eligibilityFile.delete();
      failed = false;
    } catch (_) {
      failed = true;
    }
    if (!_disposed) notifyListeners();
  }

  Future<String> exportBundle() async {
    final raw = recorder.exportRaw();
    if (raw == null || recorder.withdrawn) {
      throw const StudyException('no_exportable_registry');
    }
    if (await FileSystemEntity.type(eligibilityFile.path, followLinks: false) !=
            FileSystemEntityType.file ||
        await eligibilityFile.length() > 4096) {
      throw const StudyException('eligibility_evidence_unavailable');
    }
    final evidence = await eligibilityFile.readAsString();
    if (studyDigest(evidence) !=
        recorder.registry?['eligibility_evidence_sha256']) {
      throw const StudyException('eligibility_evidence_mismatch');
    }
    return studyCanonical({
      'schema_version': 1,
      'raw': jsonDecode(raw),
      'eligibility_evidence': jsonDecode(evidence),
    });
  }

  @override
  void dispose() {
    _disposed = true;
    super.dispose();
  }
}

class StudyScope extends InheritedWidget {
  const StudyScope({super.key, required this.session, required super.child});
  final StudySession? session;
  static StudySession? of(BuildContext context) =>
      context.dependOnInheritedWidgetOfExactType<StudyScope>()?.session;
  @override
  bool updateShouldNotify(StudyScope oldWidget) => session != oldWidget.session;
}

class StudyGate extends StatefulWidget {
  const StudyGate({
    super.key,
    required this.child,
    this.provision = const String.fromEnvironment('TIDEGLASS_STUDY_PROVISION'),
    this.supportDirectory,
    this.openRecorder,
  });
  final Widget child;
  final String provision;
  final Directory? supportDirectory;

  /// Test injection for deterministic I/O failure/race qualification.
  final Future<StudyRecorder> Function(StudyStore)? openRecorder;
  @override
  State<StudyGate> createState() => _StudyGateState();
}

class _StudyGateState extends State<StudyGate> with WidgetsBindingObserver {
  StudyProvision? provision;
  StudyRecorder? recorder;
  StudySession? session;
  Directory? support;
  bool ready = false, consent = false, working = false;
  bool _declinedForLaunch = false;
  String? error;
  @override
  void initState() {
    super.initState();
    if (widget.provision.isEmpty) {
      ready = true;
    } else {
      unawaited(_prepare());
    }
    WidgetsBinding.instance.addObserver(this);
    if (widget.provision.isNotEmpty) {
      HardwareKeyboard.instance.addHandler(_key);
      SemanticsBinding.instance.addSemanticsActionListener(_semantics);
    }
  }

  void _semantics(SemanticsActionEvent event) {
    if ({
      SemanticsAction.tap,
      SemanticsAction.longPress,
      SemanticsAction.scrollUp,
      SemanticsAction.scrollDown,
      SemanticsAction.scrollLeft,
      SemanticsAction.scrollRight,
      SemanticsAction.increase,
      SemanticsAction.decrease,
    }.contains(event.type)) {
      _activity();
    }
  }

  bool _key(KeyEvent event) {
    if (event is KeyDownEvent) _activity();
    return false;
  }

  void _activity() {
    final current = session;
    if (current != null) {
      unawaited(
        current.capture(
          () => current.recorder.activity(StudyActivity.interaction),
        ),
      );
    }
  }

  Future<void> _prepare() async {
    try {
      if (widget.provision.length > 50000) throw const FormatException();
      provision = StudyProvision.fromJson(
        Map<String, dynamic>.from(jsonDecode(widget.provision)),
      );
      support =
          widget.supportDirectory ?? await getApplicationSupportDirectory();
      recorder = await (widget.openRecorder ?? StudyRecorder.open)(
        AtomicStudyFileStore('${support!.path}/tideglass-study.json'),
      );
      if (_declinedForLaunch || !mounted) return;
      if (recorder!.withdrawn) {
        ready = true;
      } else if (recorder!.withdrawalPending) {
        session = StudySession(
          recorder!,
          provision!,
          File('${support!.path}/tideglass-study-eligibility.json'),
        )..failed = true;
        ready = true;
      } else if (recorder!.enrolled) {
        if (recorder!.registry?['study_id'] != provision!.data['study_id'] ||
            recorder!.registry?['protocol_sha256'] !=
                provision!.data['protocol_sha256'] ||
            recorder!.registry?['consent_version'] !=
                provision!.data['consent_version'] ||
            recorder!.registry?['information_sha256'] !=
                studyDigest(provision!.information) ||
            recorder!.registry?['synthetic'] != provision!.data['synthetic']) {
          throw const FormatException();
        }
        final restored = StudySession(
          recorder!,
          provision!,
          File('${support!.path}/tideglass-study-eligibility.json'),
        );
        await restored.capture(
          () => recorder!.beginProcess(config: provision!.currentConfig),
        );
        if (_declinedForLaunch || !mounted) {
          restored.dispose();
          return;
        }
        session = restored;
        ready = true;
      }
    } catch (_) {
      error =
          'Study collection is unavailable. Your harbor remains available without study recording.';
    }
    if (mounted) setState(() {});
  }

  Future<void> _enroll() async {
    if (working ||
        !consent ||
        provision == null ||
        support == null ||
        recorder == null) {
      return;
    }
    setState(() => working = true);
    try {
      final gameDirectory = Directory('${support!.path}/tideglass');
      final type = await FileSystemEntity.type(
        gameDirectory.path,
        followLinks: false,
      );
      if (type != FileSystemEntityType.notFound &&
          (type != FileSystemEntityType.directory ||
              !await gameDirectory.list(followLinks: false).isEmpty)) {
        throw const FormatException(
          'Existing harbor is not a first-launch enrollment.',
        );
      }
      final evidence = studyCanonical({
        'schema_version': 1,
        'check': 'no_prior_game_directory_entries',
        'checked_at': DateTime.now().toUtc().toIso8601String(),
        'study_id': provision!.data['study_id'],
        'candidate_sha256': provision!.data['candidate_sha256'],
      });
      final enrollment = provision!.enrollment(studyDigest(evidence));
      // A local check supports later independent eligibility adjudication; it
      // cannot prove first-ever installation or absence of restored backups.
      await support!.create(recursive: true);
      await File(
        '${support!.path}/tideglass-study-eligibility.json',
      ).writeAsString(evidence, flush: true);
      await recorder!.enroll(
        enrollment,
        provision!.currentConfig,
        eligibleFreshInstall: true,
      );
      await recorder!.beginProcess(config: provision!.currentConfig);
      session = StudySession(
        recorder!,
        provision!,
        File('${support!.path}/tideglass-study-eligibility.json'),
      );
      ready = true;
    } catch (_) {
      error =
          'Enrollment could not be recorded, or this device already has a harbor. Continue without study recording; no previous activity will be added.';
    }
    if (mounted) setState(() => working = false);
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    final current = session;
    if (current == null) return;
    if (state == AppLifecycleState.resumed) {
      unawaited(current.capture(current.recorder.foreground));
    } else if (state == AppLifecycleState.inactive ||
        state == AppLifecycleState.paused ||
        state == AppLifecycleState.detached ||
        state == AppLifecycleState.hidden) {
      unawaited(current.capture(current.recorder.background));
    }
    // Background/dispose is never claimed to be an observed clean process exit.
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    HardwareKeyboard.instance.removeHandler(_key);
    SemanticsBinding.instance.removeSemanticsActionListener(_semantics);
    session?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (ready) {
      return StudyScope(
        session: session,
        child: Listener(onPointerDown: (_) => _activity(), child: widget.child),
      );
    }
    return MaterialApp(
      home: Scaffold(
        body: SafeArea(
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 600),
              child: ListView(
                padding: const EdgeInsets.all(24),
                children: [
                  const LocalizedText(
                    'Optional Tideglass study',
                    style: TextStyle(fontSize: 26),
                  ),
                  if (provision?.data['synthetic'] == true)
                    const LocalizedText(
                      'INTERNAL SYNTHETIC TEST — not a participant enrollment',
                    ),
                  if (provision != null) LocalizedText(provision!.information),
                  const SizedBox(height: 16),
                  const LocalizedText(
                    'Study recording is separate from account telemetry. It records pseudonymous app starts, game configuration, foreground activity and collection gaps on this device. It starts only after you agree. You can copy the records or withdraw in Settings. Declining does not change your game or rewards.',
                  ),
                  if (error != null) LocalizedText(error!),
                  if (error == null && provision != null)
                    CheckboxListTile(
                      title: const LocalizedText(
                        'I have read the study information and voluntarily agree to this study.',
                      ),
                      value: consent,
                      onChanged: working
                          ? null
                          : (v) => setState(() => consent = v ?? false),
                    ),
                  if (error == null && provision != null)
                    FilledButton(
                      onPressed: consent && !working ? _enroll : null,
                      child: const LocalizedText('Agree and open the harbor'),
                    ),
                  OutlinedButton(
                    onPressed: working
                        ? null
                        : () => setState(() {
                            _declinedForLaunch = true;
                            ready = true;
                          }),
                    child: const LocalizedText(
                      'Continue without study recording',
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class StudyControls extends StatelessWidget {
  const StudyControls({super.key, required this.session});
  final StudySession session;
  @override
  Widget build(BuildContext context) => ListenableBuilder(
    listenable: session,
    builder: (context, _) => Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const LocalizedText(
          'Optional study',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        LocalizedText(
          session.failed
              ? 'Study recording has stopped after an error. Local erasure has not been confirmed; contact the study team.'
              : session.active
              ? 'Study recording is active on this device.'
              : 'Study recording has stopped. Contact the study team about missing records.',
        ),
        LocalizedText('Contact: ${session.provision.data['contact']}'),
        OutlinedButton(
          onPressed:
              session.recorder.exportRaw() == null || session.recorder.withdrawn
              ? null
              : () async {
                  final confirm = await showDialog<bool>(
                    context: context,
                    builder: (context) => AlertDialog(
                      title: const LocalizedText('Copy study records?'),
                      content: const LocalizedText(
                        'This copies your pseudonymous registry and event records to the clipboard for the study team. Other apps may read or retain a pasted copy. Withdrawing here cannot erase copies already shared.',
                      ),
                      actions: [
                        TextButton(
                          onPressed: () => Navigator.pop(context, false),
                          child: const LocalizedText('Cancel'),
                        ),
                        FilledButton(
                          onPressed: () => Navigator.pop(context, true),
                          child: const LocalizedText('Copy records'),
                        ),
                      ],
                    ),
                  );
                  if (confirm == true) {
                    try {
                      final exported = await session.exportBundle();
                      await Clipboard.setData(ClipboardData(text: exported));
                    } catch (_) {
                      if (context.mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                            content: LocalizedText(
                              'Study export could not be verified. Contact the study team; your harbor is unchanged.',
                            ),
                          ),
                        );
                      }
                    }
                  }
                },
          child: const LocalizedText('Copy study records'),
        ),
        OutlinedButton(
          onPressed: session.recorder.withdrawn
              ? null
              : () async {
                  final confirm = await showDialog<bool>(
                    context: context,
                    builder: (context) => AlertDialog(
                      title: const LocalizedText('Withdraw from the study?'),
                      content: const LocalizedText(
                        'Stop recording and erase the local study registry and events. Your harbor is unchanged. Ask the study contact to delete any previously shared copies.',
                      ),
                      actions: [
                        TextButton(
                          onPressed: () => Navigator.pop(context, false),
                          child: const LocalizedText('Keep recording'),
                        ),
                        FilledButton(
                          onPressed: () => Navigator.pop(context, true),
                          child: const LocalizedText('Withdraw and erase'),
                        ),
                      ],
                    ),
                  );
                  if (confirm == true) await session.withdraw();
                },
          child: const LocalizedText('Withdraw and erase local study records'),
        ),
      ],
    ),
  );
}

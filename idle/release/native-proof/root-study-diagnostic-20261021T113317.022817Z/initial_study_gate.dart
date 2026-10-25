import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/semantics.dart';
import 'package:flutter/services.dart';
import 'package:path_provider/path_provider.dart';
import 'package:tideglass_platform/study_recorder.dart';
import 'package:tideglass/bundled_content.dart';
import 'package:tideglass/presentation.dart';
import 'package:tideglass/palette.dart';

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
    enrollment('0' * 64); // Reject invalid enrollment metadata before consent.
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
  StudySession(
    this.recorder,
    this.provision,
    this.eligibilityFile, {
    this.erasurePending = false,
  });
  final StudyRecorder recorder;
  final StudyProvision provision;
  final File eligibilityFile;
  bool _disposed = false;
  bool failed = false;
  bool erasurePending;
  bool erasing = false;
  bool get active =>
      recorder.enrolled && !recorder.exhausted && !failed && !erasurePending;
  bool get canExport =>
      !erasing &&
      !erasurePending &&
      !recorder.withdrawalPending &&
      !recorder.withdrawn &&
      recorder.exportRaw() != null;
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
    if (erasing) return;
    erasing = true;
    erasurePending = true;
    failed = true; // Stop captures before either durable cleanup operation.
    if (!_disposed) notifyListeners();
    try {
      await recorder.withdraw();
      final type = await FileSystemEntity.type(
        eligibilityFile.path,
        followLinks: false,
      );
      if (type == FileSystemEntityType.file) {
        await eligibilityFile.delete();
      } else if (type != FileSystemEntityType.notFound) {
        throw const StudyException('unsafe_eligibility_path');
      }
      erasurePending = false;
      failed = false;
    } catch (_) {
      failed = true;
    } finally {
      erasing = false;
    }
    if (!_disposed) notifyListeners();
  }

  Future<String> exportBundle() async {
    final raw = recorder.exportRaw();
    if (!canExport || raw == null) {
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
    // Withdrawal may begin while the eligibility file is being read.
    if (!canExport) throw const StudyException('no_exportable_registry');
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
  bool prepared = false;
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
      // A stop marker can exist without a registry. If a registry remains,
      // verify its identity before attaching either active or cleanup controls.
      final registry = recorder!.registry;
      if (registry != null &&
          (registry['study_id'] != provision!.data['study_id'] ||
              registry['protocol_sha256'] !=
                  provision!.data['protocol_sha256'] ||
              registry['consent_version'] !=
                  provision!.data['consent_version'] ||
              registry['information_sha256'] !=
                  studyDigest(provision!.information) ||
              registry['synthetic'] != provision!.data['synthetic'])) {
        throw const FormatException('Study identity mismatch.');
      }
      if (recorder!.withdrawn || recorder!.withdrawalPending) {
        final cleanup = StudySession(
          recorder!,
          provision!,
          File('${support!.path}/tideglass-study-eligibility.json'),
          erasurePending: true,
        );
        await cleanup.withdraw();
        if (_declinedForLaunch || !mounted) {
          cleanup.dispose();
          return;
        }
        if (cleanup.erasurePending) {
          session = cleanup;
        } else {
          cleanup.dispose();
        }
        ready = true;
      } else if (recorder!.enrolled) {
        final restored = StudySession(
          recorder!,
          provision!,
          File('${support!.path}/tideglass-study-eligibility.json'),
        );
        // The read/identity decision is complete. Remove the enrollment gate
        // synchronously before starting this previously consented process, so a
        // delayed write cannot re-enable collection after a loading-page decline.
        session = restored;
        ready = true;
        if (mounted) setState(() {});
        await restored.capture(
          () => recorder!.beginProcess(config: provision!.currentConfig),
        );
      } else {
        prepared = true;
      }
    } catch (_) {
      error =
          'Study collection is unavailable. Your harbor remains available without study recording.';
    }
    if (mounted) setState(() {});
  }

  Future<void> _enroll() async {
    if (working ||
        !prepared ||
        _declinedForLaunch ||
        !mounted ||
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
      if (!mounted) return;
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
      theme: tideglassTheme(),
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
                  if (provision != null) ...[
                    LocalizedText(provision!.data['information']),
                    const SizedBox(height: 16),
                    LocalizedText(
                      Presentation.template('Study contact: {contact}', {
                        'contact': provision!.data['contact'],
                      }),
                    ),
                    const SizedBox(height: 16),
                    LocalizedText(
                      Presentation.template(
                        'Retention and deletion: {retention}',
                        {
                          'retention': Presentation.authored(
                            provision!.data['retention'],
                          ),
                        },
                      ),
                    ),
                  ],
                  const SizedBox(height: 16),
                  const LocalizedText(
                    'Study recording is separate from account telemetry. It records pseudonymous app starts, game configuration, foreground activity and collection gaps on this device. It starts only after you agree. You can copy the records or withdraw in Settings. Declining does not change your game or rewards.',
                  ),
                  if (error != null) LocalizedText(error!),
                  if (error == null && !prepared)
                    const LocalizedText(
                      'Checking this device’s study records…',
                    ),
                  if (error == null && provision != null && prepared)
                    CheckboxListTile(
                      title: const LocalizedText(
                        'I have read the study information and voluntarily agree to this study.',
                      ),
                      value: consent,
                      onChanged: working
                          ? null
                          : (v) => setState(() => consent = v ?? false),
                    ),
                  if (error == null && provision != null && prepared)
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
          session.erasing
              ? 'Recording has stopped. Erasing local study records…'
              : session.erasurePending
              ? 'Recording has stopped. Local erasure is incomplete. Retry erasure or contact the original study team.'
              : session.recorder.withdrawn
              ? 'Study recording has stopped. Local study records were erased.'
              : session.failed
              ? 'Study recording has stopped after an error. You can copy the available records or withdraw; contact the study team about missing records.'
              : session.active
              ? 'Study recording is active on this device.'
              : 'Study recording has stopped. Contact the study team about missing records.',
        ),
        LocalizedText(
          Presentation.template('Contact: {contact}', {
            'contact': session.provision.data['contact'],
          }),
        ),
        OutlinedButton(
          onPressed: !session.canExport
              ? null
              : () async {
                  final confirm = await showDialog<bool>(
                    context: context,
                    builder: (context) => ReadingDialog(
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
                      if (!session.canExport) {
                        throw const StudyException('no_exportable_registry');
                      }
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
          onPressed:
              session.erasing ||
                  (session.recorder.withdrawn && !session.erasurePending)
              ? null
              : () async {
                  if (session.erasurePending) {
                    await session.withdraw();
                    return;
                  }
                  final confirm = await showDialog<bool>(
                    context: context,
                    builder: (context) => ReadingDialog(
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
          child: LocalizedText(
            session.erasurePending
                ? 'Retry local erasure'
                : 'Withdraw and erase local study records',
          ),
        ),
      ],
    ),
  );
}

import 'presentation.dart';
import 'strings.dart';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:tideglass_platform/tideglass_platform.dart';

import 'native_services.dart';

/// Optional network actions are explicit. The host owns atomic gameplay import
/// and its preserved local backup; this screen never combines game balances.
class ServiceSettings extends StatefulWidget {
  const ServiceSettings({
    super.key,
    required this.manager,
    required this.onExportHarbor,
    required this.onImportHarbor,
    this.onRefreshEntitlements,
  });

  final NativeServicesManager manager;
  final Future<String> Function() onExportHarbor;
  final Future<void> Function(String) onImportHarbor;
  final Future<void> Function()? onRefreshEntitlements;

  @override
  State<ServiceSettings> createState() => _ServiceSettingsState();
}

class _ServiceSettingsState extends State<ServiceSettings> {
  final _scroll = ScrollController();
  CloudIndex? _cloud;
  String? _message;
  bool _working = false;
  String? _indexAccount;
  String? _createdCode;

  @override
  void dispose() {
    _scroll.dispose();
    super.dispose();
  }

  void _setMessage(String message) {
    if (!mounted) return;
    setState(() => _message = message);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted && _scroll.hasClients) _scroll.jumpTo(0);
    });
  }

  NativeServicesManager get manager => widget.manager;
  bool get locked => _working || manager.busy;

  Future<bool> _perform(
    Future<void> Function() action, {
    String? success,
  }) async {
    if (locked) return false;
    setState(() {
      _working = true;
      _message = null;
    });
    try {
      await action();
      if (success != null) _setMessage(success);
      return true;
    } catch (error) {
      _setMessage(_serviceMessage(error));
      return false;
    } finally {
      if (mounted) setState(() => _working = false);
    }
  }

  Future<T?> _page<T>(
    String title,
    Widget Function(BuildContext, StateSetter) content,
  ) => showDialog<T>(
    context: context,
    barrierDismissible: false,
    builder: (dialog) => Dialog.fullscreen(
      child: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 680),
            child: StatefulBuilder(
              builder: (context, update) => ListView(
                key: const ValueKey('service-dialog-scroll'),
                padding: const EdgeInsets.all(24),
                children: [
                  LocalizedText(
                    title,
                    style: Theme.of(context).textTheme.headlineMedium,
                  ),
                  const SizedBox(height: 20),
                  content(dialog, update),
                ],
              ),
            ),
          ),
        ),
      ),
    ),
  );

  Future<bool> _confirm(String title, String body, String action) async =>
      await _page<bool>(
        title,
        (dialog, _) => Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            LocalizedText(body),
            const SizedBox(height: 24),
            FilledButton(
              key: const ValueKey('service-confirm'),
              onPressed: () => Navigator.pop(dialog, true),
              child: LocalizedText(action),
            ),
            OutlinedButton(
              onPressed: () => Navigator.pop(dialog, false),
              child: const LocalizedText(UiEnglish.serviceCancel),
            ),
          ],
        ),
      ) ??
      false;

  Future<void> _showCopy(String title, String text, String explanation) async {
    if (mounted) setState(() => _working = false);
    var copied = false;
    final shortened = text.length > 12000;
    final preview = shortened ? text.substring(0, 12000) : text;
    await _page<void>(
      title,
      (dialog, update) => Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          LocalizedText(explanation),
          const SizedBox(height: 16),
          if (shortened)
            const LocalizedText(
              UiEnglish.servicePreviewShortenedForReadabilityCopyTextIncludes,
            ),
          SelectableText(preview),
          const SizedBox(height: 24),
          FilledButton(
            key: const ValueKey('service-copy'),
            onPressed: () async {
              await Clipboard.setData(ClipboardData(text: text));
              if (dialog.mounted) update(() => copied = true);
            },
            child: LocalizedText(
              copied
                  ? UiEnglish.serviceCopiedToClipboard
                  : UiEnglish.serviceCopyText,
            ),
          ),
          OutlinedButton(
            onPressed: () => Navigator.pop(dialog),
            child: const LocalizedText(UiEnglish.serviceDone),
          ),
        ],
      ),
    );
  }

  Future<void> _create() async {
    var consent = false;
    final accepted = await _page<bool>(
      UiEnglish.serviceChooseCloudStorage,
      (dialog, update) => Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const LocalizedText(UiEnglish.serviceAnAccountLetsYouUploadAndChoose),
          CheckboxListTile(
            key: const ValueKey('cloud-consent'),
            value: consent,
            contentPadding: EdgeInsets.zero,
            controlAffinity: ListTileControlAffinity.leading,
            title: const LocalizedText(
              UiEnglish.serviceIChooseOptionalCloudStorage,
            ),
            onChanged: (value) => update(() => consent = value == true),
          ),
          FilledButton(
            key: const ValueKey('create-account-confirm'),
            onPressed: consent ? () => Navigator.pop(dialog, true) : null,
            child: const LocalizedText(UiEnglish.serviceCreateAccount),
          ),
          OutlinedButton(
            onPressed: () => Navigator.pop(dialog, false),
            child: const LocalizedText(UiEnglish.serviceKeepPlayingAsGuest),
          ),
        ],
      ),
    );
    if (accepted != true || !mounted) return;
    final done = await _perform(() async {
      final created = await manager.createAccount(cloudConsent: true);
      _createdCode = created.recoveryCode;
      _cloud = null;
    });
    if (done && mounted) await _retainCreatedCode();
  }

  Future<void> _retainCreatedCode() async {
    final code = _createdCode;
    final accountId = manager.session?.accountId;
    if (code == null || accountId == null) return;
    var retained = false;
    var copied = false;
    final accepted = await _page<bool>(
      UiEnglish.serviceKeepYourRecoveryDetails,
      (dialog, update) => Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const LocalizedText(
            UiEnglish.serviceSaveBothDetailsSomewherePrivateBeforeUploading,
          ),
          const SizedBox(height: 20),
          const LocalizedText(UiEnglish.serviceAccountID),
          SelectableText(accountId),
          const SizedBox(height: 12),
          const LocalizedText(UiEnglish.serviceRecoveryCode),
          SelectableText(code, key: const ValueKey('new-recovery-code')),
          OutlinedButton(
            onPressed: () async {
              await Clipboard.setData(
                ClipboardData(
                  text:
                      UiEnglish.serviceTideglassAccountAccountIdNRecoveryCodeCode(
                        accountId,
                        code,
                      ),
                ),
              );
              if (dialog.mounted) update(() => copied = true);
            },
            child: LocalizedText(
              copied
                  ? UiEnglish.serviceCopiedToClipboard2
                  : UiEnglish.serviceCopyRecoveryDetails,
            ),
          ),
          const LocalizedText(
            UiEnglish.serviceCopyingUsesYourDeviceClipboardKeepThe,
          ),
          CheckboxListTile(
            key: const ValueKey('recovery-retained'),
            value: retained,
            contentPadding: EdgeInsets.zero,
            controlAffinity: ListTileControlAffinity.leading,
            title: const LocalizedText(
              UiEnglish.serviceIHaveSafelyKeptTheAccountID,
            ),
            onChanged: (value) => update(() => retained = value == true),
          ),
          FilledButton(
            key: const ValueKey('recovery-retained-confirm'),
            onPressed: retained ? () => Navigator.pop(dialog, true) : null,
            child: const LocalizedText(UiEnglish.serviceContinue),
          ),
          OutlinedButton(
            onPressed: () => Navigator.pop(dialog, false),
            child: const LocalizedText(
              UiEnglish.serviceKeepUploadsLockedForNow,
            ),
          ),
        ],
      ),
    );
    if (accepted == true && mounted) {
      final done = await _perform(
        manager.acknowledgeRecoveryCode,
        success:
            UiEnglish.serviceRecoveryDetailsConfirmedUploadsRemainYourChoice,
      );
      if (done) _createdCode = null;
    }
  }

  Future<void> _recover() async {
    var account = '';
    var code = '';
    final accepted = await _page<bool>(
      UiEnglish.serviceRecoverAnAccount,
      (dialog, update) => Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const LocalizedText(UiEnglish.serviceSigningInDoesNotReplaceOrUpload),
          const SizedBox(height: 20),
          TextField(
            key: const ValueKey('recover-account-id'),
            autocorrect: false,
            enableSuggestions: false,
            decoration: InputDecoration(
              labelText: Presentation.text(UiEnglish.serviceAccountID2),
            ),
            onChanged: (value) => update(() => account = value),
          ),
          _secretField(
            UiEnglish.serviceRecoveryCode2,
            'recover-code',
            (value) => update(() => code = value),
          ),
          const SizedBox(height: 20),
          FilledButton(
            key: const ValueKey('recover-confirm'),
            onPressed: account.trim().isNotEmpty && code.trim().isNotEmpty
                ? () => Navigator.pop(dialog, true)
                : null,
            child: const LocalizedText(
              UiEnglish.serviceSignInWithoutChangingHarbor,
            ),
          ),
          OutlinedButton(
            onPressed: () => Navigator.pop(dialog, false),
            child: const LocalizedText(UiEnglish.serviceCancel2),
          ),
        ],
      ),
    );
    final accountId = account.trim();
    final recoveryCode = code.trim();
    if (accepted != true || !mounted) return;
    await _perform(() async {
      await manager.recoverAccount(
        accountId: accountId,
        recoveryCode: recoveryCode,
      );
      _cloud = null;
      _createdCode = null;
      await widget.onRefreshEntitlements?.call();
    }, success: UiEnglish.serviceSignedInYourLocalHarborIsUnchanged);
  }

  Future<void> _refreshCloud() => _perform(() async {
    final accountId = manager.session!.accountId;
    final result = await manager.client!.cloudIndex();
    _cloud = result;
    _indexAccount = accountId;
  }).then((_) {});

  Future<void> _upload() async {
    final index = _cloud;
    if (index == null || !manager.recoveryAcknowledged) return;
    if (!await _confirm(
      UiEnglish.serviceUploadThisHarbor,
      UiEnglish.serviceACompleteCopyOfYourCurrentLocal,
      UiEnglish.serviceUploadCurrentHarbor,
    )) {
      return;
    }
    if (!mounted) return;
    await _perform(() async {
      final exported = await widget.onExportHarbor();
      _cloud = await manager.client!.uploadSnapshot(
        exported,
        expectedGeneration: index.generation,
      );
    }, success: UiEnglish.serviceHarborUploadedCloudBranchesRemainSeparate);
  }

  Future<void> _choose(CloudSnapshotInfo snapshot) async {
    final index = _cloud;
    if (index == null) return;
    if (!await _confirm(
      UiEnglish.serviceUseThisCloudBranch,
      UiEnglish.serviceBranchSnapshotBranchIdNRevisionSnapshotRevisionN(
        snapshot.branchId,
        snapshot.revision,
        snapshot.settledThrough.toUtc().toIso8601String(),
      ),
      UiEnglish.serviceChooseBranchAndImport,
    )) {
      return;
    }
    if (!mounted) return;
    var selected = false;
    final done = await _perform(() async {
      final exported = await manager.client!.downloadSnapshot(snapshot.saveId);
      _cloud = await manager.client!.selectSnapshot(
        snapshot.saveId,
        expectedGeneration: index.generation,
        confirmSelection: true,
      );
      selected = true;
      await widget.onImportHarbor(exported);
    }, success: UiEnglish.serviceCloudBranchSelectedAndImportedThePrevious);
    if (!done && selected && mounted) {
      _setMessage(UiEnglish.serviceTheCloudBranchWasSelectedButLocal);
    }
  }

  Future<void> _rotate() async {
    var current = '';
    final next = TideglassServiceClient.generateRecoveryCode();
    final accountId = manager.session!.accountId;
    var retained = false;
    var copied = false;
    final accepted = await _page<bool>(
      UiEnglish.serviceReplaceYourRecoveryCode,
      (dialog, update) => Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const LocalizedText(UiEnglish.serviceKeepThisNewCodeBeforeSendingThe),
          const SizedBox(height: 16),
          LocalizedText(UiEnglish.serviceAccountIDAccountId(accountId)),
          const LocalizedText(UiEnglish.serviceNewRecoveryCode),
          SelectableText(next, key: const ValueKey('rotation-new-code')),
          OutlinedButton(
            onPressed: () async {
              await Clipboard.setData(
                ClipboardData(
                  text:
                      UiEnglish.serviceTideglassAccountAccountIdNRecoveryCodeNext(
                        accountId,
                        next,
                      ),
                ),
              );
              if (dialog.mounted) update(() => copied = true);
            },
            child: LocalizedText(
              copied
                  ? UiEnglish.serviceCopiedToClipboard3
                  : UiEnglish.serviceCopyNewRecoveryDetails,
            ),
          ),
          _secretField(
            UiEnglish.serviceCurrentRecoveryCode,
            'rotation-current-code',
            (value) => update(() => current = value),
          ),
          CheckboxListTile(
            key: const ValueKey('rotation-retained'),
            value: retained,
            contentPadding: EdgeInsets.zero,
            controlAffinity: ListTileControlAffinity.leading,
            title: const LocalizedText(
              UiEnglish.serviceIHaveSafelyKeptTheNewCode,
            ),
            onChanged: (value) => update(() => retained = value == true),
          ),
          FilledButton(
            key: const ValueKey('rotation-confirm'),
            onPressed: retained && current.trim().isNotEmpty
                ? () => Navigator.pop(dialog, true)
                : null,
            child: const LocalizedText(UiEnglish.serviceReplaceRecoveryCode),
          ),
          OutlinedButton(
            onPressed: () => Navigator.pop(dialog, false),
            child: const LocalizedText(UiEnglish.serviceCancel3),
          ),
        ],
      ),
    );
    final old = current.trim();
    if (accepted != true || !mounted) return;
    final done = await _perform(() async {
      await manager.rotateRecoveryCode(old, newRecoveryCode: next);
    }, success: UiEnglish.serviceRecoveryCodeReplacedUseTheNewCode);
    if (!done && mounted) {
      _setMessage(UiEnglish.serviceTheRecoveryCodeChangeWasNotConfirmed);
    }
  }

  Future<void> _signOut({bool localOnly = false}) async {
    if (!await _confirm(
      localOnly
          ? UiEnglish.serviceForgetThisDeviceSignIn
          : UiEnglish.serviceSignOutOfThisDevice,
      localOnly
          ? UiEnglish.serviceThisRemovesThisDeviceSStoredSign
          : UiEnglish.serviceThisAsksTheServiceToRevokeThis,
      localOnly
          ? UiEnglish.serviceForgetSignInOnThisDevice
          : UiEnglish.serviceSignOut,
    )) {
      return;
    }
    if (!mounted) return;
    await _perform(
      () async {
        await manager.signOut(localOnly: localOnly);
        _cloud = null;
        _createdCode = null;
      },
      success: localOnly
          ? UiEnglish.serviceDeviceSignInForgottenServerRevocationWas
          : UiEnglish.serviceDeviceSessionRevokedAndSignInCleared,
    );
  }

  Future<void> _delete() async {
    var code = '';
    var confirmed = false;
    final accepted = await _page<bool>(
      UiEnglish.serviceDeleteTheCloudAccount,
      (dialog, update) => Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const LocalizedText(
            UiEnglish.serviceThisPermanentlyDeletesThisServiceAccountAnd,
          ),
          _secretField(
            UiEnglish.serviceCurrentRecoveryCode2,
            'delete-recovery-code',
            (value) => update(() => code = value),
          ),
          CheckboxListTile(
            key: const ValueKey('delete-account-consent'),
            value: confirmed,
            contentPadding: EdgeInsets.zero,
            controlAffinity: ListTileControlAffinity.leading,
            title: const LocalizedText(
              UiEnglish.serviceIUnderstandThatThisCloudAccountAnd,
            ),
            onChanged: (value) => update(() => confirmed = value == true),
          ),
          FilledButton(
            key: const ValueKey('delete-account-confirm'),
            onPressed: confirmed && code.trim().isNotEmpty
                ? () => Navigator.pop(dialog, true)
                : null,
            child: const LocalizedText(UiEnglish.serviceDeleteCloudAccount),
          ),
          OutlinedButton(
            onPressed: () => Navigator.pop(dialog, false),
            child: const LocalizedText(UiEnglish.serviceCancel4),
          ),
        ],
      ),
    );
    final recoveryCode = code.trim();
    if (accepted != true || !mounted) return;
    await _perform(() async {
      await manager.deleteAccount(
        recoveryCode: recoveryCode,
        confirmDelete: true,
      );
      _cloud = null;
      _createdCode = null;
    }, success: UiEnglish.serviceCloudAccountDeletedYourLocalHarborIs);
  }

  Future<void> _telemetry(bool enabled) async {
    if (enabled &&
        !await _confirm(
          UiEnglish.serviceShareOptionalUsageReports,
          UiEnglish.serviceReportsHelpUnderstandSessionsAndGameFlows,
          UiEnglish.serviceAllowUsageReports,
        )) {
      return;
    }
    if (!mounted) return;
    await _perform(
      () => manager.setTelemetryConsent(enabled),
      success: enabled
          ? UiEnglish.serviceUsageReportsEnabledByYourChoice
          : UiEnglish.serviceUsageCollectionStoppedAndRemoteDeletionConfirmed,
    );
  }

  @override
  Widget build(BuildContext context) => ListenableBuilder(
    listenable: manager,
    builder: (context, _) {
      final signedIn = manager.signedIn;
      final cloud = _indexAccount == manager.session?.accountId ? _cloud : null;
      return Scaffold(
        appBar: AppBar(title: const LocalizedText(UiEnglish.serviceServices)),
        body: SafeArea(
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 760),
              child: ListView(
                key: const ValueKey('services-scroll'),
                controller: _scroll,
                padding: const EdgeInsets.all(24),
                children: [
                  if (_message != null)
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      child: Semantics(
                        liveRegion: true,
                        child: LocalizedText(
                          _message!,
                          key: const ValueKey('service-result'),
                        ),
                      ),
                    ),
                  LocalizedText(
                    UiEnglish.serviceYourHarborYourChoice,
                    style: Theme.of(context).textTheme.headlineMedium,
                  ),
                  const SizedBox(height: 12),
                  const LocalizedText(
                    UiEnglish.serviceGuestPlayAndLocalSavesWorkWithout,
                  ),
                  if (!manager.configured) ...[
                    const SizedBox(height: 20),
                    const LocalizedText(
                      UiEnglish.serviceOnlineServicesAreNotConfiguredInThis,
                      key: ValueKey('services-unconfigured'),
                    ),
                  ],
                  if (manager.lastError == 'secure_session_not_saved' ||
                      manager.lastError == 'secure_session_unavailable')
                    const Padding(
                      padding: EdgeInsets.symmetric(vertical: 16),
                      child: LocalizedText(
                        UiEnglish.serviceDeviceSignInCouldNotBeSaved,
                      ),
                    ),
                  if (manager.lastError == 'secure_privacy_unavailable')
                    const LocalizedText(
                      UiEnglish.serviceReportPreferencesCouldNotBeReadSecurely,
                    ),
                  if (manager.lastError == 'secure_session_cleanup_required')
                    const LocalizedText(
                      UiEnglish.serviceTheServerSignOutOrDeletionCompleted,
                    ),
                  if (locked)
                    Padding(
                      padding: EdgeInsets.symmetric(vertical: 12),
                      child: LinearProgressIndicator(
                        semanticsLabel: Presentation.text(
                          UiEnglish.serviceWaitingForServiceResponse,
                        ),
                      ),
                    ),
                  const SizedBox(height: 20),
                  _section(UiEnglish.serviceLocalCopy),
                  _button(
                    UiEnglish.serviceExportLocalHarbor,
                    'export-local-harbor',
                    () => _perform(() async {
                      final data = await widget.onExportHarbor();
                      if (mounted) {
                        await _showCopy(
                          UiEnglish.serviceLocalHarborExport,
                          data,
                          UiEnglish.serviceThisIsACopyOfYourLocal,
                        );
                      }
                    }),
                  ),
                  if (manager.configured && !signedIn) ...[
                    _section(UiEnglish.serviceOptionalAccount),
                    _button(
                      UiEnglish.serviceCreateACloudAccount,
                      'create-account',
                      _create,
                    ),
                    _button(
                      UiEnglish.serviceRecoverAnExistingAccount,
                      'recover-account',
                      _recover,
                    ),
                  ],
                  if (signedIn) ...[
                    _section(UiEnglish.serviceAccount),
                    const LocalizedText(UiEnglish.serviceAccountID3),
                    SelectableText(manager.session!.accountId),
                    if (!manager.recoveryAcknowledged) ...[
                      const SizedBox(height: 12),
                      const LocalizedText(
                        UiEnglish
                            .serviceUploadsAreLockedUntilRecoveryDetailsAre,
                      ),
                      if (_createdCode != null)
                        _button(
                          UiEnglish.serviceKeepRecoveryDetails,
                          'retain-recovery-details',
                          _retainCreatedCode,
                        ),
                    ],
                    _section(UiEnglish.serviceCloudBranches),
                    const LocalizedText(
                      UiEnglish.serviceRefreshToSeeActualSavedBranchesA,
                    ),
                    _button(
                      UiEnglish.serviceRefreshCloudBranches,
                      'refresh-cloud',
                      _refreshCloud,
                    ),
                    if (cloud != null) ...[
                      LocalizedText(
                        UiEnglish.serviceCloudRevisionCloudGeneration(
                          cloud.generation,
                        ),
                      ),
                      if (cloud.selectionRequired)
                        const LocalizedText(
                          UiEnglish.serviceMoreThanOneBranchNeedsYourReview,
                        ),
                      if (cloud.snapshots.isEmpty)
                        const LocalizedText(
                          UiEnglish.serviceNoCloudSavesHaveBeenUploaded,
                        ),
                      for (final snapshot in cloud.snapshots)
                        _branch(snapshot, cloud),
                      _button(
                        UiEnglish.serviceUploadCurrentHarbor2,
                        'upload-harbor',
                        manager.recoveryAcknowledged ? _upload : null,
                      ),
                    ],
                    _section(UiEnglish.serviceRecoveryAndAccountData),
                    _button(
                      UiEnglish.serviceReplaceRecoveryCode2,
                      'rotate-recovery',
                      _rotate,
                    ),
                    _button(
                      UiEnglish.serviceExportAccountData,
                      'export-account',
                      () => _perform(() async {
                        final data = await manager.client!.exportAccount();
                        if (mounted) {
                          await _showCopy(
                            UiEnglish.serviceAccountDataExport,
                            const JsonEncoder.withIndent('  ').convert(data),
                            UiEnglish.serviceThisIsTheDataReturnedByYour,
                          );
                        }
                      }),
                    ),
                    _button(
                      UiEnglish.serviceSignOutOfThisDevice2,
                      'sign-out',
                      _signOut,
                    ),
                    _button(
                      UiEnglish.serviceForgetDeviceSignInWithoutNetwork,
                      'forget-session',
                      () => _signOut(localOnly: true),
                    ),
                    _button(
                      UiEnglish.serviceDeleteCloudAccount2,
                      'delete-account',
                      _delete,
                    ),
                  ],
                  _section(UiEnglish.serviceOptionalUsageReports),
                  LocalizedText(
                    manager.telemetryEnabled
                        ? UiEnglish.serviceCollectionIsOn
                        : UiEnglish.serviceCollectionIsOff,
                  ),
                  const LocalizedText(
                    UiEnglish.serviceThisConsentIsSeparateFromCloudStorage,
                  ),
                  if (manager.pendingTelemetryDeletion) ...[
                    const LocalizedText(
                      UiEnglish.serviceLocalCollectionIsStoppedRemoteDeletionIs,
                      key: ValueKey('telemetry-deletion-pending'),
                    ),
                    if (signedIn)
                      _button(
                        UiEnglish.serviceRetryReportDeletion,
                        'retry-telemetry-delete',
                        () => _telemetry(false),
                      ),
                  ],
                  if (signedIn && !manager.pendingTelemetryDeletion) ...[
                    if (!manager.telemetryEnabled)
                      _button(
                        UiEnglish.serviceAllowUsageReports2,
                        'enable-telemetry',
                        () => _telemetry(true),
                      ),
                    _button(
                      UiEnglish.serviceStopReportsAndDeleteRemoteEvents,
                      'disable-telemetry',
                      () => _telemetry(false),
                    ),
                  ],
                  if (!signedIn)
                    const LocalizedText(
                      UiEnglish
                          .serviceRemoteReportPreferencesRequireAnAccountConnection,
                    ),
                  const SizedBox(height: 32),
                ],
              ),
            ),
          ),
        ),
      );
    },
  );

  Widget _section(String title) => Padding(
    padding: const EdgeInsets.only(top: 24, bottom: 12),
    child: LocalizedText(title, style: Theme.of(context).textTheme.titleLarge),
  );

  Widget _button(String title, String key, VoidCallback? action) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 5),
    child: OutlinedButton(
      key: ValueKey(key),
      style: OutlinedButton.styleFrom(minimumSize: const Size(48, 48)),
      onPressed: locked ? null : action,
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 8),
        child: LocalizedText(title, textAlign: TextAlign.center),
      ),
    ),
  );

  Widget _branch(CloudSnapshotInfo snapshot, CloudIndex index) => Card(
    margin: const EdgeInsets.symmetric(vertical: 8),
    child: Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          LocalizedText(
            index.selectedSaveId == snapshot.saveId
                ? UiEnglish.serviceSelectedCloudSave
                : snapshot.isTip
                ? UiEnglish.serviceBranchTip
                : UiEnglish.serviceEarlierSave,
            style: Theme.of(context).textTheme.titleMedium,
          ),
          LocalizedText(
            UiEnglish.serviceBranchSnapshotBranchId(snapshot.branchId),
          ),
          LocalizedText(UiEnglish.serviceSaveSnapshotSaveId(snapshot.saveId)),
          LocalizedText(
            UiEnglish.serviceRevisionSnapshotRevision(snapshot.revision),
          ),
          LocalizedText(
            UiEnglish.serviceSettledThroughSnapshotSettledThroughToUtcToIsoString(
              snapshot.settledThrough.toUtc().toIso8601String(),
            ),
          ),
          const SizedBox(height: 8),
          _button(
            UiEnglish.serviceChooseThisBranch,
            'choose-cloud-${snapshot.saveId}',
            () => _choose(snapshot),
          ),
        ],
      ),
    ),
  );
}

Widget _secretField(String label, String key, ValueChanged<String> onChanged) =>
    Padding(
      padding: const EdgeInsets.symmetric(vertical: 12),
      child: TextField(
        key: ValueKey(key),
        obscureText: true,
        autocorrect: false,
        enableSuggestions: false,
        decoration: InputDecoration(labelText: Presentation.text(label)),
        onChanged: onChanged,
      ),
    );

String _serviceMessage(Object error) {
  if (error is ServiceException) {
    if (error.status == 409) {
      return UiEnglish.serviceCloudDataChangedOnAnotherDeviceRefresh;
    }
    if (error.status == 401 || error.code == 'authentication_required') {
      return UiEnglish.serviceTheAccountSessionNeedsRecoveryYourLocal;
    }
    if (error.status == 403) {
      return UiEnglish.serviceTheServiceDidNotAuthorizeThisAction;
    }
    if (error.code == 'service_timeout' ||
        error.code == 'service_unavailable') {
      return UiEnglish.serviceTheServiceCouldNotConfirmThisRequest;
    }
  }
  // Raw exceptions may contain transport or credential details; never render them.
  return UiEnglish.serviceThisActionCouldNotBeConfirmedYour;
}

import 'presentation.dart';
import 'strings.dart';
import 'package:flutter/material.dart';
import 'game_controller.dart';
import 'native_services.dart';
import 'support_screen.dart';
import 'support_service_bridge.dart';

class ServiceSupportScreen extends StatefulWidget {
  const ServiceSupportScreen({
    super.key,
    required this.game,
    required this.manager,
  });
  final GameController game;
  final NativeServicesManager manager;
  @override
  State<ServiceSupportScreen> createState() => _ServiceSupportScreenState();
}

class _ServiceSupportScreenState extends State<ServiceSupportScreen> {
  late final bridge = SupportServiceBridge(widget.game, widget.manager);
  @override
  void dispose() {
    bridge.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => ListenableBuilder(
    listenable: Listenable.merge([bridge, widget.manager]),
    builder: (context, _) => SupportScreen(
      game: widget.game,
      onCompletedBriefing: bridge.completeBriefing,
      onRewardedAd:
          widget.manager.adsAvailable && widget.manager.recoveryAcknowledged
          ? bridge.watchAd
          : null,
      serviceBusy: bridge.busy,
      servicePanel: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          if (bridge.busy) const LinearProgressIndicator(),
          if (bridge.message != null)
            Semantics(liveRegion: true, child: LocalizedText(bridge.message!)),
          if (!widget.manager.adsAvailable)
            const LocalizedText(
              UiEnglish.serviceOptionalAdsAreUnavailableEveryUnusedSlot,
            ),
          if (widget.manager.signedIn)
            OutlinedButton(
              key: const ValueKey('restore-support-delivery'),
              onPressed: bridge.busy ? null : bridge.restoreClaims,
              child: const LocalizedText(
                UiEnglish.serviceCheckAccountTokenDelivery,
              ),
            ),
          const LocalizedText(
            UiEnglish.serviceTokensUseTheSameSixSlotsWhichever,
          ),
        ],
      ),
    ),
  );
}

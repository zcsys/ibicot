/// English help is presentation content, separate from economic rules and saves.
/// IDs remain stable; help_screen applies the existing pseudolocale boundary.
enum HelpTopic {
  play,
  rechart,
  away,
  notes,
  recovery,
  privacy,
  credits,
  releaseNotes,
}

enum HelpAction { account, localRecovery, privacySettings, licenses }

class HelpSection {
  const HelpSection(this.id, this.title, this.paragraphs);
  final String id, title;
  final List<String> paragraphs;
}

class HelpArticle {
  const HelpArticle(
    this.topic,
    this.title,
    this.summary,
    this.sections, {
    this.actions = const [],
  });
  final HelpTopic topic;
  final String title, summary;
  final List<HelpSection> sections;
  final List<HelpAction> actions;
}

abstract final class HelpCopy {
  static const title = 'The harbor handbook';
  static const intro =
      'Choose a topic. Your harbor keeps its progress while you read.';
  static const backToTopics = 'All help topics';
  static const account = 'Open account and cloud settings';
  static const localRecovery = 'Open local save and recovery controls';
  static const privacySettings = 'Open privacy choices';
  static const licenses = 'Open software licenses';
  static const brand = 'Tideglass';
  static const developmentVersion = '0.1.0+1';
  static const externalUnavailable =
      'Public support and privacy links are not configured in this development build. No message is sent from this handbook.';
  static const developmentNotice =
      'Development reference · not a public release announcement';
  static String action(HelpAction action) => switch (action) {
    HelpAction.account => account,
    HelpAction.localRecovery => localRecovery,
    HelpAction.privacySettings => privacySettings,
    HelpAction.licenses => licenses,
  };
}

abstract final class HelpContent {
  static HelpArticle article(HelpTopic topic) =>
      articles.firstWhere((a) => a.topic == topic);
  static const articles = <HelpArticle>[
    HelpArticle(
      HelpTopic.play,
      'Build your harbor',
      'Purchases, automation, calibration and separate fleets.',
      [
        HelpSection('first-light', 'Begin with one light', [
          'Your first Spark Skiff already earns Radiance. Buy another from the harbor fleet when its price is affordable. Five producer kinds make Radiance; each successive purchase of a kind costs more.',
          'Buy 1 makes one purchase. Buy max spends what the fleet can currently afford. Forecasts assume the displayed fleet and conditions; a later purchase or an expiring bonus can change the result.',
        ]),
        HelpSection('fleet-growth', 'Let small producers stay useful', [
          'At 25, 50, 75 and 100 of a producer, that entire tier doubles its output. At 25 Charts, cross-tier connections let early producers strengthen later ones. Compare the displayed price and added network output instead of assuming the newest kind is always best.',
          'Automatic buying unlocks at 10 Charts. Choose payback-based buying or a priority order. One saved plan slot is included; extra slots hold alternative plans and do not produce extra income by themselves. Automatic Rechart needs 100 Charts and your explicit Chart-gain and minimum-run settings.',
        ]),
        HelpSection('calibrations', 'A quiet calibration', [
          'A calibration uses one Focus charge. Trace the constellation without a timer, undo a step, or restart. The accessible crew-help button gives the same completion and Focus effect. No reflex or speed test is required.',
        ]),
        HelpSection('separate-fleets', 'Read the rules of each fleet', [
          'Challenge dossiers have separate fleets, goals, caps and connections. Your main harbor continues working. Focus, Support and Rechart are not available inside a challenge, and challenge money does not enter your main wallet.',
          'The seasonal fleet is also separate. Main-harbor Charts and paid appearances do not increase its production. The Season screen shows its saved dates, badge goals and 30-level pass. After the scheduled end, an archived run can be resumed from that screen. This development build uses a local preview schedule, not an announced public season.',
        ]),
      ],
    ),
    HelpArticle(
      HelpTopic.rechart,
      'Rechart without surprises',
      'What resets, what stays, and how to decide.',
      [
        HelpSection('reset-preview', 'Read the preview first', [
          'Rechart exchanges the current main fleet for permanent Charts. The first claim becomes available at 1 billion lifetime Radiance. Preview the additional Charts and the permanent multiplier before confirming. Cancelling the preview keeps your current fleet.',
          'There is no universal best reset moment. A larger claim improves your permanent multiplier, while waiting lets the existing fleet keep earning. Consider the gain and the time you want to spend rebuilding; simulated strategies are not a promise of human completion time.',
        ]),
        HelpSection('reset-loss', 'What you rebuild', [
          'Your main-harbor Radiance wallet is cleared and purchased main producers are removed. One free starting Spark Skiff returns. New purchases then use the stronger permanent Chart multiplier.',
        ]),
        HelpSection('reset-retention', 'What you keep', [
          'Keep lifetime Radiance, existing and newly claimed Charts, Survey Notes, stored Focus, remaining Focus time, completed Surveys and their timers, and automation settings and saved plans.',
          'Keep campaign restoration, archive and calibration discoveries, dossier ownership and progress, the separate seasonal fleet and pass progress, earned appearances and your preferences. Current daily contracts and the shared daily Support record remain; Rechart does not refill their allowance. Any remaining Support effect continues for its remaining time.',
        ]),
      ],
    ),
    HelpArticle(
      HelpTopic.away,
      'While you are away',
      'Offline rates, stored timers, contracts and shared Support.',
      [
        HelpSection('offline-rates', 'One absence, three rates', [
          'For one continuous absence, the first 24 hours of production earn at full rate. The next 48 hours earn at one quarter rate. Production stops after 72 hours away until you return. This limit is not restarted by a loading chunk or a second tap on the return summary.',
          'Returning settles your actual fleet, purchases and expiring effects over elapsed time. The return summary reports that settlement. Saving and recovery must finish before it is treated as committed progress.',
        ]),
        HelpSection('stored-timers', 'Store a little readiness', [
          'Focus stores one charge every 2 hours, up to 12. One charge supplies 10 minutes of a 20% production effect. Spending several charges adds time rather than multiplying the strength.',
          'A Survey completes every 8 hours, up to 3 stored Surveys. Collecting each gives 10 Survey Notes. Full storage waits for you to collect or spend; it does not create a streak penalty.',
        ]),
        HelpSection('daily-contracts', 'A backlog, not a streak', [
          'Three daily contract slots are retained for up to seven account days. Read each assigned goal and claim it when complete. An unclaimed slot can be rerolled once. Newly assigned goals do not count activity from before assignment.',
          'A seasonal alternative uses the same daily slot and claim receipt as its main-harbor goal. Completing both routes cannot grant the slot twice. Daily boundaries use the saved account-day offset. Changing time zone does not move that boundary, and turning the clock back does not replay an earlier day.',
        ]),
        HelpSection('shared-support', 'Six shared Support slots', [
          'Free crew briefings and optional verified rewarded ads share six slots per account day. They give the same Support token. Refusing an ad, a failed ad or no available ad does not remove the free briefing route. Unspent daily tokens do not accumulate into a larger allowance tomorrow.',
          'Spend a token once on a 20-minute, 25% production effect, or on an eligible offline Salvage cache. Salvage is capped by genuine recorded offline production and the displayed claim; it does not double your whole absence. The token and cache cannot be claimed twice.',
          'Local reminders start off. Enable them only if you want them, choose quiet hours and the reminder kinds, and turn them off at any time. Opening a reminder grants nothing. Device delivery can be delayed or denied without affecting play.',
        ]),
      ],
    ),
    HelpArticle(
      HelpTopic.notes,
      'Choose how to spend Notes',
      'Separate campaign needs from optional storage and decoration.',
      [
        HelpSection('note-costs', 'The prices to compare', [
          'A new challenge dossier costs 100 Survey Notes once. An owned dossier can be replayed for free. Only one challenge fleet is active at a time; replacing or restarting it discards that active run, so read the confirmation first.',
          'An extra saved automation-plan slot costs 50 Survey Notes. Up to five extra slots are available after automation unlocks. A core harbor decoration also costs 50 Notes once; there are six. These slots and decorations are optional for the campaign ending.',
        ]),
        HelpSection('campaign-first', 'Read your current chapter goal', [
          'Some chapter goals require particular dossiers. Check Restoration before spending Notes on an optional plan slot, decoration or another dossier. Spending those Notes first can delay access to a needed dossier and therefore delay the ending.',
          'A purchased plan slot only stores another plan. A decoration changes the harbor appearance. Neither is required to increase the existing plan’s efficiency. You can finish the campaign without buying every optional collection item.',
          'Play at your own pace. Balance simulations compare rules and spending choices; they do not predict how many days a person will need to learn or finish the game.',
        ]),
      ],
    ),
    HelpArticle(
      HelpTopic.recovery,
      'Save and recover your harbor',
      'Local copies, cloud branches, recovery codes and deletion.',
      [
        HelpSection('local-copies', 'Keep a local copy', [
          'The native game saves locally. Use Export my harbor in the Logbook to copy a complete export into storage you control. Keep an older copy before replacing your current harbor. An export is game data, not an account recovery code or proof of a purchase.',
          'If a save is damaged, the recovery screen may offer a valid backup. Keep the damaged files or your export until you have checked the restored harbor. Do not uninstall or clear app data as a first recovery step: that can remove your local copies.',
          'Importing chooses one complete compatible branch. It does not combine wallets, Charts or rewards. The import flow preserves the previous local branch before replacement; verify the chosen branch and its progress before continuing.',
        ]),
        HelpSection('cloud-choice', 'Cloud is a separate choice', [
          'An account is optional. When an account service is configured, cloud setup asks for consent and shows an account ID and recovery code. Retain both before acknowledging the code or uploading. Credentials belong in secure account storage, never in a game export.',
          'Recovering an account does not automatically overwrite a guest harbor. Inspect real cloud branches and their revisions, then explicitly choose one. The current local branch is preserved by the import flow. Upload conflicts require reviewing the latest branch; they are not resolved by adding the two wallets together.',
        ]),
        HelpSection('recovery-code', 'Protect the code before changing it', [
          'Keep the account ID and recovery code somewhere you can reach if this device is lost. Do not send them in a support message or include them in a screenshot.',
          'Code rotation requires the current code. Retain the proposed replacement before submitting the change. If the response is lost, the server may already have changed the code; use the retained replacement to recover and check the account rather than discarding it.',
          'If the code is lost but a valid device session remains, keep that session and export your local harbor. If there is no valid session and no code, this recovery method cannot recover the account. A local save copy may still recover your game, but it cannot prove account or paid ownership.',
        ]),
        HelpSection('logout-delete', 'Signing out is not deleting', [
          'Signing out ends the requested session when the service confirms it. Forgetting credentials only on this device is an offline local action; it cannot claim to revoke a remote session. Neither action is account deletion.',
          'Account deletion needs explicit confirmation and the current recovery code. Confirmed service deletion removes the active account data while leaving the current local guest game. It does not cancel an Apple or Google purchase or erase an export you saved elsewhere. Backup erasure and third-party storage depend on the final operator’s policy.',
        ]),
      ],
      actions: [HelpAction.localRecovery, HelpAction.account],
    ),
    HelpArticle(
      HelpTopic.privacy,
      'Privacy and support',
      'Optional services, separate consent and honest availability.',
      [
        HelpSection('guest-privacy', 'Guest play comes first', [
          'You can play the local harbor without an account, cloud upload, telemetry consent or rewarded ad. Optional services may be unavailable in a development build or during an outage. Their absence does not unlock paid ownership or block the guest economy.',
          'A configured account service stores account identifiers, explicit save uploads and the records needed for verified purchases and shared Support. It does not use a gameplay export to store your recovery code. A purchase’s verification and restore status is shown separately from your local game.',
          'Paid appearances require verified ownership. Offline verification can expire, and a fresh online check may be needed to display them again. This does not change production or earned free appearances.',
        ]),
        HelpSection('telemetry-choice', 'Quality reports need their own consent', [
          'Telemetry starts off and is separate from cloud consent. Enabling it permits a defined set of session, progression and diagnostic events for that account. The client does not send pre-consent history, recovery codes, free-form text or a wallet dump in those events.',
          'Turning reports off clears the local queue immediately and requests deletion of the service’s events. If the service is unreachable, settings show the pending deletion and provide a retry. Guest play continues.',
        ]),
        HelpSection('data-control', 'Export, delete and choose destinations', [
          'Account settings offer account-data export and account deletion when the service is configured. Account export excludes raw credentials and store proofs. Your own local copies are separate and remain under your control.',
          'An authorized soundtrack export uses a destination you choose through the device. A personal copy already saved to another app or location cannot be recalled by account deletion or a later refund.',
        ]),
        HelpSection('support-availability', 'Development availability', [
          HelpCopy.externalUnavailable,
          'Use the local recovery instructions and available in-app account controls. A public support mailbox and published privacy policy are not available in this development build.',
          'If you later report a problem through an announced support channel, describe the action, visible error and build version. Leave out account tokens, recovery codes, save exports and payment details unless a verified, appropriate recovery process specifically requires them.',
        ]),
      ],
      actions: [HelpAction.privacySettings, HelpAction.account],
    ),
    HelpArticle(
      HelpTopic.credits,
      'Credits and licenses',
      'How this development build was made.',
      [
        HelpSection('development-credit', 'Development', [
          'Tideglass is being created by an AI-assisted development team directed by the project owner.',
        ]),
        HelpSection('visual-credit', 'Code-native visuals', [
          'The lighthouse, harbor, staged producers and appearance overlays were authored for Tideglass as vector geometry and native drawing code. Their reusable shapes are rendered directly by the client. The store lighthouse artwork uses the same original geometry.',
        ]),
        HelpSection('score-credit', 'Original synthesized score', [
          'The ambient pieces and effect cues were authored for Tideglass with explicit musical phrases and mathematical synthesis. No third-party recording, sampled instrument library or reference melody was incorporated into that score. Music and effects have independent volume and mute controls.',
        ]),
        HelpSection('software-credit', 'Software and notices', [
          'Tideglass uses Flutter, Dart and open-source packages. Their bundled license notices are available below.',
        ]),
      ],
      actions: [HelpAction.licenses],
    ),
    HelpArticle(
      HelpTopic.releaseNotes,
      'Development release notes',
      'Current changes and feature availability.',
      [
        HelpSection('development-status', 'Local development build', [
          'This local development build includes the game features below. Its version is shown at the end of this page. Optional online features depend on a configured service and may be unavailable.',
        ]),
        HelpSection('included-systems', 'Implemented game and comfort features', [
          'The client includes the main fleet and Rechart, offline settlement and recovery, six restoration chapters, eighteen archive entries, twelve calibrations, twelve challenge dossiers, and a separate seasonal fleet with pass progression.',
          'It also includes free shared-slot crew briefings, automation plans, collection appearances, reduced motion, larger text, separate audio controls, and opt-in local reminders with quiet hours. Purchases and rewarded ads appear only through their configured, verified service paths.',
        ]),
        HelpSection('current-improvements', 'Current development improvements', [
          'The handbook now explains reset retention, offline limits, Note spending and recovery. Long headings and confirmations wrap and scroll at larger text sizes.',
          'Note-spending guidance distinguishes campaign dossiers from optional plan slots and decorations. Choosing optional purchases first can postpone a needed dossier.',
        ]),
        HelpSection('release-limits', 'Unavailable services', [
          'Online account recovery, verified purchases, rewarded ads and soundtrack downloads may be unavailable. The game shows their configured status; local play and free crew briefings remain available.',
          HelpCopy.externalUnavailable,
        ]),
      ],
    ),
  ];
}

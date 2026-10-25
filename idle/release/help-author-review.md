# Harbor handbook — author implementation and integration handoff

Date: 2026-10-19. Owner: client_native. Status: author verified; independent acceptance remains separate.

## Scope

Help/recovery maps S27 through M5-03 and preparatory M7-05 work. Large text, semantic navigation and presentation checks map S26/S31/S32 through M5-02. Store creative maps S43 through M5-06 and preparatory M7-05. This does not complete launch support, hosting, store submission, physical-device or human acceptance gates.

## Delivered

- `game/mobile/lib/help_content.dart`: immutable English topic/section catalogue with stable IDs, separate from rules/saves. Eight topics cover play, Rechart, away timers/Support, Notes, recovery, privacy, credits and development changes.
- `game/mobile/lib/help_screen.dart`: real navigable topic index and articles using the existing pseudo boundary, wrapped headings, semantic section headers, reading-order focus and minimum 48dp actions. Optional host callbacks are shown only when supplied. The license action opens Flutter's actual bundled license page.
- `game/mobile/test/help_test.dart`: six checks for immutable coverage, every article/section at 320px/200%, semantic headings, bounded index navigation, real optional callbacks, license navigation, actual app entry/export behavior and host captures.

Final constructor:

```dart
HelpScreen({
  HelpTopic? initialTopic,
  VoidCallback? onOpenAccount,
  VoidCallback? onOpenLocalRecovery,
  VoidCallback? onOpenPrivacySettings,
})
```

The default opens the index. `initialTopic` opens a direct article. From an indexed article, All help topics pops to the existing index; from a direct article it replaces that route with the index. Repeated reading therefore does not accumulate duplicate index routes.

The lead integrated `open-handbook` in Logbook and `open-handbook-settings` in Settings. Account/privacy callbacks reuse the existing service screen. Local recovery opens existing export/import actions and keeps their confirmations. The smoke test opens both actual application entries, calls the existing export path once, observes the exact export text, confirms no import occurred and confirms byte-equivalent core JSON before/after help.

## Content accuracy

The help states full-rate production for the first 24 hours of an absence, quarter-rate for the next 48 hours and a 72-hour production stop; Focus 2-hour / 12-charge storage; Survey 8-hour / 3 stored / 10 Notes; six daily shared free/ad Support slots; explicit consent for reminders and telemetry; Rechart loss/retention including separate fleets and remaining Support time. These values were compared with the current core sources rather than copied from superseded design drafts.

Note spending distinguishes a 100-Note first dossier purchase/free owned replay from optional 50-Note plan slots and core decorations. It tells players to inspect their chapter goal because optional spending can postpone a required dossier. It gives no simulated completion day as a human pacing promise.

Recovery describes explicit branch selection without wallet merging, local preservation before import, retaining IDs/codes before upload/rotation, lost-response rotation, lost-code limits, remote signout versus offline local forgetting, deletion versus local game and store purchases, and pending telemetry deletion. Source privacy material was `services/docs/PRIVACY.md`; no public policy URL/contact was fabricated. Paid appearance guidance explains that offline verification can expire and a fresh online check may be needed, without changing production/free ownership.

Credits name the AI-assisted team/project-owner direction and the original code-native visuals and mathematically synthesized score. They invent no people, studio, copyright owner or exclusive rights. Process/legal review detail belongs to source provenance and this handoff, not the player flow. Release notes list concrete changes and current service availability; developer test checklists and simulation-defect history were removed from the player copy after lead review.

## Evidence

| Check | Result | Evidence |
|---|---:|---|
| English focused tests | 6 passed | `release/help-english-tests.log` |
| Compile-time pseudo focused tests | 6 passed | `release/help-pseudo-tests.log` |
| Complete mobile analyzer | No issues | `release/help-analyze.log` |
| Viewport/text size | 320 logical px / 200% | Both test modes |
| Visual inspection | Six host PNGs; Notes/recovery/privacy in both modes | `release/help-proof/` |

The lead inspected the English Notes capture. The author inspected the three pseudo images and all topic-navigation results: wrapped headings, no reported overflow/clipping, selectable routes and scrollable long copy. Claims are host-renderer/semantic-tree evidence, not physical VoiceOver/TalkBack or native device approval. No economy, service behavior, save format, scheduling or dependency was changed by this lane.

The earlier complete mobile 255-test localization run predates this help implementation. The later commerce 294-test independent run also predates the help integration. This handoff claims only the focused 6 + 6 checks and current analyzer above; a fresh candidate/full regression is owned by the lead/release lane.

## Reproduce

From `game/mobile`:

```sh
../../tool/flutter test test/help_test.dart --reporter expanded
../../tool/flutter test test/help_test.dart --dart-define=TIDEGLASS_PSEUDO=true --reporter expanded
../../tool/flutter analyze
```

`release/help-author-evidence.json` pins source and evidence. The Flutter lane and production source ownership were released after these checks. Public support/privacy/deletion contacts, deployed services, physical accessibility, human reading comprehension and actual store review remain separate gates.

# Tideglass v1 sound direction

Director decision, 25 October 2026. Adopt the existing original score, eight cues and implemented playback policy as the v1 creative direction. This decision selects authored material and integration behavior; it does not assert that a listening session or physical-device mix check took place. No audio asset, gain, economy rule or production source changes with this decision.

The harbor should feel patient and inhabited. Use the score's restrained synthesized glass, felt and sustained tones, with space between melodic phrases. Keep ordinary actions brief; reserve longer musical gestures for milestones and Rechart. Sound accompanies visible feedback, and critical information remains available without hearing it.

| Context | Adopted piece | Musical direction and existing runtime route |
|---|---|---|
| Main harbor before the ending | A Harbor of Small Lights | 60 BPM, D Dorian; warm sustained harmony, sparse glass melody. Selected by bootstrap and on return from the season. |
| Season fleet | The Glass Current | 72 BPM, G major with suspended second; soft mallet and arpeggio movement. Selected when opening the season. |
| Main harbor after the ending | Where the Sky Comes Home | 54 BPM, F Lydian / D Dorian; slower, open harmony. Selected from the saved ending state and on return from the season. |

Retain the eight authored cues: purchase, panel, claim, calibration, survey, unlock, milestone and rechart. The unlock cue is present in the library but has no current automatic controller emission; this decision preserves that routing and does not claim that all eight cues trigger during gameplay. Only accepted visible foreground actions may trigger routed cues. Income ticks, save loading and offline replay remain silent; stale or future events, muted/background state and rapid same-cue repeats are suppressed. Returning to the app restarts the selected ambient piece without replaying a backlog of effects.

Keep the existing default music preference 0.32 and effects preference 0.55, with independent sliders, independent mute controls and master mute. The native music driver applies half the selected music level. Up to eight effect voices share a 0.9 gain budget; extra simultaneous voices are dropped. Preserve system silence/routing behavior, no background playback and the existing fail-muted preference recovery. These are chosen implementation values, not a perceptual loudness certification.

The musical source and mathematical synthesis are original work by the authorized AI development team. No external commission, purchased recording, human performance or legal exclusivity is claimed. The existing three-track soundtrack package remains tied to the supporter offer; its local ZIP is not proof of authenticated paid delivery.

Existing native evidence proves decoder initialization, all eleven AAC decodes and advancing playback clocks on the recorded iPhone, iPad and Android simulator/emulator targets. Independent actual-widget tests prove the controls with an explicitly fake audio driver; that evidence is distinct from native playback evidence. Physical speaker/headphone listening, mix balance, route/call interruptions, genuine soundtrack fulfillment and final distribution review remain open. Store previews remain accurately described as silent. M5-06 and broader S23 release acceptance are not granted by this bounded creative decision.

Source and evidence hashes are recorded in the accompanying director decision under `release/audio/`. Subsequent playtest or device findings may require a specifically reviewed correction; they do not require replacing this palette without evidence.

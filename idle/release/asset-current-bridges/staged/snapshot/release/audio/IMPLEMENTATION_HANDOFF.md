# Tideglass original audio and producer presentation handoff

The five audio packages and 25 producer presentations are authored and integrated through new native client components. They remain `in_production`; file presence and host tests do not satisfy native device, listening, commerce or full release acceptance.

## Actual deliverables

- `source/audio/score/tideglass.score.json`: original musical source, explicit harmonic voicings, melodic phrases and eight cue scores. Three ambient pieces run 64.000, 53.333 and 71.111 seconds.
- `tools/audio/render_score.py`: original mathematical instruments and room reflections, 48 kHz / 24-bit stereo WAV masters, AAC LC exports and numerical measurements. No external recordings, sampled instruments or reference melody are incorporated.
- `source/audio/masters/`: three music masters and eight cue masters. `game/mobile/assets/audio/` contains the 11 matching AAC runtime files, totaling 2,646,248 bytes.
- `release/downloads/tideglass-original-soundtrack.zip`: 52,699,186-byte local soundtrack package containing the same three masters, cover SVG, musical source, synthesis source, dependency versions, measurements and credits. Excluded from initial app install. A local ZIP is not authenticated supporter fulfillment.
- `game/mobile/lib/audio_bus.dart`: native audioplayers 6.8.1 adapter, lifecycle policy, separate music/SFX volumes and mute, master mute, atomic preference storage, bounded voice pool and stale-event suppression.
- `game/mobile/lib/audio_settings.dart`: scroll-compatible native controls. Root/client own integration into application and accepted-action routing.
- `source/art/producers/`: 25 editable scene descriptions. `tools/assets/export_producers.py` authors geometry and emits matching SVG plus compiled native geometry. `game/assets/producers/` contains 25 SVGs and descriptors.
- `game/mobile/lib/producer_art.dart`: `StagedProducerArt(tier: 0..4, count: int, size: 72, locked: false, selected: false)`. Five threshold stages at 0/25/50/75/100, static reduced-motion parity, visible lock badge and selected frame. Adjacent heading/count supplies semantics.
- `release/art/producer-contact-sheet.png`: actual Flutter Canvas renderer, all 25 stages together. Review labels use a host system font only; that font is not bundled in the application or content.

## Playback integration

Construct one `TideAudioBus` per bootstrap with `NativeTideAudioDriver` and `FileAudioPreferenceStore` pointing at the app-support directory's `audio-preferences.json`. Call `initialize` asynchronously without blocking economic save loading. `startMusic` selects `harbor`, `current` or `dawn`; repeating the currently playing track adjusts volume without restarting it. `AudioSettings(audio: bus)` exposes persistent controls.

Call `playCue` only after an accepted, visible foreground action. Available cues are `purchase`, `panel`, `claim`, `calibration`, `survey`, `unlock`, `milestone`, `rechart`. Income ticks, save load/import and offline replay must not synthesize action cues. `offline: true`, stale events older than 750 ms, future events, background state and muted state are all rejected. Same-cue repetitions within 100 ms are dropped. No queue replays on return.

The native adapter allocates one music player and at most eight effects voices; a ninth simultaneous effect is dropped. It respects system silence, follows system routing, mixes with other apps, and requests no background playback. Lifecycle transitions stop all effects and music; foreground return restarts only the selected ambient track. Actual headphone-route and call interruption behavior still requires native qualification.

Music gain is capped at half the preference value. Active effects divide a 0.9 gain budget among occupied voices, preventing worst-case coherent summation from clipping at maximum controls. With measured decoded peaks, the combined bound is below 0.712 amplitude (about −2.95 dBFS). This mathematical bound is not a substitute for listening/mix approval.

Partial native setup failure is cleaned up across every allocated player; a rejected initialization future cannot bypass disposal. Preference read failure defaults to muted rather than guessing a previous mute choice. Preference write failure leaves current controls effective and surfaces a warning. Muting is applied before waiting for a slow disk write.

## Evidence and limits

`release/audio/components-host-test.log` records 18 passing tests: 12 policy/persistence tests, two tests using the actual AudioPlayer native method/event bridge with a mocked platform, and four native Canvas producer tests. The bridge tests inject partial setup failure, verify cleanup, enforce eight effect voices/one music player, and check aggregate gain. These are host tests; no real decoder/device is represented by the mock bridge.

`release/audio/component-analyzer.log` records component analysis. `release/audio/render-measurements.json` records source and decoded-AAC duration, clipping count, DC offset, integrated LUFS estimate, 4× oversampled peak estimate and boundary step. All decoded music sample counts exactly match their masters; decoded loop boundary steps are below −81 dBFS. The numerical meter is an implementation estimate, not a certified meter. `release/audio/asset-integrity.json` checks source/export/client hashes and the soundtrack ZIP.

All original producer geometry is now constrained to the 100×100 view box, including stroke width. The first review sheet allowed an outer Observatory ring to extend above its view box; its center was corrected and an explicit primitive-boundary regression added. Current contact sheet and source reflect the corrected geometry.

Independent client review lives at `release/art/producer-independent-review.md`. Physical-device minimum-size appearance, performance and all variants still require their release gates. Root/client integrate main and seasonal cards; challenge cards/harbor may still use earlier base silhouettes until those owners update them.

## Remaining release gates

1. Build and decode every AAC member on both iOS and Android, verify repeated loops and real lifecycle transitions.
2. Human speaker/headphone audition, mix approval, call interruption and headphone disconnection tests.
3. Project-owner distribution terms review of the documented original material. Credits record authoring without asserting legal copyright eligibility, exclusivity or a legal opinion.
4. Authenticated supporter download hosting, entitlement restoration and fulfillment tests. No host/account exists yet; no paid ownership is granted by this work.
5. Native device producer/harbor/cosmetic presentation and performance qualification; host contact sheets establish neither device performance nor production acceptance.

No original scope IDs, counts, prices, producer math, prestige rules, challenge economics or paid rewards changed.

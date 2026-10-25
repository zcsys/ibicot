import 'presentation.dart';
import 'strings.dart';
import 'dart:async';
import 'package:flutter/material.dart';
import 'audio_bus.dart';

/// Drop into the existing settings scroll view. No economic state is changed.
class AudioSettings extends StatelessWidget {
  const AudioSettings({super.key, required this.audio});
  final TideAudioBus audio;

  @override
  Widget build(BuildContext context) => ListenableBuilder(
    listenable: audio,
    builder: (context, _) {
      final preferences = audio.preferences;
      void update(AudioPreferences next) =>
          unawaited(audio.setPreferences(next));
      return Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          SwitchListTile(
            title: const LocalizedText(UiEnglish.audioMuteAllSound),
            value: preferences.muted,
            onChanged: (value) => update(preferences.copyWith(muted: value)),
          ),
          SwitchListTile(
            title: const LocalizedText(UiEnglish.audioMusic),
            subtitle: const LocalizedText(UiEnglish.audioQuietHarborThemes),
            value: !preferences.musicMuted,
            onChanged: (value) =>
                update(preferences.copyWith(musicMuted: !value)),
          ),
          Semantics(
            label: Presentation.text(UiEnglish.audioMusicVolume),
            child: Slider(
              value: preferences.musicVolume,
              divisions: 20,
              label: Presentation.text(
                '${(preferences.musicVolume * 100).round()}%',
              ),
              semanticFormatterCallback: (value) =>
                  UiEnglish.audioValueRoundPercent((value * 100).round()),
              onChanged: (value) =>
                  update(audio.preferences.copyWith(musicVolume: value)),
            ),
          ),
          SwitchListTile(
            title: const LocalizedText(UiEnglish.audioSoundEffects),
            subtitle: const LocalizedText(UiEnglish.audioActionsAndDiscoveries),
            value: !preferences.sfxMuted,
            onChanged: (value) =>
                update(preferences.copyWith(sfxMuted: !value)),
          ),
          Semantics(
            label: Presentation.text(UiEnglish.audioSoundEffectsVolume),
            child: Slider(
              value: preferences.sfxVolume,
              divisions: 20,
              label: Presentation.text(
                '${(preferences.sfxVolume * 100).round()}%',
              ),
              semanticFormatterCallback: (value) =>
                  UiEnglish.audioValueRoundPercent2((value * 100).round()),
              onChanged: (value) =>
                  update(audio.preferences.copyWith(sfxVolume: value)),
            ),
          ),
          if (audio.warning != null)
            Padding(
              padding: const EdgeInsets.all(16),
              child: LocalizedText(audio.warning!),
            ),
        ],
      );
    },
  );
}

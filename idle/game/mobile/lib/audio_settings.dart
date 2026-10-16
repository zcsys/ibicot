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
            title: const Text('Mute all sound'),
            value: preferences.muted,
            onChanged: (value) => update(preferences.copyWith(muted: value)),
          ),
          SwitchListTile(
            title: const Text('Music'),
            subtitle: const Text('Quiet harbor themes'),
            value: !preferences.musicMuted,
            onChanged: (value) =>
                update(preferences.copyWith(musicMuted: !value)),
          ),
          Semantics(
            label: 'Music volume',
            child: Slider(
              value: preferences.musicVolume,
              divisions: 20,
              label: '${(preferences.musicVolume * 100).round()}%',
              semanticFormatterCallback: (value) =>
                  '${(value * 100).round()} percent',
              onChanged: (value) =>
                  update(audio.preferences.copyWith(musicVolume: value)),
            ),
          ),
          SwitchListTile(
            title: const Text('Sound effects'),
            subtitle: const Text('Actions and discoveries'),
            value: !preferences.sfxMuted,
            onChanged: (value) =>
                update(preferences.copyWith(sfxMuted: !value)),
          ),
          Semantics(
            label: 'Sound effects volume',
            child: Slider(
              value: preferences.sfxVolume,
              divisions: 20,
              label: '${(preferences.sfxVolume * 100).round()}%',
              semanticFormatterCallback: (value) =>
                  '${(value * 100).round()} percent',
              onChanged: (value) =>
                  update(audio.preferences.copyWith(sfxVolume: value)),
            ),
          ),
          if (audio.warning != null)
            Padding(
              padding: const EdgeInsets.all(16),
              child: Text(audio.warning!),
            ),
        ],
      );
    },
  );
}

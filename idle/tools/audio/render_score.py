#!/usr/bin/env python3
"""Render the authored Tideglass score. No samples or external audio are used.

Run with .tooling/audio-python/bin/python tools/audio/render_score.py.
Requires numpy, scipy, soundfile, and macOS afconvert (AAC export/verification).
The score is musical source; this file is the reusable synthesis/export adapter.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import tempfile
import wave
import zipfile

import numpy as np
import scipy
from scipy.signal import lfilter, resample_poly
import soundfile as sf

ROOT = Path(__file__).resolve().parents[2]
SCORE_PATH = ROOT / 'source/audio/score/tideglass.score.json'
SCORE = json.loads(SCORE_PATH.read_text())
SR = SCORE['sample_rate']
TAU = 2 * math.pi
RUNTIME = ROOT / 'game/mobile/assets/audio'
MASTERS = ROOT / 'source/audio/masters'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def note_hz(note):
    offsets = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
    accidental = 1 if '#' in note else -1 if 'b' in note else 0
    midi = 12 * (int(note[-1]) + 1) + offsets[note[0]] + accidental
    return 440 * 2 ** ((midi - 69) / 12)


def instrument(note, seconds, kind, gain, pan=0, phase=0):
    n = max(2, round(seconds * SR))
    t = np.arange(n) / SR
    hz = note_hz(note)
    if kind == 'pad':
        envelope = np.sin(np.pi * np.minimum(t / 1.6, 1) / 2) ** 2
        envelope *= np.sin(np.pi * np.minimum((seconds - t) / 2.4, 1) / 2) ** 2
        tone = (.82 * np.sin(TAU * hz * t + phase)
                + .13 * np.sin(TAU * hz * 2 * t + phase)
                + .05 * np.sin(TAU * hz * 3 * t + phase))
        tone *= .94 + .06 * np.cos(TAU * .12 * t + phase)
    elif kind == 'glass':
        envelope = (1 - np.exp(-t / .012)) * np.exp(-t / (seconds * .30))
        envelope *= np.minimum((seconds - t) / .18, 1).clip(0, 1) ** 2
        tone = (np.sin(TAU * hz * t) + .24 * np.sin(TAU * hz * 2 * t) * np.exp(-t / .8)
                + .10 * np.sin(TAU * hz * 3.01 * t) * np.exp(-t / .4)
                + .045 * np.sin(TAU * hz * 4.02 * t) * np.exp(-t / .25)) / 1.385
    else:
        envelope = (1 - np.exp(-t / .007)) * np.exp(-t / (seconds * .22))
        envelope *= np.minimum((seconds - t) / .12, 1).clip(0, 1) ** 2
        tone = (np.sin(TAU * hz * t) + .18 * np.sin(TAU * hz * 2 * t) * np.exp(-t / .12)) / 1.18
    mono = tone * envelope * gain
    # Constant-power pan. No antiphase stereo widening; mono remains readable.
    angle = (pan + 1) * np.pi / 4
    return np.column_stack((mono * np.cos(angle), mono * np.sin(angle)))


def add(dst, src, at, cyclic=False):
    start = round(at * SR)
    if cyclic:
        start %= len(dst)
        count = min(len(src), len(dst) - start)
        dst[start:start + count] += src[:count]
        if count < len(src):
            dst[:len(src) - count] += src[count:]
    else:
        count = min(len(src), len(dst) - start)
        if count > 0:
            dst[start:start + count] += src[:count]


def space(audio, cyclic):
    # Authored stereo early reflections, not a sampled impulse response.
    wet = audio.copy()
    for seconds, gain in [(.173, .12), (.293, .10), (.479, .07), (.787, .05), (1.271, .025)]:
        delay = round(seconds * SR)
        if cyclic:
            wet += np.roll(audio[:, ::-1], delay, axis=0) * gain
        else:
            wet[delay:] += audio[:-delay, ::-1] * gain
    return wet


def master(audio, peak_db, cyclic):
    audio = space(audio, cyclic)
    audio -= audio.mean(axis=0)
    audio *= 10 ** (peak_db / 20) / max(np.abs(audio).max(), 1e-12)
    # A 12 ms boundary taper prevents discontinuity without an audible long gap.
    ramp = np.sin(np.linspace(0, np.pi / 2, round(.012 * SR))) ** 2
    audio[:len(ramp)] *= ramp[:, None]
    audio[-len(ramp):] *= ramp[::-1, None]
    return audio


def music(track):
    beat = 60 / track['bpm']
    audio = np.zeros((round(64 * beat * SR), 2))
    for phrase in range(2):
        for bar, chord in enumerate(track['bars']):
            start = (phrase * 32 + bar * 4) * beat
            for voice, note in enumerate(chord):
                add(audio, instrument(note, 6.5 * beat, 'pad', .052,
                                      (voice - 2) * .16, voice * .7), start - .8 * beat, True)
            # Six sparse pulses, changing the second phrase's voicing and gaps.
            pattern = [0, 2, 4, 1, 3, 2] if phrase == 0 else [0, 3, 1, 4, 2, 3]
            for index, when in enumerate([.5, 1.25, 2, 2.5, 3.25, 3.75]):
                if track['id'] == 'dawn' and index % 2:
                    continue
                note = chord[pattern[index]]
                note = note[:-1] + str(int(note[-1]) + 1)
                add(audio, instrument(note, 1.8 * beat, 'felt', .027,
                                      -.35 if index % 2 == 0 else .35), start + when * beat, True)
        for index, (note, when, length) in enumerate(track['melody']):
            # Answering phrase rises on its last two notes, then resolves at loop.
            if phrase == 1 and index in (len(track['melody']) - 3,):
                note = note[:-1] + str(int(note[-1]) + 1)
            add(audio, instrument(note, (length + 1.7) * beat, 'glass', .083,
                                  .18 * math.sin(index)), (phrase * 32 + when) * beat, True)
    return master(audio, -8, True)


def cue(name, notes):
    duration = max(at + length for _, at, length in notes) + 1.3
    audio = np.zeros((round(duration * SR), 2))
    for i, (note, at, length) in enumerate(notes):
        add(audio, instrument(note, length, 'glass', .21, (i % 3 - 1) * .15), at)
        if name in ('milestone', 'rechart', 'unlock'):
            add(audio, instrument(note, length, 'pad', .06, 0, .4), at)
    return master(audio, -8 if name in ('panel', 'purchase') else -5, False)


def measurements(audio):
    # ITU-R BS.1770 K-weighting at the fixed 48 kHz rate, stereo unit weights,
    # 400 ms blocks / 100 ms hop, -70 LUFS absolute and -10 LU relative gate.
    filtered = lfilter([1.53512485958697, -2.69169618940638, 1.19839281085285],
                      [1, -1.69065929318241, .73248077421585], audio, axis=0)
    filtered = lfilter([1, -2, 1], [1, -1.99004745483398, .99007225036621], filtered, axis=0)
    powers = np.array([np.square(filtered[i:i + 19200]).mean(axis=0).sum()
                       for i in range(0, max(len(audio) - 19200 + 1, 1), 4800)])
    lufs = -.691 + 10 * np.log10(np.maximum(powers, 1e-20))
    absolute = powers[lufs > -70]
    relative = -.691 + 10 * math.log10(absolute.mean()) - 10 if len(absolute) else -70
    gated = powers[(lufs > -70) & (lufs > relative)]
    integrated = -.691 + 10 * math.log10(gated.mean()) if len(gated) else -120
    oversampled = resample_poly(audio, 4, 1, axis=0)
    peak = np.abs(audio).max()
    return {
        'duration_seconds': round(len(audio) / SR, 6), 'samples': len(audio),
        'sample_peak_dbfs': round(20 * math.log10(max(peak, 1e-12)), 3),
        'four_times_oversampled_peak_dbtp_estimate': round(20 * math.log10(max(np.abs(oversampled).max(), 1e-12)), 3),
        'integrated_lufs_bs1770_estimate': round(integrated, 3),
        'dc_offset_max': float(np.abs(audio.mean(axis=0)).max()),
        'boundary_step_dbfs': round(20 * math.log10(max(np.abs(audio[-1] - audio[0]).max(), 1e-12)), 3),
        'clipped_samples': int((np.abs(audio) >= 1).sum()),
        'measurement_note': 'Local numerical estimate, not a certified meter or a listening review.'
    }


def write_asset(name, audio, package, title, loop=False):
    master_path = MASTERS / f'{name}.wav'
    runtime_path = RUNTIME / f'{name}.m4a'
    sf.write(master_path, audio, SR, subtype='PCM_24')
    subprocess.run(['/usr/bin/afconvert', str(master_path), str(runtime_path),
                    '-f', 'm4af', '-d', 'aac', '-b', '128000', '-q', '127'], check=True)
    with tempfile.TemporaryDirectory() as tmp:
        decoded_path = Path(tmp) / 'decoded.wav'
        subprocess.run(['/usr/bin/afconvert', str(runtime_path), str(decoded_path),
                        '-f', 'WAVE', '-d', 'LEF32'], check=True)
        decoded, decoded_sr = sf.read(decoded_path, always_2d=True)
        assert decoded_sr == SR and decoded.shape[1] == 2
        decoded_stats = measurements(decoded)
    output_path = ROOT / 'game/assets/audio' / package / runtime_path.name
    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(runtime_path, output_path)
    return {'id': f'{package}.{name}', 'title': title, 'source_path': str(master_path.relative_to(ROOT)),
            'source_sha256': digest(master_path), 'runtime_path': str(output_path.relative_to(ROOT)),
            'runtime_sha256': digest(output_path), 'flutter_asset': f'audio/{runtime_path.name}',
            'codec': 'AAC LC in MPEG-4 audio container, 48 kHz stereo, nominal 128 kbit/s',
            'runtime_bytes': output_path.stat().st_size, 'bus': 'music' if loop else 'sfx',
            'loop': loop, 'loop_start_sample': 0 if loop else None,
            'loop_end_sample_exclusive': len(audio) if loop else None,
            'source_measurements': measurements(audio), 'decoded_aac_measurements': decoded_stats,
            'native_decode_verified': False, 'listening_review': None}


def package_descriptor(package, members):
    data = {'schema_version': 1, 'id': package, 'status': 'authored_pending_independent_review',
            'members': members, 'score_source': str(SCORE_PATH.relative_to(ROOT)),
            'source_score_sha256': digest(SCORE_PATH), 'renderer': 'tools/audio/render_score.py',
            'renderer_sha256': digest(Path(__file__)), 'credits': 'source/audio/CREDITS.txt',
            'visual_equivalents': 'All cues accompany an explicit accepted action, visible reward or confirmation. Audio never carries unique progression information.',
            'device_playback_evidence': None}
    for base in ['source/audio', 'game/assets/audio']:
        path = ROOT / base / package / 'package.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2) + '\n')
    return data


def main():
    for directory in [RUNTIME, MASTERS, ROOT / 'release/audio']:
        directory.mkdir(parents=True, exist_ok=True)
    groups = {k: [] for k in ['audio.ambient_score', 'audio.interaction', 'audio.milestone', 'audio.rechart']}
    for track in SCORE['tracks']:
        print(f'Rendering {track["title"]}', flush=True)
        groups['audio.ambient_score'].append(write_asset(track['id'], music(track), 'audio.ambient_score', track['title'], True))
    for name, notes in SCORE['cue_scores'].items():
        group = f'audio.{name}' if name in ('milestone', 'rechart') else 'audio.interaction'
        groups[group].append(write_asset(name, cue(name, notes), group, name.title()))
    descriptors = [package_descriptor(package, members) for package, members in groups.items()]
    report = {'schema_version': 1, 'status': 'render_and_decode_checks_passed_not_auditioned',
              'sample_rate': SR, 'source_format': '48 kHz / 24-bit stereo PCM WAV',
              'tool_versions': {'numpy': np.__version__, 'scipy': scipy.__version__, 'soundfile': sf.__version__,
                                'afconvert': 'macOS system Audio File Convert; OS version recorded in capability-and-rights.json'},
              'compressed_runtime_total_bytes': sum(a['runtime_bytes'] for v in groups.values() for a in v),
              'members': [a for v in groups.values() for a in v],
              'checks': {'exact_three_music_tracks': len(groups['audio.ambient_score']) == 3,
                         'exact_six_interaction_cues': len(groups['audio.interaction']) == 6,
                         'no_source_or_decoded_clipping': all(a[k]['clipped_samples'] == 0 for v in groups.values() for a in v for k in ['source_measurements', 'decoded_aac_measurements']),
                         'decoded_true_peak_below_minus_one': all(a['decoded_aac_measurements']['four_times_oversampled_peak_dbtp_estimate'] < -1 for v in groups.values() for a in v)},
              'pending': ['Actual iOS/Android decode and loop timing', 'Human headphones and speaker audition',
                          'Audio focus, phone call, headphones unplugged and background interruption qualification',
                          'Approved authenticated supporter download route and purchase restoration']}
    (ROOT / 'release/audio/render-measurements.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'checks': report['checks'], 'runtime_bytes': report['compressed_runtime_total_bytes']}), flush=True)


if __name__ == '__main__':
    main()

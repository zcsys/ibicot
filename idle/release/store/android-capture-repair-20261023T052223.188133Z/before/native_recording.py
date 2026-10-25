"""Unedited simulator capture synchronized with the native gallery fixture."""
from __future__ import annotations

import json
from pathlib import Path
import re
import signal
import struct
import subprocess
import time

APP_ID = 'dev.tideglass.game'
READY = 'TIDEGLASS_NATIVE_CAPTURE_READY '
DONE = 'TIDEGLASS_NATIVE_CAPTURE_DONE'


def capture_manifest(evidence: Path, payload: dict, recording: dict, device: str) -> dict:
    """Describe raw, validated capture files without rewriting their pixels."""
    import hashlib
    expected = {f"{payload['device_label']}-capture-{screen}.png" for screen in
                ('main', 'chapter', 'challenge', 'season')}
    screenshots = []
    for value in payload.get('screenshots', []):
        file = Path(value).resolve()
        if file.parent != evidence.resolve() or file.name not in expected:
            raise ValueError('Unexpected gallery screenshot path')
        data = file.read_bytes()
        if data[:8] != b'\x89PNG\r\n\x1a\n' or data[12:16] != b'IHDR' or len(data) < 24:
            raise ValueError('Gallery screenshot is not a PNG with dimensions')
        width, height = struct.unpack('>II', data[16:24])
        if min(width, height) <= 0:
            raise ValueError('Gallery screenshot has invalid dimensions')
        screenshots.append({'file': file.name, 'width': width, 'height': height,
                            'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)})
    if {row['file'] for row in screenshots} != expected or len(screenshots) != 4:
        raise ValueError('All four distinct gallery screens are required')
    video = evidence / 'gameplay.mp4'
    if not recording.get('passed') or not video.is_file():
        raise ValueError('Successful native recording is required for the gallery manifest')
    return {
        'candidate_fingerprint': payload['candidate_fingerprint'],
        'verification_id': payload['verification_id'],
        'harness_sha256': payload['harness_sha256'],
        'device': device, 'device_label': payload['device_label'],
        'platform': payload['platform'], 'os_version': payload['os_version'], 'run_id': payload['run_id'],
        'provenance': payload['provenance'], 'platform_locale': payload['platform_locale'],
        'seeded_core': payload['seeded_core'], 'seeded_story': payload['seeded_story'],
        'actual_purchase_count_delta': payload['actual_purchase_count_delta'],
        'real_gameplay_elapsed_ms': payload['real_gameplay_elapsed_ms'],
        'screenshots': screenshots,
        'video': {'file': video.name, 'bytes': video.stat().st_size,
                  'sha256': hashlib.sha256(video.read_bytes()).hexdigest(), **recording['media']},
        'editing': 'None. Raw production UI screenshots and native recording.',
        'store_submission_status': 'Draft engineering capture; not uploaded or store-approved',
    }


def signal_path(platform: str, directory: str, label: str, run_id: str,
                ios_container: str | None = None) -> Path:
    """Accept only this run's app-private fixture, never an arbitrary log path."""
    for value in (label, run_id):
        if not re.fullmatch(r'[A-Za-z0-9_-]+', value):
            raise ValueError('Unsafe capture identity')
    tail = f'native-verification/capture-{label}-{run_id}'
    path = Path(directory)
    if platform == 'ios':
        if not ios_container:
            raise ValueError('iOS app container is required')
        expected = Path(ios_container).resolve() / 'Library/Application Support' / tail
        if path.resolve() != expected or path.is_symlink():
            raise ValueError('Capture signal is outside the exact iOS fixture')
    elif platform == 'android':
        allowed = {Path(prefix) / 'files' / tail for prefix in
                   (f'/data/user/0/{APP_ID}', f'/data/data/{APP_ID}')}
        if path not in allowed or '..' in path.parts:
            raise ValueError('Capture signal is outside the exact Android fixture')
    else:
        raise ValueError('Unsupported capture platform')
    return path / 'recording-started'


class GalleryRecorder:
    def __init__(self, root: Path, evidence: Path, platform: str, device: str,
                 label: str, run_id: str):
        self.root, self.evidence = root, evidence
        self.platform, self.device = platform, device
        self.label, self.run_id = label, run_id
        self.process = None
        self.recorder_log = None
        self.started = False
        self.done = False
        self.remote = f'/sdcard/tideglass-{evidence.name}.mp4'
        self.video = evidence / 'gameplay.mp4'
        self.report = {'platform': platform, 'device': device, 'audio_recorded': False,
                       'editing': 'None; native simulator screen recorder output',
                       'commands': [], 'errors': []}

    def run(self, command: list[str], timeout: int = 40):
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        self.report['commands'].append({'command': command, 'exit_code': result.returncode,
                                       'output': result.stdout + result.stderr})
        if result.returncode:
            raise RuntimeError('Native capture command failed: ' + command[0])
        return result.stdout.strip()

    def adb(self, *args: str):
        return [str(self.root / '.tooling/android-sdk/platform-tools/adb'),
                '-s', self.device, *args]

    def observe(self, log_text: str):
        if not self.started and READY in log_text:
            raw = log_text.split(READY, 1)[1].splitlines()[0]
            directory = json.loads(raw)['directory']
            container = None
            if self.platform == 'ios':
                container = self.run(['xcrun', 'simctl', 'get_app_container', self.device, APP_ID, 'data'])
            flag = signal_path(self.platform, directory, self.label, self.run_id, container)
            if self.platform == 'ios':
                command = ['xcrun', 'simctl', 'io', self.device, 'recordVideo',
                           '--codec=h264', '--force', str(self.video)]
            else:
                command = self.adb('shell', 'screenrecord', '--time-limit', '27', self.remote)
            self.recorder_log = (self.evidence / 'recorder.log').open('w')
            self.process = subprocess.Popen(command, stdout=self.recorder_log, stderr=subprocess.STDOUT)
            self.report['commands'].append({'command': command, 'kind': 'screen-recorder'})
            self.started = True
            if self.platform == 'ios':
                deadline = time.monotonic() + 15
                while 'Recording started' not in (self.evidence / 'recorder.log').read_text(errors='replace'):
                    if self.process.poll() is not None or time.monotonic() >= deadline:
                        raise RuntimeError('simctl did not acknowledge its first recorded video frame')
                    time.sleep(.1)
                self.report['start_acknowledgement'] = 'simctl first recorded video frame'
            else:
                time.sleep(1)
                self.report['start_acknowledgement'] = 'screenrecord process alive after one second; final MP4 duration independently checked'
            if self.process.poll() is not None:
                raise RuntimeError('Native recorder stopped before fixture acknowledgement')
            if self.platform == 'ios':
                flag.write_text('Native recorder process is running.\n')
            else:
                self.run(self.adb('shell', 'run-as', APP_ID, 'touch', str(flag)))
            self.report['fixture_acknowledged'] = True
        if DONE in log_text and not self.done:
            self.done = True
            if self.platform == 'ios' and self.process and self.process.poll() is None:
                self.process.send_signal(signal.SIGINT)

    def finish(self):
        if not self.started:
            self.report['errors'].append('No synchronized gallery start marker')
        if not self.done:
            self.report['errors'].append('No completed gameplay marker')
        if self.process:
            if self.platform == 'ios' and self.process.poll() is None:
                self.process.send_signal(signal.SIGINT)
            try:
                self.report['recorder_exit_code'] = self.process.wait(timeout=35)
            except subprocess.TimeoutExpired:
                self.process.terminate()
                self.process.wait(timeout=10)
                self.report['errors'].append('Native recorder exceeded its bounded duration')
            if self.recorder_log:
                self.recorder_log.close()
            if self.platform == 'android':
                try:
                    self.run(self.adb('pull', self.remote, str(self.video)))
                    self.run(self.adb('shell', 'rm', self.remote))
                except (RuntimeError, subprocess.TimeoutExpired) as error:
                    self.report['errors'].append(str(error))
        if self.video.is_file():
            try:
                metadata = json.loads(self.run(['xcrun', 'swift', str(self.root / 'tool/native_video_metadata.swift'), str(self.video)], timeout=60))
                self.report['media'] = metadata
                if not 15 <= metadata['duration_seconds'] <= 30:
                    self.report['errors'].append('Footage duration is outside the requested 15–30 seconds')
                if metadata['audio_track_count'] != 0:
                    self.report['errors'].append('Unexpected audio track in declared silent capture')
            except (RuntimeError, ValueError, subprocess.TimeoutExpired) as error:
                self.report['errors'].append('Media metadata: ' + str(error))
        else:
            self.report['errors'].append('Native video artifact is missing')
        self.report['passed'] = not self.report['errors']
        (self.evidence / 'recording.json').write_text(json.dumps(self.report, indent=2) + '\n')
        return self.report


def run_with_gallery(command: list[str], cwd: Path, env: dict[str, str], recorder: GalleryRecorder):
    log_path = recorder.evidence / 'run.log'
    with log_path.open('w') as log:
        process = subprocess.Popen(command, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT)
        try:
            while process.poll() is None:
                recorder.observe(log_path.read_text(errors='replace'))
                time.sleep(.2)
            recorder.observe(log_path.read_text(errors='replace'))
        except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as error:
            recorder.report['errors'].append('Recorder orchestration: ' + str(error))
            # Preserve the failed test's output; interrupt rather than leaving a
            # fixture waiting forever for an acknowledgement that cannot arrive.
            process.send_signal(signal.SIGINT)
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.terminate()
                process.wait(timeout=10)
        returncode = process.wait()
    return returncode, recorder.finish()

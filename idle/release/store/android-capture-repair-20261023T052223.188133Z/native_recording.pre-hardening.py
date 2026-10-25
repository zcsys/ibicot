"""Unedited simulator capture synchronized with the native gallery fixture."""
from __future__ import annotations

import hashlib
import json
import shlex
import zlib
from pathlib import Path
import re
import signal
import struct
import subprocess
import time

APP_ID = 'dev.tideglass.game'
READY = 'TIDEGLASS_NATIVE_CAPTURE_READY '
DONE = 'TIDEGLASS_NATIVE_CAPTURE_DONE'
SCREENSHOT = 'TIDEGLASS_NATIVE_SCREENSHOT_READY '
IDENTITY_KEYS = ('verification_id', 'candidate_fingerprint', 'harness_sha256',
                 'device_label', 'run_id', 'platform', 'scenario')
SCREENS = ('main', 'chapter', 'challenge', 'season')


def raw_png_size(data: bytes) -> tuple[int, int]:
    """Validate unmodified adb PNG framing/CRC and dimensions, never encode pixels."""
    if not 33 <= len(data) <= 32 * 1024 * 1024 or data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('Raw screenshot is not a bounded PNG')
    offset, kinds, size = 8, [], None
    while offset < len(data):
        if offset + 12 > len(data):
            raise ValueError('Truncated raw PNG chunk')
        length, kind = struct.unpack('>I4s', data[offset:offset + 8])
        end = offset + length + 12
        if end > len(data):
            raise ValueError('Truncated raw PNG payload')
        body = data[offset + 8:end - 4]
        crc = struct.unpack('>I', data[end - 4:end])[0]
        if zlib.crc32(kind + body) & 0xffffffff != crc:
            raise ValueError('Raw PNG CRC mismatch')
        if not kinds:
            if kind != b'IHDR' or length != 13:
                raise ValueError('Raw PNG has no valid first IHDR')
            width, height, depth, color, comp, filt, interlace = struct.unpack('>IIBBBBB', body)
            if not (0 < width <= 8192 and 0 < height <= 8192 and depth == 8
                    and color in (2, 6) and comp == filt == interlace == 0):
                raise ValueError('Unexpected Android raw screenshot format')
            size = (width, height)
        elif kind == b'IHDR':
            raise ValueError('Duplicate raw PNG IHDR')
        kinds.append(kind)
        offset = end
        if kind == b'IEND':
            if length or offset != len(data):
                raise ValueError('Invalid raw PNG end')
            break
    if kinds[-1:] != [b'IEND'] or b'IDAT' not in kinds:
        raise ValueError('Incomplete raw PNG')
    return size


def process_start_ticks(stat: str, pid: int) -> int:
    """Linux stat field22, allowing spaces/parentheses in the comm field."""
    prefix, separator, tail = stat.rpartition(') ')
    if not separator or not prefix.startswith(f'{pid} ('):
        raise ValueError('Recorder stat identity is malformed')
    fields = tail.split()
    if len(fields) < 20 or not fields[19].isdigit() or int(fields[19]) <= 0:
        raise ValueError('Recorder process start identity is missing')
    return int(fields[19])


def marker_values(log_text: str, marker: str) -> list[str]:
    prefix = r'(?:flutter: |[IEW]/flutter\s*\(\s*\d+\s*\): )?'
    return re.findall(r'^' + prefix + re.escape(marker) + r'([^\r\n]*)$',
                      log_text, re.MULTILINE)



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
    if payload.get('platform') == 'android':
        receipts = payload.get('android_screencaps')
        if not isinstance(receipts, list) or len(receipts) != 4 or receipts != recording.get('android_screenshots'):
            raise ValueError('Android screenshot receipts do not match host capture')
        by_file = {row['file']: row for row in screenshots}
        for index, receipt in enumerate(receipts):
            name = f"{payload['device_label']}-capture-{SCREENS[index]}.png"
            if receipt.get('sequence') != index + 1 or receipt.get('file') != name:
                raise ValueError('Android screenshot receipt order differs')
            if any(receipt.get(key) != payload.get(key) for key in IDENTITY_KEYS):
                raise ValueError('Android screenshot receipt identity differs')
            if any(receipt.get(key) != by_file[name][key] for key in ('sha256', 'bytes', 'width', 'height')):
                raise ValueError('Android raw screenshot differs from receipt')
        if payload.get('android_recording_stop') != recording.get('android_recording_stop'):
            raise ValueError('Android recording stop receipt differs')
        if not recording.get('android_recording_stop', {}).get('recorder_stopped'):
            raise ValueError('Android recorder did not acknowledge the real endpoint')
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
        self.capture_identity = None
        self.capture_directory = None
        self.screenshot_markers = []
        self.android_recorder_identity = None
        if not re.fullmatch(r'[A-Za-z0-9_.-]+', evidence.name) or '..' in evidence.name:
            raise ValueError('Unsafe evidence directory identity')
        if evidence.is_symlink():
            raise ValueError('Evidence directory must not be a symlink')
        self.remote = f'/sdcard/tideglass-{evidence.name}.mp4'
        self.video = evidence / 'gameplay.mp4'
        self.report = {'platform': platform, 'device': device, 'audio_recorded': False,
                       'editing': 'None; native simulator screen recorder output',
                       'commands': [], 'errors': []}

    def run(self, command: list[str], timeout: int = 40, input_text: str | None = None):
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout, input=input_text)
        self.report['commands'].append({'command': command, 'exit_code': result.returncode,
                                       'output': result.stdout + result.stderr})
        if result.returncode:
            raise RuntimeError('Native capture command failed: ' + command[0])
        return result.stdout.strip()

    def adb(self, *args: str):
        return [str(self.root / '.tooling/android-sdk/platform-tools/adb'),
                '-s', self.device, *args]

    def bind_command(self, command: list[str]):
        if self.platform != 'android':
            return
        definitions = {}
        for part in command:
            if part.startswith('--dart-define='):
                key, value = part[len('--dart-define='):].split('=', 1)
                if key in definitions:
                    raise ValueError('Duplicate native command identity')
                definitions[key] = value
        identity = {
            'verification_id': definitions.get('TIDEGLASS_VERIFICATION_ID'),
            'candidate_fingerprint': definitions.get('TIDEGLASS_CANDIDATE_FINGERPRINT'),
            'harness_sha256': definitions.get('TIDEGLASS_HARNESS_SHA256'),
            'device_label': definitions.get('TIDEGLASS_DEVICE_LABEL'),
            'run_id': definitions.get('TIDEGLASS_RUN_ID'),
            'platform': 'android', 'scenario': definitions.get('TIDEGLASS_SCENARIO'),
        }
        if (identity['verification_id'] != self.evidence.name or identity['device_label'] != self.label
                or identity['run_id'] != self.run_id or identity['scenario'] != 'capture-gallery'
                or not re.fullmatch(r'[a-f0-9]{64}', identity['candidate_fingerprint'] or '')
                or identity['harness_sha256'] != hashlib.sha256((self.evidence / 'harness.dart').read_bytes()).hexdigest()):
            raise ValueError('Android capture command identity does not match evidence')
        self.capture_identity = identity

    def checked_request(self, raw: str) -> dict:
        request = json.loads(raw)
        if not isinstance(request, dict) or self.capture_identity is None:
            raise ValueError('Android capture request has no bound command identity')
        if any(request.get(key) != value for key, value in self.capture_identity.items()):
            raise ValueError('Android capture request identity mismatch')
        directory = request.get('directory')
        if not isinstance(directory, str):
            raise ValueError('Android capture directory is missing')
        signal_path('android', directory, self.label, self.run_id)
        if self.capture_directory is not None and directory != self.capture_directory:
            raise ValueError('Android capture directory changed within this run')
        self.capture_directory = directory
        return request

    def acknowledge(self, filename: str, payload: dict):
        if not re.fullmatch(r'(?:screenshot-[1-4]-ready|recording-stopped)\.json', filename):
            raise ValueError('Unsafe screenshot acknowledgement name')
        destination = Path(self.capture_directory) / filename
        pending = str(destination) + '.pending'
        # Fully write a fresh temporary, then atomically publish without replacing
        # an existing acknowledgement. All paths are this exact private fixture.
        shell = (f'set -C; cat > {shlex.quote(pending)} && '
                 f'ln {shlex.quote(pending)} {shlex.quote(str(destination))} && '
                 f'rm {shlex.quote(pending)}')
        self.run(self.adb('shell', 'run-as', APP_ID, 'sh', '-c', shlex.quote(shell)),
                 timeout=5, input_text=json.dumps(payload, sort_keys=True) + '\n')

    def capture_android_screenshot(self, raw: str):
        request = self.checked_request(raw)
        index = len(self.screenshot_markers)
        if index >= 4 or request.get('sequence') != index + 1 or type(request.get('sequence')) is not int:
            raise ValueError('Unexpected Android screenshot sequence')
        expected = f'{self.label}-capture-{SCREENS[index]}.png'
        if request.get('file') != expected or self.done or (index == 0 and self.started) or (index > 0 and not self.started):
            raise ValueError('Unexpected Android screenshot name or phase')
        elapsed = request.get('gameplay_elapsed_ms')
        if type(elapsed) is not int or not 0 <= elapsed <= 180000 or (index == 0 and elapsed != 0):
            raise ValueError('Invalid screenshot real elapsed time')
        if index and elapsed < self.report['android_screenshots'][-1]['gameplay_elapsed_ms']:
            raise ValueError('Screenshot real elapsed time moved backward')
        if any(type(request.get(k)) is not int or not 0 < request[k] <= 8192 for k in ('width', 'height')):
            raise ValueError('Invalid screenshot device geometry')
        if index and self.process.poll() is not None:
            raise RuntimeError('Android recorder exited before gallery completion')
        path = self.evidence / expected
        if path.exists() or path.is_symlink():
            raise ValueError('Refusing to replace a raw Android screenshot')
        command = self.adb('exec-out', 'screencap', '-p')
        start = time.monotonic_ns()
        result = subprocess.run(command, capture_output=True, timeout=5)
        end = time.monotonic_ns()
        self.report['commands'].append({'command': command, 'exit_code': result.returncode,
                                       'stderr': result.stderr.decode(errors='replace'),
                                       'raw_bytes': len(result.stdout)})
        if result.returncode:
            raise RuntimeError('Android raw screencap failed')
        # Preserve the actual returned bytes even if validation fails; never repair.
        with path.open('xb') as target:
            target.write(result.stdout)
        width, height = raw_png_size(result.stdout)
        if (width, height) != (request['width'], request['height']):
            raise ValueError('Raw screenshot geometry differs from the app view')
        receipt = {**request, 'sha256': hashlib.sha256(result.stdout).hexdigest(),
                   'bytes': len(result.stdout), 'capture_method': 'adb exec-out screencap -p',
                   'host_capture_start_monotonic_ns': start, 'host_capture_end_monotonic_ns': end}
        self.report.setdefault('android_screenshots', []).append(receipt)
        self.acknowledge(f'screenshot-{index + 1}-ready.json', receipt)
        self.screenshot_markers.append(raw)

    def recorder_identity(self, pid: int) -> dict:
        if type(pid) is not int or not 1 < pid < 2**31:
            raise ValueError('Invalid owned recorder PID')
        before = self.run(self.adb('shell', 'cat', f'/proc/{pid}/stat'), timeout=5)
        argv = self.run(self.adb('shell', 'cat', f'/proc/{pid}/cmdline'), timeout=5).split('\0')
        argv = [value for value in argv if value]
        after = self.run(self.adb('shell', 'cat', f'/proc/{pid}/stat'), timeout=5)
        tick = process_start_ticks(before, pid)
        if tick != process_start_ticks(after, pid):
            raise ValueError('Owned recorder process identity changed during observation')
        if (len(argv) != 4 or argv[0] not in ('screenrecord', '/system/bin/screenrecord')
                or argv[1:] != ['--time-limit', '27', self.remote]):
            raise ValueError('PID is not the exact owned screenrecord command')
        return {'pid': pid, 'start_ticks': tick, 'argv': argv}

    def stop_android_recorder(self):
        identity = self.android_recorder_identity
        if identity is None:
            raise ValueError('No validated owned Android recorder identity')
        current = self.recorder_identity(identity['pid'])
        if current != identity:
            raise ValueError('Refusing to signal a changed Android recorder identity')
        self.run(self.adb('shell', 'kill', '-2', str(identity['pid'])), timeout=5)
        code = self.process.wait(timeout=8)
        if code != 0:
            raise RuntimeError('Owned Android recorder failed during finalization')
        self.report['android_recorder_stop'] = {'identity': current,
            'host_monotonic_ns': time.monotonic_ns(), 'exit_code': code}

    def observe(self, log_text: str):
        if self.platform == 'android':
            screenshots = marker_values(log_text, SCREENSHOT)
            if screenshots[:len(self.screenshot_markers)] != self.screenshot_markers:
                raise ValueError('Screenshot request history changed')
            for request in screenshots[len(self.screenshot_markers):]:
                self.capture_android_screenshot(request)
        if not self.started and READY in log_text:
            raw = log_text.split(READY, 1)[1].splitlines()[0]
            if self.platform == 'android':
                entries = marker_values(log_text, READY)
                if len(entries) != 1 or len(self.screenshot_markers) != 1:
                    raise ValueError('Android recording start requires the exact main screenshot')
                directory = self.checked_request(entries[0])['directory']
            else:
                directory = json.loads(raw)['directory']
            container = None
            if self.platform == 'ios':
                container = self.run(['xcrun', 'simctl', 'get_app_container', self.device, APP_ID, 'data'])
            flag = signal_path(self.platform, directory, self.label, self.run_id, container)
            if self.platform == 'ios':
                command = ['xcrun', 'simctl', 'io', self.device, 'recordVideo',
                           '--codec=h264', '--force', str(self.video)]
            else:
                shell = (f'screenrecord --time-limit 27 {shlex.quote(self.remote)} & '
                         'capture_pid=$!; echo TIDEGLASS_SCREENRECORD_PID=$capture_pid; '
                         'wait "$capture_pid"')
                command = self.adb('shell', shell)
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
                deadline = time.monotonic() + 5
                matches = []
                while not matches:
                    matches = re.findall(r'^TIDEGLASS_SCREENRECORD_PID=([0-9]+)$',
                        (self.evidence / 'recorder.log').read_text(errors='replace'), re.MULTILINE)
                    if len(matches) > 1 or self.process.poll() is not None or time.monotonic() >= deadline:
                        raise RuntimeError('No unique owned screenrecord launch PID')
                    if not matches:
                        time.sleep(.05)
                self.android_recorder_identity = self.recorder_identity(int(matches[0]))
                self.report['android_recorder_start'] = {'identity': self.android_recorder_identity,
                    'host_monotonic_ns': time.monotonic_ns()}
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
            if self.platform == 'android':
                entries = marker_values(log_text, DONE + ' ')
                if len(entries) != 1 or len(self.screenshot_markers) != 4 or not self.started:
                    raise ValueError('Android completed marker requires four exact screenshots')
                request = self.checked_request(entries[0])
                elapsed = request.get('gameplay_elapsed_ms')
                if type(elapsed) is not int or elapsed < self.report['android_screenshots'][-1]['gameplay_elapsed_ms']:
                    raise ValueError('Invalid Android real endpoint')
                if self.process.poll() is not None:
                    raise RuntimeError('Android recorder exited before its real endpoint')
                self.stop_android_recorder()
                receipt = {**request, 'recorder_stopped': True,
                           'recorder_identity': self.android_recorder_identity,
                           'host_stop_monotonic_ns': time.monotonic_ns()}
                self.acknowledge('recording-stopped.json', receipt)
                self.report['android_recording_stop'] = receipt
            self.done = True
            if self.platform == 'ios' and self.process and self.process.poll() is None:
                self.process.send_signal(signal.SIGINT)

    def finish(self):
        if not self.started:
            self.report['errors'].append('No synchronized gallery start marker')
        if not self.done:
            self.report['errors'].append('No completed gameplay marker')
        if self.process:
            if self.platform == 'android' and self.process.poll() is None and self.android_recorder_identity is not None:
                try:
                    self.stop_android_recorder()
                except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as error:
                    self.report['errors'].append('Android recorder cleanup: ' + str(error))
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
                    if self.video.exists() or self.video.is_symlink():
                        raise RuntimeError('Refusing to replace the raw Android video')
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
    recorder.bind_command(command)
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

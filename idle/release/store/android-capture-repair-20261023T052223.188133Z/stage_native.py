from pathlib import Path
P=Path(__file__).resolve().parent/'staged/native_recording.py';s=P.read_text()
s=s.replace('import json\n','import hashlib\nimport json\nimport shlex\nimport zlib\n')
s=s.replace("DONE = 'TIDEGLASS_NATIVE_CAPTURE_DONE'", """DONE = 'TIDEGLASS_NATIVE_CAPTURE_DONE'
SCREENSHOT = 'TIDEGLASS_NATIVE_SCREENSHOT_READY '
IDENTITY_KEYS = ('verification_id', 'candidate_fingerprint', 'harness_sha256',
                 'device_label', 'run_id', 'platform', 'scenario')
SCREENS = ('main', 'chapter', 'challenge', 'season')


def raw_png_size(data: bytes) -> tuple[int, int]:
    \"\"\"Validate unmodified adb PNG framing/CRC and dimensions, never encode pixels.\"\"\"
    if not 33 <= len(data) <= 32 * 1024 * 1024 or data[:8] != b'\\x89PNG\\r\\n\\x1a\\n':
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
    \"\"\"Linux stat field22, allowing spaces/parentheses in the comm field.\"\"\"
    prefix, separator, tail = stat.rpartition(') ')
    if not separator or not prefix.startswith(f'{pid} ('):
        raise ValueError('Recorder stat identity is malformed')
    fields = tail.split()
    if len(fields) < 20 or not fields[19].isdigit() or int(fields[19]) <= 0:
        raise ValueError('Recorder process start identity is missing')
    return int(fields[19])


def marker_values(log_text: str, marker: str) -> list[str]:
    prefix = r'(?:flutter: |[IEW]/flutter\\s*\\(\\s*\\d+\\s*\\): )?'
    return re.findall(r'^' + prefix + re.escape(marker) + r'([^\\r\\n]*)$',
                      log_text, re.MULTILINE)
""")
s=s.replace("    if not recording.get('passed') or not video.is_file():", """    if payload.get('platform') == 'android':
        receipts = payload.get('android_screencaps')
        if not isinstance(receipts, list) or len(receipts) != 4 or receipts != recording.get('android_screenshots'):
            raise ValueError('Android screenshot receipts do not match host capture')
        by_file = {row['file']: row for row in screenshots}
        for index, receipt in enumerate(receipts):
            name = f\"{payload['device_label']}-capture-{SCREENS[index]}.png\"
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
    if not recording.get('passed') or not video.is_file():""")
s=s.replace("        self.done = False\n", """        self.done = False
        self.capture_identity = None
        self.capture_directory = None
        self.screenshot_markers = []
        self.android_recorder_identity = None
        if not re.fullmatch(r'[A-Za-z0-9_.-]+', evidence.name) or '..' in evidence.name:
            raise ValueError('Unsafe evidence directory identity')
        if evidence.is_symlink():
            raise ValueError('Evidence directory must not be a symlink')
""")
s=s.replace('    def run(self, command: list[str], timeout: int = 40):\n        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)', '    def run(self, command: list[str], timeout: int = 40, input_text: str | None = None):\n        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout, input=input_text)')
needle='    def observe(self, log_text: str):\n'
methods='''    def bind_command(self, command: list[str]):
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
        if not re.fullmatch(r'(?:screenshot-[1-4]-ready|recording-stopped)\\.json', filename):
            raise ValueError('Unsafe screenshot acknowledgement name')
        destination = Path(self.capture_directory) / filename
        pending = str(destination) + '.pending'
        # Fully write a fresh temporary, then atomically publish without replacing
        # an existing acknowledgement. All paths are this exact private fixture.
        shell = (f'set -C; cat > {shlex.quote(pending)} && '
                 f'ln {shlex.quote(pending)} {shlex.quote(str(destination))} && '
                 f'rm {shlex.quote(pending)}')
        self.run(self.adb('shell', 'run-as', APP_ID, 'sh', '-c', shlex.quote(shell)),
                 timeout=5, input_text=json.dumps(payload, sort_keys=True) + '\\n')

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
        argv = self.run(self.adb('shell', 'cat', f'/proc/{pid}/cmdline'), timeout=5).split('\\0')
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
'''
s=s.replace(needle,methods)
s=s.replace("            directory = json.loads(raw)['directory']\n", """            if self.platform == 'android':
                entries = marker_values(log_text, READY)
                if len(entries) != 1 or len(self.screenshot_markers) != 1:
                    raise ValueError('Android recording start requires the exact main screenshot')
                directory = self.checked_request(entries[0])['directory']
            else:
                directory = json.loads(raw)['directory']
""")
s=s.replace("                command = self.adb('shell', 'screenrecord', '--time-limit', '27', self.remote)", """                shell = (f'screenrecord --time-limit 27 {shlex.quote(self.remote)} & '
                         'capture_pid=$!; echo TIDEGLASS_SCREENRECORD_PID=$capture_pid; '
                         'wait \"$capture_pid\"')
                command = self.adb('shell', shell)""")
s=s.replace("            else:\n                time.sleep(1)\n                self.report['start_acknowledgement']", """            else:
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
                self.report['start_acknowledgement']""")
s=s.replace("        if DONE in log_text and not self.done:\n            self.done = True", """        if DONE in log_text and not self.done:
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
            self.done = True""")
s=s.replace("        if self.process:\n            if self.platform == 'ios'", """        if self.process:
            if self.platform == 'android' and self.process.poll() is None and self.android_recorder_identity is not None:
                try:
                    self.stop_android_recorder()
                except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as error:
                    self.report['errors'].append('Android recorder cleanup: ' + str(error))
            if self.platform == 'ios'""")
s=s.replace("                    self.run(self.adb('pull', self.remote, str(self.video)))", """                    if self.video.exists() or self.video.is_symlink():
                        raise RuntimeError('Refusing to replace the raw Android video')
                    self.run(self.adb('pull', self.remote, str(self.video)))""")
s=s.replace("    log_path = recorder.evidence / 'run.log'", "    recorder.bind_command(command)\n    log_path = recorder.evidence / 'run.log'")
P.write_text(s)

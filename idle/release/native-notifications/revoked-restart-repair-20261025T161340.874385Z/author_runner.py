from pathlib import Path
b=Path(__file__).resolve().parent
p=b/'staged/tool/verify_native_reminders.py'
s=p.read_text().replace('import verify_native\n','import verify_native\nimport reminder_restart as restart\n')
s=s.replace("require(scenario in SCENARIOS, 'Reminder scenario is not allowlisted')", "require(scenario in SCENARIOS | restart.SCENARIOS, 'Reminder scenario is not allowlisted')\n    require(scenario not in restart.SCENARIOS or re.fullmatch(r'emulator-[0-9]+', device), 'Restart protocol requires Android emulator')")
s=s.replace("choices=sorted(SCENARIOS)","choices=sorted(SCENARIOS | restart.SCENARIOS)")
s=s.replace("    args = parser.parse_args()", "    parser.add_argument('--predecessor', type=Path)\n    parser.add_argument('--revocation-evidence', type=Path)\n    args = parser.parse_args()\n    require(bool(args.predecessor) == (args.scenario == 'revoked-recover') and bool(args.revocation_evidence) == bool(args.predecessor), 'Recovery requires exact predecessor and actual UI evidence; other scenarios forbid both')")
s=s.replace("        pins = {}", "        if args.scenario in restart.SCENARIOS:\n            sources['reminder_restart.py'] = Path(restart.__file__)\n        pins = {}")
s=s.replace("'device_label': args.label, 'platform': platform}","'device_label': args.label, 'platform': platform, 'device': args.device}")
s=s.replace("        errors = []; process = None", "        errors = []; process = None; prior = None; prior_checkpoint = None\n        restart_host = restart.Host(ROOT, context, evidence) if args.scenario in restart.SCENARIOS else None")
s=s.replace("        try:\n            with (evidence / 'run.log').open('w') as log_file:","""        try:
            if args.scenario == 'revoked-recover':
                prior, prior_checkpoint = restart.validate_predecessor(args.predecessor.resolve(), context,
                    pins, args.revocation_evidence.resolve(), verify_native.native_log_errors)
                report['predecessor'] = {'path': str(args.predecessor.resolve()), 'sha256': sha(args.predecessor)}
                packet = restart.read_json(args.revocation_evidence)
                operator_paths = {'operator.json': args.revocation_evidence,
                    **{name: args.revocation_evidence.parent / name for name in packet['files_sha256']}}
                report['operator_input_pins'] = {str(path.resolve()): sha(path) for path in operator_paths.values()}
                for name, path in operator_paths.items(): shutil.copyfile(path, evidence / ('revocation-' + name))
                denied = restart_host.command('shell', 'dumpsys', 'package', BUNDLE)
                (evidence / 'recovery-permission-before-launch.txt').write_bytes(denied)
                restart.permission(denied.decode(), False)
                for name, want in prior_checkpoint['files_sha256'].items():
                    require(restart.digest(restart_host.read_private(name)) == want, 'Predecessor data changed before recovery launch')
                require(restart.digest(restart_host.read_private('revoke-checkpoint.json')) == prior['restart_preparation']['checkpoint_sha256'], 'Device predecessor checkpoint changed')
                restart_host.save_receipts()
                command.extend(['--dart-define=TIDEGLASS_PREDECESSOR_ID=' + prior['verification_id'],
                    '--dart-define=TIDEGLASS_PREDECESSOR_CHECKPOINT=' + prior['restart_preparation']['checkpoint_sha256']])
                (evidence / 'started.json').write_text(json.dumps(report, indent=2) + '\\n')
            with (evidence / 'run.log').open('w') as log_file:""")
s=s.replace("                        print('OS ACTION ' + json.dumps(value, sort_keys=True), flush=True)","""                        if args.scenario == 'revoked-prepare' and value.get('action') == restart.READY:
                            require('restart_preparation' not in report, 'Repeated revocation checkpoint')
                            report['restart_preparation'] = restart_host.capture_preparation(value, (evidence / 'run.log').read_bytes())
                            print('REVOCATION CHECKPOINT CAPTURED ' + json.dumps(report['restart_preparation'], sort_keys=True), flush=True)
                        print('OS ACTION ' + json.dumps(value, sort_keys=True), flush=True)""")
s=s.replace("            errors.extend(payload_errors(payload, context, log))\n            if process.returncode != 0: errors.append('Native driver exited unsuccessfully')", """            if args.scenario == 'revoked-prepare':
                require(not result_path.exists(), 'Interrupted preparation unexpectedly produced a test result')
                report['restart_death'] = restart_host.capture_death(report.get('restart_preparation', {}))
                errors.extend(restart.interrupted_errors(log, (evidence / 'run.log').read_bytes(),
                    report.get('restart_preparation'), report.get('restart_death'), process.returncode, verify_native.native_log_errors))
            else:
                if args.scenario == 'revoked-recover':
                    errors.extend(restart.recovery_errors(payload, context, prior, prior_checkpoint, log, MARKER, verify_native.native_log_errors))
                    for name, want in payload.get('recovery_save_files_after', {}).items():
                        require(restart.digest(restart_host.read_private(name)) == want, 'Recovery native save export differs')
                    require(restart.digest(restart_host.read_private('notification_preferences.json')) == payload.get('preferences_sha256'), 'Recovery native preferences differ')
                    require(restart.digest(restart_host.read_private('revoke-checkpoint.json')) == prior['restart_preparation']['checkpoint_sha256'], 'Recovery changed predecessor checkpoint')
                    restart_host.save_receipts()
                else:
                    errors.extend(payload_errors(payload, context, log))
                if process.returncode != 0: errors.append('Native driver exited unsuccessfully')""")
s=s.replace("            report['errors'] = errors", """            if prior is not None:
                try:
                    require(sha(args.predecessor) == report['predecessor']['sha256'], 'Predecessor report changed during recovery')
                    require(all(sha(Path(path)) == want for path, want in report['operator_input_pins'].items()), 'Actual UI evidence changed during recovery')
                    restart.validate_predecessor(args.predecessor.resolve(), context, pins,
                        args.revocation_evidence.resolve(), verify_native.native_log_errors)
                except Exception as error:
                    errors.append('Final predecessor observation failed: ' + str(error))
            if restart_host is not None:
                try: restart_host.save_receipts()
                except Exception as error: errors.append('Final restart receipts failed: ' + str(error))
            report['errors'] = errors""")
s=s.replace("            report['passed'] = not errors", "            report['passed'] = not errors and args.scenario != 'revoked-prepare'\n            report['status'] = ('os-interrupted-awaiting-ui-evidence' if not errors and args.scenario == 'revoked-prepare' else 'passed' if not errors else 'failed')")
s=s.replace("        return 0 if report['passed'] else 1", "        return 0 if report['passed'] or report['status'] == 'os-interrupted-awaiting-ui-evidence' else 1")
p.write_text(s)

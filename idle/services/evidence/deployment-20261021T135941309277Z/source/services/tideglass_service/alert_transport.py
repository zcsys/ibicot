"""Opt-in aggregate alert delivery. Receiver receipt is not human acknowledgement."""
import argparse
import hashlib
import http.client
import json
import re
import ssl
import subprocess
import sys
import time
from urllib.parse import urlsplit

from .operating_config import decode, fields, integer, private_bytes

CHECKS = frozenset('database google_acknowledgements support_delivery apple_native_completion ownership_observations reconciliation telemetry_consent telemetry_timestamps critical_flows disk backup operator'.split())
# Unknown future health codes are represented by a fixed safe value, never copied.
CODES = frozenset('''database_missing database_unreadable database_not_regular database_not_private database_empty database_changed_while_opening database_deadline_exceeded database_deadline_or_sqlite_failure missing_schema_definition unsupported_database_objects unsupported_or_incomplete_schema unsupported_or_missing_indexes unsupported_table_structure unsupported_schema_version invalid_feature_configuration database_integrity_failure database_foreign_key_failure backup_is_live_database pending_age_threshold no_server_completion_observation provider_freshness_counts durable_queue_counts no_worker_table events_without_current_consent future_server_receipt_timestamps scan_limit_exceeded retained_consented_event_sample filesystem_free_space disk_usage_unavailable backup_not_specified integrity_and_filesystem_mtime_only backup_unavailable health_deadline_exceeded health_command_failed'''.split())
STATUSES = frozenset({'warning', 'unknown', 'critical'})
IDENTITY = re.compile(r'^[a-zA-Z0-9_-]{1,40}$')
TOKEN = re.compile(r'^[a-zA-Z0-9._~-]{24,256}$')


def read_config(path):
    value = decode(private_bytes(path))
    fields(value, {'version', 'enabled'}, {'environment', 'recipients', 'attempts', 'attempt_seconds', 'backoff_seconds', 'allow_loopback_http'})
    integer(value['version'], 1, 1)
    if type(value['enabled']) is not bool:
        raise ValueError('Explicit enablement required.')
    if not value['enabled']:
        if set(value) != {'version', 'enabled'}:
            raise ValueError('Disabled configuration must contain no recipients.')
        return value
    fields(value, {'version', 'enabled', 'environment', 'recipients', 'attempts', 'attempt_seconds', 'backoff_seconds'}, {'allow_loopback_http'})
    if not isinstance(value['environment'], str) or not IDENTITY.fullmatch(value['environment']):
        raise ValueError('Nonidentifying environment label required.')
    integer(value['attempts'], 1, 3)
    integer(value['attempt_seconds'], 1, 5)
    integer(value['backoff_seconds'], 0, 1)
    allow = value.get('allow_loopback_http', False)
    if type(allow) is not bool:
        raise ValueError('Explicit local transport option required.')
    targets = value['recipients']
    if not isinstance(targets, list) or not 1 <= len(targets) <= 2:
        raise ValueError('One or two explicit receivers required.')
    identities, urls = set(), set()
    for target in targets:
        fields(target, {'id', 'url', 'token_file'})
        if not isinstance(target['id'], str) or not IDENTITY.fullmatch(target['id']) or target['id'] in identities:
            raise ValueError('Unique nonidentifying receiver ID required.')
        identities.add(target['id'])
        address = target['url']
        if (not isinstance(address, str) or not address.isascii() or len(address) > 512
                or any(ord(c) <= 32 or ord(c) == 127 for c in address)):
            raise ValueError('Invalid receiver URL.')
        url = urlsplit(address)
        if (url.username or url.password or url.query or url.fragment or not url.hostname
                or '\\' in address or not url.path.startswith('/') or url.port == 0):
            raise ValueError('Receiver URL cannot carry credentials, query or fragment.')
        if url.scheme == 'http':
            if not allow or url.hostname != '127.0.0.1':
                raise ValueError('Unencrypted transport requires explicit literal loopback.')
        elif url.scheme != 'https':
            raise ValueError('TLS receiver required.')
        if address in urls:
            raise ValueError('Duplicate receiver.')
        urls.add(address)
        token = private_bytes(target['token_file'], 256).decode('ascii')
        if not TOKEN.fullmatch(token):
            raise ValueError('Bounded bearer credential required.')
    return value


def envelope(report, environment):
    """Project only fixed categorical signals; no account IDs, paths or counts."""
    if (not isinstance(report, dict) or report.get('format') != 'tideglass-local-health-v1'
            or type(report.get('generated_at')) is not int or report['generated_at'] < 0
            or report.get('status') not in STATUSES | {'ok'}):
        raise ValueError('Health report required.')
    signals = report.get('signals')
    if not isinstance(signals, list) or len(signals) > 16:
        raise ValueError('Bounded signals required.')
    filtered = []
    for signal in signals:
        if not isinstance(signal, dict) or signal.get('check') not in CHECKS or signal.get('status') not in STATUSES:
            raise ValueError('Unknown health signal.')
        code = signal.get('code')
        filtered.append({'check': signal['check'], 'status': signal['status'],
                         'code': code if isinstance(code, str) and code in CODES else 'unrecognized_health_code'})
    if (report['status'] == 'ok') != (not filtered):
        raise ValueError('Health status contradicts signals.')
    body = {'format': 'tideglass-operator-alert-v1', 'environment': environment,
            'generated_at': report['generated_at'], 'status': report['status'],
            'signals': filtered, 'release_gate_verified': False}
    body['delivery_id'] = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return body


def _attempt(request):
    """Executed in a killable child: DNS and trickling bodies cannot outlive parent budget."""
    fields(request, {'config_path', 'config_digest', 'recipient_id', 'payload'})
    config = read_config(request['config_path'])
    digest = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()
    if not config['enabled'] or digest != request['config_digest']:
        raise ValueError('Explicit unchanged delivery configuration required.')
    target = next(row for row in config['recipients'] if row['id'] == request['recipient_id'])
    payload = request['payload']
    checked = envelope({'format': 'tideglass-local-health-v1',
                        'generated_at': payload.get('generated_at'), 'status': payload.get('status'),
                        'signals': payload.get('signals')}, config['environment'])
    if payload != checked:
        raise ValueError('Invalid internal envelope.')
    token = private_bytes(target['token_file'], 256).decode('ascii')
    if not TOKEN.fullmatch(token):
        raise ValueError('Invalid rotated receiver credential.')
    url = urlsplit(target['url'])
    cls = http.client.HTTPSConnection if url.scheme == 'https' else http.client.HTTPConnection
    options = {'context': ssl.create_default_context()} if url.scheme == 'https' else {}
    connection = cls(url.hostname, port=url.port, timeout=config['attempt_seconds'], **options)
    try:
        body = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()
        connection.request('POST', url.path, body, {'Content-Type': 'application/json',
                           'Authorization': 'Bearer '+token, 'Connection': 'close',
                           'Idempotency-Key': payload['delivery_id']})
        response = connection.getresponse()
        # No redirects, ambient HTTP proxies, response bodies in logs or Retry-After sleeps.
        if response.status not in (200, 202):
            return {'receipt': False, 'code': 'receiver_http_failure'}
        if response.getheader('Content-Type', '').split(';')[0].strip().lower() != 'application/json':
            return {'receipt': False, 'code': 'invalid_receipt'}
        data = response.read(4097)
        if len(data) > 4096:
            return {'receipt': False, 'code': 'invalid_receipt'}
        value = decode(data)
        if (not isinstance(value, dict) or set(value) != {'accepted', 'delivery_id'}
                or value['accepted'] is not True or value['delivery_id'] != payload['delivery_id']):
            return {'receipt': False, 'code': 'invalid_receipt'}
        return {'receipt': True, 'code': 'receiver_accepted'}
    finally:
        connection.close()


def deliver(report, config_path=None):
    if config_path is None:
        return {'status': 'disabled', 'receipts': [], 'human_acknowledged': False}
    config = read_config(config_path)
    if not config['enabled']:
        return {'status': 'disabled', 'receipts': [], 'human_acknowledged': False}
    payload = envelope(report, config['environment'])
    if not payload['signals']:
        return {'status': 'no_signals', 'receipts': [], 'human_acknowledged': False}
    receipts = []
    for target in config['recipients']:
        # Child rereads the same explicitly enabled private config; no secret crosses stdin.
        outcome = {'receipt': False, 'code': 'transport_failure'}
        for attempt in range(1, config['attempts']+1):
            request = {'config_path': str(config_path), 'config_digest': hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest(),
                       'recipient_id': target['id'], 'payload': payload}
            try:
                child = subprocess.run([sys.executable, '-m', 'services.tideglass_service.alert_transport', '--attempt'],
                    input=json.dumps(request).encode(), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                    timeout=config['attempt_seconds'], check=False)
                result = decode(child.stdout) if child.returncode == 0 and len(child.stdout) <= 256 else None
                if (not isinstance(result, dict) or set(result) != {'receipt', 'code'}
                        or type(result['receipt']) is not bool
                        or result['code'] not in {'receiver_accepted', 'invalid_receipt', 'receiver_http_failure', 'transport_failure'}
                        or result['receipt'] != (result['code'] == 'receiver_accepted')):
                    outcome = {'receipt': False, 'code': 'transport_failure'}
                else:
                    outcome = result
            except subprocess.TimeoutExpired:
                outcome = {'receipt': False, 'code': 'attempt_deadline_exceeded'}
            if outcome['receipt']:
                break
            if attempt < config['attempts']:
                time.sleep(config['backoff_seconds'])
        receipts.append({'recipient_id': target['id'], 'attempts': attempt, **outcome})
    return {'status': 'receiver_accepted' if all(x['receipt'] for x in receipts) else 'delivery_incomplete',
            'delivery_id': payload['delivery_id'], 'receipts': receipts, 'human_acknowledged': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--attempt', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--config')
    parser.add_argument('--report', help='Owner-only local health JSON; absent config disables delivery.')
    args = parser.parse_args()
    try:
        if args.attempt:
            # Private child protocol only. Public operator invocation uses --report.
            request = decode(sys.stdin.buffer.read(32769))
            result = _attempt(request)
        else:
            report = decode(private_bytes(args.report, 65536)) if args.report else None
            result = deliver(report, args.config)
        print(json.dumps(result, sort_keys=True))
        return 0 if result.get('status') != 'delivery_incomplete' else 2
    except Exception:
        print(json.dumps({'receipt': False, 'code': 'transport_failure'}) if args.attempt
              else json.dumps({'status': 'configuration_or_report_invalid', 'human_acknowledged': False}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

#!/usr/bin/env python3
"""Offline, aggregate-only analysis of an explicitly supplied study registry.

This tool neither collects telemetry nor certifies registry completeness/consent.
Protocol and data are separate inputs so missing returns cannot erase installs.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import re
import sys

DAY = 86400
Z95 = 1.959963984540054
EXCLUSIONS = {'staff', 'automation', 'invalid_install'}
LIMIT = 32 * 1024 * 1024
TOKEN = re.compile(r'[A-Za-z0-9_-]{1,80}\Z')
HASH = re.compile(r'[a-f0-9]{64}\Z')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def keys(obj, required, optional=()):
    require(isinstance(obj, dict), 'Expected an object')
    require(set(required) <= set(obj) <= set(required) | set(optional),
            'Missing or unrecognized fields')


def integer(value):
    return type(value) is int and 0 <= value < 2**53


def token(value):
    return isinstance(value, str) and TOKEN.fullmatch(value) is not None


def wilson(successes, count):
    """Two-sided 95% Wilson score interval for an observed binomial fraction."""
    require(type(count) is int and type(successes) is int and 0 <= successes <= count,
            'Invalid binomial counts')
    if count == 0:
        return None
    p = successes / count
    z2 = Z95 * Z95
    denominator = 1 + z2 / count
    center = (p + z2 / (2 * count)) / denominator
    radius = Z95 * math.sqrt(p * (1-p) / count + z2 / (4 * count * count)) / denominator
    return [max(0.0, center-radius), min(1.0, center+radius)]


def covers(intervals, start, end):
    cursor = start
    for left, right in sorted(intervals):
        if right <= cursor:
            continue
        if left > cursor:
            return False
        cursor = max(cursor, right)
        if cursor >= end:
            return True
    return False


def validate(protocol, data):
    keys(protocol, ['schema_version', 'study_id', 'synthetic', 'preregistered_at',
                    'enrollment_start', 'enrollment_end', 'primary_outcome',
                    'design', 'exclusion_rules', 'baseline', 'registry_population',
                    'registry_source', 'session_definition', 'missing_data_rule'])
    require(protocol['schema_version'] == 1 and type(protocol['schema_version']) is int,
            'Unsupported protocol version')
    require(type(protocol['synthetic']) is bool, 'Synthetic marker must be explicit')
    require(token(protocol['study_id']), 'Invalid study ID')
    for field in ['preregistered_at', 'enrollment_start', 'enrollment_end']:
        require(integer(protocol[field]), 'Protocol must be preregistered before analysis')
    require(protocol['preregistered_at'] <= protocol['enrollment_start'] < protocol['enrollment_end'],
            'Preregistration must precede the enrollment window')
    require(protocol['primary_outcome'] == 'D7' and protocol['design'] == 'descriptive_no_experiment',
            'This analyzer implements the preregistered descriptive D7 design only')
    require(isinstance(protocol['exclusion_rules'], list) and
            len(protocol['exclusion_rules']) == 3 and set(protocol['exclusion_rules']) == EXCLUSIONS,
            'Exclusions must preserve staff, automation and known-invalid rules only')
    baseline = protocol['baseline']
    keys(baseline, ['candidate_sha256', 'economy_sha256', 'content_sha256', 'config'])
    require(all(isinstance(baseline[k], str) and HASH.fullmatch(baseline[k])
                for k in ['candidate_sha256', 'economy_sha256', 'content_sha256']),
            'Baseline hashes are required')
    require(token(baseline['config']), 'Baseline config is required')
    require(protocol['registry_population'] in {'all_eligible_first_launches', 'opt_in_study'},
            'Unknown registry population')
    for field in ['registry_source', 'session_definition', 'missing_data_rule']:
        require(isinstance(protocol[field], str) and 1 <= len(protocol[field]) <= 2000,
                'Registry provenance and measurement definitions are required')
    keys(data, ['schema_version', 'synthetic', 'cutoff', 'installs', 'sessions'])
    require(type(data['schema_version']) is int and data['schema_version'] == 2,
            'Unsupported data version')
    require(type(data['synthetic']) is bool and data['synthetic'] == protocol['synthetic'],
            'Synthetic and real populations must not be mixed')
    require(integer(data['cutoff']) and data['cutoff'] >= protocol['enrollment_start'],
            'Invalid observation cutoff')
    require(isinstance(data['installs'], list) and len(data['installs']) <= 100000,
            'Registry must be a bounded list')
    require(isinstance(data['sessions'], list) and len(data['sessions']) <= 500000,
            'Sessions must be a bounded list')
    installs = {}
    for row in data['installs']:
        keys(row, ['id', 'first_launch', 'platform', 'device_group', 'acquisition',
                   'baseline_config', 'exclusion', 'observable_intervals'])
        require(token(row['id']) and len(row['id']) >= 8 and row['id'] not in installs,
                'Install IDs must be unique opaque study tokens')
        require(integer(row['first_launch']) and protocol['enrollment_start'] <= row['first_launch']
                < protocol['enrollment_end'] and row['first_launch'] <= data['cutoff'],
                'Install is outside the registered enrollment window/cutoff')
        require(row['platform'] in {'ios', 'android', 'test'}, 'Invalid platform')
        require(protocol['synthetic'] or row['platform'] != 'test', 'Test data in a real study')
        require(token(row['device_group']) and token(row['acquisition']), 'Invalid stratum')
        require(row['baseline_config'] == baseline['config'], 'Mixed baseline cohort; analyze separately')
        require(row['exclusion'] is None or row['exclusion'] in EXCLUSIONS, 'Unregistered exclusion')
        intervals = row['observable_intervals']
        require(isinstance(intervals, list) and len(intervals) <= 10000, 'Invalid coverage intervals')
        for interval in intervals:
            require(isinstance(interval, list) and len(interval) == 2 and all(integer(t) for t in interval)
                    and row['first_launch'] <= interval[0] < interval[1] <= data['cutoff'],
                    'Coverage must be a positive interval within observed follow-up')
        installs[row['id']] = row
    seen_sessions = set()
    sessions = defaultdict(list)
    for row in data['sessions']:
        keys(row, ['install_id', 'session_id', 'start', 'end', 'crashed', 'valid', 'return_eligible', 'config'])
        require(isinstance(row['install_id'], str) and row['install_id'] in installs,
                'Session is absent from the fixed registry')
        pair = (row['install_id'], row['session_id'])
        require(token(row['session_id']) and pair not in seen_sessions, 'Duplicate or invalid session')
        seen_sessions.add(pair)
        install = installs[row['install_id']]
        require(integer(row['start']) and install['first_launch'] <= row['start'] <= data['cutoff'],
                'Session time is outside observed follow-up')
        require(row['end'] is None or (integer(row['end']) and row['start'] <= row['end'] <= data['cutoff']),
                'Invalid session end')
        require(type(row['valid']) is bool and type(row['crashed']) is bool
                and type(row['return_eligible']) is bool and token(row['config']),
                'Explicit record validity, return eligibility, crash observation and config are required')
        require(row['valid'] or not row['return_eligible'],
                'An invalid record cannot establish a return')
        if row['valid']:
            sessions[row['install_id']].append(row)
    return installs, sessions


def retention(rows, sessions, cutoff, day):
    mature = [i for i in rows if i['first_launch'] + (day+1)*DAY <= cutoff]
    returned = complete = unknown = changed = 0
    for install in mature:
        start = install['first_launch'] + day*DAY
        end = start + DAY
        observations = sessions[install['id']]
        found = any(s['return_eligible'] and start <= s['start'] < end for s in observations)
        coverage = covers(install['observable_intervals'], start, end)
        returned += found
        complete += coverage
        unknown += not found and not coverage
        changed += any(s['config'] != install['baseline_config'] and s['start'] < end for s in observations)
    n = len(mature)
    return {'day':day, 'eligible_mature_installs':n,
            'not_yet_mature_installs':len(rows)-n, 'observed_returns':returned,
            'fully_observable_windows':complete, 'unresolved_return_status':unknown,
            'observed_config_change_before_window_end':changed,
            'observed_return_fraction':returned/n if n else None,
            'observed_fraction_wilson_95':wilson(returned,n),
            'missing_data_identification_bounds':[returned/n,(returned+unknown)/n] if n else None}


def stability(rows, sessions):
    records = [s for row in rows for s in sessions[row['id']]]
    n = len(records)
    crashed = sum(s['crashed'] for s in records)
    ended = sum(s['end'] is not None and not s['crashed'] for s in records)
    return {'valid_observed_sessions':n, 'reported_crash_sessions':crashed,
            'completed_without_reported_crash':ended, 'unknown_outcomes':n-ended-crashed,
            'completed_fraction_lower_bound':ended/n if n else None,
            'observed_completed_fraction_wilson_95':wilson(ended,n),
            'native_crash_reporting_and_critical_flow_gate_verified':False}


def summarize(protocol, data):
    installs, sessions = validate(protocol, data)
    eligible = [row for row in installs.values() if row['exclusion'] is None]
    def group(rows):
        return {'eligible_installs':len(rows),
                'retention':[retention(rows,sessions,data['cutoff'],day) for day in (1,7,30)],
                'sessions':stability(rows,sessions)}
    strata = {}
    for field in ['platform','platform_device','acquisition']:
        buckets = defaultdict(list)
        for row in eligible:
            name = row['platform'] + '/' + row['device_group'] if field == 'platform_device' else row[field]
            buckets[name].append(row)
        strata[field] = {name:group(rows) for name,rows in sorted(buckets.items())}
    return {'schema_version':2, 'status':'synthetic_fixture' if data['synthetic'] else 'descriptive_observations_only',
            'study_id':protocol['study_id'], 'cutoff':data['cutoff'], 'baseline':protocol['baseline'],
            'primary_outcome':protocol['primary_outcome'],
            'registry_population_claim':protocol['registry_population'],
            'registry_completeness_independently_verified':False,
            'enrollment_closed':data['cutoff'] >= protocol['enrollment_end'],
            'whole_registered_window_d30_mature':data['cutoff'] >= protocol['enrollment_end'] + 31*DAY,
            'registered_installs':len(installs),
            'exclusions':dict(sorted(Counter(i['exclusion'] for i in installs.values() if i['exclusion']).items())),
            'invalid_session_records':sum(not s['valid'] for s in data['sessions']),
            'overall':group(eligible), 'exploratory_strata':strata,
            'planning_targets':{'eligible_starts':500,'observed_sessions':10000},
            'review_hypotheses':{'D1':0.35,'D7':0.15,'D30':0.07},
            'release_ready':False,
            'limits':[
                'Registry provenance and lawful collection require independent verification; this tool cannot recover unrecorded installs.',
                'Dn uses the full half-open age window [n*24h,(n+1)*24h). Each window includes only mature registered installs.',
                'Missing observations stay in the denominator. Identification bounds allow every unresolved return to be absent or present.',
                'Wilson intervals describe observed fractions under binomial sampling; they do not correct consent, missingness or recruitment bias.',
                'Config changes remain in the primary denominator and are disclosed; material changes require separately preregistered cohorts.',
                'Strata are exploratory, unadjusted comparisons, not powered causal experiments.',
                'Unknown session outcomes are not crash-free. Provider telemetry and critical-flow/device review remain required.',
                'No synthetic run, statistical threshold or calendar timestamp establishes human study, release or support acceptance.'
            ]}


def load_json(path):
    with Path(path).open('rb') as stream:
        blob = stream.read(LIMIT + 1)
    require(len(blob) <= LIMIT, 'Input exceeds the 32 MiB limit')
    def unique(pairs):
        result = {}
        for key,value in pairs:
            require(key not in result, 'Duplicate JSON key')
            result[key] = value
        return result
    return json.loads(blob, object_pairs_hook=unique, parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Non-finite JSON value'))), hashlib.sha256(blob).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', required=True)
    parser.add_argument('--data', required=True)
    args = parser.parse_args()
    try:
        protocol, protocol_hash = load_json(args.protocol)
        data, data_hash = load_json(args.data)
        report = summarize(protocol,data)
        report['inputs_sha256'] = {'protocol':protocol_hash, 'data':data_hash,
                                   'analyzer':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
        print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
        return 0
    except (OSError,ValueError,TypeError,KeyError,RecursionError) as error:
        # No input records or raw exception text are echoed; those may be private.
        print(json.dumps({'status':'invalid_input','error_type':type(error).__name__,
                          'message':'Study inputs failed validation; inspect the local schema and records.'}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

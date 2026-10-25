"""Synthetic verifier review only; never native permission/delivery evidence."""
import copy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tool'))
import test_native_reminders as fixtures
import verify_native_reminders as verifier

results = []
def rejects(name, change, scenario='delivery', log_change=lambda log: log):
    context, value = fixtures.specimen(scenario)
    change(value)
    try:
        errors = verifier.payload_errors(value, context, log_change(fixtures.log_for(value)))
    except Exception as error:
        raise AssertionError(f'{name}: malformed payload escaped as {type(error).__name__}') from error
    assert errors, name
    results.append({'case': name, 'rejected': True, 'errors': errors})

rejects('native PID bound in result and action', lambda v: v.update(process_id=71))
rejects('delivery from other reminder ID', lambda v: v.update(delivered_records=[{'id': 77102, 'body': v['plan']['body']}]))
rejects('correct notification with wrong body', lambda v: v.update(delivered_records=[{'id': 77101, 'body': 'unrelated'}]))
rejects('wall clock forward but insufficient elapsed real time', lambda v: v.update(returned_utc_ms=9999999, returned_elapsed_ms=1000))
rejects('resumed before actual home departure is not delivery', lambda v: v.update(lifecycle_events=[{'state':'resumed','utc_ms':1360000},{'state':'paused','utc_ms':1360001}]))
rejects('unpersisted background snapshot', lambda v: v['plan'].update(saved_payload_sha256=None))
rejects('cancelled pending but delivered still present', lambda v: v.update(return_active_ids=[77101]))
rejects('quiet plan still queued on return', lambda v: v.update(return_pending_ids=[77101]), 'quiet-cancel')
rejects('revoked OS permission with enabled durable preference', lambda v: v.update(revoked_opt_in_stays_disabled=False), 'revoked')
rejects('OS action from a different actual process', lambda v: v['actions'][1].update(process_id=99))
rejects('late native failure overrides both success markers', lambda v: None, log_change=lambda log: log+'flutter: Unhandled Exception: teardown failure\n')
rejects('OS prompt lifecycle during default initialization', lambda v: v.update(initialization_lifecycle_events=[{'state':'inactive','utc_ms':100}]), 'default')

# Frozen production identity and installed artifact mismatches are already
# reproduced by the author's suite; source review also checks the real main()
# orchestration, not just synthetic validator shapes.
print(json.dumps({'cases':results,'count':len(results),'native_execution':False},indent=2))

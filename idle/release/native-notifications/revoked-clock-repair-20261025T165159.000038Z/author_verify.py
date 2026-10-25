"""Read-only arithmetic and preservation review; no device or Flutter calls."""
from pathlib import Path
import hashlib,json,sys,difflib
from decimal import Decimal
base=Path(__file__).resolve().parent
root=base.parents[2]
sys.path[:0]=[str(base/'staged/tool'),str(root/'tool')]
import reminder_restart as restart
import verify_native_reminders as runner
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
checks=[];pins={}
def check(value,label):
    if not value:raise AssertionError(label)
    checks.append(label)
def pin(rel):
    p=root/rel;pins[rel]=sha(p);return p
baseline=json.loads((base/'baseline.json').read_bytes())
for rel,want in baseline.items():check(sha(pin(rel))==want,'live baseline unchanged: '+rel)
qa=pin('release/qa/revoked-preparation-clock-finding-20261025T164732.753979Z/REVIEW.md')
old=pin('release/native-notifications/integration-android-20261025T164440025420Z/verification.json'); prior=json.loads(old.read_bytes())
check(sha(old)=='f8d460bebd26e7bb63c61ae609f6dc57606a1b3a22442572c1f9c180eb3a2413','rejected preparation report unchanged')
operator=pin('release/native-notifications/revoked-restart-operator-20261025T164440025420Z/operator.json')
pin('release/native-notifications/revoked-restart-operator-20261025T164440025420Z/checkpoint.json')
# Existing evidence remains untouched, including exact files referenced by old report.
for rel,want in prior['evidence_sha256'].items():
    p=old.parent/rel;check(sha(p)==want,'old preparation evidence preserved: '+rel);pins[str(p.relative_to(root))]=sha(p)
old_operator=json.loads(operator.read_bytes())
for rel,want in old_operator['files_sha256'].items():
    p=operator.parent/rel;check(sha(p)==want,'old operator evidence preserved: '+rel);pins[str(p.relative_to(root))]=sha(p)
ctx={**prior,'scenario':'revoked-recover','verification_id':'READ_ONLY_NEGATIVE_CONTROL'}
try:
    restart.validate_predecessor(old,ctx,prior['source_pins'],operator,runner.verify_native.native_log_errors)
except (ValueError,KeyError,TypeError) as e:
    rejection=type(e).__name__+': '+str(e)
else:raise AssertionError('Old uncalibrated packet was incorrectly accepted')
check('clock_model' in rejection,'old packet rejected for absent prospective calibration')
diag=pin('release/native-notifications/revocation-clock-diagnostic-20261025T164645.898891Z/diagnostic.json')
check(sha(diag)=='637eb1f3ffd56701ad3f56498656b0baf47d8bf8b2d3979917229909988bc934','posthoc diagnostic input unchanged')
values=json.loads(diag.read_bytes());arithmetic=[]
for i,row in enumerate(values['samples']):
    p=diag.parent/row['raw_file'];check(sha(p)==row['sha256'],'actual diagnostic raw sample pin '+str(i));pins[str(p.relative_to(root))]=sha(p)
    device=restart.device_nanoseconds(p.read_text());check(device==row['device_utc_ns'],'actual native integer precision '+str(i))
    bounds=[row['host_before_ns']-device,row['host_after_ns']-device]
    check(all(Decimal(n)/Decimal(1_000_000)==Decimal(str(v)) for n,v in zip(bounds,row['host_minus_device_bounds_ms'])),'actual raw request/response arithmetic '+str(i))
    arithmetic.append({'sample':i,'host_minus_device_ns':bounds})
check(all('started_stamp' not in r and 'clock_phase' not in r for r in values['samples']),'posthoc diagnostic is not a prospective same-run protocol packet')
# No invented host monotonic history, pre-event samples or permission state.
report={'purpose':'Staged clock-protocol author controls only; no native qualification',
        'checks':checks,'input_pins':pins,'old_packet_rejected':rejection,
        'actual_posthoc_arithmetic':arithmetic,
        'limits':['Diagnostic arithmetic does not retroactively calibrate old permission event.','No Flutter/device/runtime command executed.','Future native preparation/recovery and independent review still required.']}
(base/'preservation-and-diagnostic.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'checks':len(checks),'input_pins':len(pins),'old_packet_rejected':rejection}))
patch=[]
for name in ['reminder_restart.py','test_reminder_restart.py','test_reminder_clock.py']:
    before=base/'before'/name;after=base/'staged/tool'/name
    patch.extend(difflib.unified_diff(before.read_text().splitlines(keepends=True) if before.exists() else [],after.read_text().splitlines(keepends=True),fromfile='a/tool/'+name if before.exists() else '/dev/null',tofile='b/tool/'+name))
(base/'clock-protocol.patch').write_text(''.join(patch))

#!/usr/bin/env python3
"""Resume only unqualified Android cells after explicit reviewed tool promotion."""
import hashlib,json
from execute_cells import ROOT,EVIDENCE,cell
assert hashlib.sha256((ROOT/'tool/verify_current_runtime.py').read_bytes()).hexdigest()=='d1ea6d05085f05a0a3bb6c768531ef7659272e41993858c0551618f74ce5c847'
assert hashlib.sha256((ROOT/'game/mobile/integration_test/current_runtime_test.dart').read_bytes()).hexdigest()=='102be09eb8043ce9bb496156d9f37b1834c3084ddf58fef073e7c25cdc3c55d5'
# Lead approval of the separately pinned collector bridge is a prerequisite to
# invoking this script; no collector or candidate mutation happens here.
prefix='v3b00-android-probe-fixed'
for stage in ['beforeWrite','afterFlush','afterRename']:
 prior=cell('android','runtime-save-hold-'+stage,prefix+'-save-'+stage)
 cell('android','runtime-save-recover-'+stage,prefix+'-save-'+stage,prior)
prior=cell('android','runtime-transition-start',prefix+'-transition')
cell('android','runtime-transition-reopen',prefix+'-transition',prior)
cell('android','runtime-study-default',prefix+'-default',observe=True)
prior=cell('android','runtime-study-enroll',prefix+'-enroll',observe=True)
cell('android','runtime-study-restart',prefix+'-enroll',prior)
prior=cell('android','runtime-study-crash-hold',prefix+'-studycrash')
cell('android','runtime-study-crash-reopen',prefix+'-studycrash',prior)
cell('android','runtime-study-capacity',prefix+'-capacity')
record={'label':'android','scenarios':['runtime-study-storage-withdraw','runtime-study-withdraw-reopen'],'status':'deferred','reason':'Reviewed test-only withdrawal barrier promotion follows successful original-harness Android observers and terminal independent cases.'}
with (EVIDENCE/'deferred-cells.jsonl').open('a') as out:out.write(json.dumps(record)+'\n')
cell('android','runtime-cache-grace',prefix+'-cache')

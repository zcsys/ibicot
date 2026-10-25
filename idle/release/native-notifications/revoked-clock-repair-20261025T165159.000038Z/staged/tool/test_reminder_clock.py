"""Prospective clock/causal-evidence controls; synthetic data, no native commands."""
import copy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import reminder_restart as restart
from test_reminder_restart import NOW, clock_receipts, encode, receipt, shape, stamp, world


def shift_device(row, ns):
    value=restart.device_nanoseconds(row['stdout'])+ns
    row['stdout']=f'{value//1_000_000_000}.{value%1_000_000_000:09d}\n'


def shift_host_stamp(value, ns):
    value['utc_ns'] += ns


class ClockModelTests(unittest.TestCase):
    def setUp(self):
        self.context,_,self.marker,_=shape()
        self.rows=clock_receipts(self.context)
    def model(self,rows=None):return restart.clock_model(self.rows if rows is None else rows,self.context,42)
    def test_measured_offset_envelope_and_millisecond_exit_precision(self):
        model=self.model()
        self.assertEqual((model['host_minus_device_lower_ns'],model['host_minus_device_upper_ns']),(430_000_000,450_000_000))
        self.assertEqual(restart.validate_clock_event(model,self.context,self.marker,NOW+10000),((NOW+10000)*1_000_000+430_000_000,(NOW+10000)*1_000_000+451_000_000))
    def test_positive_and_negative_offsets_are_measured_without_fixed_slack(self):
        for offset in (-500,0,440,900):
            with self.subTest(offset=offset):
                model=self.model(clock_receipts(self.context,offset))
                self.assertEqual(model['host_minus_device_lower_ns'],(offset-10)*1_000_000)
                restart.validate_clock_event(model,self.context,self.marker,NOW+10000)
    def test_raw_date_precision_and_malformed_output(self):
        self.assertEqual(restart.device_nanoseconds('1792946805.479504220\n'),1792946805479504220)
        for raw in ('1792946805.479504','1792946805.479504220 junk','-1.000000000','NaN','1792946805.479504220\n\n',None):
            with self.subTest(raw=raw),self.assertRaises(ValueError):restart.device_nanoseconds(raw)
    def test_missing_or_posthoc_only_clock_measurements_rejected(self):
        for rows in ([],self.rows[3:],self.rows[:3]*2):
            with self.subTest(length=len(rows)),self.assertRaises(ValueError):self.model(rows)
    def test_cross_run_device_or_pid_clock_receipt_rejected(self):
        for key,value in [('run_id','other'),('verification_id','old'),('device','emulator-5554'),('process_id',99)]:
            rows=copy.deepcopy(self.rows);rows[0]['clock_context'][key]=value
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'identity mismatch'):self.model(rows)
    def test_wrong_command_failure_or_unstamped_probe_rejected(self):
        for change in (lambda r:r['argv'].__setitem__(-1,'+%s'),lambda r:r.update(exit_code=1),lambda r:r.pop('started_stamp'),lambda r:r.update(stderr='error')):
            rows=copy.deepcopy(self.rows);change(rows[0])
            with self.assertRaises(ValueError):self.model(rows)
    def test_legacy_time_cannot_substitute_for_monotonic_receipt(self):
        rows=copy.deepcopy(self.rows);rows[0]['started_utc_ms']+=1
        with self.assertRaisesRegex(ValueError,'Legacy receipt'):self.model(rows)
    def test_long_round_trip_and_broad_uncertainty_fail_closed(self):
        rows=copy.deepcopy(self.rows)
        rows[-1]['finished_stamp']=stamp(NOW+12400);rows[-1]['finished_utc_ms']=NOW+12400
        with self.assertRaisesRegex(ValueError,'round trip'):self.model(rows)
        # Six individually allowed 200ms probes, but their 200ms offset envelope
        # is insufficiently precise. No fabricated 500ms event tolerance.
        rows=[]
        for phase,start in [('before_exports',1000),('after_death',12000)]:
            for i in range(3):
                at=NOW+start+i*300
                r=receipt(['shell','date','-u','+%s.%N'],'',at,duration_ms=200)
                d=(at+100-440)*1_000_000;r['stdout']=f'{d//1_000_000_000}.{d%1_000_000_000:09d}\n'
                r.update(clock_phase=phase,clock_context=self.rows[0]['clock_context']);rows.append(r)
        with self.assertRaisesRegex(ValueError,'uncertainty too broad'):self.model(rows)
    def test_host_wall_jump_rejected_even_with_adjusted_legacy_fields(self):
        rows=copy.deepcopy(self.rows)
        for key in ('started_stamp','finished_stamp'):shift_host_stamp(rows[-1][key],10_000_000)
        rows[-1]['started_utc_ms']+=10;rows[-1]['finished_utc_ms']+=10
        with self.assertRaisesRegex(ValueError,'wall/monotonic clock jumped'):self.model(rows)
    def test_device_clock_jump_between_phases_rejected(self):
        rows=copy.deepcopy(self.rows)
        for row in rows[3:]:shift_device(row,100_000_000)
        with self.assertRaisesRegex(ValueError,'offset changed'):self.model(rows)
    def test_inconsistent_samples_inside_phase_rejected(self):
        rows=copy.deepcopy(self.rows);shift_device(rows[1],30_000_000)
        with self.assertRaisesRegex(ValueError,'within phase'):self.model(rows)
    def test_reversed_or_duplicate_measurements_rejected(self):
        rows=copy.deepcopy(self.rows);rows[0],rows[1]=rows[1],rows[0]
        with self.assertRaises(ValueError):self.model(rows)
        rows=copy.deepcopy(self.rows);rows[1]['stdout']=rows[0]['stdout']
        with self.assertRaisesRegex(ValueError,'did not increase'):self.model(rows)
    def test_bounded_host_stamp_and_mutated_model_rejected(self):
        rows=copy.deepcopy(self.rows);rows[0]['started_stamp']['monotonic_upper_ns']+=2_000_000
        with self.assertRaisesRegex(ValueError,'clock read too broad'):self.model(rows)
        model=self.model();model['host_minus_device_lower_ns']-=1
        with self.assertRaisesRegex(ValueError,'differs from raw'):restart.validate_clock_event(model,self.context,self.marker,NOW+10000)
    def test_stale_initial_bracket_kill_before_pre_or_after_post_rejected(self):
        model=self.model()
        old={**self.marker,'utc_ms':NOW-31000}
        with self.assertRaisesRegex(ValueError,'stale'):restart.validate_clock_event(model,self.context,old,NOW+10000)
        for kill in (NOW+100,NOW+15000):
            with self.subTest(kill=kill),self.assertRaisesRegex(ValueError,'prospectively bracket'):restart.validate_clock_event(model,self.context,self.marker,kill)
    def test_late_postdeath_and_overall_stale_brackets_rejected(self):
        rows=copy.deepcopy(self.rows)
        for row in rows[3:]:
            shift_device(row,40_000_000_000)
            for k in ('started_stamp','finished_stamp'):
                for field in row[k]:row[k][field]+=40_000_000_000
            row['started_utc_ms']+=40000;row['finished_utc_ms']+=40000
        model=self.model(rows)
        with self.assertRaisesRegex(ValueError,'Post-death clock bracket too late'):restart.validate_clock_event(model,self.context,self.marker,NOW+10000)
        for row in rows[3:]:
            shift_device(row,180_000_000_000)
            for k in ('started_stamp','finished_stamp'):
                for field in row[k]:row[k][field]+=180_000_000_000
            row['started_utc_ms']+=180000;row['finished_utc_ms']+=180000
        with self.assertRaisesRegex(ValueError,'stale for this bounded preparation'):self.model(rows)
    def test_host_records_actual_clock_command_with_same_run_context(self):
        with TemporaryDirectory() as tmp,patch.object(restart.subprocess,'run') as call:
            call.return_value.returncode=0;call.return_value.stdout=b'1792946805.479504220\n';call.return_value.stderr=b''
            host=restart.Host(Path(tmp),self.context,Path(tmp));host.sample_clock('before_exports',42)
            self.assertEqual(call.call_count,3)
            self.assertTrue(all(r['argv'][3:]==['shell','date','-u','+%s.%N'] and r['clock_context']['process_id']==42 for r in host.receipts))
            for row in host.receipts:restart.receipt_stamps(row)


class CausalOperatorTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.base=Path(self.temp.name)
        self.prior,_,_,_,self.path=world(self.base)
        self.packet=restart.read_json(self.path);self.pids=restart.read_json(self.path.parent/'pid-observations.json')
    def check(self,packet=None,prior=None,pids=None):
        return restart.validate_operator_timing(self.packet if packet is None else packet,self.prior if prior is None else prior,self.pids if pids is None else pids)
    def test_async_kill_after_input_returns_with_real_skew_and_causal_receipts(self):
        value=self.check()
        self.assertGreater(value['kill_host_interval_ns'][0],self.packet['host_timeline']['action_finished']['utc_ns'])
        self.assertIn('causal_PID_UI_evidence_also_required',value['timing_relation'])
    def test_missing_live_absent_or_wrong_pid_receipt_rejected(self):
        for rows in ([],self.pids[:1],[self.pids[1],self.pids[0]]):
            with self.assertRaises(ValueError):self.check(pids=rows)
        for key,value in [('stdout','99\n'),('exit_code',1)]:
            rows=copy.deepcopy(self.pids);rows[0][key]=value
            with self.assertRaisesRegex(ValueError,'live/absent'):self.check(pids=rows)
    def test_monotonic_timeline_required_and_host_jump_rejected(self):
        p=copy.deepcopy(self.packet);p.pop('host_timeline')
        with self.assertRaisesRegex(ValueError,'timeline'):self.check(packet=p)
        p=copy.deepcopy(self.packet)
        for k in p['host_timeline']:p['host_timeline'][k]['utc_ns']+=10_000_000;p[k+'_utc_ms']+=10
        with self.assertRaisesRegex(ValueError,'wall/monotonic clock jumped'):self.check(packet=p)
    def test_actual_export_ready_must_precede_on_and_tap(self):
        prior=copy.deepcopy(self.prior);prior['restart_preparation']['host_ready_stamp']=stamp(NOW+10300)
        with self.assertRaisesRegex(ValueError,'before confirmed prekill export'):self.check(prior=prior)
    def test_late_off_observation_or_stale_live_observation_rejected(self):
        p=copy.deepcopy(self.packet);p['after_utc_ms']=NOW+50000;p['host_timeline']['after']=stamp(NOW+50000)
        with self.assertRaisesRegex(ValueError,'OFF observation too late'):self.check(packet=p)
        p=copy.deepcopy(self.packet);p['before_utc_ms']=NOW+4500;p['host_timeline']['before']=stamp(NOW+4500)
        rows=copy.deepcopy(self.pids);rows[0]=receipt(['shell','pidof',restart.BUNDLE],'42\n',NOW+5000)
        with self.assertRaisesRegex(ValueError,'alive observation is stale'):self.check(packet=p,pids=rows)
    def test_kill_outside_tap_off_window_not_hidden_by_precision(self):
        prior=copy.deepcopy(self.prior);prior['restart_death']['kill_utc_ms']=NOW+9000
        with self.assertRaisesRegex(ValueError,'inconsistent with actual tap-to-OFF'):self.check(prior=prior)
    def test_export_after_last_alive_cannot_be_accepted_by_timestamp(self):
        rows=restart.read_json(self.base/'restart-host-receipts.json');target=next(i for i,r in enumerate(rows) if 'head' in r['argv'])
        row=rows.pop(target);last=next(i for i,r in enumerate(rows) if '/proc/42/cmdline' in r['argv'] and r['started_utc_ms']>NOW+2500)
        row.update(started_stamp=stamp(NOW+3200),finished_stamp=stamp(NOW+3201),started_utc_ms=NOW+3200,finished_utc_ms=NOW+3201);rows.insert(last+1,row)
        with self.assertRaisesRegex(ValueError,'causally bracketed'):restart.validate_host_receipts(rows,self.prior,self.prior['restart_preparation'],self.prior['restart_death'])
    def test_host_receipt_wall_jump_and_wrong_raw_model_fail(self):
        rows=restart.read_json(self.base/'restart-host-receipts.json');row=next(r for r in rows if 'head' in r['argv'])
        for k in ('started_stamp','finished_stamp'):row[k]['utc_ns']+=10_000_000
        row['started_utc_ms']+=10;row['finished_utc_ms']+=10
        with self.assertRaisesRegex(ValueError,'wall/monotonic clock jumped'):restart.validate_host_receipts(rows,self.prior,self.prior['restart_preparation'],self.prior['restart_death'])
        rows=restart.read_json(self.base/'restart-host-receipts.json');shift_device(rows[0],1)
        with self.assertRaisesRegex(ValueError,'Raw same-run clock receipts differ'):restart.validate_host_receipts(rows,self.prior,self.prior['restart_preparation'],self.prior['restart_death'])


if __name__=='__main__':unittest.main()

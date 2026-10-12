"""Isolated full-world retail treatment with versioned observations and provenance."""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile
import time
import numpy as np
from economy.core import model as M
from economy.core.state import validate_storage
from economy.server.runtime import KernelRuntime
from economy.server.persistence import save_checkpoint
from tools.buying_research.provenance import provenance, ROOT, sha
from tools.buying_research.recording import Recorder
from .engine import RetailEngine, ReplenishmentReferenceEngine, IndustrialReferenceEngine, IndustrialCompiledEngine
from .purchase_reporting import schema


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--ticks', type=int, default=360)
    p.add_argument('--seed', type=int, default=137)
    p.add_argument('--cfg', default='{}')
    p.add_argument('--policy', choices=('retail','t2-reference','industrial-reference','industrial-compiled'), default='retail')
    p.add_argument('--seller-history-window', type=int, default=0, help='Optional read-only phase history retention; zero disables it.')
    p.add_argument('--trace-sample', type=int, default=0, help='Maximum sampled buyers per tier/phase/tick; zero disables traces.')
    a = p.parse_args()
    engine_type = {'retail':RetailEngine, 't2-reference':ReplenishmentReferenceEngine, 'industrial-reference':IndustrialReferenceEngine, 'industrial-compiled':IndustrialCompiledEngine}[a.policy]
    if a.seller_history_window < 0 or (a.seller_history_window and a.policy not in ('industrial-reference','industrial-compiled')):
        p.error('seller history requires a nonnegative window and both industrial tiers')
    if a.trace_sample < 0 or (a.trace_sample and a.policy not in ('industrial-reference','industrial-compiled')):
        p.error('decision traces require a nonnegative sample and both industrial tiers')
    if a.ticks < 1:
        p.error('ticks must be positive')
    overrides = json.loads(a.cfg)
    overrides['seed'] = a.seed
    spec = dict(treatment=engine_type.policy, configOverrides=overrides,
                seed=a.seed, ticks=a.ticks, window=[1, a.ticks], scenario='none', startCheckpoint=None,
                sellerHistoryWindow=a.seller_history_window, traceSample=a.trace_sample)
    manifest = provenance(a.output, spec)
    # Capture the entire new implementation, including untracked source/tests.
    paths = set(manifest['sourceHashes'])
    paths.update(str(x.relative_to(ROOT)) for x in (ROOT / 'tools/buying_v2').glob('*.py'))
    paths.update(str(x.relative_to(ROOT)) for x in (ROOT / 'tests/py').glob('test_buying*.py'))
    paths.update(str(x.relative_to(ROOT)) for x in (ROOT / 'docs').glob('buying-behavior-*.md'))
    hashes = {name: sha(ROOT / name) for name in sorted(paths)}
    manifest['sourceHashes'] = hashes
    manifest['sourceIdentity'] = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()
    with tarfile.open(a.output / 'source.tar.gz', 'w:gz') as archive:
        for name in hashes:
            archive.add(ROOT / name, arcname=name)
    (a.output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    try:
        rt = KernelRuntime(overrides)
        engine = engine_type(rt, history_window=a.seller_history_window, trace_sample=a.trace_sample)
        w = rt.world
        (a.output / 'config.json').write_text(json.dumps(rt.cfg, indent=2) + '\n')
        (a.output / 'purchase-schema.json').write_text(json.dumps(schema(engine.industrial_coverage), indent=2) + '\n')
        (a.output / 'initial-snapshot.json').write_text(json.dumps(rt.publish()) + '\n')
        recorder = Recorder(a.output, w, rt.cfg)
        durations = []
        trace_durations = []
        observations = []
        industrial_observations = []
        started = time.perf_counter()
        with (a.output / 'ticks.jsonl').open('x') as stream:
            for tick in range(1, a.ticks + 1):
                old0, old1 = w.t0Inv.copy(), w.t1Fin.copy()
                before = time.perf_counter()
                engine.step(tick)
                durations.append(time.perf_counter() - before)
                trace_before = time.perf_counter()
                if a.trace_sample:
                    with (a.output / f'decision-traces-{tick:06}.json').open('x') as trace_stream:
                        json.dump([trace.export() for trace in engine.decision_traces.values()] +
                                  ([engine.retail_trace.export()] if engine.retail_trace is not None else []), trace_stream,
                                  allow_nan=False, separators=(',', ':'))
                        trace_stream.write('\n')
                trace_durations.append(time.perf_counter()-trace_before if a.trace_sample else 0.)
                rt.tick, rt.month = tick, tick // 30
                rt.lastTickT0Produced[:] = w.t0Inv - old0 + w.t0Sold
                rt.lastTickT1Made[:] = w.t1Fin - old1 + w.t1Sold
                recorder.record(w, tick, rt.state, old0, old1)
                observations.append(engine.observations.copy())
                industrial_observations.append(engine.industrial_observations.copy())
                stream.write(json.dumps(dict(tick=tick, stepMs=durations[-1] * 1000, traceWriteMs=trace_durations[-1] * 1000,
                                             **recorder.invariants())) + '\n')
                if tick % 30 == 0 or tick == a.ticks:
                    stream.flush()
                    print(json.dumps(dict(tick=tick, elapsed=time.perf_counter() - started, **recorder.invariants())), flush=True)
                if tick % 360 == 0 or tick == a.ticks:
                    validate_storage(w, rt.cfg)
                    np.savez_compressed(a.output / f'purchase-{tick-len(observations)+1:06}-{tick:06}.npz',
                                        ticks=np.arange(tick-len(observations)+1, tick+1), observations=np.array(observations),
                                        industrialObservations=np.array(industrial_observations))
                    if engine.seller_history is not None:
                        engine.seller_history.save(a.output / f'seller-history-{tick:06}.npz')
                    observations.clear()
                    industrial_observations.clear()
        recorder.flush(w, a.ticks)
        save_checkpoint(str(a.output / f'checkpoint-{a.ticks:06}'), rt.cfg, a.ticks, w, rt.state,
                        {**rt.checkpoint_metadata(), 'purchasePolicy': engine.policy})
        (a.output / 'final-snapshot.json').write_text(json.dumps(rt.publish()) + '\n')
        inv = recorder.invariants()
        passed = all(inv[k] <= 1 for k in ('maxCompanyToleranceRatio', 'maxMoneyToleranceRatio', 'maxGoodsToleranceRatio')) and inv['minStock'] >= 0 and inv['minCash'] >= 0
        manifest.update(status='complete', invariantGate=bool(passed), invariants=inv,
                        runtimeSeconds=time.perf_counter()-started,
                        traceWriteSeconds=sum(trace_durations),
                        finalTraceArrayBytes=sum(a.nbytes for t in engine.decision_traces.values() for a in t.arrays) +
                            (sum(a.nbytes for a in engine.retail_trace.arrays) if engine.retail_trace is not None else 0),
                        warmMedianMs=float(np.median(durations[1:]))*1000 if len(durations)>1 else None,
                        caveat='Isolated '+a.policy+' treatment. Unisolated screening timing; no fairness or adoption claim. Industrial coverage is declared in purchase-schema.json; candidate stock checks are not incoming orders.')
    except BaseException as exc:
        manifest.update(status='failed', error=repr(exc))
        raise
    finally:
        (a.output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()

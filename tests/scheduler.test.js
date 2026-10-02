'use strict';

const assert = require('node:assert/strict');
const { createWorker } = require('./worker_harness');

let now = 0, nextId = 0, perf = 0;
const pending = new Map();
const worker = createWorker({ t2FirmCount: 1000, endUserCount: 20000 }, {
  performance: { now: () => ++perf * 10 },
  setTimeout(fn, delay) {
    const id = ++nextId;
    pending.set(id, { fn, at: now + delay });
    return id;
  },
  clearTimeout(id) { pending.delete(id); },
});
function advance(ms) {
  const end = now + ms;
  while (true) {
    const next = [...pending.entries()].sort((a, b) => a[1].at - b[1].at)[0];
    if (!next || next[1].at > end) break;
    now = next[1].at;
    pending.delete(next[0]);
    next[1].fn();
  }
  now = end;
}
function expectSingleTimer(delay) {
  assert.equal(pending.size, 1, 'Only one simulation timer may be active');
  assert.equal([...pending.values()][0].at - now, delay);
}

worker.send({ type: 'run', mode: 'fixed' });
expectSingleTimer(500);
worker.send({ type: 'run', mode: 'max' });
expectSingleTimer(0);
worker.send({ type: 'run', mode: 'fixed' });
expectSingleTimer(500);
const resumedTick = worker.inspect().tick;
for (let i = 0; i < 5; i++) worker.send({ type: 'run', mode: 'fixed' });
assert.equal(worker.inspect().tick, resumedTick, 'Repeated Run clicks must not advance extra ticks');
expectSingleTimer(500);
advance(499);
assert.equal(worker.inspect().tick, resumedTick, 'Run must wait for its fixed interval');
advance(1);
assert.equal(worker.inspect().tick, resumedTick + 1);
advance(1000);
assert.equal(worker.inspect().tick, resumedTick + 3, 'Run must maintain two ticks per second');
expectSingleTimer(500);

worker.send({ type: 'run', mode: 'max' });
const maxTick = worker.inspect().tick;
for (let i = 0; i < 5; i++) worker.send({ type: 'run', mode: 'max' });
assert.equal(worker.inspect().tick, maxTick, 'Repeated Run Max clicks must not start extra batches');
expectSingleTimer(0);
worker.send({ type: 'pause' });
assert.equal(pending.size, 0);
advance(2000);
assert.equal(worker.inspect().tick, maxTick, 'Pause must stop every simulation timer');
worker.send({ type: 'run', mode: 'fixed' });
expectSingleTimer(500);
worker.send({ type: 'reset', cfg: { t2FirmCount: 1000, endUserCount: 20000 } });
assert.equal(pending.size, 0);
advance(1000);
assert.equal(worker.inspect().tick, 0, 'Reset must leave the simulation stopped');
console.log('scheduler mode switching: ok');

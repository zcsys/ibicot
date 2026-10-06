'use strict';
const assert = require('node:assert/strict');
const {createWorker} = require('./worker_harness');
const base = {t2FirmCount:100,endUserCount:1000,consumerActivation:0,sigma:0};
const legacy = createWorker(base);
const sparse = createWorker({...base,researchPriceMinimumOpportunities:10});
const L = legacy.inspect().W, S = sparse.inspect().W;
const initial = S.t2Price.slice(0,S.t2LineCount);
for(let tick=0;tick<120;tick++) {legacy.step();sparse.step();}
assert.ok(L.t2Price.some((quote,line)=>line<L.t2LineCount && quote<initial[line]-.01), 'Calendar-only learner lowers quotes without order traffic');
for(let line=0;line<S.t2LineCount;line++) {
  assert.equal(S.t2Price[line],initial[line], 'Candidate does not infer price rejection from an absent market');
  assert.equal(S.t2LearnOpportunity[line],0);
}
assert.equal(sparse.inspect().cfg.researchPriceMinimumOpportunities,10);
assert.equal(legacy.inspect().cfg.researchPriceMinimumOpportunities,0, 'Candidate is off by default');
S.t2LearnTicks[0]=70000;
assert.equal(S.t2LearnTicks[0],70000,'Sparse observation counters do not wrap at 65,536 ticks');
S.t2LearnTicks[0]=3600;
for(let tick=0;tick<30;tick++)sparse.step();
assert.ok(S.t2Price[0]<initial[0],'A stale quote eventually explores even when the entire market has no orders');
const active = createWorker({t2FirmCount:100,endUserCount:10000,researchPriceMinimumOpportunities:10,sigma:0});
const W = active.inspect().W;
for(let tick=0;tick<90;tick++)active.step();
assert.ok(W.t2Price.some((quote,line)=>line<W.t2LineCount&&Math.abs(quote-initial[line])>.01), 'Informative traffic still enables price exploration');
assert.ok(W.t2LearnTicks.slice(0,W.t2LineCount).some(age=>age<90), 'Observation batches reset after a decision');
assert.ok(W.t2Opportunities.some(n=>n>0));
console.log('Research price observation: no-traffic patience, informative-trade learning, long counters, default unchanged: ok');

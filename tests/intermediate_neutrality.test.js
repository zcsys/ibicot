'use strict';
const assert = require('node:assert/strict');
const {createWorker} = require('./worker_harness');
const w=createWorker({t2FirmCount:1,endUserCount:1}), {W,cfg}=w.inspect();
for(let i=0;i<W.t1Fin.length;i++) W.t1Fin[i]=W.t1Operates[i]?10:0;
const counts=Array.from({length:10},()=>new Map());
for(let tick=0;tick<100;tick++) {
 const offers=w.kernel.marketOffers(W,1,tick);
 for(let market=0;market<10;market++) {
  assert.equal(offers[market].length,100);
  const chosen=w.kernel.chooseSupplier(offers[market],W.t1Fin,W.t1Price,-1,W.t1Rel,cfg);
  counts[market].set(chosen,(counts[market].get(chosen)||0)+1);
 }
}
for(const selections of counts) {
 assert.equal(selections.size,100,'Every equal-price firm must lead once per complete rotation');
 assert.ok([...selections.values()].every(count=>count===1));
}
const offers=w.kernel.marketOffers(W,1,17)[0], preferred=offers[5];
W.t1Price[preferred]-=.01;
const ranked=w.kernel.marketOffers(W,1,17)[0];
assert.equal(ranked[0],preferred,'Market rotation must preserve cheaper offer priority');
W.t1Fin[preferred]=0;
assert.notEqual(w.kernel.chooseSupplier(ranked,W.t1Fin,W.t1Price,-1,W.t1Rel,cfg),preferred);
W.t1Fin[preferred]=10; W.t1Price[preferred]+= .03;
assert.equal(w.kernel.chooseSupplier(w.kernel.marketOffers(W,1,17)[0],W.t1Fin,W.t1Price,preferred,W.t1Rel,cfg),preferred,
 'Earned preference may retain a slightly more expensive stocked supplier');
console.log('All ten real Tier 1 cohorts: equal-price rotation, cheaper quotes, stockouts and earned preference: ok');

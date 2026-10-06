'use strict';
const assert=require('node:assert/strict');
const {createWorker}=require('./worker_harness');
// Complete firm topology; a tiny external-buyer fixture is enough to inspect
// initial direction allocation. No profit or calibration outcome is inferred.
const w=createWorker({endUserCount:1}),{W,cfg}=w.inspect();
assert.equal(cfg.t2FirmCount,61950);
for(let product=0;product<10;product++) {
 let up=0;
 for(let offset=0;offset<100;offset++) up+=W.t1LearnDirection[(product*100+offset)*10+product]>0;
 assert.equal(up,50,'Every Tier 1 product must start with half its firms exploring each direction');
}
const rawGroups=new Map();
for(let firm=0;firm<20;firm++) {
 let width=0;
 for(let material=0;material<4;material++) if(Number.isFinite(W.t0Price[firm*4+material])) width++;
 const group=rawGroups.get(width)||{count:0,up:0};
 group.count++;group.up+=W.t0LearnDirection[firm*4]>0;rawGroups.set(width,group);
 for(let material=1;material<4;material++) assert.equal(W.t0LearnDirection[firm*4+material],W.t0LearnDirection[firm*4]);
}
for(const group of rawGroups.values())assert.equal(group.up,group.count/2);
const exposure=Array.from({length:200},()=>({up:0,total:0}));
for(let line=0;line<W.t2LineCount;line++) {
 const firm=W.t2LineFirm[line],weight=1/W.t2FirmLineCount[firm],market=exposure[W.t2LineProduct[line]];
 market.total+=weight;market.up+=W.t2LearnDirection[line]>0?weight:0;
 assert.equal(W.t2LearnDirection[line],(firm+cfg.seed)%2?1:-1);
}
for(const market of exposure) assert.ok(Math.abs(market.up/market.total-.5)<.005,
 'Each Tier 2 market must have nearly equal initial price-experiment exposure');
assert.equal(cfg.initialDemandForecastScale,0);
assert.ok(W.t1DemandEMA.every(value=>value===0));
assert.ok(W.t2DemandEMA.every(value=>value===0));
w.step();
assert.ok(W.t2Fin.some(value=>value>0),'Fresh factories still build bootstrap stock without invented historical orders');
console.log('Initial quote experiments: balanced Tier 0 widths, 50/50 Tier 1 cohorts and <0.5% Tier 2 exposure imbalance: ok');

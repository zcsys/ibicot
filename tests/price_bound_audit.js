'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {performance}=require('node:perf_hooks');
const {createWorker}=require('./worker_harness');
const {createPriceAudit,assertPriceHealth}=require('./price_audit_helpers');
const ticks=Number(process.env.PRICE_AUDIT_TICKS||3600);
const windowTicks=Number(process.env.PRICE_AUDIT_WINDOW||360);
const seed=Number(process.env.PRICE_AUDIT_SEED||12345);
assert.ok(Number.isInteger(ticks)&&ticks>=windowTicks);
assert.ok(Number.isInteger(windowTicks)&&windowTicks>0);
let audit;
const worker=createWorker({seed},{onBeforeTier0Reprice:W=>audit.onBeforeTier0Reprice(W)});
const {W,cfg}=worker.inspect();
assert.equal(cfg.endUserCount,1000000);assert.equal(cfg.t2FirmCount,50000);
audit=createPriceAudit(worker.model,cfg,{windowStart:ticks-windowTicks+1,windowTicks});
const started=performance.now();
for(let tick=1;tick<=ticks;tick++){
  audit.begin(tick,W);worker.step();audit.end(W);
  if(tick%360===0)console.log(JSON.stringify({progress:tick,ticks,elapsedSeconds:(performance.now()-started)/1000}));
}
const report={seed,ticks,elapsedSeconds:(performance.now()-started)/1000,...audit.report()};
const output=path.resolve(process.env.PRICE_AUDIT_OUTPUT||`reports/price-bound-audit-current-${seed}-${ticks}.json`);
fs.mkdirSync(path.dirname(output),{recursive:true});fs.writeFileSync(output,JSON.stringify(report,null,2)+'\n');
if(process.env.PRICE_AUDIT_ENFORCE==='1')assertPriceHealth(report);
console.log(JSON.stringify({output,seed,ticks,byTier:report.byTier,inactiveMarkets:report.inactiveMarkets}));

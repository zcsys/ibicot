'use strict';
// One reproducible gate for model behavior, reporting and full-scale balance.
// --quick runs only contract/scenario checks; the default also runs two seeds
// for 3,600 ticks each, with per-market price audits in their final windows.
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { createHash } = require('node:crypto');
const root = path.resolve(__dirname, '..');
const quick = process.argv.includes('--quick');
const checks = [
  'model_contract', 'colony_catalogue', 'compound_consumers', 'comparisons', 'pricing_model', 'price_audit', 'tier_boundaries', 'inventory_limits',
  'calibration_contract', 'source_engine', 'tier2_contract', 'ui_actions',
  'scheduler', 'dashboard', 'tier2_analytics', 'market_shocks', 'market_competition', 'market_scarcity', 'player_strategy',
].map(name => ({ name, file: `tests/${name}.test.js` }));
if (!quick) for (const seed of [12345,31415]) checks.push({
  name: `long_run_${seed}`, file: 'tests/long_run_balance.test.js',
  env: { BALANCE_SEED: String(seed), BALANCE_TICKS: '3600' },
});
fs.mkdirSync(path.join(root,'reports','quality-logs'), { recursive: true });
const results = [];
const sourceFingerprint = Object.fromEntries(['engine/model.js','engine/reference_kernel.js','phase0_economy_engine_worker.js']
  .map(file => [file,createHash('sha256').update(fs.readFileSync(path.join(root,file))).digest('hex')]));
for (const check of checks) {
  const log = path.join(root,'reports','quality-logs',`${check.name}.log`);
  console.log(`Running ${check.name}…`);
  const fd = fs.openSync(log,'w'), started = Date.now();
  const run = spawnSync(process.execPath,[check.file],{
    cwd:root,env:{...process.env,...check.env},stdio:['ignore',fd,fd],
  });
  fs.closeSync(fd);
  results.push({ name:check.name,passed:run.status===0,seconds:(Date.now()-started)/1000,log });
  if(run.status!==0){
    console.error(fs.readFileSync(log,'utf8').slice(-6000));
    fs.writeFileSync(path.join(root,`reports/scarcity-aware-quality-${quick?'quick':'full'}.json`),JSON.stringify({passed:false,sourceFingerprint,results},null,2)+'\n');
    process.exit(run.status||1);
  }
  console.log(`PASS ${check.name}`);
}
fs.writeFileSync(path.join(root,`reports/scarcity-aware-quality-${quick?'quick':'full'}.json`),JSON.stringify({passed:true,sourceFingerprint,results},null,2)+'\n');
console.log(`PASS: ${results.length} quality checks (${quick?'quick':'full'} suite)`);

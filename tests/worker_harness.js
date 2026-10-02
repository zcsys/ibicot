'use strict';

const fs = require('node:fs');
const path = require('node:path');
const { performance } = require('node:perf_hooks');
const root = path.resolve(__dirname, '..');

// Execute the actual worker sources in one native JS realm. A VM proxy around
// Math/typed arrays distorts million-agent timings; no alternate engine is used.
function createWorker(cfg = {}, runtime = {}) {
  const self = { postMessage(message) { this.lastMessage = message; if (message.type === 'snapshot') this.snapshot = message.data; } };
  const schedules = [];
  let source = ['engine/model.js', 'engine/reference_kernel.js', 'phase0_economy_engine_worker.js']
    .map((file) => fs.readFileSync(path.join(root, file), 'utf8').replace(/^importScripts\(.*\);$/m, ''))
    .join('\n');
  if (runtime.onBeforeTier0Reprice) {
    const boundary = '    priceMarkets(W, cfg, profiles, products, tick);';
    if (source.split(boundary).length !== 2) throw new Error('Expected one wholesale repricing boundary');
    source = source.replace(boundary, '    onBeforeTier0Reprice(W);\n' + boundary);
  }
  const api = new Function('self', 'performance', 'setTimeout', 'clearTimeout', 'onBeforeTier0Reprice', source + '\nreturn { step, publish, reset, inspect: () => ({ W, cfg, tick, sourceState }), kernel: self.Phase0ReferenceKernel, model: self.Phase0Model };')
    (self, runtime.performance || performance,
      runtime.setTimeout || ((fn) => { schedules.push(fn); return schedules.length; }),
      runtime.clearTimeout || (() => {}), runtime.onBeforeTier0Reprice);
  const send = (data) => { self.onmessage({ data }); if (self.lastMessage?.type === 'error') throw new Error(self.lastMessage.message); };
  send({ type: 'init', cfg });
  return { ...api, self, send, schedules, snapshot: () => { api.publish(); return self.snapshot; } };
}

module.exports = { createWorker };

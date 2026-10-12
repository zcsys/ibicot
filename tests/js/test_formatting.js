// Execute the production formatters and compare their text with the former
// locale formatting API, including rounding boundaries and signed zero.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const source = fs.readFileSync('web/app.js', 'utf8');
const formatters = source.slice(source.indexOf('  function fmt5('), source.indexOf('  function drawLine('));
const ctx = vm.createContext({});
vm.runInContext(formatters + '\nglobalThis.formatters = {fmtMoney, fmtInt, compactAxis};', ctx);
const {fmtMoney, fmtInt, compactAxis} = ctx.formatters;
const values = [0, -0, Infinity, -Infinity, NaN, 0.005, -0.005, 1.005, 0.999999, 999.999, 1e20];
for (let i = -1000; i <= 1000; i++) values.push(i * 123.456789);
const oldMoney = (x, d) => Number.isFinite(x) ? '$' + x.toLocaleString(undefined, {minimumFractionDigits: d, maximumFractionDigits: d}) : '—';
for (const x of values) {
  for (const d of [0, 1, 2, 3, 5]) assert.equal(fmtMoney(x, d), oldMoney(x, d));
  assert.equal(fmtInt(x), Number.isFinite(x) ? Math.round(x).toLocaleString() : '—');
  for (const money of [false, true]) {
    const m = Math.abs(x);
    const [scale, suffix] = m >= 1e12 ? [1e12, 'T'] : m >= 1e9 ? [1e9, 'B'] : m >= 1e6 ? [1e6, 'M'] : m >= 1e3 ? [1e3, 'k'] : [1, ''];
    const expected = Number.isFinite(x) ? (money ? '$' : '') + (x/scale).toLocaleString(undefined, {maximumFractionDigits: 2}) + suffix : '—';
    assert.equal(compactAxis(x, money), expected);
  }
}
for (const x of [null, undefined, '1234.56', '', true]) {
  const n = Number(x);
  assert.equal(fmtInt(x), Number.isFinite(n) ? Math.round(n).toLocaleString() : '—');
}
if (process.argv.includes('--benchmark')) {
  const bench = fn => {
    const begin = performance.now();
    for (let i = 0; i < 50000; i++) fn(i * 123.456789, 2);
    return performance.now() - begin;
  };
  console.log(JSON.stringify({old_ms: bench(oldMoney), cached_ms: bench(fmtMoney)}));
}
console.log('formatting: exact output matches for locale', new Intl.NumberFormat().resolvedOptions().locale);

'use strict';
const assert=require('node:assert/strict');const {createWorker}=require('./worker_harness');
const M=createWorker({t2FirmCount:1,endUserCount:1}).model;
for(let sector=0;sector<10;sector++) {
 const products=M.T2_PRODUCTS.filter(p=>p.sectorIndex===sector),options=M.portfolioOptions(products);
 assert.equal(options.length,6195);
 assert.deepEqual([1,2,3,4].map(k=>options.filter(p=>p.length===k).length),[20,190,1140,4845]);
 const identities=options.map(p=>p.map(x=>x.code).sort().join('|'));
 assert.equal(new Set(identities).size,6195);
 assert.ok(options.every(p=>p.every(x=>x.sectorIndex===sector)));
 for(const p of products)assert.equal(options.filter(o=>o.includes(p)).length,1160);
}
console.log('6,195 distinct 1–4-product portfolios per sector; 1,160 occurrences per product: ok');

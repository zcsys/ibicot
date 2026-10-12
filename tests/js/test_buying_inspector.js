'use strict';
const assert=require('node:assert/strict');
const {samples,filter,quantities}=require('../../web/buying-inspector.js');
const industrial={tick:1,tier:2,phase:4,sampling:'systematic',population:100,requestedSample:2,decisions:[
 {firm:7,status:'captured',materials:[[9,0,0,8,1,2,8,3,2,3]],offers:[[0,1,10,2,10,2,10],[0,2,15,6,8,6,6]]},
 {firm:8,status:'callback-not-observed'}]};
const retail={tick:2,kind:'distributor-decision',decisions:[{buyer:7,status:'inactive'},
 {buyer:9,status:'captured',inputs:{goodsCost:0,feePaid:0},offers:[]}]};
const rows=samples({traces:[industrial,retail]});
assert.equal(rows.length,4);
assert.equal(rows[0].tier,'T2 C4');
assert.equal(rows[2].tier,'T3');
assert.equal(rows[0].doc,undefined,'exports must not duplicate every sibling decision');
assert.deepEqual(quantities(rows[0]),{purchased:8,goods:110,fees:3});
assert.equal(quantities(rows[1]),null);
assert.equal(quantities(rows[2]),null);
assert.deepEqual(quantities(rows[3]),{purchased:0,goods:0,fees:0});
assert.deepEqual(filter(rows,{tier:'T3',tick:'all',outcome:'all',buyer:'7'}),[rows[2]]);
assert.deepEqual(filter(rows,{tier:'all',tick:'1',outcome:'captured',buyer:''}),[rows[0]]);
assert.equal(filter(rows,{tier:'all',tick:'all',outcome:'all',buyer:'999'}).length,0);
console.log('Buying inspector projections pass');

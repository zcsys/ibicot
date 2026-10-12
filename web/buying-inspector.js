(function () {
  'use strict';
  function samples(data) {
    return data.traces.flatMap(doc => doc.decisions.map(row => ({tick:doc.tick,
      tier:doc.kind==='distributor-decision'?'T3':doc.tier===1?'T1':`T2 C${doc.phase}`,
      buyer:row.buyer??row.firm,status:row.status,row,sampling:{algorithm:doc.sampling,population:doc.population,requestedSample:doc.requestedSample}})));
  }
  function filter(rows,query) {
    return rows.filter(r=>(query.tier==='all'||r.tier===query.tier)&&(query.tick==='all'||r.tick===Number(query.tick))&&
      (query.outcome==='all'||r.status===query.outcome)&&(query.buyer===''||r.buyer===Number(query.buyer)));
  }
  function quantities(sample) {
    if(sample.status!=='captured')return null;
    const retail=sample.tier==='T3', row=sample.row;
    return {purchased:row.offers.reduce((sum,o)=>sum+o[retail?4:5],0),
      goods:retail?row.inputs.goodsCost:row.offers.reduce((sum,o)=>sum+o[2]*o[5],0),
      fees:retail?row.inputs.feePaid:row.materials.reduce((sum,m)=>sum+m[9],0)};
  }
  if(typeof module!=='undefined')module.exports={samples,filter,quantities};
  if(typeof document==='undefined')return;
  const $=id=>document.getElementById(id),num=new Intl.NumberFormat('en-US',{maximumFractionDigits:4});
  const fmt=v=>v==null?'—':num.format(v);
  function node(tag,text,cls){const n=document.createElement(tag);if(text!=null)n.textContent=String(text);if(cls)n.className=cls;return n;}
  function table(headers,rows){const wrap=node('div',null,'table-wrap'),t=node('table'),head=node('thead'),tr=node('tr');for(const h of headers)tr.append(node('th',h));head.append(tr);t.append(head);const body=node('tbody');for(const row of rows){const r=node('tr');for(const value of row)r.append(node('td',value));body.append(r);}t.append(body);wrap.append(t);return wrap;}
  try {
    const data=JSON.parse($('inspection-data').textContent);
    if(data.version!==1)throw Error('Unsupported inspection report version');
    const all=samples(data).sort((a,b)=>a.tick-b.tick||a.tier.localeCompare(b.tier)||a.buyer-b.buyer);
    let filtered=all,page=0,exportUrl=null;const size=50;
    $('run').textContent=`${data.run} · Seed ${data.seed} · Ticks ${data.window[0]}–${data.window[1]} · ${data.policy}`;
    $('verification').textContent=`Verification ${data.verification.status}: ${data.verification.scope}`;
    $('source').textContent=data.sourceIdentity;
    for(const tier of [...new Set(all.map(r=>r.tier))]){const option=node('option',tier);option.value=tier;$('tier').append(option);}
    for(const tick of [...new Set(all.map(r=>r.tick))]){const option=node('option',tick);option.value=tick;$('tick').append(option);}
    function detail(sample){
      const out=$('detail');out.replaceChildren();if(!sample){out.append(node('p','No matching samples. Change the filters.','subtle'));return;}
      out.append(node('h2',`${sample.tier} · Buyer ${sample.buyer} · Tick ${sample.tick}`));
      const labels={'inactive':'This Distributor did not activate. No demand, search or purchase is inferred.',
        'zero-potential':'This Distributor activated, but its rounded potential quantity was zero. No supplier search occurred.',
        'callback-not-observed':'Procurement was not observed for this sampled company and phase. This is not a measured zero-demand decision.'};
      if(sample.status!=='captured'){out.append(node('p',labels[sample.status]||sample.status,'notice'));return;}
      const q=quantities(sample),retail=sample.tier==='T3',r=sample.row,stats=node('dl');
      for(const [label,value] of [['Items purchased',fmt(q.purchased)],['Goods payment',`$${fmt(q.goods)}`],['Loyalty fees',`$${fmt(q.fees)}`],['Offers observed',r.offers.length]]){const box=node('div');box.append(node('dt',label),node('dd',value));stats.append(box);}out.append(stats);
      if(retail){const h=r.inputs;out.append(node('p',`Product ${h.market} · Potential ${fmt(h.potentialQuantity)} items · Incumbent ${h.incumbent<0?'unassigned':h.incumbent} → ${h.preferenceAfter<0?'unassigned':h.preferenceAfter} · Incumbent-quote quantity ${fmt(h.bid)} · Formula fee $${fmt(h.formulaFee)}`,'subtle'));}
      else {out.append(node('p',`Opening cash $${fmt(r.cash)} · Free storage ${fmt(r.freeSpace)} spaces · Purchase lot ${r.lot} items`,'subtle'));
        out.append(node('h3','Input orders'),table(['Material','Held items','Target deficit','Funded bid¹','Old preference','New preference','Fee paid'],r.materials.map(m=>[m[0],fmt(m[1]),fmt(m[3]),fmt(m[6]),m[5]<0?'Unassigned':m[5],m[8]<0?'Unassigned':m[8],`$${fmt(m[9])}`])));
        out.append(node('p','¹ Funded bid is the original incumbent’s own-quote quantity, not a sum across offers.','subtle small'));}
      out.append(node('h3','Discovered offers and selected requests'));
      if(!r.offers.length)out.append(node('p','No eligible offers were discovered.','notice'));
      else out.append(table(retail?['Supplier line','Quote / item','Opening stock','Quantity at quote','Purchased','Actual request']:['Material',sample.tier==='T1'?'Supplier company ID':'Supplier book ID','Quote / item','Opening stock','Funded at quote','Purchased','Actual request'],r.offers.map(o=>retail?[o[0],`$${fmt(o[1])}`,fmt(o[2]),fmt(o[3]),fmt(o[4]),fmt(o[5])]:[r.materials[o[0]][0],o[1],`$${fmt(o[2])}`,fmt(o[3]),fmt(o[4]),fmt(o[5]),fmt(o[6])])));
      out.append(node('p','Quote quantities are separate alternatives, not additive market demand. Actual requests include remaining quantities; purchased quantities are the selected deliveries.','subtle small'));
    }
    function render(){const start=page*size,rows=filtered.slice(start,start+size);$('choices').replaceChildren();$('status').textContent=`${filtered.length.toLocaleString()} sampled entries · ${filtered.filter(r=>r.status==='captured').length.toLocaleString()} captured decisions in this filter`;
      $('page').textContent=filtered.length?`${start+1}–${start+rows.length} of ${filtered.length}`:'0 results';$('previous').disabled=page===0;$('next').disabled=start+size>=filtered.length;
      for(const r of rows){const b=node('button',`${r.tier} · Buyer ${r.buyer}\nTick ${r.tick} · ${r.status}`,'choice');b.style.whiteSpace='pre-line';b.setAttribute('aria-pressed','false');b.onclick=()=>{for(const other of $('choices').children)other.setAttribute('aria-pressed','false');b.setAttribute('aria-pressed','true');detail(r);};$('choices').append(b);}if(rows.length)$('choices').firstChild.click();else detail(null);}
    function apply(){$('export-panel').hidden=true;$('export-data').value='';if(exportUrl){URL.revokeObjectURL(exportUrl);exportUrl=null;}filtered=filter(all,{tier:$('tier').value,tick:$('tick').value,outcome:$('outcome').value,buyer:$('buyer').value});page=0;render();}
    for(const id of ['tier','tick','outcome','buyer'])$(id).addEventListener(id==='buyer'?'input':'change',apply);
    $('previous').onclick=()=>{page--;render();};$('next').onclick=()=>{page++;render();};
    $('download').onclick=()=>{const text=JSON.stringify({version:1,run:data.run,policy:data.policy,seed:data.seed,sourceIdentity:data.sourceIdentity,sourceWindow:data.window,entries:filtered},null,2);if(exportUrl)URL.revokeObjectURL(exportUrl);exportUrl=URL.createObjectURL(new Blob([text],{type:'application/json'}));$('export-data').value=text;$('save-export').href=exportUrl;$('export-count').textContent=`${filtered.length} samples from the current filters. Full precision and recorded IDs are preserved.`;$('export-panel').hidden=false;};
    $('totals').append(table(['Input market','Buyer tier','Decisions','Items purchased','Positive purchase legs','Goods spend','Fees','Fee incidence'],data.aggregate.rows.map(r=>[r.product,r.buyerTier.toUpperCase(),fmt(r.decisions),fmt(r.purchasedQuantity),fmt(r.positiveLegs),r.goodsSpend==null?'—':`$${fmt(r.goodsSpend)}`,r.feeAmount==null?'—':`$${fmt(r.feeAmount)}`,r.feeIncidence==null?'—':`${fmt(100*r.feeIncidence)}%`])));
    render();
  } catch(error) {$('error').textContent=`Report could not be displayed: ${error.message}`;}
})();

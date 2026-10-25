/* Different-author actual Chrome checks. Synthetic credentials never enter output. */
const {chromium}=require('playwright');
const fs=require('node:fs');const path=require('node:path');
const base=process.argv[2],output=process.argv[3];let browser,stage='startup';const results=[];
const check=(value,label)=>{if(!value)throw new Error(label);};
async function api(method,endpoint,body,token){const r=await fetch(base+endpoint,{method,headers:{...(body?{'Content-Type':'application/json'}:{}),...(token?{Authorization:'Bearer '+token}:{})},body:body?JSON.stringify(body):undefined});return {status:r.status,data:await r.json()};}
(async()=>{
 browser=await chromium.launch({channel:'chrome',headless:true});const version=browser.version();
 async function scenario(name,body){stage=name;const context=await browser.newContext({viewport:{width:320,height:900}});const page=await context.newPage();let requests=[];let errors=0;
  page.on('pageerror',()=>errors++);page.on('request',r=>requests.push({method:r.method(),path:new URL(r.url()).pathname}));
  const account=(await api('POST','/v1/accounts',{consent_cloud:true})).data;
  await page.goto(base+'/account/delete');
  const review=async()=>{await page.locator('#account-id').fill(account.account_id);await page.locator('#recovery-code').fill(account.recovery_code);await page.getByRole('button',{name:'Continue to confirmation'}).click();check(await page.locator('#confirmation').isVisible(),'confirmation');};
  const confirm=async()=>{await page.locator('#understood').check();await page.locator('#delete-account').click();};
  await body({context,page,account,review,confirm,requests});
  check(errors===0,'page_error');await context.close();results.push({scenario:name,passed:true});
 }
 await scenario('confirmation expiry at two minutes sends no request',async({page,account,review,requests})=>{
  await page.clock.install();await review();await page.clock.fastForward(119999);check(await page.locator('#confirmation').isVisible(),'not_early');
  await page.clock.fastForward(1);check(await page.locator('#credentials').isVisible(),'expired');
  check((await page.locator('#status').textContent()).includes('confirmation expired'),'expiry_copy');
  check(!requests.some(r=>r.method!=='GET'),'expiry_no_request');check((await api('GET','/v1/cloud',null,account.session_token)).status===200,'account_retained');
 });
 await scenario('duplicate in-flight clicks send one auth and one delete',async({page,account,review,confirm,requests})=>{
  let release,entered;const gate=new Promise(r=>release=r),seen=new Promise(r=>entered=r);
  await page.route('**/v1/sessions',async route=>{entered();await gate;await route.continue();});
  await review();await confirm();await seen;
  check(await page.locator('#delete-account').isDisabled(),'delete_disabled');check(await page.locator('#cancel').isDisabled(),'cancel_disabled');
  await page.locator('#delete-account').evaluate(button=>{button.dispatchEvent(new MouseEvent('click',{bubbles:true}));button.dispatchEvent(new MouseEvent('click',{bubbles:true}));});
  check(requests.filter(r=>r.path==='/v1/sessions').length===1,'one_auth');release();
  await page.getByRole('status').filter({hasText:'Account deletion confirmed'}).waitFor();await page.locator('#credentials').waitFor({state:'visible'});
  check(requests.filter(r=>r.method==='DELETE').length===1,'one_delete');check((await api('GET','/v1/cloud',null,account.session_token)).status===401,'deleted');
 });
 await scenario('navigation before confirmation discards secrets without requests',async({page,account,review,requests})=>{
  await review();await page.goto('about:blank');check(!requests.some(r=>r.method!=='GET'),'no_auth');
  await page.goto(base+'/account/delete');check(await page.locator('#account-id').inputValue()===''&&await page.locator('#recovery-code').inputValue()==='','inputs_empty');
  check((await api('GET','/v1/cloud',null,account.session_token)).status===200,'account_retained');
 });
 await scenario('malformed auth identity cannot delete and temporary session is revoked',async({page,account,review,confirm,requests})=>{
  let temporary='';await page.route('**/v1/sessions',async route=>{const r=await route.fetch();const data=await r.json();temporary=data.session_token;data.account_id='00000000-0000-0000-0000-000000000000';await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(data)});});
  await review();await confirm();await page.getByRole('status').filter({hasText:'Authentication did not complete'}).waitFor();await page.locator('#credentials').waitFor({state:'visible'});
  check(!requests.some(r=>r.method==='DELETE'),'no_delete');check((await api('GET','/v1/cloud',null,temporary)).status===401,'temporary_revoked');check((await api('GET','/v1/cloud',null,account.session_token)).status===200,'original_retained');
 });
 for(const [name,body] of [['null','null'],['oversized',JSON.stringify({junk:'x'.repeat(9000)})],['invalid JSON','{']]){
  await scenario('malformed authentication '+name+' never deletes',async({page,account,review,confirm,requests})=>{
   await page.route('**/v1/sessions',route=>route.fulfill({status:200,contentType:'application/json',body}));await review();await confirm();
   await page.getByRole('status').filter({hasText:'Authentication did not complete'}).waitFor();await page.locator('#credentials').waitFor({state:'visible'});
   check(!requests.some(r=>r.method==='DELETE'),'no_delete');check((await api('GET','/v1/cloud',null,account.session_token)).status===200,'account_retained');
  });
 }
 await scenario('malformed deletion flags never display confirmed',async({page,account,review,confirm})=>{
  await page.route('**/v1/account',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({deleted:'true',guest_progress_unchanged:true,store_purchases_not_cancelled:true})}));
  await review();await confirm();await page.getByRole('status').filter({hasText:'Deletion was not confirmed'}).waitFor();await page.locator('#credentials').waitFor({state:'visible'});
  check((await api('GET','/v1/cloud',null,account.session_token)).status===200,'account_retained');
 });
 await scenario('navigation during uncommitted delete revokes temporary session only',async({context,page,account,review,confirm})=>{
  let temporary='',entered,release;const seen=new Promise(r=>entered=r),gate=new Promise(r=>release=r);
  page.on('response',async r=>{if(new URL(r.url()).pathname==='/v1/sessions'&&r.status()===200){try{temporary=(await r.json()).session_token;}catch(_){}}});
  await context.route('**/v1/account',async route=>{entered();await gate;await route.abort('aborted').catch(()=>{});});
  await review();await confirm();await seen;check(temporary.length===43,'temporary_observed');
  await page.goto('about:blank');release();let revoked=false;
  for(let i=0;i<50;i++){if((await api('GET','/v1/cloud',null,temporary)).status===401){revoked=true;break;}await new Promise(r=>setTimeout(r,100));}
  check(revoked,'navigation_revoked');check((await api('GET','/v1/cloud',null,account.session_token)).status===200,'original_retained');
 });
 await browser.close();browser=null;
 fs.writeFileSync(path.join(output,'review-browser-report.json'),JSON.stringify({synthetic:true,passed:true,browser:'isolated headless Chrome',browser_version:version,scenarios:results,limits:['No public endpoint, physical accessibility, real account or store qualification.','Expiry uses Playwright virtual browser timer; HTTP operations are actual isolated loopback.','Malformed responses and held navigation request are explicit browser-route fault injection.']},null,2)+'\n');
 process.stdout.write(JSON.stringify({passed:true,scenarios:results.length})+'\n');
})().catch(async()=>{if(browser)await browser.close().catch(()=>{});fs.writeFileSync(path.join(output,'review-browser-report.json'),JSON.stringify({synthetic:true,passed:false,failed_stage:stage,completed:results},null,2)+'\n');process.stderr.write('Independent browser check failed at: '+stage+'\n');process.exitCode=1;});

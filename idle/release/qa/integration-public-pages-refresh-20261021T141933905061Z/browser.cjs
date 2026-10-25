const {chromium}=require('/Users/csys/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path');
(async()=>{
 const base=process.argv[2],out=process.argv[3];const browser=await chromium.launch({channel:'chrome',headless:true});
 const rows=[],requests=[],failures=[];
 try{
  const context=await browser.newContext();const page=await context.newPage();
  page.on('request',r=>{requests.push(r.url());if(!r.url().startsWith(base+'/'))failures.push('external request '+r.url())});
  page.on('pageerror',e=>failures.push('pageerror '+e));
  for(const [width,height]of [[320,720],[1024,768]])for(const percent of [100,150,200])for(const name of ['index.html','privacy.html']){
   await page.setViewportSize({width,height});await page.goto(base+'/'+name);await page.evaluate(s=>document.documentElement.style.fontSize=s+'%',percent);
   await page.keyboard.press('Tab');const skip=await page.locator('.skip').evaluate(e=>e===document.activeElement);if(!skip)throw Error('keyboard skip not first');
   await page.keyboard.press('Enter');if(!page.url().endsWith('#main'))throw Error('skip does not navigate');
   const details=page.locator('details');for(let i=0;i<await details.count();i++){const d=details.nth(i);await d.locator('summary').click();if(!await d.evaluate(e=>e.open))throw Error('real details action failed');}
   const observation=await page.evaluate(()=>{
    const issues=[],texts=[];let rects=0;
    if(document.documentElement.scrollWidth>innerWidth)issues.push('horizontal page overflow');
    if(document.querySelectorAll('h1').length!==1)issues.push('h1');
    if(document.querySelectorAll('script,form,input,iframe').length)issues.push('active content');
    const tree=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
    while(tree.nextNode()){
     const n=tree.currentNode,p=n.parentElement;if(!p||p.closest('.skip'))continue;
     const st=getComputedStyle(p);if(st.display==='none'||st.visibility==='hidden'||!n.textContent.trim())continue;
     const range=document.createRange();let count=0;
     for(const m of n.textContent.matchAll(/\S+/g)){
      range.setStart(n,m.index);range.setEnd(n,m.index+m[0].length);
      for(const box of range.getClientRects()){
       rects++;count++;
       if(box.left<-.5||box.right>innerWidth+.5||box.height>innerHeight+.5)issues.push({text:m[0],left:box.left,right:box.right,height:box.height});
       window.scrollBy(0,box.top-innerHeight/2);
       const actual=range.getBoundingClientRect();
       if(actual.top<-.5||actual.bottom>innerHeight+.5)issues.push({readThrough:m[0],top:actual.top,bottom:actual.bottom});
      }
     }
     if(count)texts.push(n.textContent.trim());
    }
    return{issues,rects,text_nodes:texts.length,details_open:[...document.querySelectorAll('details')].every(e=>e.open),font:getComputedStyle(document.documentElement).fontSize,body_font:getComputedStyle(document.body).fontSize,links:[...document.querySelectorAll('a')].map(e=>e.getAttribute('href'))};
   });
   if(observation.issues.length)throw Error(JSON.stringify({width,height,percent,name,observation}));
   if(name==='privacy.html'&&width===320&&percent===200){await page.locator('#study h2').scrollIntoViewIfNeeded();await page.screenshot({path:path.join(out,'privacy-study-phone200.png')});}
   rows.push({width,height,percent,page:name,keyboard_skip:true,...observation});
  }
  if(failures.length)throw Error(JSON.stringify(failures));
  if((await context.cookies()).length)throw Error('cookies');
  fs.writeFileSync(path.join(out,'browser.json'),JSON.stringify({rows,passed:true,requests,external_requests:0,cookies:0,physical_or_screenreader_proof:false},null,2)+'\n');
  await context.close();
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});

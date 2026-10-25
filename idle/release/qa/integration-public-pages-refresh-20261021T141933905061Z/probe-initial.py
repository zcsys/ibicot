from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
import hashlib,json,http.server,threading,subprocess,functools
ROOT=Path.cwd();OUT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
class Page(HTMLParser):
 def __init__(self):super().__init__();self.ids=[];self.links=[];self.tags=[];self.refs=[];self.text=[]
 def handle_starttag(self,t,attrs):
  a=dict(attrs);self.tags.append(t)
  if 'id'in a:self.ids.append(a['id'])
  if t=='a':self.links.append(a.get('href',''))
  self.refs +=[a[x]for x in ['src','href']if x in a]
 def handle_data(self,s):
  if s.strip():self.text.append(s.strip())
pages={}
for n in ['index.html','privacy.html']:
 p=Page();p.feed((ROOT/'release/public-pages/dist'/n).read_text());pages[n]=p
 assert len(p.ids)==len(set(p.ids))and p.tags.count('h1')==1
 assert not set(p.tags)&{'script','input','form','iframe'}
 assert '#main'in p.links
 assert all(not urlsplit(x).scheme and not urlsplit(x).netloc for x in p.refs)
links=[]
for n,p in pages.items():
 for href in p.links:
  u=urlsplit(href);target=u.path or n;assert target in pages and not u.query
  assert not u.fragment or u.fragment in pages[target].ids
  links.append({'source':n,'href':href,'resolved':True})
for kind,n in [('support_page','index.html'),('privacy_page','privacy.html')]:
 desc=json.loads((ROOT/f'game/content/locales/en-US/support.{kind}.json').read_text());assert desc['visible_text_segments']==pages[n].text and desc['links']==pages[n].links
 assert desc['actual_page_sha256']==sha(ROOT/'release/public-pages/dist'/n)
 p=json.loads((ROOT/f'source/provenance/asset.support.{kind}.json').read_text())
 assert p['reviewer']is None and p['review_evidence']is None and p['production_acceptance']is False
 for rel,h in (p['source_media_sha256']|p['exported_sha256']).items():assert sha(ROOT/rel)==h,rel
 assert p['original_required_variants']==['text_scale_100','text_scale_150','text_scale_200','pseudolocalized']
pub=json.loads((ROOT/'release/public-pages/publication.json').read_text());assert pub['public_release_authorized']is False and pub['status']=='local_draft_not_published'
assert all(pub[k]is None for k in ['operator','support_contact','privacy_contact','support_url','privacy_url','web_deletion_request_url','approved_backup_retention','native_sdk_data_audit'])
handler=functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(OUT/'source/release/public-pages/dist'))
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
cmd=['/Users/csys/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node',str(OUT/'browser.cjs'),f'http://127.0.0.1:{server.server_port}',str(OUT)]
try:
 with(OUT/'browser.log').open('w')as log:result=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
finally:server.shutdown();server.server_close();thread.join()
assert result.returncode==0,(result.returncode,str(OUT/'browser.log'))
before=json.loads((OUT/'source-before.json').read_text());after={p:sha(ROOT/p)for p in before};assert before==after
(OUT/'verification.json').write_text(json.dumps({'source_before':before,'source_after':after,'source_unchanged':True,'links':links,'export_and_provenance_equal':True,'no_status_changes':True,'browser_command':cmd,'browser_exit_code':result.returncode,'server_closed':True,'publication_approved':False},indent=2)+'\n')
print(json.dumps({'source_files':len(before),'local_links':len(links),'browser_conditions':12,'pass':True}))

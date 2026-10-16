#!/usr/bin/env python3
"""Original authored vector geometry emits editable JSON, SVG and matching Dart."""
import hashlib,json,pathlib,html
ROOT=pathlib.Path(__file__).resolve().parents[2]
C={'navy':'#102a37','dark':'#173643','line':'#45616b','teal':'#79e0cc','light':'#c8ede3','amber':'#f4ca88','blue':'#86b7c8','glass':'#2c6471','deep':'#071923'}
NAMES=['Spark Skiff','Prism Nursery','Tide Dynamo','Aurora Loom','Dawn Observatory']
STAGES=[0,25,50,75,100]

def shape(kind,data,fill='none',stroke=None,width=1.6):
 d={'type':kind,**data,'fill':C.get(fill,fill)}
 if stroke:d.update(stroke=C.get(stroke,stroke),stroke_width=width)
 return d

def poly(points,fill,stroke=None,width=1.6):return shape('polygon',{'points':points},fill,stroke,width)
def line(x1,y1,x2,y2,color='teal',width=1.6):return shape('line',dict(x1=x1,y1=y1,x2=x2,y2=y2),stroke=color,width=width)
def circle(x,y,r,fill,stroke=None,width=1.6):return shape('circle',dict(cx=x,cy=y,r=r),fill,stroke,width)
def ellipse(x,y,rx,ry,fill,stroke=None,width=1.6):return shape('ellipse',dict(cx=x,cy=y,rx=rx,ry=ry),fill,stroke,width)
def rect(x,y,w,h,fill,stroke=None,r=0):return shape('rect',dict(x=x,y=y,width=w,height=h,radius=r),fill,stroke)
def star(x,y,r=3):return poly([[x,y-r],[x+r*.35,y-r*.35],[x+r,y],[x+r*.35,y+r*.35],[x,y+r],[x-r*.35,y+r*.35],[x-r,y],[x-r*.35,y-r*.35]],'amber')

def scene(tier,stage):
 s=[ellipse(50,89,39,4,'dark'),line(12,94,88,94,'line',1)]
 layers=['working silhouette']
 if tier==0:
  s += [poly([[15,69],[84,69],[72,83],[29,83]],'glass','teal'),line(25,73,77,73,'amber'),line(48,68,48,24,'light',2),poly([[51,28],[51,62],[76,62]],'teal'),poly([[44,39],[44,63],[26,63]],'blue'),circle(61,76,2,'amber')]
  if stage>=1:s += [poly([[8,73],[25,73],[21,80],[12,80]],'dark','teal'),line(21,73,31,69),poly([[78,71],[93,71],[87,79],[77,79]],'dark','teal')];layers+=['stabilizing outriggers']
  if stage>=2:s += [poly([[30,22],[48,12],[66,22]],'light'),line(48,24,48,12,'amber'),line(30,22,48,27),line(66,22,48,27),rect(32,51,7,9,'amber')];layers+=['upper prism canopy']
  if stage>=3:s += [line(19,60,19,71,'amber'),circle(19,57,3,'amber'),line(77,62,77,69,'amber'),circle(77,59,3,'amber'),line(28,68,70,68,'light',2)];layers+=['navigation lamps and deck rail']
  if stage>=4:s += [circle(48,15,9,'none','amber',1),star(48,6,3),line(35,16,24,29,'amber',1),line(61,16,72,29,'amber',1),star(24,29,2),star(72,29,2)];layers+=['solar crown and guiding stars']
 elif tier==1:
  s += [rect(24,69,52,12,'glass','teal',3),poly([[27,69],[27,40],[50,24],[73,40],[73,69]],'glass','teal'),line(50,24,50,69,'light'),line(27,40,73,40,'light'),line(37,34,37,69,'line'),line(63,34,63,69,'line'),ellipse(50,63,12,4,'dark'),line(50,62,50,49,'amber'),poly([[50,50],[42,45],[45,55]],'teal'),poly([[50,52],[58,44],[56,57]],'light')]
  if stage>=1:s += [rect(8,71,14,10,'dark','teal',2),rect(78,71,14,10,'dark','teal',2),line(15,71,15,60),circle(15,57,3,'amber'),line(85,71,85,60),circle(85,57,3,'amber')];layers+=['satellite growing beds']
  if stage>=2:s += [line(18,70,18,38,'teal'),line(82,70,82,38,'teal'),line(18,38,30,30,'teal'),line(82,38,70,30,'teal'),star(18,35,3),star(82,35,3)];layers+=['light collecting trellis']
  if stage>=3:s += [line(50,24,50,15,'amber'),poly([[50,18],[39,11],[43,24]],'teal'),poly([[50,18],[61,11],[57,24]],'light'),circle(50,14,3,'amber')];layers+=['high prism bloom']
  if stage>=4:s += [line(15,57,8,32,'amber',1),line(8,32,32,15,'amber',1),line(85,57,92,32,'amber',1),line(92,32,68,15,'amber',1),star(32,15,4),star(68,15,4),star(50,7,3)];layers+=['triple bloom constellation']
 elif tier==2:
  s += [rect(19,76,62,8,'glass','teal',2),rect(26,62,9,14,'dark','line'),rect(65,62,9,14,'dark','line'),circle(50,50,24,'dark','teal',2),circle(50,50,17,'glass','line'),circle(50,50,6,'amber','light')]
  for a,b,c,d in [(50,28,50,42),(50,58,50,72),(28,50,42,50),(58,50,72,50),(35,35,44,44),(56,56,65,65),(35,65,44,56),(56,44,65,35)]:s +=[line(a,b,c,d,'teal',3)]
  if stage>=1:s += [circle(50,50,29,'none','amber',1),circle(50,21,2,'amber'),circle(21,50,2,'amber'),circle(79,50,2,'amber')];layers+=['outer tide ring']
  if stage>=2:s += [rect(6,54,8,22,'glass','teal',2),rect(86,54,8,22,'glass','teal',2),circle(10,50,6,'dark','teal'),circle(90,50,6,'dark','teal'),line(10,44,10,56,'amber'),line(90,44,90,56,'amber')];layers+=['twin auxiliary turbines']
  if stage>=3:s += [line(15,51,15,19,'blue',2),line(85,51,85,19,'blue',2),rect(15,16,70,5,'glass','teal',2),circle(31,18.5,2,'amber'),circle(69,18.5,2,'amber')];layers+=['upper power bridge']
  if stage>=4:s += [star(50,7,5),line(29,15,35,7,'amber'),line(71,15,65,7,'amber'),circle(35,7,2,'teal'),circle(65,7,2,'teal'),line(24,86,76,86,'amber')];layers+=['three crest tide crown']
 elif tier==3:
  s += [rect(17,77,66,7,'glass','teal',2),poly([[23,77],[27,27],[35,27],[39,77]],'glass','teal'),poly([[61,77],[65,27],[73,27],[77,77]],'glass','teal'),line(31,29,69,29,'amber',2),line(35,40,65,56,'teal',2),line(35,48,65,64,'blue',2),line(35,56,65,72,'teal',2),circle(31,24,4,'amber'),circle(69,24,4,'amber')]
  if stage>=1:s += [line(35,39,65,71,'light',1),line(35,71,65,39,'amber',1),line(50,34,50,73,'teal',1)];layers+=['cross woven light threads']
  if stage>=2:s += [poly([[12,62],[24,54],[36,62],[48,54],[60,62],[72,54],[88,62],[88,68],[72,60],[60,68],[48,60],[36,68],[24,60],[12,68]],'blue')];layers+=['second woven horizon']
  if stage>=3:s += [rect(27,12,8,12,'glass','teal',2),rect(65,12,8,12,'glass','teal',2),poly([[24,12],[31,5],[38,12]],'amber'),poly([[62,12],[69,5],[76,12]],'amber'),line(35,15,65,15,'light')];layers+=['raised twin lantern towers']
  if stage>=4:s += [line(8,41,31,17,'amber',1),line(31,17,50,7,'amber',1),line(50,7,69,17,'amber',1),line(69,17,92,41,'amber',1),star(8,41,3),star(50,7,4),star(92,41,3)];layers+=['complete constellation arch']
 else:
  s += [rect(24,67,52,15,'glass','teal',3),rect(31,59,38,8,'blue','teal',2),poly([[28,57],[30,43],[38,31],[50,27],[62,31],[70,43],[72,57]],'glass','teal',2),line(50,28,50,57,'light'),line(31,44,69,44,'line'),rect(44,68,12,14,'dark','line',3),poly([[48,40],[69,22],[75,28],[55,46]],'blue','light'),circle(73,24,4,'amber')]
  if stage>=1:s += [rect(9,76,15,6,'glass','teal',2),line(15,75,15,62,'teal'),poly([[11,63],[26,52],[30,57],[15,68]],'blue','light')];layers+=['survey telescope annex']
  if stage>=2:s += [ellipse(50,46,36,13,'none','amber',1),circle(15,43,3,'amber'),circle(84,50,2,'teal')];layers+=['calibrated orbital ring']
  if stage>=3:s += [rect(76,65,15,16,'glass','teal',2),poly([[74,65],[77,56],[83,52],[89,56],[93,65]],'blue','teal'),line(83,53,83,65,'light'),rect(8,39,8,12,'glass','teal',2),circle(12,36,5,'amber')];layers+=['companion cupola and signal lantern']
  if stage>=4:s += [ellipse(50,36,39,27,'none','teal',1),star(50,8,4),star(16,21,3),star(88,31,3),line(16,21,50,8,'amber',1),line(50,8,88,31,'amber',1),circle(50,46,43,'none','line',.7)];layers+=['dawn orrery and star crown']
 return {'schema_version':1,'id':f'producer.{tier+1:02d}.stage.{stage}','family':NAMES[tier],'tier_index':tier,'stage_index':stage,'ownership_threshold':STAGES[stage],'view_box':[0,0,100,100],'style':'Original layered harbor instrument in navy/cyan/amber','layers':layers,'shapes':s,'motion':'Static: the same presentation is used with reduced motion; no information depends on animation.','locked_variant':'Same silhouette at 35% opacity plus a native lock badge; adjacent card states the unlock condition.','selected_variant':'Native 2px amber frame outside the artwork; no change to economic hitbox.'}

def svg(s):
 parts=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="256" height="256">']
 for d in s['shapes']:
  k=d['type'];a={key:value for key,value in d.items() if key not in ('type','stroke_width','radius')}
  if 'stroke_width'in d:a['stroke-width']=d['stroke_width']
  if 'radius'in d:a['rx']=d['radius']
  if 'points'in a:a['points']=' '.join(','.join(map(str,p)) for p in a['points'])
  parts.append('<'+k+' '+' '.join(f'{key}="{html.escape(str(value))}"' for key,value in a.items())+'/>')
 return '\n'.join(parts+['</svg>'])

def main():
 scenes=[scene(t,s) for t in range(5) for s in range(5)]
 dart='// Generated from source/art/producers/*.scene.json by tools/assets/export_producers.py.\n// Original editable geometry. Do not edit this generated copy.\nconst producerScenes = <Map<String, dynamic>>'+json.dumps(scenes,separators=(',',':'))+';\n'
 (ROOT/'game/mobile/lib/producer_art_data.dart').write_text(dart)
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 contract_path=ROOT/'implementation/art/production_contract.json';contract=json.loads(contract_path.read_text())
 manifest_path=ROOT/'implementation/content/launch_manifest.json';manifest=json.loads(manifest_path.read_text())
 for scene_data in scenes:
  id=scene_data['id'];asset='asset.'+id
  row=next(a for a in contract['assets'] if a['asset_id']==asset)
  source=ROOT/row['source_descriptor_path'];source.parent.mkdir(parents=True,exist_ok=True);source.write_text(json.dumps(scene_data,indent=2)+'\n')
  vector=ROOT/'game/assets/producers'/f'{id}.svg';vector.write_text(svg(scene_data))
  export=ROOT/row['export_descriptor_path'];export.write_text(json.dumps({'schema_version':1,'id':id,'status':'authored_pending_independent_review','source':row['source_descriptor_path'],'source_sha256':sha(source),'svg':str(vector.relative_to(ROOT)),'svg_sha256':sha(vector),'runtime':'game/mobile/lib/producer_art_data.dart','runtime_renderer':'game/mobile/lib/producer_art.dart','stage_threshold':scene_data['ownership_threshold'],'variants':row['required_variants'],'raster_texture_bytes':0,'native_device_qualification':None},indent=2)+'\n')
  sources=[row['source_descriptor_path'],'tools/assets/export_producers.py','game/mobile/lib/producer_art.dart'];exports=[str(vector.relative_to(ROOT)),row['export_descriptor_path'],'game/mobile/lib/producer_art_data.dart']
  provenance={'asset_id':asset,'author_or_tool':'Tideglass AI art engineer; original declarative vector geometry','creation_date':'2026-10-16','source_media_paths':sources,'source_media_sha256':{p:sha(ROOT/p) for p in sources},'source_kind':'original_authored_vector','license_or_authorship_basis':'Original mathematical paths and geometric construction authored for Tideglass; no external image or reference media incorporated. No legal copyright eligibility claim.','license_evidence_paths':[],'allowed_uses':['Prepared for Tideglass in-client rendering and previews'],'attribution_text':'Original visual assets: Tideglass AI development team.','reference_asset_permissions':'No third-party reference assets used','export_tool_and_version':'tools/assets/export_producers.py v1; Python standard library','exported_paths':exports,'exported_sha256':{p:sha(ROOT/p) for p in exports},'reviewer':None,'review_evidence':None}
  (ROOT/row['provenance_path']).write_text(json.dumps(provenance,indent=2)+'\n')
  row.update(status='in_production',source_exists=True,export_exists=True,verification_evidence=None)
  for a in manifest['assets']:
   if a['id']==asset:a.update(delivery_status='in_production',source_path=row['source_descriptor_path'],license_evidence=row['provenance_path'])
 for family in manifest['producer_families']:
  family['production_status']='in_production'
  for stage in family.get('presentations',family.get('stages',[])):
   if isinstance(stage,dict) and 'production_status'in stage:stage['production_status']='in_production'
 contract_path.write_text(json.dumps(contract,indent=2)+'\n');manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
 print(json.dumps({'producer_presentations':len(scenes),'thresholds':STAGES,'verified':0}))

if __name__=='__main__':main()

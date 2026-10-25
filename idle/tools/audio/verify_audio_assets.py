#!/usr/bin/env python3
"""Integrity gate for authored local audio; never native/listening acceptance."""
import hashlib,json,pathlib,zipfile
root=pathlib.Path(__file__).resolve().parents[2]
errors=[]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ids=['audio.ambient_score','audio.interaction','audio.milestone','audio.rechart','audio.soundtrack']
report=json.loads((root/'release/audio/render-measurements.json').read_text())
for id in ids:
 package=json.loads((root/f'game/assets/audio/{id}/package.json').read_text())
 assert package['id']==id
 provenance=json.loads((root/f'source/provenance/asset.{id}.json').read_text())
 for key in ['source_media_sha256','exported_sha256']:
  for rel,expected in provenance[key].items():
   path=root/rel
   if not path.is_file() or sha(path)!=expected:errors.append(f'Hash mismatch: {rel}')
 for member in package.get('members',[]):
  runtime=root/'game/mobile/assets'/member['flutter_asset']
  if sha(runtime)!=member['runtime_sha256']:errors.append(f'Client audio differs: {runtime.name}')
  stats=member['decoded_aac_measurements']
  if stats['clipped_samples'] or stats['four_times_oversampled_peak_dbtp_estimate']>=-1:errors.append(f'Peak ceiling failed: {member["id"]}')
  if member['loop'] and stats['samples']!=member['source_measurements']['samples']:errors.append(f'Loop duration mismatch: {member["id"]}')
 if id=='audio.soundtrack':
  path=root/package['download_path']
  if sha(path)!=package['download_sha256']:errors.append('Soundtrack archive hash mismatch')
  with zipfile.ZipFile(path) as z:
   if z.testzip():errors.append('Corrupt soundtrack ZIP')
   if len([n for n in z.namelist() if n.endswith('.wav')])!=3:errors.append('Soundtrack must reuse exactly three ambient masters')
if len(report['members'])!=11:errors.append('Expected three music tracks and eight cues')
result={'status':'pass' if not errors else 'fail','audio_packages':5,'rendered_members':11,'scope':'Local source/export/client/ZIP integrity and measured decoded PCM only','errors':errors,'not_established':['Native decode, gapless playback and route interruption','Human listening and mix approval','Paid entitlement and authenticated download fulfillment']}
(root/'release/audio/asset-integrity.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result));raise SystemExit(bool(errors))

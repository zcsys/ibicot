"""Independent graph traversal that deliberately removes authored solutions."""
import hashlib, json, pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]

def solve(data):
    nodes={n['key'] for n in data['nodes']}; links={n:set() for n in nodes}
    for a,b in data['edges']: links[a].add(b); links[b].add(a)
    def walk(path):
        if len(path)==len(nodes): return path if path[-1]==data['end'] else None
        for node in sorted(links[path[-1]]-set(path)):
            if node==data['end'] and len(path)<len(nodes)-1: continue
            found=walk(path+[node])
            if found: return found
    return walk([data['start']])

def main():
    rows=[]
    for n in range(1,13):
        p=ROOT/f'game/mobile/assets/calibrations/calibration.{n:02}.pattern.json'
        source=ROOT/f'game/content/calibrations/calibration.{n:02}.pattern.json'
        data=json.loads(p.read_text());data.pop('solution');route=solve(data)
        assert route and len(set(route))==len(data['nodes']) and route[0]==data['start'] and route[-1]==data['end']
        assert data['focus_cost']==1 and data['reward_profile_id']=='calibration.standard'
        assert data['time_limit_seconds'] is None and data['repeat_collectible_grant'] is False
        assert p.read_bytes()==source.read_bytes()
        assert solve(dict(data,edges=[])) is None
        rows.append({'id':data['id'],'nodes':len(data['nodes']),'edges':len(data['edges']),
                     'independent_route':route,'authored_solution_not_used':True,
                     'source_bundle_equal':True,'no_links_negative_rejected':True,
                     'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    print(json.dumps({'patterns':rows,'all_twelve_solvable':True,
                      'reward_profile_one_focus_untimed_no_duplicate':True},indent=2))
if __name__=='__main__':main()

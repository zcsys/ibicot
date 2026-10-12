"""Fixed-capacity typed branch state and supply storage for compiled search."""
import numpy as np
from .jit import njit
from .continuation_program import _array
from .continuation_resident import _replay


@njit
def _load(pool,row):
    m=pool[11][row]
    return (pool[0][row].copy(),pool[1][row].copy(),pool[2][row].copy(),pool[3][row].copy(),
        pool[4][row].copy(),pool[5][row].copy(),pool[6][row].copy(),m[0],pool[7][row].copy(),
        pool[8][row].copy(),pool[9][row].copy(),bool(m[1]),pool[10][row].copy(),m[2])


@njit
def _store(pool,row,state,supply):
    pool[0][row]=state[0];pool[1][row]=state[1];pool[2][row]=state[2];pool[3][row]=state[3]
    pool[4][row]=state[4];pool[5][row]=state[5];pool[6][row]=state[6]
    pool[7][row]=state[8];pool[8][row]=state[9];pool[9][row]=state[10];pool[10][row]=state[12]
    pool[11][row,0]=state[7];pool[11][row,1]=1 if state[11] else 0;pool[11][row,2]=state[13]
    pool[12][row]=supply


@njit
def _claim(live,generations):
    for row in range(len(live)):
        if not live[row]:
            if generations[row]==9223372036854775807:raise ValueError('branch generation exhausted')
            generations[row]+=1;live[row]=True
            return row
    return -1


@njit
def _check(live,generations,row,generation):
    if row<0 or row>=len(live) or not live[row] or generations[row]!=generation:raise ValueError('stale or invalid branch handle')


@njit
def _step(pool,row,company,kinds,labels,io,fo,floats,event,allocation,observe,persistent,scenario_stop):
    offsets=np.array([0,len(allocation)],np.int64)
    state,records,supply=_replay(_load(pool,row),company,kinds,labels,io,fo,pool[12][row],floats,
        event,event+1,offsets,allocation,observe,persistent,scenario_stop,-1,np.empty(0,np.int64),np.empty(0))
    _store(pool,row,state,supply)
    return records


class BranchLimit(ValueError):
    def __init__(self,diagnostics):super().__init__('branch arena capacity exhausted');self.diagnostics=diagnostics


class BranchArena:
    def __init__(self,template,capacity):
        if not isinstance(capacity,int) or isinstance(capacity,bool) or capacity<1:raise ValueError('positive branch capacity required')
        self.template=template.fork();self.capacity=capacity;self.live=np.zeros(capacity,np.bool_)
        self.generations=np.zeros(capacity,np.int64);self.search_metadata=np.zeros((capacity,3),np.int64);self.active=0;self.peak=0;self.allocations=0
        state=template.data
        self.pool=tuple(np.empty((capacity,len(state[i])),dtype=state[i].dtype) for i in (0,1,2,3,4,5,6,8,9,10,12))+(np.empty((capacity,3),np.int64),np.empty((capacity,len(template.integers)),np.int64))

    def diagnostics(self):
        return dict(capacity=self.capacity,active=self.active,peakBranches=self.peak,allocations=self.allocations,
            searchMetadataBytes=self.search_metadata.nbytes,
            poolBufferBytes=self.live.nbytes+self.generations.nbytes+self.search_metadata.nbytes+sum(a.nbytes for a in self.pool),
            templateBufferBytes=sum(a.nbytes for a in self.template.data if isinstance(a,np.ndarray))+self.template.integers.nbytes+sum(a.nbytes for record in self.template.observations for a in record))

    def _check(self,handle):
        if not isinstance(handle,tuple) or len(handle)!=2 or any(not isinstance(x,int) or isinstance(x,bool) or not 0<=x<2**63 for x in handle):raise ValueError('invalid branch handle')
        _check(self.live,self.generations,*handle)
        return handle[0]

    def _claim(self):
        row=int(_claim(self.live,self.generations))
        if row<0:raise BranchLimit(self.diagnostics())
        self.active+=1;self.peak=max(self.peak,self.active);self.allocations+=1
        return row,int(self.generations[row])

    def create(self):
        handle=self._claim();_store(self.pool,handle[0],self.template.data,self.template.integers)
        self.search_metadata[handle[0]].fill(0)
        return handle

    def fork(self,handle):
        source=self._check(handle);child=self._claim()
        _store(self.pool,child[0],_load(self.pool,source),self.pool[12][source])
        self.search_metadata[child[0]]=self.search_metadata[source]
        return child

    def release(self,handle):
        row=self._check(handle);self.search_metadata[row].fill(0);self.live[row]=False;self.active-=1

    def export(self,handle):
        row=self._check(handle);resident=self.template.fork()
        resident.data=_load(self.pool,row);resident.integers=self.pool[12][row].copy()
        # Observations/history are separate search storage, not state-arena data.
        resident.observations=();resident.observation_positions=()
        return resident

    def step(self,handle,scenario,index,allocation=None,*,observe=True):
        row=self._check(handle);p=self.template.program
        if not isinstance(scenario,int) or isinstance(scenario,bool) or not 0<=scenario<len(p.probabilities):raise ValueError('invalid branch scenario')
        if not isinstance(index,int) or isinstance(index,bool) or index<0:raise ValueError('invalid branch event')
        if not isinstance(observe,bool):raise ValueError('invalid observation mode')
        event=int(p.scenario_offsets[scenario])+index
        if event>=p.scenario_offsets[scenario+1]:raise ValueError('invalid branch event')
        iv=self.pool[12][row,int(p.integer_offsets[event]):int(p.integer_offsets[event+1])]
        if p.event_kinds[event]==0:
            if iv[0]!=iv[1]:raise ValueError('purchase requires resolved funded demands')
            if allocation is None or len(allocation)!=iv[0]:raise ValueError('purchase allocation required')
            if any(not isinstance(q,int) or isinstance(q,bool) or q<0 for q in allocation):raise ValueError('invalid purchase allocation')
            for i in range(int(iv[0])):
                if iv[4+4*iv[0]+i]<0 or iv[4+4*iv[0]+i]%iv[7+4*i]:raise ValueError('invalid funded whole-lot quantity')
        else:
            if allocation is not None:raise ValueError('allocation supplied for non-purchase')
            allocation=()
        return tuple(_step(self.pool,row,self.template.company_data,p.event_kinds,p.event_labels,p.integer_offsets,p.float_offsets,p.floats,
            event,_array(allocation,'<i8'),observe,self.template.supply=='persistent-arrivals',int(p.scenario_offsets[scenario+1])))


@njit
def _query_step(pool,row,company,kinds,labels,io,fo,floats,event,allocation,observe,persistent,scenario_stop,iv,fv):
    state,records,supply=_replay(_load(pool,row),company,kinds,labels,io,fo,pool[12][row],floats,event,event+1,
        np.array([0,len(allocation)],np.int64),allocation,observe,persistent,scenario_stop,event,iv,fv)
    _store(pool,row,state,supply)
    return records


class ArenaResident:
    """Search adapter owning one arena handle; history/funding IDs live in the arena."""
    def __init__(self,arena,handle):
        self.arena=arena;self.handle=handle
        template=arena.template
        for name in ('company','initial','program','events','labels','company_data','supply','native'):
            setattr(self,name,getattr(template,name))
        self.observations=();self.observation_positions=()

    @property
    def data(self):return _load(self.arena.pool,self.arena._check(self.handle))

    @property
    def integers(self):return self.arena.pool[12][self.arena._check(self.handle)]

    def _get_metadata(self,column):
        return int(self.arena.search_metadata[self.arena._check(self.handle),column])

    def _set_metadata(self,column,value):
        row=self.arena._check(self.handle)
        if not isinstance(value,int) or isinstance(value,bool) or not 0<=value<2**63:
            raise ValueError('invalid branch search metadata')
        self.arena.search_metadata[row,column]=value

    history_node=property(lambda self:self._get_metadata(0),lambda self,value:self._set_metadata(0,value))
    history_count=property(lambda self:self._get_metadata(1),lambda self,value:self._set_metadata(1,value))
    funding_node=property(lambda self:self._get_metadata(2),lambda self,value:self._set_metadata(2,value))

    def fork(self):
        child=ArenaResident(self.arena,self.arena.fork(self.handle))
        child.observations=self.observations;child.observation_positions=self.observation_positions
        return child

    def release(self):self.arena.release(self.handle)

    def snapshot(self):return self.arena.export(self.handle).snapshot()

    def run(self,scenario,allocations,*,start=0,stop=None,observe=False):
        # Search dispatches exactly one event per call. Reject broader calls
        # rather than silently weakening Resident.run's segment atomicity.
        if stop!=start+1:raise ValueError('arena search adapter requires one event')
        event=int(self.program.scenario_offsets[scenario])+start
        required={start} if self.program.event_kinds[event]==0 else set()
        if set(allocations)!=required:raise ValueError('missing or extra purchase allocation indices')
        records=self.arena.step(self.handle,scenario,start,allocations.get(start),observe=observe)
        self.observations+=records
        if observe:self.observation_positions+=(start,)

    def funding_purchase(self,scenario,index,allocation,*,offer=None,observe=True):
        from .continuation_query import prepare
        iv,fv,selected=prepare(self,scenario,index,offer)
        if len(allocation)!=len(selected) or any(not isinstance(q,int) or isinstance(q,bool) or q<0 for q in allocation):raise ValueError('invalid query allocation')
        p=self.program;event=int(p.scenario_offsets[scenario])+index;row=self.arena._check(self.handle)
        records=_query_step(self.arena.pool,row,self.company_data,p.event_kinds,p.event_labels,p.integer_offsets,p.float_offsets,p.floats,
            event,_array(allocation,'<i8'),observe,self.supply=='persistent-arrivals',int(p.scenario_offsets[scenario+1]),iv,fv)
        self.observations+=tuple(records)
        if observe:self.observation_positions+=(index,)
        return tuple(int(i) for i in selected)

    def set_funded_demands(self,scenario,index,demands):
        from .continuation_resident import Resident
        Resident.set_funded_demands(self,scenario,index,demands)

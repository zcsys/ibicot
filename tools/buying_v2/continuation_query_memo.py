"""Opt-in exact cross-group funding reuse, bounded by entries and payload bytes.

This experimental index uses Python bytes/OrderedDict; it is not the final
compiled memo representation. A cache belongs to one solve/program only.
"""
from collections import OrderedDict
import struct
import numpy as np


class QueryMemo:
    def __init__(self,program,capacity,max_bytes):
        if any(not isinstance(x,int) or isinstance(x,bool) or x<1 for x in (capacity,max_bytes)):raise ValueError('positive memo limits required')
        self.program=program;self.capacity=capacity;self.max_bytes=max_bytes;self.entries=OrderedDict()
        self.bytes=0;self.peak_bytes=0;self.peak=0;self.hits=0;self.misses=0;self.evictions=0;self.oversized=0

    def key(self,group,index,iv,fv):
        parts=[struct.pack('<qq',index,len(group))];prefix=None
        def array(a):
            data=a.tobytes();parts.append(struct.pack('<q',len(data)));parts.append(data)
        array(iv);array(fv)
        for scenario,r,_ in group:
            if r.program is not self.program or r.history_count!=index:raise ValueError('incompatible memo scope')
            if prefix is None:prefix=r.history_node
            elif prefix!=r.history_node:raise ValueError('memo requires a common observed prefix')
            parts.append(struct.pack('<q',scenario))
            parts.append(r.supply.encode()+b'\0')
            state=r.data
            for value in state[:7]:array(value)
            parts.append(struct.pack('<q',int(state[7])))
            if state[7]>=0:
                for value in state[8:11]:array(value)
            parts.append(struct.pack('<qq',int(state[11]),int(state[13])))
            array(state[12][:state[13]])
            p=self.program;event=int(p.scenario_offsets[scenario])+index
            end=int(p.scenario_offsets[scenario+1])
            array(r.integers[p.integer_offsets[event]:p.integer_offsets[end]])
        return b''.join(parts)

    def get(self,key):
        entry=self.entries.get(key)
        if entry is None:self.misses+=1;return None
        self.hits+=1;return entry[0]

    def put(self,key,answer):
        quantities,goods,value=answer;answer=(tuple(quantities),float(goods),float(value))
        size=len(key)+8*len(quantities)+16
        if size>self.max_bytes:self.oversized+=1;return
        if key in self.entries:
            previous=self.entries.pop(key);self.bytes-=previous[1]
        while len(self.entries)>=self.capacity or self.bytes+size>self.max_bytes:
            _,(_,old)=self.entries.popitem(last=False);self.bytes-=old;self.evictions+=1
        self.entries[key]=(answer,size);self.bytes+=size;self.peak_bytes=max(self.peak_bytes,self.bytes);self.peak=max(self.peak,len(self.entries))

    def diagnostics(self):
        return dict(capacity=self.capacity,maxPayloadBytes=self.max_bytes,entries=len(self.entries),payloadBytes=self.bytes,
            peakEntries=self.peak,peakPayloadBytes=self.peak_bytes,hits=self.hits,misses=self.misses,evictions=self.evictions,oversized=self.oversized,
            scope='Retained key/answer payload only; excludes Python objects and pending frame keys.')

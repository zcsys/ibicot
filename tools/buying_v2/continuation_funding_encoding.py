"""Numeric completed-funding records from typed query answers."""
import numpy as np
from .jit import njit


@njit
def encode_answers(index,event,floats,incumbents,requests,ready,quantities,values):
    offers=event[0];inputs=len(incumbents)
    if index<0 or inputs<1 or len(requests)!=offers+1 or quantities.shape[1]!=inputs:raise ValueError('invalid funding answer dimensions')
    for ordinal in range(offers+1):
        row=requests[ordinal]
        if row<0 or row>=len(ready) or not ready[row]:raise ValueError('query answer not completed')
        if not np.isfinite(values[row]).all() or values[row,0]<0 or np.any(quantities[row]<0):raise ValueError('invalid funding answer')
    demands=np.empty(offers,np.int64)
    for i in range(offers):
        material=event[4+4*i]
        if material<0 or material>=inputs:raise ValueError('invalid offer material')
        demands[i]=quantities[requests[i+1],material]
    iv=np.empty(3+3*inputs+offers*(2+inputs),np.int64);fv=np.empty(1+2*offers,np.float64)
    iv[0]=index;iv[1]=inputs;iv[2]=offers
    joint=requests[0];fv[0]=values[joint,0]
    for material in range(inputs):
        chosen=-1
        for i in range(offers):
            if event[4+4*i]!=material:continue
            if event[5+4*i]==incumbents[material]:chosen=i;break
            if chosen<0 or floats[4+i]<floats[4+chosen] or (floats[4+i]==floats[4+chosen] and event[5+4*i]<event[5+4*chosen]):chosen=i
        iv[3+material]=event[5+4*chosen] if chosen>=0 else -1
        iv[3+inputs+material]=demands[chosen] if chosen>=0 else 0
        iv[3+2*inputs+material]=quantities[joint,material]
    cursor=3+3*inputs
    for i in range(offers):
        row=requests[i+1];iv[cursor]=event[4+4*i];iv[cursor+1]=event[5+4*i]
        for m in range(inputs):iv[cursor+2+m]=quantities[row,m]
        fv[1+2*i]=values[row,0];fv[2+2*i]=values[row,1];cursor+=2+inputs
    return demands,iv,fv

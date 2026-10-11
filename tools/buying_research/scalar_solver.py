"""Allocation-free two-input specialization of the proved unit-lot envelope.

The caller owns a reusable breakpoint scratch array. Return a scalar tuple so a
population loop need not allocate result arrays for each considered basket.
"""
import math
from .jit import njit
from .solvers import industrial_value


@njit
def solve(nm,held,ratios,spaces,slots,room,prices,stocks,counts,prefs,fees,bids,
          bound,finished,output_price,mean,conversion,cash,reserve,points):
    npnt=2;points[0]=0;points[1]=bound+1
    for m in range(nm):
        point=int(math.floor(held[m]/ratios[m]))+1
        if 0<point<bound+1:points[npnt]=point;npnt+=1
        pf=prefs[m];fee=0.
        if pf>=0 and bids[m]>0 and stocks[m,pf]>=bids[m]:fee=fees[m]
        for s in range(counts[m]):
            point=int(math.floor((held[m]+min(stocks[m,s],ratios[m]*bound))/ratios[m]))+1
            if 0<point<bound+1:points[npnt]=point;npnt+=1
            if pf>=0 and s!=pf and prices[m,pf]>prices[m,s]:
                root=(held[m]+fee/(prices[m,pf]-prices[m,s]))/ratios[m]
                if root>bound+1:continue
                low=int(math.floor(root))
                for point in (low,low+1):
                    if 0<point<bound+1:points[npnt]=point;npnt+=1
    for i in range(1,npnt):
        point=points[i];j=i-1
        while j>=0 and points[j]>point:points[j+1]=points[j];j-=1
        points[j+1]=point
    best0=-1;best1=-1;bq0=0;bq1=0;bf0=0.;bf1=0.;by=0;bcost=0.;bscore=-1e300
    for section in range(npnt-1):
        low=points[section];high=points[section+1]-1
        if high<low:continue
        coeff=0.;constant=0.;sp_coeff=0.;sp_constant=0.;valid=True
        s0=-1;s1=-1;f0=0.;f1=0.
        for m in range(nm):
            q=int(max(0.,ratios[m]*low-held[m]))
            if q==0:continue
            pf=prefs[m];fee=0.
            if pf>=0 and bids[m]>0 and stocks[m,pf]>=bids[m]:fee=fees[m]
            cheapest=1e300;winner=-1
            for s in range(counts[m]):
                if stocks[m,s]<q:continue
                cost=q*prices[m,s]+(fee if s!=pf else 0.)
                if cost<cheapest-1e-9 or (abs(cost-cheapest)<=1e-9 and s==pf):cheapest=cost;winner=s
            if winner<0:valid=False;break
            charge=fee if winner!=pf else 0.
            if m==0:s0=winner;f0=charge
            else:s1=winner;f1=charge
            high=min(high,int(math.floor(slots[m]/ratios[m])))
            coeff+=ratios[m]*prices[m,winner];constant+=charge-held[m]*prices[m,winner]
            sp_coeff+=ratios[m]*spaces[m];sp_constant-=held[m]*spaces[m]
        if not valid:continue
        if sp_coeff>0:high=int(math.floor(max(-1.,min(float(high),(room-sp_constant)/sp_coeff))))
        if coeff+reserve>0:high=int(math.floor(max(-1.,min(float(high),(cash-constant)/(coeff+reserve)))))
        if high<low:continue
        marginal=conversion+coeff
        root=(mean*math.log(output_price/marginal)-finished if mean>0 and output_price>0 and marginal>0
              else float(high) if marginal<=0 and mean>0 else 0.)
        for side in range(2):
            y=max(low,min(high,int(math.floor(root)) if side==0 else int(math.ceil(root))))
            q0=int(max(0.,ratios[0]*y-held[0]));q1=int(max(0.,ratios[1]*y-held[1])) if nm==2 else 0
            cost=(q0*prices[0,s0]+f0 if q0 else 0.)+(q1*prices[1,s1]+f1 if q1 else 0.)
            space=q0*spaces[0]+(q1*spaces[1] if nm==2 else 0.)
            if cost+reserve*y>cash or space>room:continue
            score=industrial_value(y,finished,output_price,mean,conversion)-cost
            tol=1e-9+1e-12*max(abs(score),abs(bscore))
            choose=bscore==-1e300 or score>bscore+tol
            if abs(score-bscore)<=tol:
                if cost<bcost-1e-9:choose=True
                elif abs(cost-bcost)<=1e-9 and y<by:choose=True
            if choose:
                best0=s0;best1=s1;bq0=q0;bq1=q1;bf0=f0;bf1=f1;by=y;bcost=cost;bscore=score
    return best0,best1,bq0,bq1,bf0,bf1,by,bscore,bcost

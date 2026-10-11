"""Standalone research figures; use the isolated plot-runtime Python environment."""
import argparse
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def series(path,end=None):
    schema=json.loads((path/'measurement-schema.json').read_text());ix={k:i for i,k in enumerate(schema['fields'])}
    masks={t:np.array([p['tier']==t for p in schema['products']]) for t in ('t0','t1','t2')}
    output=[]
    for f in sorted(path.glob('products-*.npz')):
        with np.load(f,allow_pickle=False) as z:
            ticks=z['ticks'];data=z['data']
            if end is not None:
                take=ticks<=end;ticks=ticks[take];data=data[take]
            for start in range(0,len(ticks),30):
                x=data[start:start+30];ts=ticks[start:start+30]
                r={'tick':float(ts.mean()),'year':float(ts.mean()/360),'start':int(ts[0]),'end':int(ts[-1])}
                for tier,mask in masks.items():
                    totals=x[:,mask,:].sum(axis=(0,1));rev=totals[ix['revenue']];units=totals[ix['sold']]
                    net=rev-totals[ix['cogs']]+totals[ix['switchIncome']]-totals[ix['switchExpense']]-totals[ix['rent']]
                    r[tier+'Margin']=net/rev if rev else np.nan
                    r[tier+'Utilization']=totals[ix['made']]/totals[ix['capacity']] if totals[ix['capacity']] else np.nan
                    r[tier+'Price']=rev/units if units else np.nan
                    r[tier+'Units']=units/len(ts)
                    r[tier+'Profit']=net/len(ts)
                    r[tier+'Retail']=totals[ix['retailSold']]/len(ts)
                output.append(r)
    return output


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--runs',nargs='+',type=Path,required=True)
    p.add_argument('--labels',nargs='+',required=True);p.add_argument('--end',type=int)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if len(a.runs)!=len(a.labels):raise ValueError('One label per run')
    if len(a.runs)>4:raise ValueError('This comparison layout supports at most four runs; split larger comparisons explicitly')
    a.output.mkdir(parents=True,exist_ok=False)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,
        'axes.spines.right':False,'axes.grid':True,'grid.alpha':.18,'figure.facecolor':'white','savefig.facecolor':'white'})
    colors=['#234F6E','#BB523D','#32856C','#94649C']
    data=[series(x,a.end) for x in a.runs]
    fig,axs=plt.subplots(2,2,figsize=(12,7.3),layout='constrained')
    if len(data)==1:
        rows=data[0];x=[r['year'] for r in rows]
        for tier,label,color in zip(('t0','t1','t2'),('Extractors','Refineries','Manufacturers'),colors):
            axs[0,0].plot(x,[100*r[tier+'Margin'] for r in rows],label=label,color=color)
            axs[0,1].plot(x,[100*r[tier+'Utilization'] for r in rows],label=label,color=color)
        for tier,label,color in zip(('t1','t2'),('Refineries','Manufacturers'),colors[1:]):
            axs[1,0].plot(x,[r[tier+'Price'] for r in rows],label=label,color=color)
        axs[1,1].plot(x,[r['t2Retail']/1e6 for r in rows],color=colors[2])
        titles=('Net margin · % of goods revenue','Realized output · % of nominal capacity',
                'Realized goods price · $ per item','Final retail sales · million items per tick')
        fig.suptitle(a.labels[0]+' · monthly posted accounts',fontsize=15,fontweight='bold')
        for ax in axs.flat:
            if max(x)>20:ax.axvline(20,color='#888888',linestyle=':',linewidth=1)
        axs[1,0].legend(frameon=False)
    else:
        titles=('Final retail sales · million items per tick','Refinery net margin · %',
                'Manufacturer net margin · %','Manufacturer realized output · % of capacity')
        for rows,label,color in zip(data,a.labels,colors):
            x=[r['year'] for r in rows]
            for ax,key,scale in zip(axs.flat,('t2Retail','t1Margin','t2Margin','t2Utilization'),(1e-6,100,100,100)):
                ax.plot(x,[scale*r[key] for r in rows],label=label,color=color)
        fig.suptitle('Matched buying-policy comparison · monthly posted accounts',fontsize=15,fontweight='bold')
    for ax,title in zip(axs.flat,titles):ax.set_title(title,loc='left',fontsize=11);ax.set_xlabel('Simulated years (360 ticks each)')
    axs[0,0].legend(frameon=False,fontsize=9)
    fig.savefig(a.output/'economy.png',dpi=180);fig.savefig(a.output/'economy.svg')
    plt.close(fig)
    export=[[{k:(None if isinstance(v,(float,np.floating)) and not np.isfinite(v) else v) for k,v in row.items()}
             for row in rows] for rows in data]
    (a.output/'figure-data.json').write_text(json.dumps(dict(runs=[str(x.resolve()) for x in a.runs],labels=a.labels,
        end=a.end,series=export,notes='Period margins and prices use summed accounts. Undefined ratios appear as gaps. No independent-sample interpretation of ticks.'),indent=2,allow_nan=False)+'\n')
    (a.output/'render-environment.json').write_text(json.dumps(dict(matplotlib=matplotlib.__version__,numpy=np.__version__),indent=2)+'\n')


if __name__=='__main__':main()

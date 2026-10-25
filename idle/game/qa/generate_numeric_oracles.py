"""Non-author arithmetic probes. No production implementation is imported."""
from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path
import json,random
rng=random.Random(561230)
def ceil_fraction(v):return (v.numerator+v.denominator-1)//v.denominator
def total(t,n):return ceil_fraction(Fraction(30*20**t*10**6)*sum((Fraction(28,25)**k for k in range(n)),Fraction(0)))
def threshold(charts):
 rhs=charts**20*10**195
 lo,hi=0,1
 while hi**13*10**20<rhs:hi*=2
 while lo<hi:
  mid=(lo+hi)//2
  if mid**13*10**20>=rhs:hi=mid
  else:lo=mid+1
 return lo
result={'method':'Python Fraction summation for settled prices; independent binary search for exact prestige thresholds; Decimal 90-digit sqrt/ln for output. Fixed random seed561230.','prices':[],'thresholds':[],'rates':[],'logs':[]}
for tier in range(5):
 for own in [1,9,10,24,25,49,50,74,75,99,100,149]:
  for amount in [1,7]:result['prices'].append({'tier':tier,'owned':own,'quantity':amount,'micros':str(total(tier,own+amount)-total(tier,own))})
for c in [10,11,24,25,26,99,100,101,10000,10**9,10**30]:result['thresholds'].append({'charts':str(c),'micros':str(threshold(c))})
with localcontext() as ctx:
 ctx.prec=90
 for i in range(80):
  counts=[rng.choice([1,9,10,24,25,26,49,50,51,75,99,100,101,500,10000]) for j in range(5)]
  charts=rng.choice([0,10,24,25,26,99,100,10000,10**9,10**30]);permanent=1+(Decimal(charts)/10).sqrt(); rates=[]
  x=[(1+Decimal(counts[j])/25).ln()/Decimal(2).ln() for j in range(2)]
  for j,n in enumerate(counts):
   synergy=Decimal(1)
   if charts>=25 and j>=3:
    a,b=(Decimal('.2'),Decimal('.1')) if j==3 else (Decimal('.1'),Decimal('.25'))
    synergy+=a*x[0]+b*x[1]
   rates.append(Decimal(20**j*n*2**min(n//25,4))*permanent*synergy)
  result['rates'].append({'counts':counts,'charts':str(charts),'output':str(sum(rates))})
 for n in [1,2,24,25,26,49,50,51,99,100,10000,10**9]:result['logs'].append({'numerator':str(25+n),'denominator':'25','value':str((Decimal(25+n)/25).ln()/Decimal(2).ln())})
p=Path(__file__).with_name('numeric_oracles.json');p.write_text(json.dumps(result,indent=2)+'\n');print({k:len(v) for k,v in result.items() if isinstance(v,list)})

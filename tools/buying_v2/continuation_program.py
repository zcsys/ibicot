"""Lossless typed calendar representation; no economic execution or search.

Schemas 1/2 use per-event integer/float payloads and CSR-style offsets. Arrays
have immutable bytes backing and own no caller buffers. Label strings remain
outside compiled execution. Decode validates both structure and ledger calendar.
"""
from dataclasses import dataclass
import math
import numpy as np
from .phase_ledger import (Purchase,OpenBook,SettleBook,SharedSettleBook,SetQuotes,
                          Rent,EndTick,validate_state)
from .industry_oracle import Offer
from .phase_oracle import Scenario
from .scenario_validation import validate_calendar
from .quantity_value import LinearQuantityValue

KINDS=(Purchase,OpenBook,SettleBook,SharedSettleBook,SetQuotes,Rent,EndTick)


@dataclass(frozen=True,eq=False)
class Program:
    version: int
    inputs: int
    lines: int
    labels: tuple
    probabilities: np.ndarray
    scenario_offsets: np.ndarray
    event_kinds: np.ndarray
    event_labels: np.ndarray
    integer_offsets: np.ndarray
    float_offsets: np.ndarray
    integers: np.ndarray
    floats: np.ndarray
    terminal_offsets: np.ndarray
    terminal_values: np.ndarray
    terminal_modes: np.ndarray | None = None
    terminal_quantities: np.ndarray | None = None


INTEGER_ARRAYS=('scenario_offsets','event_kinds','event_labels','integer_offsets','float_offsets','integers','terminal_offsets')
FLOAT_ARRAYS=('probabilities','floats','terminal_values')


def _integer(value):
    if not isinstance(value,int) or isinstance(value,bool) or not -(2**63)<=value<2**63:
        raise ValueError('calendar integer must fit signed int64')
    return value


def _array(values,kind):
    if kind=='<i8':values=[_integer(v) for v in values]
    elif any(float(v)!=v for v in values):raise ValueError('calendar number cannot be represented losslessly in float64')
    array=np.asarray(values,dtype=kind)
    if kind=='<f8' and not np.isfinite(array).all():raise ValueError('nonfinite calendar number')
    return np.frombuffer(array.tobytes(),dtype=kind)


def _validate_scenarios(company,initial,scenarios):
    validate_state(company,initial)
    if not scenarios or any(not math.isfinite(s.probability) or s.probability<0 for s in scenarios):
        raise ValueError('invalid scenario probabilities')
    if abs(math.fsum(s.probability for s in scenarios)-1)>1e-12:raise ValueError('invalid scenario probabilities')
    structure=tuple((type(e),e.label) for e in scenarios[0].events)
    for scenario in scenarios:
        validate_calendar(company,initial,scenario)
        if tuple((type(e),e.label) for e in scenario.events)!=structure:
            raise ValueError('scenario calendars/labels differ')


def compile_calendar(company,initial,scenarios):
    scenarios=tuple(scenarios);_validate_scenarios(company,initial,scenarios)
    labels=[];label_ids={};kinds=[];event_labels=[];scenario_offsets=[0]
    integer_offsets=[0];float_offsets=[0];integers=[];floats=[]
    terminal_offsets=[0];terminal_values=[];terminal_modes=[];terminal_quantities=[]
    for scenario in scenarios:
        for event in scenario.events:
            if event.label not in label_ids:
                label_ids[event.label]=len(labels);labels.append(event.label)
            event_labels.append(label_ids[event.label]);kinds.append(KINDS.index(type(event)))
            iv=[];fv=[]
            if type(event) is Purchase:
                n=len(event.offers)
                if len(event.funded_demands) not in (0,n) or any(q<0 for q in event.funded_demands):
                    raise ValueError('invalid explicit funded demands')
                iv=[n,len(event.funded_demands),len(event.active_lines),2 if event.frozen_overhead is not None else int(event.overhead_timing=='after')]
                for offer in event.offers:iv.extend((offer.material,offer.supplier,offer.stock,offer.lot))
                iv.extend(event.funded_demands);iv.extend(event.active_lines)
                fv=[event.fee_unit_cost,event.fee_multiple,event.rent_bill,event.rent_threshold]
                fv.extend(o.price for o in event.offers);fv.extend(event.reliability)
                if event.frozen_overhead is not None:fv.append(event.frozen_overhead)
            elif type(event) in (SettleBook,SharedSettleBook):
                iv=[len(event.demand),*event.demand];fv=[event.fee_income]
                if type(event) is SharedSettleBook:
                    iv.append(len(event.groups))
                    for group in event.groups:iv.extend((len(group),*group))
            elif type(event) is SetQuotes:iv=[len(event.quotes)];fv=list(event.quotes)
            elif type(event) is Rent:fv=[event.bill,event.threshold]
            elif type(event) is EndTick:fv=[event.alpha]
            integers.extend(iv);floats.extend(fv)
            integer_offsets.append(len(integers));float_offsets.append(len(floats))
        scenario_offsets.append(len(kinds))
        for table in scenario.input_values+scenario.finished_values:
            native=isinstance(table,LinearQuantityValue)
            terminal_modes.append(int(native))
            terminal_values.extend(table.values if native else table)
            terminal_quantities.extend(table.quantities if native else range(len(table)))
            terminal_offsets.append(len(terminal_values))
    version=2 if any(type(e) is Purchase and e.frozen_overhead is not None for s in scenarios for e in s.events) else 1
    if any(terminal_modes):version=3
    if any(q!=int(q) for q in (*initial.held,*initial.finished,*company.slots,*(initial.book.quantity if initial.book else ()))):version=4
    return Program(version,len(initial.held),len(initial.finished),tuple(labels),
        _array([s.probability for s in scenarios],'<f8'),_array(scenario_offsets,'<i8'),
        _array(kinds,'<i8'),_array(event_labels,'<i8'),_array(integer_offsets,'<i8'),
        _array(float_offsets,'<i8'),_array(integers,'<i8'),_array(floats,'<f8'),
        _array(terminal_offsets,'<i8'),_array(terminal_values,'<f8'),
        _array(terminal_modes,'<i8') if version>=3 else None,
        _array(terminal_quantities,'<f8') if version>=3 else None)


def _offsets(array,total,length):
    if len(array)!=length or not len(array) or int(array[0])!=0 or int(array[-1])!=total:
        raise ValueError('invalid calendar offsets')
    if any(int(a)>int(b) or int(a)<0 for a,b in zip(array,array[1:])):
        raise ValueError('invalid calendar offsets')


def decode_calendar(program,company,initial):
    if not isinstance(program,Program) or type(program.version) is not int or program.version not in (1,2,3,4):
        raise ValueError('unsupported calendar schema')
    if type(program.inputs) is not int or type(program.lines) is not int or (program.inputs,program.lines)!=(len(initial.held),len(initial.finished)):
        raise ValueError('calendar company dimensions differ')
    if not isinstance(program.labels,tuple) or any(not isinstance(s,str) or not s for s in program.labels) or len(set(program.labels))!=len(program.labels):
        raise ValueError('invalid calendar labels')
    for name in INTEGER_ARRAYS+FLOAT_ARRAYS:
        array=getattr(program,name);dtype=np.dtype('<i8' if name in INTEGER_ARRAYS else '<f8')
        if not isinstance(array,np.ndarray) or array.dtype!=dtype or array.ndim!=1 or not array.flags.c_contiguous:
            raise ValueError('invalid calendar array type')
        if name in FLOAT_ARRAYS and not np.isfinite(array).all():raise ValueError('nonfinite calendar number')
    n=len(program.event_kinds);ns=len(program.probabilities)
    if len(program.event_labels)!=n or any(not 0<=int(k)<len(KINDS) for k in program.event_kinds) or any(not 0<=int(k)<len(program.labels) for k in program.event_labels):
        raise ValueError('invalid calendar event identity')
    _offsets(program.scenario_offsets,n,ns+1)
    _offsets(program.integer_offsets,len(program.integers),n+1)
    _offsets(program.float_offsets,len(program.floats),n+1)
    _offsets(program.terminal_offsets,len(program.terminal_values),ns*(program.inputs+program.lines)+1)
    if program.version>=3:
        for name,dtype in (('terminal_modes','<i8'),('terminal_quantities','<f8')):
            a=getattr(program,name)
            if not isinstance(a,np.ndarray) or a.dtype!=np.dtype(dtype) or a.ndim!=1 or not a.flags.c_contiguous or not np.isfinite(a).all():
                raise ValueError('invalid native terminal array')
        if len(program.terminal_modes)!=ns*(program.inputs+program.lines) or len(program.terminal_quantities)!=len(program.terminal_values) or any(m not in (0,1) for m in program.terminal_modes):
            raise ValueError('invalid native terminal dimensions/mode')
    elif program.terminal_modes is not None or program.terminal_quantities is not None:
        raise ValueError('native terminal payload requires schema 3')
    events=[]
    for index,kind in enumerate(program.event_kinds):
        label=program.labels[int(program.event_labels[index])];cls=KINDS[int(kind)]
        iv=tuple(int(x) for x in program.integers[program.integer_offsets[index]:program.integer_offsets[index+1]])
        fv=tuple(float(x) for x in program.floats[program.float_offsets[index]:program.float_offsets[index+1]])
        try:
            if cls is Purchase:
                offers,funded,active,timing=iv[:4]
                if min(offers,funded,active)<0 or timing not in (0,1,2) or len(iv)!=4+4*offers+funded+active or len(fv)!=4+2*offers+int(timing==2) or (timing==2 and program.version not in (2,3,4)):
                    raise ValueError('invalid purchase payload')
                rows=tuple(Offer(iv[4+4*i],iv[5+4*i],fv[4+i],iv[6+4*i],iv[7+4*i]) for i in range(offers))
                end=4+4*offers
                event=Purchase(label,rows,iv[end:end+funded],fv[4+offers:4+2*offers],fv[0],fv[1],iv[end+funded:],fv[2],fv[3],'after' if timing==1 else 'before',fv[-1] if timing==2 else None)
            elif cls is OpenBook:
                if iv or fv:raise ValueError('invalid opening payload')
                event=OpenBook(label)
            elif cls in (SettleBook,SharedSettleBook):
                count=iv[0]
                if count<0 or len(fv)!=1 or len(iv)<1+count:raise ValueError('invalid settlement payload')
                demand=iv[1:1+count];end=1+count
                if cls is SettleBook:
                    if len(iv)!=end:raise ValueError('extra settlement payload')
                    event=SettleBook(label,demand,fv[0])
                else:
                    groups=[];ng=iv[end];end+=1
                    if ng<1 or ng>len(iv)-end:raise ValueError('invalid group count')
                    for _ in range(ng):
                        size=iv[end];end+=1
                        if size<1 or end+size>len(iv):raise ValueError('invalid group payload')
                        groups.append(iv[end:end+size]);end+=size
                    if end!=len(iv):raise ValueError('extra group payload')
                    event=SharedSettleBook(label,demand,fv[0],tuple(groups))
            elif cls is SetQuotes:
                if len(iv)!=1 or iv[0]!=len(fv):raise ValueError('invalid quote payload')
                event=SetQuotes(label,fv)
            elif cls is Rent:
                if iv or len(fv)!=2:raise ValueError('invalid rent payload')
                event=Rent(label,*fv)
            else:
                if iv or len(fv)!=1:raise ValueError('invalid tick payload')
                event=EndTick(label,fv[0])
        except (IndexError,TypeError) as error:
            raise ValueError('truncated calendar payload') from error
        events.append(event)
    scenarios=[];width=program.inputs+program.lines
    for i,probability in enumerate(program.probabilities):
        tables=[]
        for j in range(i*width,(i+1)*width):
            a,b=program.terminal_offsets[j:j+2]
            values=tuple(float(v) for v in program.terminal_values[a:b])
            if program.version>=3 and program.terminal_modes[j]:
                table=LinearQuantityValue(tuple(float(v) for v in program.terminal_quantities[a:b]),values)
            else:table=values
            tables.append(table)
        tables=tuple(tables)
        scenarios.append(Scenario(float(probability),tuple(events[program.scenario_offsets[i]:program.scenario_offsets[i+1]]),tables[:program.inputs],tables[program.inputs:]))
    scenarios=tuple(scenarios)
    canonical=compile_calendar(company,initial,scenarios)
    if canonical.version!=program.version or canonical.labels!=program.labels or any(getattr(canonical,name).tobytes()!=getattr(program,name).tobytes() for name in INTEGER_ARRAYS+FLOAT_ARRAYS):
        raise ValueError('noncanonical calendar encoding')
    if program.version>=3 and any(getattr(canonical,name).tobytes()!=getattr(program,name).tobytes() for name in ('terminal_modes','terminal_quantities')):
        raise ValueError('noncanonical native terminal encoding')
    return scenarios

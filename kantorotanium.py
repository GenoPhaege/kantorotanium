#!/usr/bin/env python3
'''
kantorotanium: optimize compressed ore purchases

Leonid Vitaliyevich Kantorovich (Russian: Леони́д Вита́льевич Канторо́вич) (19 January 1912 –
7 April 1986) was a Soviet mathematician and economist, known for his theory and development
of techniques for the optimal allocation of resources. He is regarded as the founder of
linear programming. He was the winner of the Stalin Prize in 1949 and the Nobel Memorial Prize
in Economic Sciences in 1975.  -- https://en.wikipedia.org/wiki/Leonid_Kantorovich
'''

__author__ = 'Chris Danis'
__version__ = '0.0.1'
__copyright__ = """
Copyright © 2020 Chris Danis
Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file
except in compliance with the License.  You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software distributed under the
License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
either express or implied.  See the License for the specific language governing permissions
and limitations under the License.
"""

import csv
import dataclasses
import math
import os
import requests
import time

from collections import defaultdict
from typing import Dict

from dataclasses_json import dataclass_json
from logzero import logger
from ortools.linear_solver import pywraplp

@dataclasses.dataclass
class Minerals:
    '''Minerals can be added to each other and multiplied by scalars.'''
    tritanium: int = 0
    pyerite: int = 0
    mexallon: int = 0
    isogen: int = 0
    noxcium: int = 0
    zydrine: int = 0
    megacyte: int = 0
    def __add__(self, other):
        assert isinstance(other, Minerals)
        return Minerals(*[x+y for x,y in zip(dataclasses.astuple(self), dataclasses.astuple(other))])
    def __mul__(self, scalar_number):
        return Minerals(*[x*scalar_number for x in dataclasses.astuple(self)])
    def __rmul__(self, scalar_number):
        return self.__mul__(scalar_number)


@dataclass_json
@dataclasses.dataclass
class Order:
    '''Goods for sale on the market.'''
    # TODO: do we want to model location as well?
    item_id: int
    volume_remain: int
    price: float

def get_orders(item_id: int):
    logger.info('fetching item %s', item_id)
    # TODO pagination
    URL = 'https://esi.evetech.net/latest/markets/10000002/orders/?datasource=tranquility&order_type=sell&page=1&type_id={}'.format(item_id)
    JITA_FOURFOUR_CNAP = 60003760
    r = requests.get(URL)
    r.raise_for_status()
    rv = []
    for o in r.json():
        try:
            if o['location_id'] == JITA_FOURFOUR_CNAP:
                rv.append(Order(item_id=o['type_id'], volume_remain=o['volume_remain'], price=o['price']))
        except:
            logger.warning(o)
    return rv

@dataclasses.dataclass
class Ore:
    '''A kind of ore, and how many of each mineral that one unit of ore refines into.'''
    name: str
    item_id: int
    volume: float
    refines_to: Minerals

def read_ores() -> Dict[str, Ore]:
    rv = {}
    # thanks http://eve.kassikas.net/ore/?result=f6b93757
    with open('ore_50pctbase_554_4pctimplant.csv', 'r') as f:
        for row in csv.DictReader(f):
            refines_to = Minerals(**{(k.split(' (')[0].lower()):int(v) for (k,v) in row.items() if (' (' in k)})
            o = Ore(name=row['typeName'], item_id=int(row['typeId']), volume=float(row['volume']), refines_to=refines_to)
            rv[o.name] = o
    return rv

ores = read_ores()
minerals = [f.name for f in dataclasses.fields(Minerals)]

all_orders = []
ALL_ORDERS_JSON = 'all_orders.json'
if os.path.exists(ALL_ORDERS_JSON) and time.time() - os.path.getmtime(ALL_ORDERS_JSON) < 3600:
    logger.info('using cached orders')
    with open(ALL_ORDERS_JSON, 'r') as f:
        all_orders = Order.schema().loads(f.read(), many=True)
else:
    logger.info('downloading orders')
    for oreitem in [o.item_id for o in ores.values()]:
        all_orders.extend(get_orders(oreitem))
    with open(ALL_ORDERS_JSON, 'w+') as f:
        f.write(Order.schema().dumps(all_orders, many=True))

names = {o.item_id:n for (n,o) in ores.items()}

rounded_orders = {}
for o in all_orders:
    r = o
    r.price = round(r.price, 0)
    k = f'{names[r.item_id]} at {math.ceil(r.price):,}'
    if k in rounded_orders:
        rounded_orders[k].volume_remain += r.volume_remain
    else:
        rounded_orders[k] = r


solver = pywraplp.Solver('minerals', pywraplp.Solver.GLOP_LINEAR_PROGRAMMING)

order_vars = {k:solver.NumVar(0, v.volume_remain, k) for (k,v) in rounded_orders.items()}

# Objective function: minimize cost of what we buy.
objective = solver.Objective()
for k, var in order_vars.items():
    objective.SetCoefficient(var, rounded_orders[k].price)
objective.SetMinimization()


# \!/ Problem specification - you want to edit this part.
for_phoons = Minerals(2.5e6, 9.9e6, 1e6)
twenty_thoraxes = Minerals(10.3e6, 1.29e6, 0.35e6, 94.06e3, 26.73e3, 10.11e3, 2567)
twenty_moas = 2*Minerals(5.45e6, 1.39e6, 0.3564e6, 88.12e3, 23.77e3, 11.28e3, 3458)
twenty_stabbers = 2*Minerals(4.56e6, 1.683e6, 0.3564e6, 92.07e3, 24.752e3, 11.09e3, 2175)

TARGET = for_phoons + twenty_thoraxes + twenty_moas + twenty_stabbers
# \!/ Problem specification - you want to edit this part.


for mineral in minerals:
    # The ores we buy need to refine into at least TARGET[mineral] many units.
    ct = solver.Constraint(getattr(TARGET, mineral), solver.infinity())
    for k, var in order_vars.items():
        ct.SetCoefficient(var, getattr(ores[names[rounded_orders[k].item_id]].refines_to, mineral))

status = solver.Solve()

print("Status: ", status, status==solver.OPTIMAL and "OPTIMAL" or "", status==solver.FEASIBLE and "SUB-OPTIMAL BUT FEASIBLE" or "")

if status in [solver.OPTIMAL, solver.FEASIBLE]:
    price = 0
    volume = 0
    to_buy = defaultdict(float)

    for k, var in order_vars.items():
        if var.solution_value() != 0:
            price += rounded_orders[k].price * var.solution_value()
            volume += ores[names[rounded_orders[k].item_id]].volume *  var.solution_value()
            print(f'{var.solution_value()}x {k} ({rounded_orders[k].volume_remain:,} available)')
            to_buy[names[rounded_orders[k].item_id]] += var.solution_value()
    print("\n\n")

    # now kronch that down from per-order into per-ore
    to_buy = {k:math.ceil(v) for k,v in to_buy.items()}
    refined_minerals = Minerals()
    for k,v in to_buy.items():
        refined_minerals += ores[k].refines_to * v
    print("Yielding:")
    for k,v in dataclasses.asdict(refined_minerals).items():
        print(f'{v:,}x {k} (excess of {v - getattr(TARGET, k):,})')
    print("\n\nINPUT TO MULTIBUY:\n")
    for k, v in to_buy.items():
        print(f'{v}x {k}')
    print(f"\n\nTotal price: {math.ceil(price):,}")
    print(f"Total volume: {volume:,} m3")


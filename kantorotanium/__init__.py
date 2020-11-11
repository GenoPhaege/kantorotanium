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
    nocxium: int = 0
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


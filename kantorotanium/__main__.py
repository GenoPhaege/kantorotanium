#!/usr/bin/env python3
'''
kantorotanium: optimize compressed ore purchases

Leonid Vitaliyevich Kantorovich (Russian: Леони́д Вита́льевич Канторо́вич) (19 January 1912 –
7 April 1986) was a Soviet mathematician and economist, known for his theory and development
of techniques for the optimal allocation of resources. He is regarded as the founder of
linear programming. He was the winner of the Stalin Prize in 1949 and the Nobel Memorial Prize
in Economic Sciences in 1975.  -- https://en.wikipedia.org/wiki/Leonid_Kantorovich
'''

import csv
import dataclasses
import itertools
import math
import os
import requests
import time

from collections import defaultdict
from typing import Dict

import more_itertools

from dataclasses_json import dataclass_json
from logzero import logger
from ortools.linear_solver import pywraplp

from kantorotanium import Minerals, Order, Ore, get_orders, read_ores_json, Purchase

def main(args=None):
    ores = read_ores_json()
    minerals = [f.name for f in dataclasses.fields(Minerals)]

    all_orders = []
    ALL_ORDERS_JSON = 'all_orders.cache.json'
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
    ten_tornadoes = Minerals(39.06e6, 9.744e6, 2.354e6, .6972e6, 0, 84592, 32914)
    ten_thrashers = Minerals(431163, 103347, 35793, 15813, 0, 1620, 234)
    five_harbs = Minerals(17.33e6, 3.713e6, .916e3, 148.5e3, zydrine=29.7e3, megacyte=11878)
    one_typhoon = Minerals(9.16e3, 2.49e6, 557e3, 147e3, 30.88e3, 16256, 4277)
    one_oracle = Minerals(5.19e6, 1.11e6, .279e6, 45218, zydrine=8773, megacyte=3475)

    one_porpoise = Minerals(3207600, 601425, 150357, 80190, 30072, zydrine=5012, megacyte=2807)
    one_procurer = Minerals(1425600, 267300, 66825, 35640, 13365, zydrine=2228, megacyte=1248)

    five_drakes = Minerals(12600000, 4500000, 810000, 90000, 36000, zydrine=9000, megacyte=1800)
    five_canes = Minerals(12474000, 4455000, 801900, 89100, 35640, zydrine=8910, megacyte=1782)

    STASH = Minerals(isogen=4.7e6, nocxium=4.9e6, zydrine=200e3, megacyte=102e3)

    TARGET = 2*Minerals(*dataclasses.astuple(twenty_thoraxes + twenty_moas + twenty_stabbers)[0:3]) + Minerals(pyerite=20e6, mexallon=2e6) + Minerals(tritanium=40e6)

    TARGET = 2*ten_tornadoes + 2*ten_thrashers + twenty_stabbers + -1*STASH
    TARGET = 20*five_harbs + -1*STASH
    TARGET = Minerals(tritanium=4811400, pyerite=1603800, mexallon=320760, isogen=89100, nocxium=13365, zydrine=3119, megacyte=1248)*1.1
    TARGET = 10*one_procurer + 2*one_porpoise + -1*STASH
    TARGET = five_drakes + five_canes + -1*STASH
    # \!/ Problem specification - you want to edit this part.


    for mineral in minerals:
        # The ores we buy need to refine into at least TARGET[mineral] many units.
        ct = solver.Constraint(getattr(TARGET, mineral), solver.infinity())
        for k, var in order_vars.items():
            ct.SetCoefficient(var, getattr(ores[names[rounded_orders[k].item_id]].refines_to, mineral) / 100.0)

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

        print("\n\n")
        to_buy_by_price = defaultdict(lambda: defaultdict(int))
        for k, var in order_vars.items():
            if var.solution_value() != 0:
                to_buy_by_price[names[rounded_orders[k].item_id]][rounded_orders[k].price] += math.ceil(var.solution_value())
        to_buy_by_price = {k: dict(sorted(v.items())) for (k,v) in to_buy_by_price.items()}
        #print(dict(to_buy_by_price))
        qtys = {}
        purchases = {}
        MAX_MULTIBUY_ROUNDS = 3
        for ore, d in to_buy_by_price.items():
            # Find the minimum-price N-partition for this ore
            best_partition = min((p for p in more_itertools.partitions(d.items()) if len(p)<=MAX_MULTIBUY_ROUNDS),
                                 key=lambda p: sum([max([t[0] for t in piece]) * sum([t[1] for t in piece]) for piece in p]))
            print(f"{ore}: {best_partition}")
            qtys[ore] = [sum([t[1] for t in piece]) for piece in best_partition]
            purchases[ore] = [Purchase(price=max([t[0] for t in piece]), qty=sum([t[1] for t in piece])) for piece in best_partition]
            #print(qtys)
        print("\n\n")
        print(qtys); print(purchases);print("\n\n")
        for batch in itertools.zip_longest(*[[f"{v}x {k}" for v in q] for k,q in qtys.items()]):
            print("INPUT TO MULTIBUY:\n")
            print("\n".join(filter(None, batch)))
            print("\n\n")


if __name__ == "__main__":
    main()

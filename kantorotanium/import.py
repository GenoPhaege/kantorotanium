#!/usr/bin/env python3

import argparse
import json

from kantorotanium import Ore, Minerals

parser = argparse.ArgumentParser()
parser.add_argument('-r', '--refine-rate', default=0.8254, help="defaults to 5/5/5, ls t1 rig tatara, RX-804 implant")
args = parser.parse_args()

with open('data_files/ore.cerlestes.de.dump.json', 'r') as f:
    j = json.load(f)
    ores = []
    for o in j:
        if not o.get('types_compressed', None):
            continue
        basename = o['names'][0]
        for (name, typeid, mult) in zip(o['names'], o['types_compressed'], [1.0, 1.05, 1.1, 1.15]):
            if name != basename:
                if basename == "Dark Ochre":
                    fullname = f"{name} Ochre"
                else:
                    fullname = f"{name} {basename}"
            else:
                fullname = name

            fullname = "Compressed " + fullname
            m = (Minerals(**o['minerals']) * mult * args.refine_rate).floor()
            # print(f"{fullname}: {typeid}: {m}")
            ore = Ore(name=fullname, item_id=typeid, refines_to=m, volume=o['volume_compressed'])
            # print(ore)
            # print(Ore.schema().dumps(ore))
            # print(Ore.schema().loads(Ore.schema().dumps(ore)))
            ores.append(ore)
    print(Ore.schema().dumps(ores, many=True))

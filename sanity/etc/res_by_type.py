from classes import controller_classes, compute_classes, quantum_classes
from ubuntu_resources import resources
from pprint import pprint

cont_res = {'service': set(),
            'package': set(),
            'file': set()}

for i in controller_classes:
    temp = resources.get(i, None)
    if temp is not None:
        for i in temp.keys():
            cont_res[i].update(set(temp[i]))

pprint(cont_res)

comp_res = {'service': set(),
            'package': set(),
            'file': set()}

for i in compute_classes:
    temp = resources.get(i, None)
    if temp is not None:
        for i in temp.keys():
            comp_res[i].update(set(temp[i]))

pprint(comp_res)

quantum_res = {'service': set(),
               'package': set(),
               'file': set()}

for i in quantum_classes:
    temp = resources.get(i, None)
    if temp is not None:
        for i in temp.keys():
            quantum_res[i].update(set(temp[i]))

pprint(quantum_res)
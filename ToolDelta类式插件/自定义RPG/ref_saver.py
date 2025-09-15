import sys
from weakref import ref
from .rpg_lib.rpg_entities import PlayerEntity, MobEntity

refs: list[ref[PlayerEntity | MobEntity]] = []

# print("References cleared ==================================")

def save_ref(ls: list[PlayerEntity | MobEntity]):
    print("References cleared ==================================!!!!")
    refs.clear()
    refs.extend([ref(i) for i in ls])


def read_ref():
    return [(ii.name, sys.getrefcount(ii)) for i in refs if (ii := i())]

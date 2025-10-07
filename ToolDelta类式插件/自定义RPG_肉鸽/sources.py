import random
from .define import FortuneEvent, MobWave

if 0:
    from .frame_areas import Area, AreaType
    from . import entry

    Mob = entry.rpg.frame_mobs.Mob

fortune_plots: list[FortuneEvent] = []
mob_waves: dict[int, list[list[MobWave]]] = {}
areas: dict["AreaType", dict[int, list["Area"]]] = {}
uniqueID2areas: dict[str, "Area"] = {}
bosses: list[type["Mob"]] = []


def check_safe():
    if len(fortune_plots) < 3:
        raise ValueError("Not enough fortune plots (at least 4)")
    if sum(len(i) for i in mob_waves.values()) < 2:
        raise ValueError("Not enough mob waves (at least 2)")
    if len(areas) < 2:
        raise ValueError("Not enough areas (at least 2)")


def get_fortune_plot():
    return random.choices(fortune_plots, [i.weight for i in fortune_plots])[0]


def get_mob_waves_by_level(level: int):
    for lv in sorted(mob_waves.keys(), reverse=True):
        if level >= lv:
            m = mob_waves[lv]
            break
    else:
        m = mob_waves[min(mob_waves.keys())]
    return random.choice(m)


def pick_boss():
    return random.choice(bosses)


def add_fortune_plot(plot: FortuneEvent):
    fortune_plots.append(plot)


def add_mob_waves(level: int, waves: list[MobWave]):
    mob_waves.setdefault(level, []).append(waves)


def add_boss_mob(mob_cls: type["Mob"]):
    bosses.append(mob_cls)


def add_area(
    type: "AreaType",
    pos: tuple[int, int, int],
    safe_pos: tuple[int, int, int],
    extra_id: int = 0,
):
    from .frame_areas import Area

    areas.setdefault(type, {}).setdefault(extra_id, []).append(
        a := Area(type, pos, safe_pos, extra_id)
    )
    uniqueID2areas[a.unique_id] = a


def get_area_by_uqid(uqid: str):
    return uniqueID2areas[uqid]

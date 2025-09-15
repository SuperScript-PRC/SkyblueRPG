from enum import Enum


class Event(str, Enum):
    INTO_WATER = r"act.in_water"
    OUT_WATER = r"act.out_water"
    INTO_FIRE = r"act.in_fire"
    OUT_FIRE = r"act.out_fire"
    INTO_LAVA = r"act.in_lava"
    OUT_LAVA = r"act.out_lava"
    INTO_DEEPWATER = r"act.in_water2"
    OUT_DEEPWATER = r"act.out_water2"
    INTO_SNOW = r"act.in_snow"
    OUT_SNOW = r"act.out_snow"

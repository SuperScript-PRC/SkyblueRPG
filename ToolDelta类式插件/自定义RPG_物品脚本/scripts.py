import random
from typing import TYPE_CHECKING
from tooldelta import Player


if TYPE_CHECKING:
    from . import SlotItem, CustomRPGItemScript

SYSTEM: "CustomRPGItemScript"


def set_system(sys: "CustomRPGItemScript"):
    global SYSTEM
    SYSTEM = sys


def use_treasure_1(slot: "SlotItem", player: Player): ...


def use_cure_heart(slot: "SlotItem", player: Player):
    "export: 生命碎片"
    playerobj = SYSTEM.rpg.player_holder.get_playerinfo(player)
    playerobj.hp = int(
        min(playerobj.hp + playerobj.tmp_hp_max * 0.25, playerobj.tmp_hp_max)
    )
    return False

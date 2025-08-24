from .frame_dungeon import Dungeon
from .dungeon_utils import RandChoice, RandChoices

rainforest = Dungeon(
    "雨林涵洞",
    "§2§l雨林涵洞",
    5,
    40,
    (1030, 15, -2564),
    (1038, 15, -2565),
    (("辐化僵尸",) * 4, ("辐化僵尸",) * 2),
    (
        ("蔚蓝点", 50),
        RandChoice("蔚蓝点", 25, 0.5),
        RandChoice("蔚蓝点", 12, 0.2),
        RandChoices(
            ["混合织料_头部", "混合织料_上身", "混合织料_腿部", "混合织料_足部"],
            2,
            5,
            6,
        ),
    ),
    20,
)

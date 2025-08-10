from typing import TYPE_CHECKING

from tooldelta import Player

if TYPE_CHECKING:
    from . import CustomRPG


class PathHolder:
    def __init__(self, sys: "CustomRPG"):
        self.sys = sys

        self.material_cfg_path = self.sys.data_path / "材料物品配置"

    def format_player_basic_path(self, player: Player):
        return self.sys.data_path / "玩家基本数据" / (player.xuid + ".json")


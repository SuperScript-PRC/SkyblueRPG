import re
from typing import TYPE_CHECKING

color_replace = re.compile(r"(§[a-z0-9])")

from .rpg_lib.player_basic_data import PlayerBasic

if TYPE_CHECKING:
    from . import CustomRPG


class QQHolder:
    def __init__(self, sys: "CustomRPG"):
        self.sys = sys
        self.api = sys.GetPluginAPI("群服互通", force=False)
        self.enabled = self.api is not None
        if self.api is not None:
            self.api.add_trigger(
                ["list", "玩家列表", "在线玩家", "在线榜"],
                None,
                "查询在线玩家榜",
                self.on_query_datas,
            )
        else:
            sys.print("§群服互通未支持")

    def init(self):
        if self.enabled:
            self.api.on_player_join = lambda _: None
            self.api.on_player_leave = lambda _: None

    def on_player_join(self, playerbas: PlayerBasic):
        if self.enabled and self.sys.rpg_settings.get_player_setting(
            playerbas.player, "rpg_qq_notify"
        ):
            self.api.sendmsg(
                self.api.linked_group,
                f"[Lv.{playerbas.Level}] {playerbas.player.name} 加入了蔚蓝空域",
            )

    def on_player_leave(self, playerbas: PlayerBasic):
        if self.enabled and self.sys.rpg_settings.get_player_setting(
            playerbas.player, "rpg_qq_notify"
        ):
            self.api.sendmsg(
                self.api.linked_group,
                f"[Lv.{playerbas.Level}] {playerbas.player.name} 离开了蔚蓝空域",
            )

    def sendmsg(self, msg: str):
        if self.enabled:
            try:
                self.api.sendmsg(self.api.linked_group, msg)
            except Exception as err:
                self.sys.print(f"§6群消息发送失败: {err}")

    def on_query_datas(self, qqid: int, args: list[str]):
        outputs = ""
        for player in self.sys.game_ctrl.players:
            playerbas = self.sys.player_holder.get_player_basic(player)
            outputs += f"\n[Lv.{playerbas.Level}] {player.name}"
            if _ := self.sys.rpg_quests.player_in_plot(player):
                outputs += " （正在剧情中）"
            if target := self.sys.entity_holder.player_in_battle(player):
                dispname = color_replace.sub("", target.name)
                outputs += f" （正在与 {dispname} 战斗）"
        self.sendmsg("在线玩家列表：" + outputs)

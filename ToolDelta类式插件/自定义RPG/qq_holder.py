from typing import TYPE_CHECKING

from .rpg_lib.player_basic_data import PlayerBasic

if TYPE_CHECKING:
    from . import CustomRPG


class QQHolder:
    def __init__(self, sys: "CustomRPG"):
        self.sys = sys
        self.api = sys.GetPluginAPI("群服互通", force=False)
        self.enabled = self.api is not None

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

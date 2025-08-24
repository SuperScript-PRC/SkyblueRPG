import time
from tooldelta import Plugin, plugin_entry, TYPE_CHECKING, utils

POWER_STORAGE_MAX = 256
BACKPACK_POWER_STORAGE_MAX = 256
GETTING_MINUTES_DELAY = 8
FLUSH_SECONDS = 60 * 8


def int_time():
    return int(time.mktime(time.localtime())) // 60


class CustomRPGPower(Plugin):
    name = "自定义RPG_体力"
    author = "ToolDelta"
    version = (0, 0, 1)

    def __init__(self, frame):
        super().__init__(frame)
        self.ListenPreload(self.on_def, priority=-100)
        self.ListenActive(self.on_active)

    def on_def(self):
        self.playerdata = self.GetPluginAPI("玩家数据存储")
        self.rpg = self.GetPluginAPI("自定义RPG")
        self.backpack = self.GetPluginAPI("虚拟背包")
        self.rpg_settings = self.GetPluginAPI("自定义RPG-设置")
        if TYPE_CHECKING:
            from 前置_玩家数据存储 import PlayerDataStorer
            from 自定义RPG import CustomRPG
            from 虚拟背包 import VirtuaBackpack
            from 自定义RPG_设置 import CustomRPGSettings

            self.playerdata: PlayerDataStorer
            self.rpg: CustomRPG
            self.backpack: VirtuaBackpack
            self.rpg_settings: CustomRPGSettings
        power_item = self.backpack.get_registed_item("蔚源")
        if power_item is None:
            raise ValueError("未注册蔚源物品")
        self.power_item = str(power_item.id)

    def on_active(self):
        self.on_timer()

    @utils.timer_event(FLUSH_SECONDS, "蔚蓝RPG:体力恢复")
    def on_timer(self):
        # if True:
        #     try:
        #         player = self.game_ctrl.players.getPlayerByName("SkyblueSuper")
        #         if player is None:
        #             self.print("no master")
        #             return
        #         self.rpg.backpack_holder.addPlayerStore(
        #             player,
        #             self.rpg.item_holder.createItem(self.power_item, 1),
        #         )
        #         self.print("Successfully add power")
        #     except Exception:
        #         import traceback

        #         self.print(traceback.format_exc())
        current_time = int_time()
        for player in self.game_ctrl.players:
            last_get = self.playerdata.get_property(player, "crpg:last_get_power", None)
            if last_get is None:
                last_get = current_time - GETTING_MINUTES_DELAY
            power_getted = min(
                POWER_STORAGE_MAX, (current_time - last_get) // GETTING_MINUTES_DELAY
            )
            player_have = self.rpg.backpack_holder.getItemCount(
                player, str(self.power_item)
            )
            final_power_getted = min(
                max(0, BACKPACK_POWER_STORAGE_MAX - player_have),
                power_getted,
            )
            if final_power_getted > 0:
                try:
                    self.rpg.backpack_holder.addPlayerStore(
                        player,
                        self.rpg.item_holder.createItem(
                            self.power_item, final_power_getted
                        ),
                    )
                except Exception:
                    import traceback

                    self.print(traceback.format_exc())
                if self.rpg_settings.get_player_setting(player, "rpg_power_tips"):
                    player_have_now = player_have + final_power_getted
                    self.rpg.show_any(
                        player, "u", f"蔚源 §u+{final_power_getted} ({player_have_now})"
                    )
                self.playerdata.set_property(
                    player, "crpg:last_get_power", current_time
                )
            elif final_power_getted < 0:
                self.rpg.show_warn(player, "蔚晶时间同步错误， 正在修正 ()")
                self.playerdata.set_property(
                    player, "crpg:last_get_power", current_time
                )


entry = plugin_entry(CustomRPGPower)

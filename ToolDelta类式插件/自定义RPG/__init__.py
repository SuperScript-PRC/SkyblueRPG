import os
import json
import time
import logging
import traceback
import importlib
import threading
from typing import Callable  # noqa: UP035
from tooldelta import (
    cfg,
    game_utils,
    Plugin,
    Player,
    utils,
    plugin_entry,
    TYPE_CHECKING,
)
from tooldelta.constants import PacketIDS
from . import (
    backpack_holder,
    display_holder,
    event_apis,
    path_holder,
    player_holder,
    mob_holder,
    entity_holder,
    item_holder,
    qq_holder,
    combat_handler,
    menu_cmds,
    snowball_gui,
)
from .rpg_lib import (
    constants,
    default_cfg,
    formatter,
    utils as rpg_utils,
    scripts_loader,
)
from .rpg_lib.init_datas import init_scoreboards
from .rpg_lib.frame_effects import find_effect_class
from .rpg_lib.lib_rpgitems import (
    ItemWeapon,
    ItemRelic,
)
from .rpg_lib.frame_objects import (
    find_weapon_class,
    find_relic_class,
)
from .rpg_lib.rpg_entities import (
    PlayerEntity,
)
# 虚拟护甲/饰品词条命名方式:
# 数值: XXX
# 数值提升(0~1): XXX+加成
# 攻击力; 攻击力加成
# 防御力; 防御力加成
# 充能效率
# 暴击率; 暴击伤害
# 生命值; 生命提升
# 效果命中; 效果抵抗

importlib.reload(scripts_loader)

for module in (
    backpack_holder,
    display_holder,
    path_holder,
    player_holder,
    mob_holder,
    entity_holder,
    item_holder,
    qq_holder,
    combat_handler,
    menu_cmds,
    snowball_gui,
):
    importlib.reload(module)

RPG_Lock = threading.RLock()
LOG = True


class CustomRPG(Plugin):
    name = "自定义RPG"
    author = "SuperScript"
    version = (0, 0, 1)

    class Types:
        AllElemTypes = tuple(f"属性{i}" for i in range(1, 8))
        # WEAPON = "武器:剑"
        SUPPORT_UPGRADE = (
            constants.WeaponType.SWORD,
            constants.RelicType.HELMET,
            constants.RelicType.CHESTPLATE,
            constants.RelicType.LEGGINGS,
            constants.RelicType.BOOTS,
            constants.RelicType.A,
            constants.RelicType.B,
            constants.RelicType.C,
            constants.RelicType.D,
        )

    constants = constants
    event_apis = event_apis
    formatter = formatter

    find_effect_class = staticmethod(find_effect_class)
    find_weapon_class = staticmethod(find_weapon_class)
    find_relic_class = staticmethod(find_relic_class)
    PlayerEntity = PlayerEntity
    ItemWeapon = ItemWeapon
    ItemRelic = ItemRelic
    # 怪物死亡给予的充能值
    MOB_DEATH_CHARGE = 5

    def __init__(self, frame):
        global SYSTEM
        SYSTEM = self
        rpg_utils.set_system(self)
        super().__init__(frame)
        self.cfg, _ = cfg.get_plugin_config_and_version(
            "蔚蓝自定义RPG系统",
            default_cfg.get_basic_cfg_standard(),
            default_cfg.get_basic_cfg_default(),
            (0, 0, 1),
        )
        self.elements: dict[str, str] = self.cfg["基本属性名称"]
        self.element_colors: dict[str, str] = {
            k: v[:2] for k, v in self.cfg["基本属性名称"].items()
        }
        self.star_light = self.cfg["星级显示"]["亮"]
        self.star_dark = self.cfg["星级显示"]["暗"]
        for dirname in (
            "玩家基本数据",
            "材料物品配置",
        ):
            os.makedirs(os.path.join(self.data_path, dirname), exist_ok=True)
        self.set_logger()
        self.ListenPreload(self.on_def)
        self.ListenActive(self.on_inject, priority=-10)
        self.ListenPlayerJoin(self.on_player_join)
        self.ListenPlayerLeave(self.on_player_leave)
        self.ListenFrameExit(self.on_frame_exit)
        self.ListenPacket(PacketIDS.UpdatePlayerGameType, self.on_gamemode_change)

    def on_def(self):
        self.print("§bSkyblueRPG 加载提示: ")
        self.print("§b本插件需要配合CustomRPG.bdx 使用!")
        self.menu = self.GetPluginAPI("聊天栏菜单", (0, 0, 1))
        self.ntag = self.GetPluginAPI("头衔系统")
        self.rpg_upgrade = self.GetPluginAPI("自定义RPG-升级系统")
        self.rpg_settings = self.GetPluginAPI("自定义RPG-设置")
        self.rpg_quests = self.GetPluginAPI("自定义RPG-剧情与任务")
        self.tutor = self.GetPluginAPI("自定义RPG-教程")
        self.cb2bot = self.GetPluginAPI("Cb2Bot通信")
        self.bigchar = self.GetPluginAPI("大字替换", (0, 0, 1))
        self.snowmenu = self.GetPluginAPI("雪球菜单v3", (0, 0, 1))
        self.backpack = self.GetPluginAPI("虚拟背包")
        self.butils = self.GetPluginAPI("基本插件功能库")
        if TYPE_CHECKING:
            global SlotItem, Item
            from ..前置_聊天栏菜单 import ChatbarMenu
            from ..前置_大字替换 import BigCharReplace
            from ..前置_Cb2Bot通信 import TellrawCb2Bot
            from ..前置_基本插件功能库 import BasicFunctionLib
            from ..雪球菜单v3 import SnowMenuV3
            from ..自定义RPG_升级系统 import CustomRPGUpgrade
            from ..自定义RPG_剧情与任务 import CustomRPGPlotAndTask
            from ..自定义RPG_教程 import CustomRPGTutorial
            from ..自定义RPG_设置 import CustomRPGSettings
            from ..虚拟背包 import VirtuaBackpack
            from ..头衔系统 import Nametitle

            self.menu: ChatbarMenu
            self.ntag: Nametitle
            self.tutor: CustomRPGTutorial
            self.cb2bot: TellrawCb2Bot
            self.bigchar: BigCharReplace
            self.snowmenu: SnowMenuV3
            self.backpack: VirtuaBackpack
            self.butils: BasicFunctionLib
            self.rpg_upgrade: CustomRPGUpgrade
            self.rpg_settings: CustomRPGSettings
            self.rpg_quests: CustomRPGPlotAndTask
        SlotItem = self.backpack.SlotItem
        Item = self.backpack.Item

        self.qq_holder = qq_holder.QQHolder(self)
        self.menu_cmds = menu_cmds.MenuCommands(self)
        self.mob_holder = mob_holder.MobHolder(self)
        self.item_holder = item_holder.ItemHolder(self)
        self.path_holder = path_holder.PathHolder(self)
        self.snowmenu_gui = snowball_gui.SnowmenuGUI(self)
        self.entity_holder = entity_holder.EntityHolder(self)
        self.player_holder = player_holder.PlayerHolder(self)
        self.combat_handler = combat_handler.CombatHandler(self)
        self.display_holder = display_holder.DisplayHolder(self)
        self.backpack_holder = backpack_holder.BackpackHolder(self)
        scripts_loader.load_all(self)
        self.item_holder.init()
        self.qq_holder.init()

        # self.cb2bot.regist_message_cb(
        #     r"sr.nearest.entities", self.handle_nearest_entities_cb
        # )

    def set_logger(self):
        self.logger = logging.Logger("自定义RPG")
        self.logger.setLevel(logging.DEBUG)
        fhdl = logging.FileHandler(self.data_path / "logs.log", mode="a")
        formatter = logging.Formatter(
            "%(asctime)s - %(filename)s[ln:%(lineno)d]: %(message)s"
        )
        fhdl.setFormatter(formatter)
        self.logger.addHandler(fhdl)

    def if_kick_player(self, player: Player, sleep=False):
        if player.name.startswith("NFull"):
            self.game_ctrl.sendwocmd(f"kick {player.safe_name}")
            return True
        return False
        if (
            not player.is_op()
            and getattr(self.frame.launcher, "serverNumber") == 59141823
        ):
            if sleep:
                time.sleep(3)
            self.game_ctrl.sendwocmd(
                f"kick {player.safe_name} §a\n§7[§cError§7]\n§c抱歉， 租赁服暂未开放， 您无法获得进入资格。"
                "\n§d您可以查看我们的交流Q 750432518 获得终测资讯。\n§6最新开启时间： 08-29 10： 00， "
                + time.strftime(
                    "§b当前 %y 年 %m 月 %d日 %H： %M： %S", time.localtime()
                )
            )
            return True
        return False

    def on_inject(self):
        self.game_ctrl.sendcmd("/tag @s add sr.rpg_bot")
        self.game_ctrl.sendwocmd("/scoreboard players reset * sr:ms_rtid")
        self.frame.add_console_cmd_trigger(
            ["srinit"], None, "初始化 RPG 计分板", lambda _: init_scoreboards()
        )
        self.mob_holder.activate()
        self.entity_holder.activate()
        self.display_holder.activate()
        self.combat_handler.activate()
        self.menu_cmds.prepare_chatbarmenu()
        self.snowmenu_gui.enable_snowmenu()
        self.init_need_init_cmds()
        self.on_timer_save_playerdatas()
        self.on_inject_2nd()

    @utils.thread_func("自定义RPG:初始化")
    def on_inject_2nd(self):
        gamemode1s = [self.getPlayer(i) for i in game_utils.getTarget("@a[m=1]")]
        with RPG_Lock:
            try:
                for player in self.game_ctrl.players:
                    if self.if_kick_player(player):
                        continue
                    self.init_game_player(player, is_creative=player in gamemode1s)
            except Exception:
                self.print_err(traceback.format_exc())
            self.print_suc("玩家数据均已初始化")
        if getattr(self.frame.launcher, "serverNumber") == 59141823:
            self.show_any("@a", "a", "蔚蓝空域系统 重载成功")

    @utils.thread_func("自定义RPG:玩家进入")
    def on_player_join(self, player: Player):
        self.game_ctrl.sendwocmd("/gamerule sendcommandfeedback false")
        if self.if_kick_player(player, sleep=True):
            return
        self.load_player(player)
        if LOG:
            basic = self.player_holder.get_player_basic(player)
            self.logger.info(
                f"{player.name} inited: level={basic.Level} exp={basic.Exp}"
            )

    def on_player_leave(self, player: Player):
        if LOG and player in self.player_holder.loaded_player_basic_data:
            basic = self.player_holder.get_player_basic(player)
            self.logger.info(
                f"{player.name} unloaded: level={basic.Level} exp={basic.Exp}"
            )
        with RPG_Lock:
            self.unload_player(player)

    def on_frame_exit(self, _):
        for player in self.frame.get_players().getAllPlayers():
            self.player_holder.remove_player(player)
        self.print_suc("自定义RPG: 全部数据已保存")

    @utils.timer_event(480, "玩家数据定时保存")
    def on_timer_save_playerdatas(self):
        if not self.player_holder.initialized:
            return
        for player in self.game_ctrl.players:
            if not player.online:
                self.print_war(f"玩家不在线却保存数据: {player.name}")
            else:
                self.player_holder.save_game_player_data(player)

    def on_gamemode_change(self, pk: dict):
        game_type = pk["GameType"]
        player = self.game_ctrl.players.getPlayerByUniqueID(pk["PlayerUniqueID"])
        if player is None:
            return False
        self.player_holder.player_change_gamemode(player, game_type)
        return False

    ##### 事件初始化 #####
    @utils.thread_func("初始化 SkyblueRPG系统")
    def init_need_init_cmds(self):
        for cmd in [f'/tag "{self.game_ctrl.bot_name}" add sr.rpg_bot']:
            time.sleep(0.05)
            self.game_ctrl.sendwocmd(cmd)
        try:
            self.all_bots = game_utils.getTarget("@a[tag=sr.rpg_bot]")
        except Exception:
            self.all_bots = []
            self.print_war("无法获取 RPG 机器人列表")
        self.print_suc("SkyblueRPG 初始化成功.")

    # 初始化玩家数据
    def init_game_player(self, player: Player, init=False, is_creative=False):
        playerinf = self.player_holder.add_player(player, init, is_creative=is_creative)
        if playerinf.weapon:
            self.game_ctrl.sendwocmd(
                r"replaceitem entity @a[name="
                + player.name
                + r'] slot.hotbar 1 iron_ingot 1 755 {"item_lock":{"mode":"lock_in_slot"}}'
            )
        self.game_ctrl.sendwocmd(
            f"scoreboard players set {player.safe_name} sr:skillmode 0"
        )
        self.print_suc(f"玩家已加载: {player.name}")

    def load_player(self, player: Player):
        with RPG_Lock:
            self.init_game_player(player, init=True)
            basic = self.player_holder.get_player_basic(player)
            weapon_uuid = basic.mainhand_weapons_uuid[0]
            titl = self.ntag.get_current_nametitle(player.name)
            if titl is None:
                format_title_text = ""
            else:
                format_title_text = (
                    "§f『" + self.ntag.get_titles().get(titl, "???") + "§r§f』 "
                )
            if weapon_uuid is None:
                format_weapon_txt = ""
            else:
                weapon_item = self.backpack_holder.getItem(player, weapon_uuid)
                assert weapon_item
                format_weapon_txt = f"提着 {weapon_item.disp_name} "
            format_level_text = (
                "§7<§f"
                + self.bigchar.replaceBig("Lv.")
                + "§a"
                + self.bigchar.replaceBig(str(basic.Level))
                + "§7>"
            )
            self.show_any(
                "@a",
                "a",
                f"{format_level_text} {format_title_text}§e{player.name}§f {format_weapon_txt}§r§a上线了",
            )

    # 玩家退出处理
    def unload_player(self, player: Player):
        if basic := self.player_holder.loaded_player_basic_data.get(player):
            weapon_uuid = basic.mainhand_weapons_uuid[0]
            if weapon_uuid is None:
                format_weapon_txt = ""
            else:
                weapon_item = self.backpack_holder.getItem(player, weapon_uuid)
                if weapon_item is not None:
                    format_weapon_txt = f"提着 {weapon_item.disp_name} "
                else:
                    format_weapon_txt = "提着 ??? "
            titl = self.ntag.get_current_nametitle(player.name)
            if titl is None:
                format_title_text = ""
            else:
                format_title_text = (
                    "§f『" + self.ntag.get_titles().get(titl, "???") + "§r§f』 "
                )
            format_level_text = (
                "§7<§f"
                + self.bigchar.replaceBig("Lv.")
                + "§a"
                + self.bigchar.replaceBig(str(basic.Level))
                + "§7>"
            )
            self.show_any(
                "@a",
                "6",
                f"{format_level_text} {format_title_text}{player.name} {format_weapon_txt}§r§6下线了",
            )
        else:
            self.print_war(f"玩家 {player.name} 没有被加载到 SkyblueRPG")
        self.player_holder.remove_player(player, True)

    def show_succ(self, player: Player, msg):
        self.show_any(player, "a", msg)

    def show_warn(self, player: Player, msg):
        self.show_any(player, "6", msg)

    def show_fail(self, player: Player, msg):
        self.show_any(player, "c", msg)

    def show_inf(self, player: Player, msg):
        self.show_any(player, "7", "§f" + msg)

    def show_any(self, target: str | Player, prefix_color_id: str, msg: str):
        if isinstance(target, Player):
            target = target.safe_name
        textjson = {"rawtext": [{"text": f"§{prefix_color_id}┃ {msg}"}]}
        self.butils.sendaicmd(
            f"tellraw {target} {json.dumps(textjson, ensure_ascii=False)}"
        )

    def add_weapon_use_listener(
        self, weapon_id: str, listener: Callable[[PlayerEntity], None]
    ):
        self.combat_handler.weapon_use_listener[weapon_id] = listener

    def getPlayer(self, playername: str):
        p = self.frame.get_players().getPlayerByName(playername)
        if p is None:
            raise ValueError(f"玩家 {playername} 不存在")
        return p


entry = plugin_entry(CustomRPG, "自定义RPG")

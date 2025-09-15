import importlib
import time
import json
import math
from tooldelta import Plugin, Player, plugin_entry, TYPE_CHECKING, utils
from . import event_apis, frame_dungeon, scripts_loader

importlib.reload(frame_dungeon)
importlib.reload(scripts_loader)


class CustomRPGDungeon(Plugin):
    name = "自定义RPG-副本"
    author = "ToolDelta"
    version = (0, 0, 1)

    event_apis = event_apis

    def __init__(self, frame):
        super().__init__(frame)
        self.ListenPreload(self.on_def)
        self.ListenActive(self.on_active)
        self.ListenFrameExit(self.on_frame_exit)
        self.ListenPlayerLeave(self.on_player_leave)

    def on_def(self):
        self.chatbar = self.GetPluginAPI("聊天栏菜单")
        self.cb2bot = self.GetPluginAPI("Cb2Bot通信")
        self.intr = self.GetPluginAPI("前置-世界交互")
        self.pdata = self.GetPluginAPI("玩家数据存储")
        self.rpg = self.GetPluginAPI("自定义RPG")
        self.rpg_mobs = self.GetPluginAPI("自定义RPG-怪物刷新")
        if TYPE_CHECKING:
            global rpg_event_apis
            from 前置_聊天栏菜单 import ChatbarMenu
            from 前置_Cb2Bot通信 import TellrawCb2Bot
            from 前置_世界交互 import GameInteractive
            from 前置_玩家数据存储 import PlayerDataStorer
            from 自定义RPG import CustomRPG, event_apis as rpg_event_apis
            from 自定义RPG_怪物刷新 import CustomRPGMobSpawner

            self.chatbar: ChatbarMenu
            self.cb2bot: TellrawCb2Bot
            self.intr: GameInteractive
            self.pdata: PlayerDataStorer
            self.rpg: CustomRPG
            self.rpg_mobs: CustomRPGMobSpawner
        self.cb2bot.regist_message_cb(r"sr.dungeon.enter", self.on_player_enter_dungeon)
        self.chatbar.add_new_trigger(
            ["rdunput"],
            [],
            "放置副本开启命令方块",
            self.manual_put_trig_cb,
            op_only=True,
        )
        self.dungeons = {d.id: d for d in scripts_loader.load_all(self)}
        self.init_listen_apis()

    def on_active(self):
        self.ticking()

    def init_listen_apis(self):
        a = self.rpg.event_apis
        for evt in (
            a.PlayerAttackMobEvent,
            a.MobAttackPlayerEvent,
            a.PlayerKillMobEvent,
            a.MobKillPlayerEvent,
        ):
            self.ListenInternalBroadcast(evt.type, self.on_event)

    def manual_put_trig_cb(self, player: Player, _):
        _, x, y, z = player.getPos()
        for d in self.dungeons.values():
            cx, cy, cz = d.entrance_pos
            if math.hypot(x - cx, y - cy, z - cz) < 10:
                j = {
                    "rawtext": [
                        {"text": r"sr.dungeon.enter"},
                        {"selector": "@p"},
                        {"text": d.id},
                    ]
                }
                cmd = f"tellraw @a[tag=sr.rpg_bot] {json.dumps(j)}"
                self.intr.place_command_block(
                    self.intr.make_packet_command_block_update(
                        (cx, cy - 1, cz), cmd, need_redstone=True
                    )
                )
                self.game_ctrl.sendcmd("tp ~~20~")
                self.rpg.show_inf(player, f"已放置 {d.id}")
                return
        self.rpg.show_fail(player, "没有可放置的副本启动命令方块")

    @utils.thread_func("玩家开启副本")
    def on_player_enter_dungeon(self, args):
        if len(args) != 2:
            self.print(f"§6不合法的副本开启调用: {args}")
            return
        target, dungeon_name = args
        target = self.game_ctrl.players.getPlayerByName(target)
        if target is None:
            self.print(f"§6玩家 {target} 不存在")
            return
        d = self.dungeons.get(dungeon_name)
        if d is None:
            self.print(f"§6不支持的副本: {dungeon_name}")
            return
        d.player_enter(self, target)

    def on_player_leave(self, player: Player):
        for d in self.dungeons.values():
            d.on_player_leave(player)

    def on_frame_exit(self, _):
        for d in self.dungeons.values():
            d.exit()

    @utils.timer_event(60, "自定义RPG:副本-计时器")
    def ticking(self):
        ntime = time.time()
        for d in self.dungeons.values():
            d.ticking(ntime)

    def on_event(self, evt):
        for d in self.dungeons.values():
            d.on_event(evt.data)

    def query_in_dungeon_players(self):
        return {
            d: d.stage.player
            for d in self.dungeons.values()
            if d.stage is not None and d.stage.player
        }


entry = plugin_entry(CustomRPGDungeon, "自定义RPG-副本")

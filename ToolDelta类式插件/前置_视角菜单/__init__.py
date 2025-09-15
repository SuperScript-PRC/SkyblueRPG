import threading
import enum
from importlib import reload
from tooldelta import Plugin, utils, Print, TYPE_CHECKING, Player, plugin_entry

from typing import Callable  # noqa
from . import mcfuncs

reload(mcfuncs)

headaction_counter: dict[Player, int] = {}


class HeadAction(str, enum.Enum):
    UP = "headmove.up"
    DOWN = "headmove.down"
    LEFT = "headmove.left"
    RIGHT = "headmove.right"
    PLAYER_LEFT = "player.left"
    SNOWBALL_EXIT = "snowball.menu.use"


# 管理玩家的视角操作
class HeadActionEnv:
    def __init__(self, sys: "SightRotation", target: Player):
        self.sys = sys
        self.target = target

    def __enter__(self):
        if headaction_counter.setdefault(self.target, 0) == 0:
            self.sys.game_ctrl.sendwocmd(
                f"tag {self.target.getSelector()} add bagdetect"
            )
        headaction_counter[self.target] += 1
        return self

    def __exit__(self, _, _2, _3):
        if self.target not in headaction_counter:
            return
        headaction_counter[self.target] -= 1
        if headaction_counter[self.target] == 0:
            self.sys.game_ctrl.sendwocmd(
                f"tag {self.target.getSelector()} remove bagdetect"
            )
            del headaction_counter[self.target]

    def wait_next_action(self, text: str | Callable[[], str], show_delay=0.5):
        return self.sys.wait_next_action(self.target, text, show_delay)


class SightRotation(Plugin):
    author = "SuperScript"
    name = "前置-视角菜单"
    version = (0, 0, 1)
    HeadAction = HeadAction

    def __init__(self, frame):
        super().__init__(frame)
        self.ListenPreload(self.on_def)
        self.ListenPlayerJoin(self.on_player_join)
        self.ListenPlayerLeave(self.on_player_leave)

    def on_def(self):
        self.game_intr = self.GetPluginAPI("前置-世界交互")
        cb2bot = self.GetPluginAPI("Cb2Bot通信")
        if TYPE_CHECKING:
            from 前置_世界交互 import GameInteractive
            from 前置_Cb2Bot通信 import TellrawCb2Bot

            self.game_intr = self.get_typecheck_plugin_api(GameInteractive)
            cb2bot = self.get_typecheck_plugin_api(TellrawCb2Bot)
        self.event_cbs: dict[Player, Callable[[str], None]] = {}
        cb2bot.regist_message_cb(
            HeadAction.UP,
            lambda msgs: self.handle_cbdat([HeadAction.UP, *msgs]),
            2,
        )
        cb2bot.regist_message_cb(
            HeadAction.DOWN,
            lambda msgs: self.handle_cbdat([HeadAction.DOWN, *msgs]),
            2,
        )
        cb2bot.regist_message_cb(
            HeadAction.LEFT,
            lambda msgs: self.handle_cbdat([HeadAction.LEFT, *msgs]),
            2,
        )
        cb2bot.regist_message_cb(
            HeadAction.RIGHT,
            lambda msgs: self.handle_cbdat([HeadAction.RIGHT, *msgs]),
            2,
        )
        cb2bot.regist_message_cb(
            HeadAction.SNOWBALL_EXIT, self.handle_interrupt, priority=2
        )
        self.frame.add_console_cmd_trigger(
            ["sight-menu"], None, "查看视角菜单相关帮助", self.cons_menu
        )

    def on_player_join(self, player: Player):
        self.game_ctrl.sendwocmd(f"/tag {player.getSelector()} remove bagdetect")

    def on_player_leave(self, player: Player):
        if player in self.event_cbs.keys():
            self.event_cbs[player](HeadAction.PLAYER_LEFT)

    def cons_menu(self, args: list[str]):
        if len(args) == 0:
            Print.clean_print("§e 控制台菜单项帮助:")
            Print.clean_print(
                " <x> <y> <z> §7在指定坐标(最好是指令区)放置本插件必须的检测命令方块组"
            )
        else:
            if len(args) != 3:
                Print.clean_print("§c参数数量错误")
            else:
                x = utils.try_int(args[0])
                y = utils.try_int(args[1])
                z = utils.try_int(args[2])
                if x is None or y is None or z is None:
                    Print.clean_print("§c坐标格式错误")
                    return
                self.put_command_block_at(mcfuncs.DETECT_HEAD, x, y, z, 0)
                Print.clean_print("§7放置命令方块任务正在进行..")

    @utils.thread_func("放置插件命令方块")
    def put_command_block_at(self, cmd_seq: list[str], x: int, y: int, z: int, delay=0):
        f = False
        for cmd in cmd_seq:
            x += 1
            pck = self.game_intr.make_packet_command_block_update(
                (x, y, z),
                cmd,
                2 if f else 1,
                tick_delay=delay if not f else 0,
            )
            f = True
            self.game_intr.place_command_block(pck, 5, 0.1)
        Print.clean_print("§a放置命令方块任务已完成.")

    def wait_next_action(self, player: Player, text: str | Callable[[], str], show_delay=0.5):
        ret: list[str | None] = [None]
        evt = threading.Event()

        def _cb(action: str):
            ret[0] = action
            evt.set()

        self.event_cbs[player] = _cb
        while ret[0] is None:
            evt.clear()
            if callable(text):
                player.setActionbar(text())
            else:
                player.setActionbar(text)
            evt.wait(show_delay)
        return ret[0]

    def handle_cbdat(self, dats: list[str]):
        if len(dats) < 2:
            return False
        p = self.frame.get_players().getPlayerByName(dats[1])
        if p is None:
            raise ValueError(f"玩家不在线: {dats[1]}")
        if p not in self.event_cbs.keys():
            return False
        if dats[0] not in HeadAction:
            return False
        self.event_cbs[p](dats[0])
        del self.event_cbs[p]
        return True

    def handle_interrupt(self, dats: list[str]):
        player = self.frame.get_players().getPlayerByName(dats[0])
        if player is None:
            raise ValueError(f"玩家不在线: {dats[1]}")
        if player not in self.event_cbs.keys():
            return False
        self.event_cbs[player](HeadAction.SNOWBALL_EXIT)
        del self.event_cbs[player]
        return True

    def create_env(self, target: Player):
        return HeadActionEnv(self, target)


entry = plugin_entry(SightRotation, "视角菜单")

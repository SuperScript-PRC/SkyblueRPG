from typing import Any, Protocol
from importlib import reload
from collections.abc import Callable
from tooldelta import Plugin, Player, utils, TYPE_CHECKING, Print, plugin_entry

from .tutorials import pve

reload(pve)


class TutorialInterface(Protocol):
    tag_name: str
    show_name: str

    @staticmethod
    def entry(sys: "CustomRPGTutorial", player: Player): ...


available_tutorials: dict[str, TutorialInterface] = {
    "pve": pve,
}

# tellraw @a[tag=sr.rpg_bot] {"rawtext":[{"text":"sr.tutorial"},{"selector":"@p"},{"text":"pve"}]}


class TutorialEnv:
    def __init__(self, sys: "CustomRPGTutorial", player: Player):
        self._current_thread = None
        self.sys = sys
        self.player = player
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback): ...

    def show(self, msg: str):
        self.sys.show(self.player, msg)

    def show_by_plot(self, msg: str):
        self.sys.rpg_plot.utils_plot_box_print(self.player.name, "教学", msg, 16, 0)
        self.show(msg)

    def show_by_plot_async(self, msg: str):
        if self._current_thread:
            self._current_thread.stop()
        self._current_thread = utils.ToolDeltaThread(
            self.show_by_plot,
            args=(msg,),
        )

    def wait_check_point(
        self,
        checkpoint_name: str,
        extra_data_checker: Callable[[Any], bool] = lambda _: True,
    ):
        self.sys.wait_check_point(self.player, checkpoint_name, extra_data_checker)

    def ok(self):
        pass
        # self.sys.rpg.show_succ()
        # self.sys.rpg.rpg_upgrade.add_player_exp(self.playername, 10)


def get_last_color(text: str):
    if "§" in text:
        color_index = text.rindex("§")
        return text[color_index : color_index + 2]
    else:
        return text


def cut_long_str(text: str, length: int = 40) -> list[str]:
    new_length = 0
    cached_str = ""
    outputs = []
    for char in text:
        cached_str += char
        if char.isascii():
            new_length += 1
        else:
            new_length += 2
        if char != "§" and new_length > length:
            outputs.append(cached_str)
            cached_str = ""
            new_length = 0
    outputs.append(cached_str)
    return outputs


class CustomRPGTutorial(Plugin):
    name = "自定义RPG-教程系统"
    author = "SuperScript"
    version = (0, 0, 1)

    def __init__(self, frame):
        super().__init__(frame)
        self.make_data_path()
        self.checkpoint_cbs: dict[str, Callable[[bool], None]] = {}
        self.ListenPreload(self.on_def)

    def on_def(self):
        self.rpg = self.GetPluginAPI("自定义RPG")
        self.rpg_plot = self.GetPluginAPI("自定义RPG-剧情与任务")
        self.cb2bot = self.GetPluginAPI("Cb2Bot通信")
        if TYPE_CHECKING:
            from 自定义RPG import CustomRPG
            from 自定义RPG_剧情与任务 import CustomRPGPlotAndTask
            from 前置_Cb2Bot通信 import TellrawCb2Bot

            self.rpg = self.get_typecheck_plugin_api(CustomRPG)
            self.rpg_plot = self.get_typecheck_plugin_api(CustomRPGPlotAndTask)
            self.cb2bot = self.get_typecheck_plugin_api(TellrawCb2Bot)
        utils.tempjson.load_and_read(
            self.format_data_path("records.json"),
            need_file_exists=False,
            default={},
        )
        self.cb2bot.regist_message_cb("sr.tutorial", self.executor)

    def wait_check_point(
        self,
        player: Player,
        checkpoint_name: str,
        extra_data_checker: Callable[[Any], bool] = lambda _: True,
    ):
        if self.checkpoint_cbs.get(player.name + ":" + checkpoint_name) is not None:
            raise ValueError("不能同时进行两个 wait_check_point")
        while 1:
            getter, setter = utils.create_result_cb(bool)
            self.checkpoint_cbs[player.name + ":" + checkpoint_name] = setter
            g = getter(10)
            del self.checkpoint_cbs[player.name + ":" + checkpoint_name]
            if player.name not in self.game_ctrl.allplayers:
                raise SystemExit
            if g and extra_data_checker(g):
                break

    def check_point(self, checkpoint_name: str, player: Player, extra_data: Any = None):
        self._check_point_cb_call(checkpoint_name, player.name)

    def check_point_and_record(self, checkpoint_name: str, player: Player):
        self.check_point(checkpoint_name, player)
        self.record_taughter(checkpoint_name, player)

    def _check_point_cb_call(self, checkpoint_name: str, playername: str):
        if cb := self.checkpoint_cbs.get(playername + ":" + checkpoint_name):
            cb(True)

    # def check_point_easy(self, checkpoint_name: str, playername: str) -> bool:
    #     res = checkpoint_name in self.load_taught_records().get(
    #         self.xuidm.get_xuid_by_name(playername), []
    #     )
    #     self.record_taughter(checkpoint_name, playername)
    #     return res

    def executor(self, args: list[str]):
        playername, tutorial_tagname = args
        tutorial_module = available_tutorials.get(tutorial_tagname)
        if tutorial_module:
            tutorial_module.entry(self, self.rpg.getPlayer(playername))
        else:
            Print.print_war(f"未知的教程: {tutorial_tagname}")

    def load_tutorial_records(self) -> dict[str, list[str]]:
        return utils.tempjson.read(self.format_data_path("records.json"))

    def record_taughter(self, checkpoint_name: str, player: Player):
        o = self.load_tutorial_records()
        t_xuid = player.xuid
        o.setdefault(t_xuid, [])
        o1 = o[t_xuid]
        if checkpoint_name in o1:
            Print.print_war(
                f"玩家 {player.name} ({t_xuid}) 重复记录: {checkpoint_name}"
            )
        else:
            o1.append(checkpoint_name)
        o[t_xuid] = o1
        utils.tempjson.write(self.format_data_path("records.json"), o)

    def show(self, player: Player, msg: str):
        last_color = ""
        msg = "§a" + msg
        for text in cut_long_str(msg):
            text = text.replace("§r", "§r§a")
            self.rpg.show_any(player.name, "2", last_color + text)
            last_color = get_last_color(text)

    def create_tutorial_env(self, player: Player):
        return TutorialEnv(self, player)


entry = plugin_entry(CustomRPGTutorial, "自定义RPG-教程")

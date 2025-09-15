import importlib
import time
from tooldelta import Plugin, Player, TYPE_CHECKING, plugin_entry, utils
from . import frame, sign_waiter
from . import block_and_go, push_chest

importlib.reload(frame)
importlib.reload(block_and_go)
importlib.reload(push_chest)

all_games = (block_and_go.BlockAndGo, push_chest.PushChest)


class CustomRPGGames(Plugin):
    name = "自定义RPG-小游戏"

    def __init__(self, frame):
        super().__init__(frame)
        self.game_records_path = self.data_path / "关卡记录"
        self.game_records_path.mkdir(exist_ok=True)
        self.ListenPreload(self.on_def)
        self.ListenActive(self.on_active)

    def on_def(self):
        self.cb2bot = self.GetPluginAPI("Cb2Bot通信")
        self.intr = self.GetPluginAPI("前置-世界交互")
        self.bigchar = self.GetPluginAPI("大字替换")
        self.chatbar = self.GetPluginAPI("聊天栏菜单")
        self.rpg = self.GetPluginAPI("自定义RPG")
        self.snowmenu = self.GetPluginAPI("雪球菜单v3")
        if TYPE_CHECKING:
            from ..前置_Cb2Bot通信 import TellrawCb2Bot
            from ..前置_世界交互 import GameInteractive
            from ..前置_大字替换 import BigCharReplace
            from ..前置_聊天栏菜单 import ChatbarMenu
            from ..自定义RPG import CustomRPG
            from ..雪球菜单v3 import SnowMenuV3

            self.cb2bot: TellrawCb2Bot
            self.intr: GameInteractive
            self.bigchar: BigCharReplace
            self.chatbar: ChatbarMenu
            self.rpg: CustomRPG
            self.snowmenu: SnowMenuV3
        self.online_games = {cls.name: cls(self) for cls in all_games}

    def on_active(self):
        self.check_timeout()

    def record_finished_level(
        self, player: Player, game: frame.MiniGame, level_name: str, metadata=None
    ):
        old = utils.tempjson.load_and_read(
            self.game_records_path / (player.xuid + ".json"),
            need_file_exists=False,
            default={},
        )
        old.setdefault(game.name, {}).setdefault(level_name, metadata)
        utils.tempjson.load_and_write(
            self.game_records_path / (player.xuid + ".json"),
            old,
            need_file_exists=False,
        )

    def get_levels_finished(self, player: Player, game: frame.MiniGame) -> dict:
        "-> dict[level_name, metadata]"
        return utils.tempjson.load_and_read(
            self.game_records_path / (player.xuid + ".json"),
            need_file_exists=False,
            default={},
        ).get(game.name, {})

    def add_score(self, player: Player, game: frame.MiniGame, score: int) -> int:
        old = utils.tempjson.load_and_read(
            self.game_records_path / (player.xuid + ".json"),
            need_file_exists=False,
            default={},
        )
        score_data = old.get("score_datas", {})
        score_data.setdefault(game.name, 0)
        score_data[game.name] += score
        old["score_datas"] = score_data
        utils.tempjson.load_and_write(
            self.game_records_path / (player.xuid + ".json"),
            old,
            need_file_exists=False,
        )
        return score_data[game.name]

    def get_score(self, player: Player, game: frame.MiniGame) -> int:
        return (
            utils.tempjson.load_and_read(
                self.game_records_path / (player.xuid + ".json"),
                need_file_exists=False,
                default={},
            )
            .get("score_datas", {})
            .get(game.name, 0)
        )

    @utils.timer_event(30, "自定义RPG-小游戏:检查超时")
    @utils.thread_func("自定义RPG-小游戏:检查超时")
    def check_timeout(self):
        nowtime = time.time()
        for game in self.online_games.values():
            game.check_timeout(nowtime)


entry = plugin_entry(CustomRPGGames)
sign_waiter.set_system(entry)

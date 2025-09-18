import time
import json
from tooldelta import Player, utils
from typing import TypeVar, Generic
from . import event_apis, util_funcs

GameT = TypeVar("GameT", bound="MiniGame")
StageT = TypeVar("StageT", bound="MiniGameStage")

if 0:
    from . import CustomRPGGames


class MiniGame(Generic[StageT]):
    def __init_subclass__(
        cls,
        data_name: str = "unknown_game",
        name: str = "未知小游戏",
        disp_name: str = "未知小游戏",
        description: str = "...",
        coins: int = 1,
        min_player_num: int = 1,
        max_player_num: int = 1,
        winning_gets: int = 0,
        final_win_give_items: tuple[str, ...] = ("吉米克的谜题馈赠",),
    ):
        super().__init_subclass__()
        cls.data_name = data_name
        cls.name = name
        cls.disp_name = disp_name
        cls.description = description
        cls.coins = coins
        cls.min_player_num = min_player_num
        cls.max_player_num = max_player_num
        cls.winning_gets = winning_gets
        cls.final_win_give_items = final_win_give_items

    def __init__(self, sys: "CustomRPGGames"):
        self.sys = sys
        self.stages: dict[str, StageT] = {}
        self.data_path = self.sys.data_path / self.data_name
        self.level_data_path = self.data_path / "关卡数据"
        self.data_path.mkdir(exist_ok=True)
        self.level_data_path.mkdir(exist_ok=True)
        self.init()

    def init(self):
        pass

    def check_running(self, stage_id: str, start_player: Player) -> bool:
        if self.stages.get(stage_id) is not None:
            start_player.setTitle("§c游戏正在开启中")
            return True
        else:
            return False

    def set_stage(self, stage_id: str, stage: StageT | None):
        if stage is not None:
            self.stages[stage_id] = stage
        else:
            del self.stages[stage_id]

    def get_stage_by_id(self, id: str) -> StageT | None:
        return self.stages.get(id)

    def get_player_by_name(self, playername: str):
        return self.sys.game_ctrl.players.getPlayerByName(playername)

    def _finish(self, stage: StageT, win=False):
        self.set_stage(stage.stage_id, None)

    def get_leveldata_path(self, level_name: str):
        return self.level_data_path / (level_name + ".json")

    def read_leveldata_raw(self, level_name: str):
        path = self.get_leveldata_path(level_name)
        if not path.is_file():
            return None
        return utils.tempjson.load_and_read(path)

    def write_leveldata_raw(self, level_name: str, data: dict):
        with open(self.get_leveldata_path(level_name), "w", encoding="utf-8") as f:
            json.dump(
                data,
                f,
                ensure_ascii=False,
            )

    def get_leveldata_files(self):
        return [i for i in self.level_data_path.iterdir() if i.name.endswith(".json")]

    def get_player_finished_level_datas(self, player: Player):
        return self.sys.get_levels_finished(player, self)

    def get_player_unfinished_levelnames(
        self, player: Player, all_levels: list[str] | None = None, tips=True
    ):
        level_names = (
            all_levels
            or [i.name.removesuffix(".json") for i in self.get_leveldata_files()]
        ).copy()
        level_finished = self.get_player_finished_level_datas(player).keys()
        for name in level_finished:
            if name in level_names:
                level_names.remove(name)
        if not level_names:
            player.setTitle("§a", "§b你已完成该场地所有关卡")
        return level_names

    def check_timeout(
        self,
        now_time: float,
        game_timeout_time: float = 600,
        operation_timeout_time: float = 300,
    ):
        for stage in self.stages.copy().values():
            if stage.since_start(now_time) > game_timeout_time:
                stage.on_timeout(mode=0)
                stage.finish()
            elif stage.since_last_operation(now_time) > operation_timeout_time:
                stage.on_timeout(mode=1)
                stage.finish()

    def display_and_wait(
        self,
        player: Player,
        stage_id: str,
        levels: list[str],
        available_levels: list[str],
    ):
        opening = self.get_stage_by_id(stage_id) is not None
        finished_levels = len(levels) - len(available_levels)
        level_finished_disp = (
            f"§a{self.sys.bigchar.replaceBig(str(finished_levels))} §7/ §2{len(levels)}"
        )

        def _disp_cb(_, page: int):
            if page > 1:
                return None
            descs = "\n     ".join(util_funcs.cut_string(self.description, 60))
            return (
                f"§e✰ §a吉米克的谜题 - {self.disp_name} §r§f[{'§c进行中' if opening else '§3等待开启'}§f] §e✰\n"
                + f"  §7[§fi§7] {descs}\n"
                + f"  §7[§2#§7] §2已完成 {level_finished_disp} 关\n"
                + f"  §7[§b♢§7] §f开启需 §b{self.sys.bigchar.replaceBig(str(self.coins))}谜鉴币\n"
                + f"  §7[§c☻§7] §c游玩人数 {f'{self.min_player_num}人' if self.min_player_num == self.max_player_num else f'{self.min_player_num}~{self.max_player_num}人'}\n"
                + "§f选择功能：\n"
                + (
                    "§b❖ 开启谜题  §7|  ❖ 离开"
                    if page == 0
                    else "§7❖ 开启谜题  |§b  ❖ 离开"
                )
            )

        with utils.ChatbarLock(player.name):
            resp = self.sys.snowmenu.simple_select(player, _disp_cb)
            if resp is None:
                return False
            elif resp == 1:
                return False
            else:
                res = self.sys.rpg.backpack_holder.getItemCount(player, "谜鉴币")
                if res < self.coins:
                    self.sys.rpg.show_fail(player, "拥有的谜鉴币不足")
                    return False
                self.sys.rpg.backpack_holder.clearItem(player, "谜鉴币", self.coins)
            return True


class MiniGameStage(Generic[GameT]):
    min_player_num: int = 1
    max_player_num: int = 1

    def __init__(
        self,
        game: GameT,
        stage_id: str,
        level_names: list[str],
        players: list[Player],
        startgame_pos: tuple[int, int, int],
        ctrl_pos: tuple[int, int, int],
    ):
        self.main = game
        self.sys = game.sys
        self.stage_id = stage_id
        self.next_levels = level_names
        self.current_level = self.next_levels.pop(0)
        self.players = players
        self.startgame_pos = startgame_pos
        self.ctrl_pos = ctrl_pos
        self._last_operation_time = time.time()
        self.exited = False
        self.player_scores: dict[Player, int] = {}

    def activate(self, from_prev_level=False):
        """
        超类方法, 主要用于传送玩家到控制区
        """
        self._start_time = time.time()
        self.sys.BroadcastEvent(
            event_apis.StageStart(self, from_prev_level).to_broadcast()
        )
        x, y, z = self.ctrl_pos
        for player in self.players:
            self.sys.game_ctrl.sendwocmd(
                f"camera {player.safe_name} fade time 0.5 0 0.5 color 0 0 0"
            )
        time.sleep(0.5)
        for player in self.players:
            self.sys.game_ctrl.sendwocmd(f"tp {player.safe_name} {x} {y} {z}")
        self.exited = False

    def finish(self, win=False):
        """
        超类方法主要用于过关/失败/游戏退出处理
        覆写方法主要用于舞台清场处理

        覆写本方法时, 请在覆写的方法最后调用 `super().finish()`

        Args:
            win (bool, optional): 是否获胜
        """
        self.exited = True
        weijing = self.sys.rpg.item_holder.createItem("蔚晶", self.main.winning_gets)
        if win:
            for player in self.players:
                self.sys.record_finished_level(player, self.main, self.current_level)
                if weijing.count > 0:
                    self.sys.rpg.backpack_holder.giveItem(player, weijing.copy())
                if score := self.player_scores.get(player):
                    now_score = self.sys.add_score(player, self.main, score)
                    self.sys.rpg.show_any(
                        player, "b", f"§7{self.main.name}： §b+§f{score} §bPTS."
                    )
                    self.sys.rpg.show_any(player, "b", f"HI SCORE： §f{now_score:06d}")
                    del self.player_scores[player]
            if len(self.next_levels) > 0:
                self.current_level = self.next_levels.pop(0)
                self.on_next_level()
                self.sys.BroadcastEvent(
                    event_apis.StageFinished(self, True).to_broadcast()
                )
                self.activate(from_prev_level=True)
                return
            else:
                self.sys.BroadcastEvent(
                    event_apis.StageFinished(self, False).to_broadcast()
                )
        self._final_finish(win)

    def on_next_level(self):
        """
        超类方法, 可覆写为关卡切换处理
        """

    def on_timeout(self, mode=0):
        """
        超类方法, 可覆写为超时处理, 这之后会调用 finish() 方法

        Args:
            mode (int, optional): 超时模式. 游戏时间超时=0, 操作时间超时=1
        """
        for player in self.players:
            self.sys.rpg.show_fail(player, "游戏已超时， 请重开游戏")

    def _final_finish(self, win=False):
        x, y, z = self.startgame_pos
        time.sleep(0.5)
        for player in self.players:
            self.sys.game_ctrl.sendwocmd(
                f"camera {player.safe_name} fade time 0.5 0.5 0.5 color 0 0 0"
            )
            if win:
                player.setTitle("§a恭喜！", "§f✓ §b当前谜域的关卡已全部完成")
        time.sleep(0.5)
        if win:
            items_to_give = [
                self.sys.rpg.item_holder.createItem(item_id)
                for item_id in self.main.final_win_give_items
            ]
        else:
            items_to_give = []
        for player in self.players:
            for item in items_to_give:
                self.sys.rpg.backpack_holder.giveItem(player, item.copy())
            self.sys.game_ctrl.sendwocmd(f"tp {player.safe_name} {x} {y} {z}")
        self.main._finish(self, win=win)

    def update(self):
        self._last_operation_time = time.time()

    def since_last_operation(self, now_time: float):
        return now_time - self._last_operation_time

    def since_start(self, now_time: float):
        return now_time - self._start_time

    def add_score(self, player: Player, score: int):
        self.player_scores[player] = self.player_scores.get(player, 0) + score

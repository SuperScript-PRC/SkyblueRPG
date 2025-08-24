import importlib
from tooldelta import (
    Plugin,
    plugin_entry,
    Player,
    InternalBroadcast,
    TYPE_CHECKING,
)
from . import tasks, task_frame

importlib.reload(task_frame)
importlib.reload(tasks)

from .task_frame import (
    DailyTasksManager,
    BaseEvent,
    get_task_classes_from_module,
)


class CustomRPGDailyTask(Plugin):
    name = "自定义RPG-每日任务"

    def __init__(self, frame):
        super().__init__(frame)
        self._require_listen_events: set[type[BaseEvent]] = set()
        self.online_task_detetors: dict[Player, DailyTasksManager] = {}
        self.ListenPreload(self.on_def)
        self.ListenPlayerJoin(self.on_player_join)
        self.ListenPlayerLeave(self.on_player_leave)
        self.ListenActive(self.on_active)
        self.ListenFrameExit(self.on_frame_exit)
        self.inited = False

    def on_def(self):
        self.cb2bot = self.GetPluginAPI("Cb2Bot通信")
        self.rpg = self.GetPluginAPI("自定义RPG")
        self.rpg_upgrade = self.GetPluginAPI("自定义RPG-升级系统")
        self.rpg_repair = self.GetPluginAPI("自定义RPG-修补系统")
        self.rpg_fishing = self.GetPluginAPI("自定义RPG-钓鱼")
        self.rpg_food = self.GetPluginAPI("自定义RPG-食品")
        self.rpg_source = self.GetPluginAPI("自定义RPG-资源")
        self.rpg_plot = self.GetPluginAPI("自定义RPG-剧情与任务")
        if TYPE_CHECKING:
            from 前置_Cb2Bot通信 import TellrawCb2Bot
            from 自定义RPG import CustomRPG
            from 自定义RPG_升级系统 import CustomRPGUpgrade
            from 自定义RPG_修补系统 import CustomRPGRepair
            from 自定义RPG_钓鱼 import CustomRPGFishing
            from 自定义RPG_食品 import CustomRPGFood
            from 自定义RPG_资源 import CustomRPGSource
            from 自定义RPG_剧情与任务 import CustomRPGPlotAndTask

            self.cb2bot: TellrawCb2Bot
            self.rpg: CustomRPG
            self.rpg_upgrade: CustomRPGUpgrade
            self.rpg_repair: CustomRPGRepair
            self.rpg_fishing: CustomRPGFishing
            self.rpg_food: CustomRPGFood
            self.rpg_source: CustomRPGSource
            self.rpg_plot: CustomRPGPlotAndTask
        self.tasks = get_task_classes_from_module(self, tasks)
        self.cb2bot.regist_message_cb("sr.dailytasks.query", self.on_list_tasks)
        self.print(f"§a加载了 {len(self.tasks)} 个每日任务点")
        self.init_broadcast_listeners()
        self.inited = True
        # tellraw @a[tag=sr.rpg_bot] {"rawtext":[{"text":"sr.dailytasks.query"},{"selector":"@p"}]}

    def on_active(self):
        for player in self.game_ctrl.players:
            self.on_player_join(player)

    def on_player_join(self, player: Player):
        self.online_task_detetors[player] = DailyTasksManager(self, player)

    def on_player_leave(self, player: Player):
        if player in self.online_task_detetors:
            self.online_task_detetors.pop(player).unload()
        else:
            self.print(f"§6玩家 {player.name} 每日任务数据缺失")

    def on_frame_exit(self, _):
        if not self.inited:
            return
        for player in self.game_ctrl.players:
            self.online_task_detetors[player].unload()
        self.print("已保存每日任务数据")

    def init_broadcast_listeners(self):
        for evt in self._require_listen_events:
            self.ListenInternalBroadcast(evt.type, self.on_event)

    def require_listen(self, event: type[BaseEvent]):
        self._require_listen_events.add(event)

    def on_event(self, event: InternalBroadcast):
        for v in self.online_task_detetors.values():
            v.recv_event(event)

    def format_player_data_path(self, player: Player):
        return self.data_path / (player.xuid + ".json")

    def on_list_tasks(self, datas: list[str]):
        playername = datas[0]
        if player := self.game_ctrl.players.getPlayerByName(playername):
            self.online_task_detetors[player].display()


entry = plugin_entry(CustomRPGDailyTask)

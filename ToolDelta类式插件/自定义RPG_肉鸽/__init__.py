from importlib import reload
from weakref import WeakKeyDictionary
from tooldelta import Plugin, plugin_entry, Player, TYPE_CHECKING, utils
from . import frame_areas, frame_levels, frame_rogue, rogue, scripts_loader, storage

reload(frame_areas)
reload(frame_levels)
reload(frame_rogue)
reload(rogue)
reload(scripts_loader)


class CustomRPGRogue(Plugin):
    name = "自定义RPG-肉鸽"
    author = "SuperScript"
    version = (0, 0, 1)

    def __init__(self, frame):
        super().__init__(frame)
        self.storages: WeakKeyDictionary[Player, storage.RogueStatusStorage] = (
            WeakKeyDictionary()
        )
        self.storage_path = self.data_path / "玩家记录"
        self.rank_path = self.data_path / "排行.json"
        self.load_area_locks()
        self.ListenPreload(self.on_def, priority=-10)
        self.ListenActive(self.on_active, priority=-100)
        self.ListenPlayerJoin(self.on_player_join, priority=-100)
        self.ListenPlayerLeave(self.on_player_leave, priority=100)

    def on_def(self):
        self.rpg = self.GetPluginAPI("自定义RPG")
        self.rpg_plots = self.GetPluginAPI("自定义RPG-剧情与任务")
        self.rpg_mob = self.GetPluginAPI("自定义RPG-怪物刷新")
        self.backpack = self.GetPluginAPI("虚拟背包")
        self.snowmenu = self.GetPluginAPI("雪球菜单v3")
        self.sight = self.GetPluginAPI("视角菜单")
        self.cb2bot = self.GetPluginAPI("Cb2Bot通信")
        self.behavior = self.GetPluginAPI("行为监测")
        self.pdstore = self.GetPluginAPI("玩家数据存储")
        self.menu = self.GetPluginAPI("聊天栏菜单")
        self.xuidmgr = self.GetPluginAPI("XUID获取")
        self.bigchar = self.GetPluginAPI("大字替换", (0, 0, 1))
        if TYPE_CHECKING:
            global SlotItem, Item
            from ..自定义RPG import CustomRPG
            from ..自定义RPG_剧情与任务 import CustomRPGPlotAndTask
            from ..自定义RPG_怪物刷新 import CustomRPGMobSpawner
            from ..虚拟背包 import VirtuaBackpack, SlotItem, Item
            from ..雪球菜单v3 import SnowMenuV3
            from ..前置_视角菜单 import SightRotation
            from ..前置_Cb2Bot通信 import TellrawCb2Bot
            from ..前置_行为监测 import ActionListener
            from ..前置_玩家数据存储 import PlayerDataStorer
            from ..前置_聊天栏菜单 import ChatbarMenu
            from ..前置_玩家XUID获取 import XUIDGetter
            from ..前置_大字替换 import BigCharReplace

            self.rpg: CustomRPG
            self.rpg_plots: CustomRPGPlotAndTask
            self.rpg_mob: CustomRPGMobSpawner
            self.backpack: VirtuaBackpack
            self.snowmenu: SnowMenuV3
            self.sight: SightRotation
            self.cb2bot: TellrawCb2Bot
            self.behavior: ActionListener
            self.pdstore: PlayerDataStorer
            self.menu: ChatbarMenu
            self.xuidmgr: XUIDGetter
            self.bigchar: BigCharReplace
        rogue_obj = scripts_loader.load_all(self)
        self.executor = rogue.Executor(self, rogue_obj)

    def on_active(self):
        self.load_area_locks()
        for player in self.game_ctrl.players:
            self.executor._on_player_init(player)

    def on_player_join(self, player: Player):
        self.executor._on_player_init(player)

    def on_player_leave(self, player: Player):
        self.executor._on_player_exit(player)

    def on_frame_exit(self, _):
        for stor in self.storages.values():
            stor.save()
        self.dump_area_locks()

    def get_storage(self, player: Player):
        if player not in self.storages:
            self.storages[player] = self.read_storage(player)
        return self.storages[player]

    def set_storage(self, player: Player, storage: storage.RogueStatusStorage):
        self.storages[player] = storage

    def read_storage(self, player: Player):
        r = utils.tempjson.load_and_read(
            self.storage_path / f"{player.xuid}.json",
            need_file_exists=False,
            default=None,
        )
        if r is None:
            return storage.RogueStatusStorage.default(self, player)
        else:
            return storage.RogueStatusStorage.from_dict(self, player, r)

    def write_storage(self, storage: storage.RogueStatusStorage):
        utils.tempjson.load_and_write(
            self.storage_path / f"{storage.player.xuid}.json",
            storage.to_dict(),
            need_file_exists=False,
        )

    def load_area_locks(self):
        frame_areas.load_locks(
            utils.tempjson.load_and_read(
                self.data_path / "area_locks.json", need_file_exists=False, default=[]
            )
        )

    def dump_area_locks(self):
        utils.tempjson.load_and_write(
            self.data_path / "area_locks.json",
            frame_areas.dump_locks(),
            need_file_exists=False,
        )

    def read_ranks(self):
        ranks = utils.tempjson.load_and_read(
            self.rank_path, need_file_exists=False, default={}
        )
        return {k: storage.RogueRecord.from_dict(k, i) for k, i in ranks.items()}

    def write_ranks(self, ranks: list[storage.RogueRecord]):
        utils.tempjson.load_and_write(
            self.rank_path,
            {i.xuid: i.to_dict() for i in ranks},
            need_file_exists=False,
        )

    def get_rank(self, player: Player):
        return self.read_ranks().get(player.xuid)

    def update_rank(self, s: storage.RogueStatusStorage):
        all_ranks = self.read_ranks()
        all_ranks[s.player.xuid], nrs = s.to_record().update_old(
            all_ranks.get(s.player.xuid)
        )
        self.write_ranks(list(all_ranks.values()))
        return nrs


entry = plugin_entry(CustomRPGRogue)

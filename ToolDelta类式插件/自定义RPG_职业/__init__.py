import os
import sys
import importlib
from tooldelta import (
    Player,
    Plugin,
    utils,
    TYPE_CHECKING,
    plugin_entry,
)
from tooldelta.constants import PacketIDS

from . import event_apis, job_frame, jobs_carry_man, jobs_mail_deliver, jobs_cleaner

tmpjs = utils.tempjson
JOB_LIMIT = 3
JOB_LEVEL: dict[int, list[str]] = {}
CREDIT_MIN = -100
CREDIT_MAX = 100
jobs: list[type[job_frame.Job]] = []


def register_job(job: type[job_frame.Job]):
    jobs.append(job)
    JOB_LEVEL.setdefault(job.level, [])
    JOB_LEVEL[job.level].append(job.name)


if jobs_cleaner in sys.modules.values():
    importlib.reload(jobs_cleaner)
if jobs_mail_deliver in sys.modules.values():
    importlib.reload(jobs_mail_deliver)
if jobs_carry_man in sys.modules.values():
    importlib.reload(jobs_carry_man)
register_job(jobs_cleaner.Cleaner)
register_job(jobs_carry_man.CarryMan)
register_job(jobs_mail_deliver.MailDeliver)


class CustomRPGJobs(Plugin):
    name = "自定义RPG-打工职业"
    author = "SuperScript"
    version = (0, 0, 1)

    event_apis = event_apis

    def __init__(self, frame):
        super().__init__(frame)
        self.pkt_funcs: dict[int, list] = {}
        self.menu_cbs = {}
        self.inject_funcs = []
        self.loaded_jobs: dict[str, dict] = {}
        self.ListenPreload(self.on_def)
        self.ListenActive(self.on_inject)
        self.ListenPlayerJoin(self.on_player_join)
        self.ListenPlayerLeave(self.on_player_leave)
        self.ListenFrameExit(self.on_frame_exit)
        self.ListenPacket([PacketIDS.BlockEvent], self.on_pkts)

    def on_def(self):
        self.rpg = self.GetPluginAPI("自定义RPG")
        self.rpg_quests = self.GetPluginAPI("自定义RPG-剧情与任务")
        self.snowmenu = self.GetPluginAPI("雪球菜单v3")
        self.chatbar = self.GetPluginAPI("聊天栏菜单")
        self.backpack = self.GetPluginAPI("虚拟背包")
        self.cb2bot = self.GetPluginAPI("Cb2Bot通信")
        self.intr = self.GetPluginAPI("前置-世界交互")
        if TYPE_CHECKING:
            from 自定义RPG import CustomRPG
            from 自定义RPG_剧情与任务 import CustomRPGPlotAndTask
            from 雪球菜单v3 import SnowMenuV3
            from 前置_聊天栏菜单 import ChatbarMenu
            from 虚拟背包 import VirtuaBackpack
            from 前置_Cb2Bot通信 import TellrawCb2Bot
            from 前置_世界交互 import GameInteractive

            self.rpg: CustomRPG
            self.rpg_quests: CustomRPGPlotAndTask
            self.snowmenu: SnowMenuV3
            self.chatbar: ChatbarMenu
            self.backpack: VirtuaBackpack
            self.cb2bot: TellrawCb2Bot
            self.intr: GameInteractive
        os.makedirs(self.format_data_path("玩家数据"), exist_ok=True)
        self.MultiPage = MultiPage = self.snowmenu.MultiPage
        self.loaded_job_menus: dict[str, MultiPage] = {}
        self.jobs: dict[str, job_frame.Job] = {job.name: job(self) for job in jobs}
        self.cb2bot.regist_message_cb(r"career.madd", self.on_career_add)

    def _page_cb(self, player: Player, page: int):
        outputs = "§6职业选择"
        pl = list(self.get_curr_jobs_datas(player).keys())
        avali_menus = self.loaded_job_menus
        if len(pl) == 0:
            return outputs + "\n§7  无可选职业..."
        if page >= len(pl):
            return None
        for i, job_name in enumerate(pl):
            outputs += (
                "\n  §"
                + ("b" if i == page else "7")
                + f"✏ {job_name} [{self._get_job_exp(player, job_name)}] "
                + ("" if avali_menus.get(job_name) else " （不可查看）")
            )
        credit = self.get_credit(player)
        credit_lv = (
            "§c很差"
            if credit < -50
            else "§c差"
            if credit < 0
            else "§b一般"
            if credit < 20
            else "§a良好"
            if credit < 60
            else "§a非常好"
        )
        outputs += f"\n§a信誉分： §f{credit:.1f} §f（{credit_lv}§f）"
        return outputs

    def _page_ok(self, player: Player, page: int):
        pl = list(self.get_curr_jobs_datas(player).keys())
        if len(pl) == 0:
            return True
        section = pl[page]
        if menu := self.loaded_job_menus.get(section):
            return menu, 0
        else:
            return True

    def on_player_join(self, player: Player):
        r = tmpjs.load_and_read(
            self.format_data_path("玩家数据", player.xuid + ".json"),
            need_file_exists=False,
            default={"curr_jobs": {}, "avali_jobs": [], "credit": 0},
        )
        self.loaded_jobs[player.name] = r

    def on_inject(self):
        mainpage = self.snowmenu.MultiPage(
            "sr.job", self._page_cb, self._page_ok, parent_page_id="default"
        )
        self.chatbar.add_new_trigger(
            ["job"], ..., "开发者设置职业参数", self.handle_menu
        )
        for player in self.frame.get_players().getAllPlayers():
            self.on_player_join(player)
        for func in self.inject_funcs:
            func()
        self.add_menu_cb("set", self.op_set_job)
        self.snowmenu.register_main_page(mainpage, "职业面板")
        self.snowmenu.add_page(mainpage)

    def on_player_leave(self, player: Player):
        if player.name in self.loaded_jobs:
            self.save(player)
            del self.loaded_jobs[player.name]

    def on_frame_exit(self, _):
        for playername in self.loaded_jobs.keys():
            self.save(self.rpg.getPlayer(playername))

    def on_career_add(self, args):
        playername, job = args
        player = self.game_ctrl.players.getPlayerByName(playername)
        assert player
        self.plot_add_job(player, job)

    def on_pkts(self, pk):
        for func in self.pkt_funcs.get(26, []):
            func(pk)
        return False

    def handle_menu(self, player: Player, args: tuple[str]):
        if len(args) < 1:
            self.rpg.show_fail(player, "无效调用: 无效参数")
            return
        cb = self.menu_cbs.get(args[0])
        if cb is None:
            self.rpg.show_fail(player, "无效调用: 无效子功能")
        else:
            cb(player, args[1:])

    def plot_add_job(self, player: Player, job: str):
        if len(self.get_curr_jobs_datas(player)) > JOB_LIMIT:
            self.rpg.show_fail(player, "错误： 职业数达到上限")
            return
        self.add_job(player, job)

    def add_listen_pkt(self, pkID: int, func):
        self.pkt_funcs.setdefault(pkID, [])
        self.pkt_funcs[pkID].append(func)

    def op_set_job(self, player: Player, args: list[str]):
        if not player.is_op():
            self.rpg.show_fail(player, "暂无权限")
            return
        if len(args) != 1:
            self.rpg.show_fail(player, "无效参数")
            return
        job_name = args[0]
        if job_name not in (job.name for job in jobs):
            self.rpg.show_fail(player, "无效职业名")
            return
        self.loaded_jobs[player.name]["curr_jobs"][job_name] = self.init_job_data(
            job_name
        )
        self.rpg.show_any(player, "d", f"设置职业： §e{job_name}")

    def player_change_job(self, player: Player):
        jobdata = self.loaded_jobs[player.name]

        def _show_cb(_, page: int): ...

    def add_credit(self, player: Player, credit: float):
        o = self.loaded_jobs[player.name]["credit"]
        self.loaded_jobs[player.name]["credit"] = min(o + credit, CREDIT_MAX)

    def reduce_credit(self, player: Player, credit: float):
        o = self.loaded_jobs[player.name]["credit"]
        self.loaded_jobs[player.name]["credit"] = max(o - credit, CREDIT_MIN)

    def get_credit(self, player: Player) -> int:
        return self.loaded_jobs[player.name].get("credit", 0)

    def add_inject_func(self, func):
        self.inject_funcs.append(func)

    def add_menu_cb(self, trigger: str, cb):
        self.menu_cbs[trigger] = cb

    def add_job(self, player: Player, job_name: str, showto: bool = True):
        self.loaded_jobs[player.name]["curr_jobs"][job_name] = self.init_job_data(
            job_name
        )
        if showto:
            self.rpg.show_any(player, "d", f"获得新职业： §e{job_name}")

    def has_job(self, player: Player, job_name: str):
        return job_name in self.get_curr_jobs_datas(player).keys()

    def save(self, player: Player):
        tmpjs.load_and_write(
            path := self.format_data_path("玩家数据", player.xuid + ".json"),
            self.loaded_jobs[player.name],
            need_file_exists=False,
        )
        tmpjs.flush(path)

    def init_job_data(self, job_name: str):
        return {"exp": 0, "metadata": {}, "skills": 0}

    def get_job_level(self, job_name: str):
        for job_level, jobs in JOB_LEVEL.items():
            if job_name in jobs:
                return job_level
        raise ValueError(f"职业不存在: {job_name}")

    def get_curr_jobs_datas(self, player: Player):
        return self.loaded_jobs[player.name]["curr_jobs"]

    def _add_job_exp(
        self, player: Player, job_name: str, adexp: int, showto_player: bool = True
    ):
        if (job_pt := self.loaded_jobs[player.name]["curr_jobs"].get(job_name)) is None:
            raise ValueError(f"当前职业未加载在 {player.name}: {job_name}")
        job_pt["exp"] += adexp
        if showto_player:
            curr_exp = job_pt["exp"]
            self.rpg.show_any(
                player, "b", f"{job_name} §f的经验 +{adexp} §7({curr_exp})"
            )
        self.save(player)

    def _read_job_datas(self, player: Player, job_name: str):
        return self.get_curr_jobs_datas(player).get(job_name, {}).get("metadata", {})

    def _write_job_datas(self, player: Player, job_name: str, kv: dict):
        self.loaded_jobs[player.name]["curr_jobs"][job_name]["metadata"].update(kv)

    def _get_job_exp(self, player: Player, job_name: str):
        return self.get_curr_jobs_datas(player).get(job_name, {}).get("exp", 0)

    def _get_job_skillpoints(self, player: Player, job_name: str):
        return self.get_curr_jobs_datas(player)[job_name].get("skills", 0)

    def _set_job_skillpoints(self, player: Player, job_name: str, skill_points: int):
        self.get_curr_jobs_datas(player)[job_name]["skills"] = skill_points

    def _get_skill_tree_value(self, player: Player, job_name: str, skill_name: str):
        return self._read_job_datas(player, job_name).get("stree", {}).get(skill_name)

    def _add_skill_tree_value(self, player: Player, job_name: str, skill_name: str):
        (d := self._read_job_datas(player, job_name)).setdefault("stree", {})
        d["stree"].setdefault(skill_name, {})
        d["stree"][skill_name] += 1
        self._write_job_datas(player, job_name, d)


entry = plugin_entry(CustomRPGJobs, "自定义RPG-职业")

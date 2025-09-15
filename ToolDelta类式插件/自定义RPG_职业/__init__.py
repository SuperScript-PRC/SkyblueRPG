import os
import sys
import logging
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

JOB_LIMIT = 3
JOB_LEVEL: dict[int, list[str]] = {}
jobs: list[type[job_frame.Job]] = []
LOG = True


def register_job(job: type[job_frame.Job]):
    jobs.append(job)
    JOB_LEVEL.setdefault(job.level, [])
    JOB_LEVEL[job.level].append(job.name)


if job_frame in sys.modules.values():
    importlib.reload(job_frame)
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

    LOG = LOG
    LOG_EXP_ADD = False
    LOG_CREDIT_ADD = False

    def __init__(self, frame):
        super().__init__(frame)
        self.pkt_funcs: dict[int, list] = {}
        self.menu_cbs = {}
        self.inject_funcs = []
        # self.loaded_jobdatas: dict[Player, dict] = {}
        self.set_logger()
        self.ListenPreload(self.on_def)
        self.ListenActive(self.on_inject)
        self.ListenPlayerJoin(self.on_player_join)
        self.ListenPlayerLeave(self.on_player_leave)
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
        self.cb2bot.regist_message_cb(r"career.madd", self.on_job_add)
        # self.cb2bot.regist_message_cb(r"career.200", self.force_up_to_200)

    def set_logger(self):
        self.logger = logging.Logger("自定义RPG:职业系统")
        self.logger.setLevel(logging.DEBUG)
        fhdl = logging.FileHandler(self.data_path / "logs.log", mode="a")
        formatter = logging.Formatter(
            "%(asctime)s - %(filename)s[ln:%(lineno)d]: %(message)s"
        )
        fhdl.setFormatter(formatter)
        self.logger.addHandler(fhdl)

    def on_player_join(self, player: Player, reloaded=False):
        # logger debug
        if LOG and not reloaded:
            jobs = self.get_jobs(player)
            if jobs == []:
                return
            jobs_data_msgs = ", ".join(
                f"name:{i.name} exp:{i.get_exp(player)}" for i in jobs
            )
            self.logger.info(
                f"{player.name} inited with {jobs_data_msgs}, credits={self.get_credit(player)}"
            )

    def on_player_leave(self, player: Player, reloaded=False):
        if LOG and not reloaded:
            jobs = self.get_jobs(player)
            if jobs == []:
                return
            jobs_data_msgs = ", ".join(
                f"name:{i.name} exp:{i.get_exp(player)}" for i in jobs
            )
            self.logger.info(
                f"{player.name} unloaded with {jobs_data_msgs}, credits={self.get_credit(player)}"
            )

    def on_inject(self):
        def _page_ok(player: Player, page: int):
            pl = list(self.get_jobs_datas(player).keys())
            if len(pl) == 0:
                return True
            section = pl[page]
            if menu := self.loaded_job_menus.get(section):
                return menu, 0
            else:
                return True

        def _page_cb(player: Player, page: int):
            outputs = "§6职业选择"
            pl = list(self.get_jobs_datas(player).keys())
            avali_menus = self.loaded_job_menus
            if len(pl) == 0:
                return (
                    outputs + "\n  §7[§6!§7] 暂无可选职业" + "\n§7" * 7 + "\n§c低头退出"
                )
            if page >= len(pl):
                return None
            for i, job_name in enumerate(pl):
                job = self.jobs[job_name]
                exp_format = (
                    f"Lv.{job.get_level(player)}： "
                    f"{job.get_exp(player)}/"
                    f"{job.get_upgrade_exp(player)}"
                )
                outputs += (
                    "\n  §"
                    + ("b" if i == page else "7")
                    + f"✏ {job_name} [{exp_format}] "
                    + ("" if avali_menus.get(job_name) else " （无内容）")
                )
            for _ in range(8 - len(pl)):
                outputs += "\n§7"
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
            outputs += f"\n§a信誉分： §f{credit:.1f} §f（{credit_lv}§f）\n§a抬头选择 §7| §c低头退出"
            return outputs

        mainpage = self.snowmenu.MultiPage(
            "sr.job", _page_cb, _page_ok, parent_page_id="default"
        )
        self.chatbar.add_new_trigger(
            ["job"], ..., "开发者设置职业参数", self.handle_menu, op_only=True
        )
        self.add_menu_cb("addexp", self.on_force_add_job_exp)
        for player in self.frame.get_players().getAllPlayers():
            self.on_player_join(player, reloaded=True)
        for func in self.inject_funcs:
            func()
        self.add_menu_cb("set", self.op_set_job)
        self.snowmenu.register_main_page(mainpage, "职业面板")
        self.snowmenu.add_page(mainpage)

    def on_force_add_job_exp(self, player: Player, args):
        args = list(args)
        if len(args) not in (2, 3):
            self.rpg.show_fail(player, "参数错误")
            return
        utils.fill_list_index(args, ["", 0, player.name])
        job_name, exp, target = args
        if (target := self.game_ctrl.players.getPlayerByName(target)) is None:
            self.rpg.show_fail(player, "玩家不存在")
            return
        if not self.has_job(target, job_name):
            self.rpg.show_fail(player, f"{target.name} 没有这个职业")
            return
        if (exp := utils.try_int(exp)) is None:
            self.rpg.show_fail(player, "请输入正确的经验值")
            return
        job = self.jobs[job_name]
        job.add_exp(target, exp)
        self.rpg.show_succ(
            player, f"给玩家 {target.name} 添加职业 {job_name} 的经验 {exp} 成功"
        )

    def on_job_add(self, args):
        playername, job = args
        player = self.game_ctrl.players.getPlayerByName(playername)
        assert player
        self.plot_add_job(player, job)

    def on_pkts(self, pk):
        for func in self.pkt_funcs.get(26, []):
            func(pk)
        return False

    def handle_menu(self, player: Player, args: tuple[str, ...]):
        if len(args) < 1:
            self.rpg.show_fail(player, "无效调用: 无效参数")
            return
        cb = self.menu_cbs.get(args[0])
        if cb is None:
            self.rpg.show_fail(player, "无效调用: 无效子功能")
        else:
            cb(player, args[1:])

    def plot_add_job(self, player: Player, job: str):
        if len(self.get_jobs_datas(player)) > JOB_LIMIT:
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
        o = self.read_datas(player)
        o["curr_jobs"][job_name] = self.init_job_data(job_name)
        self.write_datas(player, o)
        self.rpg.show_any(player, "d", f"设置职业： §e{job_name}")

    def player_change_job(self, player: Player):
        jobdata = self.read_datas(player)

        def _show_cb(_, page: int): ...

    def get_credit(self, player: Player) -> float:
        return self.read_datas(player).get("credit", 0)

    def set_credit(self, player: Player, credit: float):
        o = self.read_datas(player)
        o["credit"] = credit
        self.write_datas(player, o)

    def add_inject_func(self, func):
        self.inject_funcs.append(func)

    def add_menu_cb(self, trigger: str, cb):
        self.menu_cbs[trigger] = cb

    def add_job(self, player: Player, job_name: str, showto: bool = True):
        if len(self.get_jobs(player)) >= 2 and not player.is_op():
            self.rpg.show_fail(player, "职业数量过多")
            return
        o = self.read_datas(player)
        o["curr_jobs"][job_name] = self.init_job_data(job_name)
        self.write_datas(player, o)
        if showto:
            self.rpg.show_any(player, "d", f"获得新职业： §e{job_name}")

    def has_job(self, player: Player, job_name: str):
        return job_name in self.get_jobs_datas(player).keys()

    def get_job_employees(self, job_name: str):
        return [i for i in self.game_ctrl.players if self.has_job(i, job_name)]

    def init_job_data(self, job_name: str):
        return {"exp": 0, "metadata": {}, "skills": 0}

    def get_level_job(self, job_name: str):
        for job_level, jobs in JOB_LEVEL.items():
            if job_name in jobs:
                return job_level
        raise ValueError(f"职业不存在: {job_name}")

    def get_jobs_datas(self, player: Player):
        return self.read_datas(player)["curr_jobs"]

    def get_job_datas(self, player: Player, job_name: str):
        # print(player.name, "GetJobDatas", self.get_jobs_datas(player)[job_name])
        return self.get_jobs_datas(player)[job_name]

    def write_job_datas(self, player: Player, job_name: str, job_datas: dict):
        # print(player.name, "SetJobDatas", job_datas)
        o = self.read_datas(player)
        o["curr_jobs"][job_name] = job_datas
        self.write_datas(player, o)

    def get_jobs(self, player: Player):
        jobs_name = self.get_jobs_datas(player).keys()
        return [self.jobs[name] for name in jobs_name]

    # def force_up_to_200(self, args):
    #     target = args[0]
    #     player = self.game_ctrl.players.getPlayerByName(target)
    #     if player is None:
    #         return
    #     for job in self.get_jobs(player):
    #         job.add_exp(player, max(0, 200 - job.get_exp(player)))

    def read_datas(self, player: Player) -> dict:
        return utils.tempjson.load_and_read(
            self.format_data_path("玩家数据", player.xuid + ".json"),
            need_file_exists=False,
            default={"curr_jobs": {}, "avali_jobs": [], "credit": 0},
        )

    def write_datas(self, player: Player, job_datas: dict):
        utils.tempjson.load_and_write(
            self.format_data_path("玩家数据", player.xuid + ".json"),
            job_datas,
            need_file_exists=False,
        )


entry = plugin_entry(CustomRPGJobs, "自定义RPG-职业")

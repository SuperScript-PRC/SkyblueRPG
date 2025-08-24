import json
import time
import threading
from tooldelta import Plugin, Player, game_utils, utils, TYPE_CHECKING, plugin_entry

_lock_instances: dict[tuple[int, int, int], threading.Lock] = {}
_global_lock = threading.Lock()


class PositionLock:
    def __init__(self, x: int, y: int, z: int):
        self.args = (x, y, z)
        self.lock_instance = None

    def __enter__(self):
        with _global_lock:
            if self.args in _lock_instances:
                self.lock_instance = _lock_instances[self.args]
            else:
                self.lock_instance = threading.Lock()
                _lock_instances[self.args] = self.lock_instance
        self.lock_instance.acquire()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.lock_instance:
            self.lock_instance.release()


class CustomRPGMobSpawner(Plugin):
    name = "自定义RPG-刷怪系统"
    author = "SuperScript"
    version = (0, 0, 1)


    def __init__(self, frame):
        super().__init__(frame)
        self.ListenPreload(self.on_def)
        self.ListenActive(self.on_inject)

    def on_def(self):
        self.rpg = self.GetPluginAPI("自定义RPG")
        self.intr = self.GetPluginAPI("前置-世界交互")
        self.cb2bot = self.GetPluginAPI("Cb2Bot通信")
        self.chatbar = self.GetPluginAPI("聊天栏菜单")
        if TYPE_CHECKING:
            from 自定义RPG import CustomRPG
            from 前置_世界交互 import GameInteractive
            from 前置_Cb2Bot通信 import TellrawCb2Bot
            from 前置_聊天栏菜单 import ChatbarMenu

            self.rpg: CustomRPG
            self.intr: GameInteractive
            self.cb2bot: TellrawCb2Bot
            self.chatbar: ChatbarMenu
        self.cb2bot.regist_message_cb("sr.mob.refresh", self.handler)
        self._iota = 0

    def on_inject(self):
        self.chatbar.add_new_trigger(
            [".mspawn"],
            [
                ("生物标签名", str, None),
                ("数量", int, 5),
                ("冷却分钟", int, 5),
                ("有效范围", int, 25),
            ],
            "设置怪物生成点",
            self.on_place_spawner,
            True,
        )
        self.chatbar.add_new_trigger(
            [".msummon"],
            [("生物标签名", str, None)],
            "手动生成生物",
            self.manual_put_mob,
            True,
        )
        # self.frame.add_console_cmd_trigger(
        #     ["srm-sync"],
        #     None,
        #     "同步 sr:mob_spawn 到 sr:mob_timer 计分板",
        #     lambda _: self.manual_sync(),
        # )
        self.on_timer()

    def manual_put_mob(self, player: Player, args: tuple):
        mob_tagname = args[0]
        mob_cls = self.rpg.mob_holder.get_mob_class(mob_tagname)
        if mob_cls is None:
            player.show("§c无效的标签名")
            return
        dim, x, y, z = player.getPos()
        self.summon(mob_tagname, x, y, z)
        player.show("§a生成生物完成")

    def summon(self, mob_tagname: str, x: float, y: float, z: float):
        with PositionLock(int(x), int(y), int(z)):
            mob_runtimeid = self.rpg.mob_holder.make_runtimeid()
            if (mob_cls := self.rpg.mob_holder.get_mob_class(mob_tagname)) is None:
                raise ValueError(f"无效的怪物标签名: {mob_tagname}")
            if mob_cls.model_id.startswith("mystructure:"):
                res = self.game_ctrl.sendwscmd_with_resp(
                    f"structure load {mob_cls.model_id} {x} {y} {z}"
                )
            else:
                res = self.game_ctrl.sendwscmd_with_resp(
                    f"summon {mob_cls.model_id} {x} {y} {z}"
                )
            if res.SuccessCount == 0:
                raise ValueError(
                    f"无法生成 {mob_tagname}({mob_cls.model_id}) 在 {x, y, z}: {res.OutputMessages[0].Message}"
                )
            self.game_ctrl.sendwocmd(
                f"scoreboard players set @e[x={x},y={y},z={z},r=1,c=1,tag=!sr.mob,type={mob_cls.model_id}] sr:ms_type {mob_cls.type_id}"
            )
            # self.game_ctrl.sendwocmd(
            #     f"effect @e[type={mob_cls.model_id},x={x},y={y},z={z},c=1] resistance 99999 100 true"
            # )
            self.game_ctrl.sendwocmd(
                f"tag @e[x={x},y={y},z={z},c=1,tag=!sr.mob,type={mob_cls.model_id}] add sr.mob_uninited"
            )
            self.game_ctrl.sendwocmd(
                f"scoreboard players set @e[x={x},y={y},z={z},c=1,tag=!sr.mob,type={mob_cls.model_id}] sr:ms_rtid {mob_runtimeid}"
            )
        return mob_runtimeid

    def summon_by_type(self, mob_type: int, x: float, y: float, z: float):
        self.summon(
            self.rpg.mob_holder.find_mob_class_by_id(mob_type).tag_name, x, y, z
        )

    @utils.timer_event(60, "更新数据化世界时间")
    def on_timer(self):
        self._on_timer()

    @utils.thread_func("怪物刷新时间检测")
    def _on_timer(self):
        res = self.game_ctrl.sendwscmd_with_resp(
            f"scoreboard players set timer sr:mob_timer {self.world_time}"
        )
        if res.SuccessCount == 0:
            self.game_ctrl.say_to("@a", "§6怪物刷新： 时间更新失败")

    def on_place_spawner(self, player: Player, args: tuple):
        dim, x, y, z = player.getPos()
        x, y, z = int(x), int(y), int(z)
        if args[0] == "r":
            if not game_utils.isCmdSuccess(
                f"scoreboard players test p_{x}_{y}_{z} sr:mob_timer 0"
            ):
                player.show(f"§6这里 ({x}, {y}, {z}) 不是生物生成点")
                return
            self.game_ctrl.sendwocmd(
                f"scoreboard players set p_{x}_{y}_{z} sr:mob_timer 0"
            )
            player.show("§a已重置刷新时间.")
            return
        elif args[0] == "c":
            resp = self.game_ctrl.sendwscmd_with_resp(
                f"scoreboard players test p_{x}_{y}_{z} sr:mob_timer 0"
            )
            if not resp.SuccessCount:
                player.show(f"§6这里 ({x}, {y}, {z}) 不是生物生成点")
                return
            t = int(resp.OutputMessages[0].Parameters[0])
            player.show(f"§a当前冷却时长到 {int(t - self.world_time)} 分钟后")
            return
        tagname: str = args[0]
        count: int = args[1]
        cdmin: int = args[2]
        lmtrange: int = args[3]
        if cdmin < 0:
            player.show("§c无效冷却数值")
            return
        if (mobcfg := self.rpg.mob_holder.get_mob_class(tagname)) is None:
            player.show("§c无效怪物标签名")
            return
        if count <= 0:
            player.show("§c无效数量")
            return
        if lmtrange <= 0:
            player.show("§c无效范围")
            return
        player.show("§b设置刷怪点中...")
        self.place_cbs_at(
            (x, y, z), mobcfg.type_id, mobcfg.model_id, lmtrange, count, cdmin
        )
        player.show("§a设置完成")

    def place_cbs_at(
        self,
        xyz: tuple[int, int, int],
        mob_type: int,
        mob_id: str,
        lmt_range: int,
        lmt_num: int,
        cdmin: int,
    ):
        x, y, z = xyz
        scb_id = f"p_{x}_{y}_{z}"
        self.iota = 1
        # 刷怪部分
        tellraw_text = json.dumps(
            {
                "rawtext": [
                    {"text": "sr.mob.refresh"},
                    {
                        "text": f"{x}, {y}, {z}, {mob_id}, {mob_type}, {lmt_num}, {cdmin}"
                    },
                    {"score": {"name": scb_id, "objective": "sr:mob_spawn"}},
                ]
            },
            ensure_ascii=False,
        )
        self.intr.place_command_block(
            self.intr.make_packet_command_block_update(
                (x, y - self.iota, z),
                f"scoreboard players set {scb_id} sr:mob_spawn 0",
                mode=1,
                tick_delay=1200,
            )
        )
        self.intr.place_command_block(
            self.intr.make_packet_command_block_update(
                (x, y - self.iota, z),
                f"execute as @e[r={lmt_range + 5},type={mob_id}] run scoreboard players add {scb_id} sr:mob_spawn 1",
                mode=2,
                conditional=False,
            )
        )
        self.intr.place_command_block(
            self.intr.make_packet_command_block_update(
                (x, y - self.iota, z),
                f"execute as @p[tag=sr.rpg_bot] unless score {scb_id} sr:mob_timer > timer sr:mob_timer run scoreboard players test {scb_id} sr:mob_spawn 0 {lmt_num - 1}",
                mode=2,
                conditional=False,
            )
        )
        self.intr.place_command_block(
            self.intr.make_packet_command_block_update(
                (x, y - self.iota, z),
                f"tellraw @a[tag=sr.rpg_bot] {tellraw_text}",
                mode=2,
                conditional=True,
            )
        )
        # self.intr.place_command_block(
        #     self.intr.make_packet_command_block_update(
        #         (x, y - self.iota, z),
        #         f"scoreboard players add {scb_id} sr:mob_timer 0",
        #         mode=2,
        #         conditional=False,
        #         tick_delay=0,
        #     )
        # )
        # 拉怪
        self.intr.place_command_block(
            self.intr.make_packet_command_block_update(
                (x, y - self.iota, z),
                f"tp @e[y=~{self.iota},r={lmt_range + 5},rm={lmt_range},type={mob_id}] ~~{self.iota}~",
                mode=1,
                conditional=False,
                tick_delay=10,
            )
        )
        self.game_ctrl.sendwocmd(f"setblock {x} {y - self.iota} {z} air")
        self.game_ctrl.sendwocmd(f"setblock {x} {y - self.iota} {z} air")
        self.game_ctrl.sendwocmd(f"setblock {x} {y - self.iota} {z} glowstone")
        self.game_ctrl.sendwocmd(
            f"scoreboard players set p_{x}_{y}_{z} sr:mob_timer {self.world_time + 1}"
        )
        self.game_ctrl.sendcmd("tp ~~20~")

    @utils.thread_func("自定义RPG:怪物生成")
    def handler(self, msgs: list[str]):
        x, y, z, mob_id, mob_type, lmt_num, cd_min = msgs[0].split(", ")
        now_exists_num = int(msgs[1])
        x, y, z, lmt_num, cd_min = int(x), int(y), int(z), int(lmt_num), int(cd_min)
        if lmt_num - now_exists_num <= 0:
            return
        for _ in range(lmt_num - now_exists_num):
            try:
                self.summon_by_type(int(mob_type), x, y, z)
            except ValueError as err:
                self.print(f"§6怪物生成失败: {err}")
            # self.game_ctrl.sendwocmd(f"summon {mob_id} {x} {y} {z}")
        # self.rpg.show_inf("@a", f"SPAWN at {x, y, z}: {mob_id}")
        # time.sleep(0.5)
        # self.game_ctrl.sendwocmd(
        #     f"scoreboard players set @e[x={x},y={y},z={z},r=2,type={mob_id}] sr:ms_type {mob_type}"
        # )
        # self.game_ctrl.sendwocmd(
        #     f"effect @e[type={mob_id},x={x},y={y},z={z}] resistance 99999 100 true"
        # )
        self.game_ctrl.sendwocmd(
            f"scoreboard players set p_{x}_{y}_{z} sr:mob_timer {self.world_time + cd_min}"
        )
        # self.game_ctrl.sendwocmd(
        #     f"tag @e[x={x},y={y},z={z},r=3,type={mob_id}] add sr.mob_uninited"
        # )

    # def sync_func(self, pk: dict):
    #     print("Syncing")
    #     self.try_sync(pk)
    #     return False

    # def try_sync(self, pk: dict):
    #     if not os.path.isfile("sr_mob_spawn_sync"):
    #         self.sync_func = lambda pk: False
    #         return
    #     for entry in pk["Entries"]:
    #         objective_name = entry["ObjectiveName"]
    #         if objective_name == "sr:mob_spawn":
    #             self.sync_mob_spawn_to_timer(pk)
    #             self.sync_func = lambda pk: False
    #             break
    #         elif objective_name != "":
    #             self.print(f"Not match: {objective_name}")

    # def sync_mob_spawn_to_timer(self, pk: dict):
    #     for entry in pk["Entries"]:
    #         if entry["ObjectiveName"]:
    #             continue
    #         entry_name = entry["DisplayName"]
    #         self.game_ctrl.sendwocmd(
    #             f"scoreboard players set {entry_name} sr:mob_timer 0"
    #         )
    #         self.print(f"Sync: {entry_name}")
    #     self.print("Sync Done")
    #     os.remove("sr_mob_spawn_sync")

    # def reboot_and_sync(self, _):
    #     @utils.thread_func("自定义RPG-怪物刷新:重启系统", thread_level=utils.ToolDeltaThread.SYSTEM)
    #     def restarter():
    #         self.frame.system_exit("normal")
    #         os._exit(0)
    #     self.game_ctrl.sendwocmd("scoreboard objectives setdisplay sidebar sr:mob_spawn")
    #     self.print("即将重启")
    #     open("sr_mob_spawn_sync", "wb").close()
    #     restarter()

    def manual_sync(self):
        resp = self.game_ctrl.sendwscmd_with_resp("scoreboard players list *")
        for o in resp.OutputMessages:
            for p in o.Parameters:
                if p.startswith("p_"):
                    self.print(f"正在同步 {p}")
                    res = self.game_ctrl.sendwscmd_with_resp(
                        f"scoreboard players set {p} sr:mob_timer 0"
                    ).SuccessCount
                    if res == 0:
                        self.print(f"§c同步失败 {p}")
                    else:
                        self.print(f"§a同步成功 {p}")

    @property
    def iota(self):
        self._iota += 1
        return self._iota

    @iota.setter
    def iota(self, n: int):
        self._iota = n

    @property
    def world_time(self):
        return int(time.time() - 1728000000) // 60


entry = plugin_entry(CustomRPGMobSpawner, "自定义RPG-怪物刷新")

import os
import time
import threading
import sqlite3
import json
from tooldelta import Plugin, Player, utils, game_utils, TYPE_CHECKING, plugin_entry
from tooldelta.constants import PacketIDS
from . import args_parser, event_apis

src_get_lock = threading.RLock()
sql_db: sqlite3.Connection | None = None
DBG_MODE = False


def get_sql(fp: str):
    global sql_db
    if sql_db is None:
        sql_db = sqlite3.connect(fp)
    return sql_db


class SourcePoint:
    def __init__(
        self,
        *,
        x: int,
        y: int,
        z: int,
        item_tagname: str,
        amount: int,
        respawn_cd_time_minute: int,
        repick_cd_time: int,
        hard: int,
        first_pick_only: bool = False,
    ):
        self.x = x
        self.y = y
        self.z = z
        self.item_tagname = item_tagname
        self.amount = amount
        self.respawn_cd_time_minute = respawn_cd_time_minute
        self.repick_cd_time = repick_cd_time
        self.hard = hard
        self.first_pick_only = first_pick_only
        if not entry.rpg.item_holder.item_exists(self.item_tagname):
            raise ValueError(f"{self.item_tagname} 不是一个有效的数据化物品")

    def dumps(self):
        return args_parser.generate_comments(
            {
                "x": self.x,
                "y": self.y,
                "z": self.z,
                "t": self.item_tagname,
                "a": self.amount,
                "c": self.respawn_cd_time_minute,
                "p": self.repick_cd_time,
                "h": self.hard,
                "f": int(self.first_pick_only),
            }
        )

    @classmethod
    def new(cls, args_str: str):
        dic = args_parser.parse_comments(args_str)
        return cls(
            x=int(dic["x"]),
            y=int(dic["y"]),
            z=int(dic["z"]),
            item_tagname=dic["t"],
            amount=int(dic["a"]),
            respawn_cd_time_minute=int(dic["c"]),
            repick_cd_time=int(dic["p"]),
            hard=int(dic["h"]),
            first_pick_only=bool(int(dic["f"])),
        )


class CustomRPGSource(Plugin):
    name = "自定义RPG-资源系统"
    author = "SuperScript"
    version = (0, 0, 1)

    event_apis = event_apis

    def __init__(self, frame):
        super().__init__(frame)
        self.ListenPreload(self.on_def)
        self.ListenActive(self.on_inject)
        self.ListenPacket(PacketIDS.LevelEvent, self.on_pkt_potion)
        self.ListenPacket(PacketIDS.BlockActorData, self.on_pkt_sign)

    def on_def(self):
        self.rpg = self.GetPluginAPI("自定义RPG")
        self.chatbar = self.GetPluginAPI("聊天栏菜单")
        self.intr = self.GetPluginAPI("前置-世界交互")
        self.cb2bot = self.GetPluginAPI("Cb2Bot通信")
        if TYPE_CHECKING:
            from 自定义RPG import CustomRPG
            from 前置_聊天栏菜单 import ChatbarMenu
            from 前置_世界交互 import GameInteractive
            from 前置_Cb2Bot通信 import TellrawCb2Bot

            self.rpg: CustomRPG
            self.chatbar: ChatbarMenu
            self.intr: GameInteractive
            self.cb2bot: TellrawCb2Bot
        os.makedirs(self.format_data_path("玩家数据"), exist_ok=True)
        self.collect_status: dict[tuple[int, int, int], tuple[int, float]] = {}
        self.cb2bot.regist_message_cb("sr.source.collect", self.handler)

    def on_inject(self):
        self.clear_cache()

    def on_pkt_potion(self, pk):
        if pk["EventType"] == 2002 and pk["EventData"] == -13083194:
            x, y, z = pk["Position"]
            # self.game_ctrl.sendwocmd(
            #     f"execute as @r in overworld positioned {x:.2f} {y:.2f} {z:.2f} if block ~~-2~ target if block ~~-3~ repeating_command_block unless block ~~-0.5~ air run setblock ~~-2~ redstone_block"
            # )
            self.game_ctrl.sendwocmd(
                f"execute as @r in overworld positioned {x:.1f} {int(y)} {z:.1f} if block ~~-3~ target if block ~~-4~ repeating_command_block unless block ~~-1~ air run setblock ~~-3~ redstone_block"
            )
            self.game_ctrl.sendwocmd(
                f"execute as @r in overworld positioned {x:.1f} {int(y)} {z:.1f} if block ~~-2~ target if block ~~-3~ repeating_command_block unless block ~~~ air run setblock ~~-2~ redstone_block"
            )
        return False

    def on_pkt_sign(self, pk):
        if "NBTData" in pk and "id" in pk["NBTData"]:
            if not (pk["NBTData"]["id"] == "Sign"):
                return False
            signText = pk["NBTData"]["FrontText"]["Text"]
            if not signText.startswith("src"):
                return False
            total_args = signText.split()
            if len(total_args) < 2:
                return False
            x, y, z = (
                pk["NBTData"]["x"],
                pk["NBTData"]["y"] - 1,
                pk["NBTData"]["z"],
            )
            nearestPlayer = game_utils.getTarget(f"@a[x={x},y={y},z={z},c=1,r=5]")
            if (
                nearestPlayer == []
                or (p := self.frame.get_players().getPlayerByName(nearestPlayer[0]))
                is None
            ):
                return False
            if not p.is_op():
                p.show("§c非管理员无权调用")
                return False
            op, *args = total_args
            if op == "srccom":
                self.on_place_common_source(p, (x, y, z), args)
            elif op == "srcfst":
                # item_tagname, amount, hard
                self.on_place_first_source(p, (x, y, z), args)
            elif op == "srclst":
                self.on_place_source_with_cd(p, (x, y, z), args)
            elif op == "src" and args == ["del"]:
                self.on_delete(p, (x, y, z))
        return False

    def handler(self, contents: list[str]):
        nearest, content = contents
        nearest = self.rpg.getPlayer(nearest)
        src_point = SourcePoint.new(content)
        x = src_point.x
        y = src_point.y
        z = src_point.z
        if (
            src_point.hard <= 1
            or self.collect_status.get((x, y, z), (0, 0))[0] >= src_point.hard
        ):
            if (x, y, z) in self.collect_status.keys():
                del self.collect_status[(x, y, z)]
            nearest.setActionbar(" §7采集进度 §f| §a§l采集完成§r §f|")
            self.ok(nearest, src_point)
        else:
            if (x, y, z) not in self.collect_status.keys():
                collect_progress, timecache = self.collect_status[(x, y, z)] = (
                    1,
                    time.time(),
                )
                timecache = time.time()
            else:
                collect_progress, timecache = self.collect_status[(x, y, z)]
                self.collect_status[(x, y, z)] = (collect_progress + 1, timecache)
            progress = int(collect_progress / src_point.hard * 30)
            fmt_bar = "§f" + "|" * progress + "§8" + "|" * (30 - progress)
            nearest.setActionbar(f" §7采集进度 §f[{fmt_bar}§f]")
        self.game_ctrl.sendwscmd_with_resp(f"clear {nearest.safe_name} splash_potion 0")
        self.game_ctrl.sendwocmd(
            f"replaceitem entity {nearest.safe_name} slot.weapon.mainhand 0 keep splash_potion"
        )
        self.game_ctrl.sendwocmd(
            f"fill {x} {y - 3} {z} {x} {y - 2} {z} target 0 replace redstone_block"
        )

    def on_place_common_source(
        self, player: Player, xyz: tuple[int, int, int], args: list[str]
    ):
        x, y, z = xyz
        try:
            utils.fill_list_index(args, ["", "1", "5", "15"])
            item_tagname = args[0]
            item_count = int(args[1])
            hard = int(args[2])
            item_cd_min = int(args[3])
            src_point = SourcePoint(
                x=x,
                y=y,
                z=z,
                item_tagname=item_tagname,
                amount=item_count,
                hard=hard,
                respawn_cd_time_minute=item_cd_min,
                repick_cd_time=item_cd_min,
            )
        except Exception as err:
            player.show(f"§c设置失败： {err}")
        self.set_command_block(src_point)
        player.show("§a设置成功")

    def on_place_source_with_cd(
        self, player: Player, xyz: tuple[int, int, int], args: list[str]
    ):
        x, y, z = xyz
        try:
            # item_tagname, item_count, hard, cd_min
            utils.fill_list_index(args, ["", "1", "5", "280"])
            item_tagname = args[0]
            item_count = int(args[1])
            hard = int(args[2])
            item_cd_min = int(args[3])
            src_point = SourcePoint(
                x=x,
                y=y,
                z=z,
                item_tagname=item_tagname,
                amount=item_count,
                hard=hard,
                respawn_cd_time_minute=10,
                repick_cd_time=item_cd_min,
            )
        except Exception as err:
            player.show(f"§c设置失败： {err}")
            return
        self.set_command_block(src_point)
        player.show("§a设置成功")

    def on_place_first_source(
        self, player: Player, xyz: tuple[int, int, int], args: list[str]
    ):
        x, y, z = xyz
        try:
            utils.fill_list_index(args, ["", "1", "5"])
            item_tagname = args[0]
            item_count = int(args[1])
            hard = int(args[2])
            src_point = SourcePoint(
                x=x,
                y=y,
                z=z,
                item_tagname=item_tagname,
                amount=item_count,
                hard=hard,
                respawn_cd_time_minute=10,
                repick_cd_time=280,
                first_pick_only=True,
            )
        except Exception as err:
            player.show(f"§c设置失败： {err}")
        rawtext = {
            "rawtext": [
                {"text": "sr.sources.collect"},
                {"selector": "@p"},
                {"text": src_point.dumps()},
            ]
        }
        cmd = f"tellraw @a[tag=sr.rpg_bot] {json.dumps(rawtext, ensure_ascii=False)}"
        self.intr.place_command_block(
            self.intr.make_packet_command_block_update((x, y - 3, z), cmd, 2, True, 20)
        )
        self.set_command_block(src_point)
        player.show("§a设置成功")

    def on_delete(self, player: Player, xyz: tuple[int, int, int]):
        x, y, z = xyz
        res = self.game_ctrl.sendwscmd_with_resp(f"structure delete res-{x}-{y}-{z}")
        if res.SuccessCount == 0:
            player.show("§6删除失败")
        else:
            player.show("§a删除成功")

    def set_command_block(self, point: SourcePoint):
        rawtext = {
            "rawtext": [
                {"text": "sr.source.collect"},
                {"selector": "@p"},
                {"text": point.dumps()},
            ]
        }
        cmd = f"tellraw @a[tag=sr.rpg_bot] {json.dumps(rawtext, ensure_ascii=False)}"
        self.intr.place_command_block(
            self.intr.make_packet_command_block_update(
                (point.x, point.y - 3, point.z), cmd, 1, True, 20
            )
        )
        self.game_ctrl.sendwocmd(f"setblock {point.x} {point.y - 2} {point.z} target")
        self.game_ctrl.sendcmd("tp ~~20~")

    def ok(self, player: Player, point: SourcePoint):
        x = point.x
        y = point.y
        z = point.z
        is_first_pick = self.is_first_pick(player, point)
        if is_first_pick:
            if point.first_pick_only:
                self.rpg.show_any(player, "a", "§d<§f+§d> §a已采集一次性资源！")
            else:
                self.rpg.show_any(player, "a", "§d<§f+§d> §a此处首次采集！")
                self.record_player_first_pick(player, point)
        if point.first_pick_only and is_first_pick:
            self.rpg.backpack_holder.giveItems(
                player,
                self.rpg.item_holder.createItems(point.item_tagname, point.amount),
            )
            self.record_player_first_pick(player, point)
            self.rpg.rpg_upgrade.add_player_exp(player, 5)
        elif self.can_repick(player, point):
            if point.first_pick_only:
                self.rpg.backpack_holder.giveItems(
                    player, self.rpg.item_holder.createItems("蔚蓝点", 5)
                )
            else:
                pick_item = point.item_tagname
                pick_item_amount = point.amount
                self.rpg.backpack_holder.giveItems(
                    player,
                    self.rpg.item_holder.createItems(pick_item, pick_item_amount),
                )
            self.record_player_last_pick(player, point)
        else:
            self.rpg.rpg_upgrade.add_player_exp(player, 1)
        structure_name = f"res-{x}-{y}-{z}"
        resp = self.game_ctrl.sendwscmd_with_resp(
            f"structure save {structure_name} {x} {y} {z} {x} {y} {z} false disk"
        )
        if resp.SuccessCount == 0:
            player.show(
                f"结构错误， 请反馈至管理员: {resp.OutputMessages[0].Message}",
            )
            return
        self.game_ctrl.sendwocmd(f"setblock {x} {y} {z} air 0 destroy")
        self.game_ctrl.sendwocmd(
            f"structure load {structure_name} {x} {y} {z} 0_degrees none block_by_block {point.respawn_cd_time_minute * 60}"
        )
        self.game_ctrl.sendwocmd(f"kill @e[x={x},y={y},z={z},r=1.6,type=item]")
        self.BroadcastEvent(
            event_apis.PlayerDigSourceEvent(player, point, is_first_pick).to_broadcast()
        )

    def record_player_first_pick(self, player: Player, point: SourcePoint):
        o = self.load_player_record(player)
        o["first"][f"{point.x},{point.y},{point.z}"] = int(time.time())
        self.save_player_record(player, o)

    def record_player_last_pick(self, player: Player, point: SourcePoint):
        o = self.load_player_record(player)
        o["last"][f"{point.x},{point.y},{point.z}"] = int(time.time())
        self.save_player_record(player, o)

    def load_player_record(self, player: Player):
        return utils.tempjson.load_and_read(
            self.format_player_data_path(player),
            False,
            default={"first": {}, "last": {}},
        )

    def save_player_record(self, player: Player, obj):
        utils.tempjson.load_and_write(
            path := self.format_player_data_path(player),
            obj,
            False,
        )
        utils.tempjson.flush(path)

    def is_first_pick(self, player: Player, point: SourcePoint):
        return (
            self.load_player_record(player)["first"].get(
                f"{point.x},{point.y},{point.z}"
            )
            is None
        )

    def can_repick(self, player: Player, point: SourcePoint):
        return (
            time.time()
            - self.load_player_record(player)["last"].get(
                f"{point.x},{point.y},{point.z}", 0
            )
            >= point.repick_cd_time * 60
        )

    def format_player_data_path(self, player: Player):
        return self.format_data_path(
            "玩家数据",
            player.xuid + ".json",
        )

    @utils.timer_event(60, "资源点采集中断缓存清理")
    def clear_cache(self):
        ntime = time.time()
        for k, v in self.collect_status.copy().items():
            if ntime - v[1] > 60:
                del self.collect_status[k]


entry = plugin_entry(CustomRPGSource, "自定义RPG-资源")

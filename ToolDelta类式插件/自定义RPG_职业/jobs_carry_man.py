import random
import time
from tooldelta import Player
from tooldelta.game_utils import getTarget
from .event_apis import PlayerFinishJobEvent
from .job_frame import Job

TRANSLATOR = {
    "stone": "石料",
    "granite": "花岗岩石料",
    "polished_granite": "磨制花岗岩石料",
    "diorite": "闪长岩石料",
    "polished_diorite": "磨制闪长岩石料",
    "andesite": "安山岩石料",
    "polished_andesite": "磨制安山岩石料",
    "brick_block": "砖块",
    "planks": "木板",
    "concrete": "混凝土",
    "stained_hardened_clay": "瓦块",
    "clay": "粘土块",
}

VAL = {
    "stone": 3.0,
    "granite": 3.0,
    "polished_granite": 3.0,
    "diorite": 3.0,
    "polished_diorite": 3.0,
    "andesite": 3.0,
    "polished_andesite": 3.0,
    "brick_block": 4.5,
    "planks": 6.0,
    "concrete": 9.0,
    "clay": 5.0,
    "stained_hardened_clay": 7.5,
}

avali_materials = {
    1: [
        ("stone", 0),
        ("granite", 0),
        ("diorite", 0),
        ("andesite", 0),
        ("brick_block", 0),
    ],
    2: [
        ("polished_granite", 0),
        ("polished_diorite", 0),
        ("polished_andesite", 0),
    ],
    3: [
        ("planks", 0),
        ("planks", 1),
        ("clay", 0),
    ],
}


def get_avali_materials(job_level: int):
    # return tuple[id, data]
    return [
        (k1, v1) for k, v in avali_materials.items() if job_level >= k for k1, v1 in v
    ]


def translate(name: str):
    return TRANSLATOR.get(name, name)


class CarryMan(Job):
    name = "建材搬运工"
    level = 1
    job_levels = (0, 112, 260, 385)

    def __init__(self, sys):
        super().__init__(sys)
        self.sys.add_listen_pkt(26, self.handle_submiter_like)
        self.L_time = 0
        self.R_time = 0
        self.U_time = 0
        self.D_time = 0
        self.sys.add_menu_cb("jzbyg-cb", self.place_cb)
        self.sys.cb2bot.regist_message_cb(
            "job.carryman.take_items",
            lambda x: self.on_get_task(self.sys.rpg.getPlayer(x[0])),
        )

    def give_rand_task(self, player: Player):
        jdatas = self.get_datas(player)
        if jdatas.get("task_taken"):
            return None
        job_lv = self.calculate_level(self.get_exp(player))
        materials: dict[str, dict[int, int]] = {}
        actua_materials: dict[str, dict[int, int]] = {}
        # JOB LEVEL
        k = 1
        match job_lv:
            case 1:
                k = 12
            case 2:
                k = 18
            case 3:
                k = 24
            case 4:
                k = 32
            case 5:
                k = 48
            case 6:
                k = 64
        for id, data in random.choices(
            get_avali_materials(job_lv),
            k=k,
        ):
            materials.setdefault(id, {})
            materials[id].setdefault(data, 0)
            materials[id][data] += 1
        actua_materials = materials.copy()
        if random.random() > 0.7:
            for id, data in random.choices(
                get_avali_materials(job_lv),
                k=1,
            ):
                actua_materials.setdefault(id, {})
                actua_materials[id].setdefault(data, 0)
                actua_materials[id][data] += 1
        for id, datas in actua_materials.items():
            for data, count in datas.items():
                self.sys.game_ctrl.sendwocmd(
                    f"give {player.safe_name} {id} {count} {data}"
                )
        tota_counts = sum(sum(j for j in i.values()) for i in actua_materials.values())
        jdatas.update(
            {
                "c": tota_counts,
                "exp_delta": 0,
                "task_taken": True,
                "takens": {k: sum(v.values()) for k, v in materials.items()},
                "salary": 0,
            }
        )
        self.write_datas(player, jdatas)
        return {k: sum(v.values()) for k, v in materials.items()}

    def handle_submiter_like(self, pk: dict):
        x, y, z = pk["Position"]
        x_move = 0
        z_move = 0
        ntime = time.time()
        if z == 397:
            if x in range(532, 546):
                if ntime - self.U_time < 1:
                    return
                self.U_time = ntime
                z_move -= 1
            else:
                return
        elif z == 377:
            if x in range(532, 546):
                if ntime - self.D_time < 1:
                    return
                self.D_time = ntime
                z_move += 1
            else:
                return
        elif x == 529:
            if z in range(380, 395):
                if ntime - self.R_time < 1:
                    return
                self.R_time = ntime
                x_move += 1
            else:
                return
        elif x == 548 and z in range(380, 395):
            if z in range(380, 395):
                if ntime - self.L_time < 1:
                    return
                self.L_time = ntime
                x_move -= 1
            else:
                return
        else:
            return
        nearestPlayer = getTarget(f"@a[x={x},y={y},z={z},c=1,r=10]")
        if nearestPlayer == []:
            return
        playername = nearestPlayer[0]
        player = self.sys.rpg.getPlayer(playername)
        if not self.has_job(player):
            return
        self.submit_tasks(
            player, (x + x_move, y + 1, z + z_move)
        )

    def submit_tasks(self, player: Player, pos: tuple[int, int, int]):
        x, y, z = pos
        rpg = self.sys.rpg
        jdatas = self.get_datas(player)
        if not jdatas.get("task_taken"):
            rpg.show_inf(player, "你不需要码放任何建材。")
            return
        need_submits = jdatas["takens"].copy()
        jdatas.setdefault("exp_delta", 0)
        blocks = self.get_blocks(x, y, z)
        bs_num = 0
        c = jdatas.get("c", 20)
        for block, count in need_submits.copy().items():
            if blocks.get(block, 0) != 0:
                submit_count = min(count, blocks[block])
                need_submits[block] = max(0, count - blocks[block])
                jdatas["salary"] += VAL[block] * min(count, blocks[block])
                bs_num += 1
                jdatas["exp_delta"] += abs(hash(f"{x,y,z}+{player.name}")) % 600 / 100 * submit_count / c
        jdatas["takens"] = need_submits
        is_ok = sum(need_submits.values()) == 0
        if bs_num == 0:
            rpg.show_warn(player, "请先在§e允许方块§6上放置建材")
        elif not is_ok:
            self.sys.game_ctrl.sendwocmd(f"fill {x} {y} {z} {x} {y + 2} {z} air")
            player.setTitle("§a", "§a已放好建材， 可以接着码放建材")
            _fmt = "， ".join(
                f"§a{translate(k)}§2x{v}§f" for k, v in blocks.items() if k != "air"
            )
            _fmt2 = "\n  ".join(
                f"§6{translate(name)}§fx{count}"
                for name, count in need_submits.items()
                if count > 0
            )
            player.setActionbar(
                f"§7已放置 {_fmt}， §7剩余：\n  {_fmt2}",
            )
            self.write_datas(player, jdatas)
        else:
            self.sys.game_ctrl.sendwocmd(f"fill {x} {y} {z} {x} {y + 2} {z} air")
            salary = int(jdatas["salary"])
            self.sys.game_ctrl.sendwocmd(
                f"execute as {player.safe_name} at @s run playsound random.levelup @s ~~~ 1 0.5"
            )
            rpg.show_succ(player, "你把所有的建材都码放到了指定地点。")
            rpg.show_succ(player, f"得到工钱 §e{salary} §b蔚蓝点")
            rpg.backpack_holder.giveItems(
                player, rpg.item_holder.createItems("蔚蓝点", salary), False
            )
            self.add_credit(player, 0.2)
            # PLOT QUEST SPEC
            q = self.sys.rpg_quests.get_quest(
                qname := "蔚蓝空域/职业入门:建材搬运工-工作"
            )
            assert q, "任务未载入: " + qname
            if q in self.sys.rpg_quests.read_quests(player):
                self.sys.rpg_quests.finish_quest(player, q)
            jdatas["task_taken"] = False
            jdatas["salary"] = 0
            jdatas["exp_delta"] = 0
            self.write_datas(player, jdatas)
            self.add_exp(player, int(1 + jdatas["exp_delta"]))
            self.sys.BroadcastEvent(
                PlayerFinishJobEvent(player, self.name, salary, bs_num).to_broadcast()
            )

    def on_get_task(self, player: Player):
        rpg = self.sys.rpg
        if not self.sys.has_job(player, self.name):
            rpg.show_fail(player, f"只有{self.name}才可以领取和搬运建材..")
            return
        res = self.give_rand_task(player)
        if res is None:
            rpg.show_warn(player, "你还没有搬运完上一次获得的材料：")
            need_submits = self.get_datas(player)["takens"]
            for name, count in need_submits.items():
                if count > 0:
                    rpg.show_warn(player, f" - §6{translate(name)}§fx{count}")
        else:
            rpg.show_any(player, "e", "§e你需要将以下材料搬运：")
            for name, count in res.items():
                zhcn_name = TRANSLATOR[name]
                rpg.show_any(player, "n", f"§6{zhcn_name} §fx {count}")

    def get_blocks(self, x: int, y: int, z: int):
        structure = self.sys.intr.get_structure((x, y, z), (1, 3, 1))
        blocks: dict[str, int] = {}
        for y in range(3):
            blockf = structure.get_block((0, y, 0)).foreground
            if blockf is None:
                block_name = "air"
            elif blockf.name.endswith("planks"):
                block_name = "planks"
            else:
                block_name = blockf.name.removeprefix("minecraft:")
            blocks.setdefault(block_name, 0)
            blocks[block_name] += 1
        return blocks

    def place_cb(self, player: Player, _):
        x, y, z = (int(i) for i in player.getPos()[1:])
        self.sys.intr.place_command_block(
            self.sys.intr.make_packet_command_block_update(
                (x, y, z),
                "tellraw @a[tag=sr.rpg_bot] "
                r'{"rawtext":[{"text":"job.carryman.take_items"},{"selector":"@p[r=5]"}]}',
                need_redstone=True,
            )
        )
        self.sys.rpg.show_succ(player, "放置已完成")
        self.sys.game_ctrl.sendcmd("tp ~~10~")


# 85174096

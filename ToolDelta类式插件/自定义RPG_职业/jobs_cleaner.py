from random import randint, choices
from tooldelta import utils, game_utils, Player
from .event_apis import PlayerFinishJobEvent
from .job_frame import Job, SYSTEM, int_time

TRASH_VALUE_AND_WGT: dict[int, dict[str, tuple[float, float]]] = {
    1: {
        "废弃空水瓶": (2, 1),
        "脏手纸": (0.4, 1.6),
        "废弃泡沫块": (1, 0.7),
        "污浊塑料片": (0.6, 1),
    },
    2: {
        "铜币": (3, 0.6),
        "损坏的电路板": (3, 0.8),
        "空玻璃瓶": (3, 0.5)
    },
    3: {
        "废旧电线卷": (5, 0.7),
        "空木盒": (4, 0.8)
    }
}

GARBAGE_SPAWN_MIN = 576
GARBAGE_SPAWN_MAX = 864
MAX_OPEN_DELAY = 240 * 20

def get_avali_garbages(level: int):
        res: dict[str, tuple[float, float]] = {}
        for i in range(1, level + 1):
            res.update(TRASH_VALUE_AND_WGT[i])
        return res


class Cleaner(Job):
    name = "环卫工"
    level = 1
    job_levels = (0, 120, 260)

    def __init__(self, sys: SYSTEM):
        super().__init__(sys)
        sys.add_menu_cb("trashbin", self.create_trash_bin)
        sys.add_menu_cb("deltrashbin", self.delete_trash_bin)
        sys.add_listen_pkt(26, self.on_handle_like_trashbin)
        sys.cb2bot.regist_message_cb(
            "job.garbage.submit", lambda a: self.submit(self.sys.rpg.getPlayer(a[0]))
        )

    def on_handle_like_trashbin(self, pk):
        x, y, z = pk["Position"]
        if pk["EventData"] == 1 and self.container_is_trash_bin(x, y, z):
            self.open_trash_bin(*pk["Position"])

    @utils.thread_func("职业:打开垃圾桶")
    def open_trash_bin(self, x: int, y: int, z: int):
        self.sys.game_ctrl.sendwocmd(f"setblock {x} {y} {z} planks 1")
        nearestPlayers = game_utils.getTarget(f"@a[x={x},y={y},z={z},c=1]")
        self.sys.game_ctrl.sendwocmd(f"structure load 垃圾桶 {x} {y} {z}")
        if nearestPlayers == []:
            self.sys.rpg.show_any("@a", "6", f"§6垃圾桶被鬼打开了 (在 {x} {y} {z})")
            return
        player = self.sys.rpg.getPlayer(nearestPlayers[0])
        if not self.sys.has_job(player, self.name):
            self.sys.rpg.show_any(player, "7", "§7你翻了一个垃圾桶， 这不是你该翻的。")
            return
        from_last_open = min(
            int_time() - self.get_trash_bin_last_open(x, y, z), MAX_OPEN_DELAY
        )
        if from_last_open <= 0:
            self.sys.rpg.show_warn(player, "垃圾桶里空空如也..")
            return
        garbages: dict[str, int] = {}
        garbage_items: list[str] = []
        garbage_weights: list[float] = []
        for k, (_, v1) in get_avali_garbages(
            self.calculate_level(self.get_exp(player))
        ).items():
            garbage_items.append(k)
            garbage_weights.append(v1)
        if garbage_items == []:
            self.sys.rpg.show_fail(player, "你翻不出垃圾了.. （请联系管理员）")
            return
        while from_last_open > 0:
            from_last_open -= randint(GARBAGE_SPAWN_MIN, GARBAGE_SPAWN_MAX)
            garbage = choices(garbage_items, garbage_weights)[0]
            garbages.setdefault(garbage, 0)
            garbages[garbage] += 1
        garbage_counts = sum(garbages.values())
        self.sys.rpg.show_any(player, "f", "§7你翻完了这个垃圾桶并获得了：")
        for garbage, count in garbages.items():
            self.sys.rpg.backpack_holder.giveItems(
                player, self.sys.rpg.item_holder.createItems(garbage, count)
            )
        self.add_exp(player, int(garbage_counts / 2))
        self.add_credit(player, garbage_counts / 12)
        self.flush_trash_bin_data(x, y, z)
        # PLOT QUEST SPEC
        q = self.sys.rpg_quests.get_quest(qname := "蔚蓝空域/职业入门:环卫工-工作")
        assert q, "任务未载入: " + qname
        if q in self.sys.rpg_quests.read_quests(player):
            self.sys.rpg_quests.finish_quest(player, q)

    def submit(self, player: Player):
        if not self.sys.has_job(player, self.name):
            self.sys.rpg.show_fail(player, "你没有领取环卫工职业， 请告知管理员")
            return
        max_val = 0
        submit_items: list[tuple[str, int]] = []
        for garbage_id, (val, _) in get_avali_garbages(
            self.calculate_level(self.get_exp(player))
        ).items():
            if (
                count := self.sys.rpg.backpack_holder.getItemCount(player, garbage_id)
            ) > 0:
                max_val += count * val
                submit_items.append((garbage_id, count))
        salary = int(max_val)
        if max_val < 1:
            # TODO: 折合 1
            self.sys.rpg.show_warn(
                player, f"总物品价值不足 1 点 ({max_val}/1) §6， 无法回收"
            )
            return
        for garbage_id, _ in submit_items:
            self.sys.rpg.backpack_holder.clearItem(
                player, garbage_id, -1, show_to_player=False
            )
        garbages = [
            (self.sys.rpg.item_holder.getOrigItem(i), count)
            for i, count in submit_items
        ]
        self.sys.rpg.show_succ(
            player, f"你将 §f{sum(i[1] for i in submit_items)}§a 件废品回收了："
        )
        for garbage, count in garbages:
            self.sys.rpg.show_any(
                # TODO: directly use Item.disp_name
                player, "7", f"§7◇ §f{garbage.disp_name} §7x §f{count}"
            )
        self.sys.rpg.show_any(player, "7", f"§e收益§7： §f{salary} §b蔚蓝点")
        self.sys.rpg.backpack_holder.giveItems(
            player, self.sys.rpg.item_holder.createItems("蔚蓝点", salary), False
        )
        self.sys.BroadcastEvent(
            PlayerFinishJobEvent(player, self.name, salary, 0).to_broadcast()
        )

    def create_trash_bin(self, player: Player, _):
        if not player.is_op():
            self.sys.rpg.show_fail(player, "暂无权限")
            return
        dim, x, y, z = (int(i) for i in player.getPos())
        self._add_trash_bin(x, y, z)
        self.sys.rpg.show_succ(player, f"垃圾桶添加成功: §f{x}, {y}, {z}")

    def delete_trash_bin(self, player: Player, _):
        if not player.is_op():
            self.sys.rpg.show_fail(player, "暂无权限")
            return
        dim, x, y, z = (int(i) for i in player.getPos())
        if self._rem_trash_bin(x, y, z):
            self.sys.rpg.show_succ(player, f"垃圾桶删除成功: §f{x}, {y}, {z}")
        else:
            self.sys.rpg.show_warn(player, "此地并无垃圾桶")

    def container_is_trash_bin(self, x: int, y: int, z: int):
        return self.format_xyz_key(x, y, z) in self.get_trash_bin_datas().keys()

    def _add_trash_bin(self, x: int, y: int, z: int):
        o = self.get_trash_bin_datas()
        o[self.format_xyz_key(x, y, z)] = 0
        self.set_trash_bin_datas(o)

    def _rem_trash_bin(self, x: int, y: int, z: int):
        o = self.get_trash_bin_datas()
        if o.get(self.format_xyz_key(x, y, z)) is not None:
            del o[self.format_xyz_key(x, y, z)]
            self.set_trash_bin_datas(o)
            return True
        else:
            return False

    def get_trash_bin_last_open(self, x: int, y: int, z: int) -> int:
        return self.get_trash_bin_datas()[self.format_xyz_key(x, y, z)]

    def flush_trash_bin_data(self, x: int, y: int, z: int):
        cleaners_amount = len(self.all_employees())
        o = self.get_trash_bin_datas()
        o[self.format_xyz_key(x, y, z)] = int_time() + randint(
            GARBAGE_SPAWN_MIN // cleaners_amount, GARBAGE_SPAWN_MAX // cleaners_amount
        )
        self.set_trash_bin_datas(o)

    def get_trash_bin_datas(self):
        return utils.tempjson.load_and_read(
            self.sys.format_data_path("trash_bins.json"),
            need_file_exists=False,
            default={},
        )

    def set_trash_bin_datas(self, obj):
        utils.tempjson.load_and_write(
            self.sys.format_data_path("trash_bins.json"), obj, need_file_exists=False
        )

    @staticmethod
    def format_xyz_key(x: int, y: int, z: int):
        return f"{x},{y},{z}"

    @staticmethod
    def format_xyz_scb(x: int, y: int, z: int):
        return f"p_{x}_{y}_{z}"

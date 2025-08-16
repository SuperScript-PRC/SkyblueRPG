import uuid
import random
import math
from tooldelta import utils, Player
from tooldelta.game_utils import getTarget
from .event_apis import PlayerFinishJobEvent
from .job_frame import Job, SYSTEM, int_time

POS = tuple[int, int, int]

MAIL_ITEMS = "$邮件包裹"

SIZE_NORMAL = 1
SIZE_MID = 2
SIZE_LARGE = 3

SIZE_VALUE = {SIZE_NORMAL: 1.0, SIZE_MID: 1.5, SIZE_LARGE: 2.0}
SIZE_FMT = {SIZE_NORMAL: "a", SIZE_MID: "b", SIZE_LARGE: "d"}
WEIGHTS = {SIZE_NORMAL: 1, SIZE_MID: 1.4, SIZE_LARGE: 1.7}


def calculate_delay_reduce(delay_seconds: int):
    return int(delay_seconds / 120)


def calculate_distance_fee(send_pos: POS, recv_pos: POS) -> int:
    sx, sy, sz = send_pos
    rx, ry, rz = recv_pos
    distance = int(math.hypot(rx - sx, ry - sy, rz - sz))
    return distance // 20


def format_timer_zhcn(timemin: int):
    fmt_string = ""
    if timemin >= 1440:
        days = timemin // 1440
        fmt_string += f"{days}天"
    if timemin >= 60 and timemin % 1440:
        hrs = timemin // 60 - (timemin // 1440 * 1440) // 60
        fmt_string += f"{hrs}小时"
    if timemin % 60:
        fmt_string += f"{timemin % 60}分钟"
    return fmt_string


class MailDeliver(Job):
    name = "邮递员"
    level = 2
    job_levels = ()

    def __init__(self, sys: SYSTEM) -> None:
        super().__init__(sys)
        sys.add_inject_func(self.inject_func)
        self.sys.add_menu_cb("ydy-cb", self.place_cb)
        self.sys.add_menu_cb("mbadd", self.on_add_mailbox)
        self.sys.add_menu_cb("mbrem", self.on_remove_mailbox)
        self.sys.add_listen_pkt(26, self.on_handle_like_mailbox)
        self.sys.cb2bot.regist_message_cb(
            "job.maildev.take_items",
            lambda x: self.on_get_task(sys.rpg.getPlayer(x[0]), x[1]),
        )
        self.backpack = sys.backpack
        self.sys.loaded_job_menus[self.name] = self.sys.MultiPage(
            "sr.job.mail_deliver",
            self.info_show,
            lambda a, b: True,
            parent_page_id="sr.job",
        )

    def info_show(self, player: Player, page: int):
        output = "§6待投递邮件列表§7>§f"
        if page > 0:
            return None
        mails = self.sys.rpg.backpack_holder.getItems(player, MAIL_ITEMS)
        if mails == [] or mails is None:
            return output + "\n  §7暂无需要派送的邮件.."
        else:
            is_beyond_maxcount = len(mails) > 12
            for mail in mails[:12]:
                metadatas = mail.metadata
                deadline = metadatas["dtime"] - int_time()
                deadline_str = (
                    format_timer_zhcn(deadline // 60)
                    if deadline >= 0
                    else f"逾期 {format_timer_zhcn(-deadline // 60)}"
                )
                address = self.format_address_readable_str(metadatas["addr"])
                output += (
                    f"\n §{SIZE_FMT[metadatas['size']]}✉ §f{address} §7: {deadline_str}"
                )
            if is_beyond_maxcount:
                output += f"  §7还有 {len(mails) - 12} 项..."
            return output

    def submit(self, player: Player, addr: POS):
        mails = self.sys.rpg.backpack_holder.getItems(player, "$邮件包裹")
        if mails is None:
            self.sys.rpg.show_warn(player, "你并没有任何需要提交的邮件。")
            return
        mails = [
            mail_item
            for mail_item in mails
            if tuple(mail_item.metadata["addr"]) == addr
        ]
        if mails == []:
            self.sys.rpg.show_warn(player, "你没有任何需要投递到这里的邮件。")
            return
        profit = 0
        count = 0
        for mail in mails:
            count += 1
            deadlock_time = mail.metadata["dtime"]
            timeout_time = int_time() - deadlock_time
            profit += (
                calculate_distance_fee(mail.metadata["sendpos"], mail.metadata["addr"])
                * SIZE_VALUE[mail.metadata["size"]]
            )
            if timeout_time > 0:
                timeout_pass = int_time() - deadlock_time
                profit -= calculate_delay_reduce(timeout_pass)
                self.sys.rpg.show_warn(
                    player,
                    f" §{SIZE_FMT[mail.metadata['size']]}✉ §6邮件已超时 {format_timer_zhcn(timeout_pass // 60)}",
                )
                self.sys.reduce_credit(player, round(timeout_pass / 300))
            jdatas = self.read_datas(player)
            jdatas.setdefault("weight", 0)
            jdatas["weight"] = max(
                0, jdatas["weight"] - (this_weight := WEIGHTS[mail.metadata["size"]])
            )
            self.write_datas(player, jdatas)
            self.add_credit(player, this_weight / 10)
            self.sys.rpg.backpack_holder.removePlayerStore(player, mail, 1)
        now_weight = jdatas["weight"]
        if now_weight > 0:
            self.sys.rpg.show_succ(
                player, f"§f{count} §a件邮件已投递 （当前负重： {now_weight:.1f}）"
            )
        else:
            self.sys.rpg.show_succ(
                player, f"§f{count} §a件邮件已投递 （全部邮件投递完成）"
            )
            # PLOT QUEST SPEC
            q = self.sys.rpg_quests.get_quest(qname := "蔚蓝空域/职业入门:邮递员-工作")
            assert q, "任务未载入: " + qname
            if q in self.sys.rpg_quests.read_quests(player):
                self.sys.rpg_quests.finish_quest(player, q)
        profit = int(max(0, profit))
        exp = int(this_weight)
        self.sys.rpg.backpack_holder.giveItems(
            player, self.sys.rpg.item_holder.createItems("蔚蓝点", profit)
        )
        self.delete_mail_records(player, [mail.metadata["ud"] for mail in mails])
        self.add_exp(player, exp)
        self.sys.BroadcastEvent(
            PlayerFinishJobEvent(player, self.name, profit, exp).to_broadcast()
        )

    def get_random_address(
        self, center: tuple[int, int] | None = None, radius: int = 300
    ) -> POS | None:
        addresses = utils.tempjson.load_and_read(
            self.format_address_db_path(), need_file_exists=False, default=[]
        )
        if len(addresses) == 0:
            return None
        if center is None:
            x, y, z = random.choice(addresses)
            return x, y, z
        else:
            cx, cz = center
            return random.choice(
                [
                    (x, y, z)
                    for x, y, z in addresses
                    if math.hypot(x - cx, z - cz) <= radius
                ]
            )

    def on_get_task(self, player: Player, send_pos_data: str):
        x, y, z = (int(i) for i in send_pos_data.split(","))
        if not self.sys.has_job(player, self.name):
            self.sys.rpg.show_fail(player, "你还不是邮递员， 无法取出待配送邮件")
        else:
            self.spawn_single_random_task((x, y, z), player)

    def handout_single_task(
        self,
        player: Player,
        send_addr: POS,
        recv_addr: POS,
        size: int,
        deadlock_delay: int,
    ):
        ud = uuid.uuid4().hex
        deadlock_time = int_time() + deadlock_delay
        mail_item = self.sys.rpg.item_holder.createItems(
            MAIL_ITEMS,
            metadata={
                "ud": ud,
                "dtime": deadlock_time,
                "addr": list(recv_addr),
                "size": size,
                "sendpos": list(send_addr),
            },
        )[0]
        self.sys.rpg.backpack_holder.giveItem(player, mail_item)
        jdatas = self.read_datas(player)
        jdatas["weight"] += WEIGHTS[size]
        self.write_datas(player, jdatas)
        self.add_mail_record(player, ud, deadlock_delay)
        self.sys.rpg.show_succ(
            player, f"你接取了一封邮件 （当前负重： {jdatas['weight']:.1f}）"
        )

    def spawn_single_random_task(self, send_addr: POS, player: Player):
        recv_addr = self.get_random_address((send_addr[0], send_addr[2]), 300)
        if recv_addr is None:
            self.sys.rpg.show_fail(player, "收件地址太少(0个)， 请反馈给管理员")
            return
        jdatas = self.read_datas(player)
        # TODO: Job Level Related
        weight = jdatas.setdefault("weight", 0)
        if weight >= 8:
            self.sys.rpg.show_warn(player, "你接取够多邮件了， 请先送达一些邮件")
            return
        deadlock_delay = random.randint(86400, 172000)
        size = random.choices(
            [SIZE_NORMAL, SIZE_MID, SIZE_LARGE], weights=[0.7, 0.2, 0.1]
        )[0]
        self.handout_single_task(player, send_addr, recv_addr, size, deadlock_delay)

    def add_mail_record(self, gsender: Player, mail_uuid: str, deadlock_time: int):
        path = self.sys.format_data_path("mails.json")
        content = utils.tempjson.load_and_read(path, need_file_exists=False, default={})
        content.setdefault(gsender.xuid, {})
        content[gsender.xuid][mail_uuid] = {"dtime": deadlock_time}
        utils.tempjson.load_and_write(path, content, need_file_exists=False)

    def delete_mail_records(self, gsender: Player, mail_uuids: list[str]):
        path = self.sys.format_data_path("mails.json")
        content = utils.tempjson.load_and_read(path, need_file_exists=False, default={})
        for mail_uuid in mail_uuids:
            del content[gsender.xuid][mail_uuid]
        utils.tempjson.load_and_write(path, content, need_file_exists=False)

    def read_mail_records(self):
        return utils.tempjson.load_and_read(
            self.sys.format_data_path("mails.json"), need_file_exists=False, default={}
        )

    def inject_func(self):
        pack = self.backpack.get_registed_item(MAIL_ITEMS)
        assert pack, f"{MAIL_ITEMS}物品未载入系统"
        pack.description = self.format_desc

    def format_desc(self, slot):
        metadatas = slot.metadata
        deadline = metadatas["dtime"] - int_time()
        deadline_str = (
            format_timer_zhcn(deadline // 60)
            if deadline >= 0
            else f"逾期 {format_timer_zhcn(-deadline // 60)}"
        )
        return (
            f"  收件地址： {self.format_address_readable_str(metadatas['addr'])}\n"
            f"  收件剩余期限： {deadline_str}"
        )

    def on_handle_like_mailbox(self, pk):
        x, y, z = pk["Position"]
        content = self.read_addresses()
        if pk["EventData"] != 1 or [x, y, z] not in content:
            return
        self.sys.game_ctrl.sendwocmd(f"setblock {x} {y} {z} planks 1")
        nearestPlayers = getTarget(f"@a[x={x},y={y},z={z},c=1]")
        self.sys.game_ctrl.sendwocmd(f"structure load 收件箱 {x} {y} {z}")
        if nearestPlayers == []:
            self.sys.rpg.show_any("@a", "6", f"§6收件箱被鬼打开了 (在 {x} {y} {z})")
            return
        player = self.sys.rpg.getPlayer(nearestPlayers[0])
        self.submit(player, (x, y, z))

    def place_cb(self, player: Player, _):
        x, y, z = (int(i) for i in player.getPos()[1:])
        self.sys.intr.place_command_block(
            self.sys.intr.make_packet_command_block_update(
                (x, y, z),
                "tellraw @a[tag=sr.rpg_bot] "
                r'{"rawtext":[{"text":"job.maildev.take_items"},{"selector":"@p"}, {"text":"'
                f"{x},{y},{z}"
                r'"}]}',
                need_redstone=True,
            )
        )
        self.sys.rpg.show_succ(player, "放置已完成")
        self.sys.game_ctrl.sendcmd("tp ~~10~")

    def on_add_mailbox(self, player: Player, _):
        x, y, z = (int(i) for i in player.getPos()[1:])
        addr = x, y, z
        self.remove_address(addr)
        self.add_address(addr)
        self.sys.rpg.show_succ(player, f"收件箱已创建在 {addr}")

    def on_remove_mailbox(self, player: Player, _):
        x, y, z = (int(i) for i in player.getPos()[1:])
        addr = x, y, z
        if self.remove_address(addr):
            self.sys.rpg.show_succ(player, "已移除收件箱")
        else:
            self.sys.rpg.show_warn(player, "此处没有收件箱")

    def format_address_db_path(self):
        return self.sys.format_data_path("mail_addresses.json")

    def add_address(self, addr: POS):
        content = self.read_addresses()
        content.append(list(addr))
        utils.tempjson.write(self.format_address_db_path(), content)

    def remove_address(self, addr: POS):
        content = self.read_addresses()
        if res := list(addr) in content:
            content.remove(list(addr))
        utils.tempjson.write(self.format_address_db_path(), content)
        return res

    def read_addresses(self):
        return utils.tempjson.load_and_read(
            self.format_address_db_path(), need_file_exists=False, default=[]
        )

    @staticmethod
    def format_address_readable_str(addr: POS):
        adr1, adr2, adr3 = addr
        s1 = f"N{adr1:.4d}" if adr1 < 0 else adr1
        s2 = f"N{adr2:.4d}" if adr2 < 0 else adr2
        s3 = f"N{adr3:.4d}" if adr3 < 0 else adr3
        return f"{s1}-{s2}-{s3}"

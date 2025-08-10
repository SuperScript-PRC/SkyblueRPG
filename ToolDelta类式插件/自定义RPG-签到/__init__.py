import os
import time
from dataclasses import dataclass
from tooldelta import Player, Plugin, utils, TYPE_CHECKING, plugin_entry


@dataclass
class SignData:
    last_sign_day: int
    last_sign_time: int
    continuous_sign_days: int
    sum_sign_days: int

    @classmethod
    def read(cls, dat):
        return cls(dat["last_t"], dat["last"], dat["cont"], dat["sum"])

    def dump(self):
        return {
            "last_d": self.last_sign_day,
            "last": self.last_sign_time,
            "cont": self.continuous_sign_days,
            "sum": self.sum_sign_days,
        }


SIGN_DELAY = 72000


class CustomRPGSource(Plugin):
    name = "自定义RPG-签到系统"
    author = "SuperScript"
    version = (0, 0, 1)

    def __init__(self, frame):
        super().__init__(frame)
        self.ListenPreload(self.on_def)

    def on_def(self):
        self.rpg = self.GetPluginAPI("自定义RPG")
        self.chatbar = self.GetPluginAPI("聊天栏菜单")
        if TYPE_CHECKING:
            from 自定义RPG import CustomRPG
            from 前置_聊天栏菜单 import ChatbarMenu

            self.rpg: CustomRPG
            self.chatbar: ChatbarMenu
        self.make_data_path()

    def on_sign(self, player: Player):
        sign_data = self.get_sign_data(player)
        if not self.can_sign(sign_data):
            tleft = sign_data.last_sign_time + SIGN_DELAY - self.gtime
            self.rpg.show_fail(player, "你今天已经签到过了")
            self.rpg.show_fail(
                player, f"还需要过 {self.format_timer_zhcn(tleft)} 才可以签到哦"
            )
        else:
            self.sign(player, sign_data)

    def sign(self, player: Player, sign_data: SignData):
        continous_sign_day = sign_data.continuous_sign_days
        self.rpg.show_any(player, "a", f"连续签到 §e{continous_sign_day} §d天")
        self.rpg.show_any(player, "d", f"连续签到 §e{continous_sign_day} §d天")
        self.rpg.show_any(player, "6", f"累计签到 §e{sign_data.sum_sign_days} §6天")
        award_pool = self.get_continous_award_pool()
        award_pool[continous_sign_day - 1](player)
        self.do_flush_sign(player)

    def get_continous_award_pool(self):
        createItems = self.rpg.createItems
        giveItems = self.rpg.giveItems

        def day1(player: Player): ...
        def day2(player: Player):
            giveItems(player, createItems("蔚蓝点", 100))

        def day3(player: Player): ...

        return [day1, day2]

    def get_sign_data(self, player: Player):
        tota = self.get_all_sign_datas()
        return tota.get(player.xuid) or SignData(self.gday, self.gtime, 0, 0)

    def do_flush_sign(self, player: Player):
        tota = self.get_all_sign_datas()
        player_last = tota.get(player.xuid) or SignData(self.gday, self.gtime, 0, 0)
        player_last.sum_sign_days += 1
        if self.is_continuous_sign(player_last):
            player_last.continuous_sign_days += 1
        else:
            player_last.continuous_sign_days = 1
        player_last.last_sign_day = self.gday
        player_last.last_sign_time = self.gtime
        tota[player.xuid] = player_last
        self.set_sign_data(tota)

    def get_all_sign_datas(self) -> dict[str, SignData]:
        f = (
            utils.tempjson.load_and_read(
                self.format_data_path("签到数据.json"),
                need_file_exists=False,
            )
            or {}
        )
        return {k: SignData.read(v) for k, v in f.items()}

    def set_sign_data(self, obj: dict[str, SignData]):
        utils.tempjson.load_and_write(
            os.path.join(self.data_path, "签到数据.json"),
            {k: v.dump() for k, v in obj.items()},
            False,
        )

    def can_sign(self, sign_data: SignData) -> bool:
        return self.gtime - sign_data.last_sign_time > SIGN_DELAY

    def is_continuous_sign(self, sign_data: SignData) -> bool:
        return self.gday - sign_data.last_sign_day <= 1

    @staticmethod
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

    @property
    def gtime(self):
        return int(time.time() - 1728000000)

    @property
    def gday(self):
        return self.gtime // 86400


entry = plugin_entry(CustomRPGSource)

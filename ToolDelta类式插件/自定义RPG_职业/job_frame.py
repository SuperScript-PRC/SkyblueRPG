from typing import Union
from time import time
from tooldelta import Player

if 0:
    from . import CustomRPGJobs

SYSTEM = Union["CustomRPGJobs"]

CREDIT_MIN = -100
CREDIT_MAX = 100


def int_time():
    return int(time()) - 1728000000


class Job:
    name: str
    level: int
    job_levels: tuple[int, ...]

    def __init__(self, sys: SYSTEM):
        self.sys = sys

    def calculate_level(self, exp: int):
        if exp == 0:
            return 1
        for i, j in enumerate(self.job_levels):
            if exp < j:
                return i
        return len(self.job_levels) - 1

    def has_job(self, player: Player):
        return self.sys.has_job(player, self.name)

    def get_level(self, player: Player):
        return self.calculate_level(self.get_exp(player))

    def get_upgrade_exp(self, player: Player):
        return self.job_levels[self.calculate_level(self.get_exp(player))]

    def get_exp(self, player: Player):
        dats = self.get_datas(player)
        if "exp" not in dats.keys():
            # IT WILL NEVER HAPPENS
            player.show("§4ERROR §c你的职业经验数据出错， 请告诉管理员")
            self.sys.logger.error(
                f"{player.name}: {self.name} get exp data error: got {dats}"
            )
        return dats.get("exp", 0)

    def add_exp(self, player: Player, exp: int, showto_player=True):
        datas = self.get_datas(player)
        if "exp" not in datas.keys():
            # IT WILL NEVER HAPPENS
            player.show("§4ERROR §c你的职业经验数据出错， 请告诉管理员")
            self.sys.logger.error(
                f"{player.name}: {self.name} add exp data error: got {datas}"
            )
        datas["exp"] = datas.get("exp", 0) + exp
        if showto_player:
            curr_exp = datas["exp"]
            self.sys.rpg.show_any(
                player, "b", f"{self.name} §f的经验 +{exp} §7({curr_exp})"
            )
        self.write_datas(player, datas)
        if self.sys.LOG:
            if exp > 0:
                self.sys.logger.info(
                    f"{player.name}: {self.name} +exp {exp}({curr_exp})"
                )
        self.sys.save(player)

    def add_credit(self, player: Player, credit: float):
        o = self.sys.loaded_jobdatas[player]["credit"]
        now_credit = self.sys.loaded_jobdatas[player]["credit"] = min(
            o + credit, CREDIT_MAX
        )
        if self.sys.LOG:
            if credit > 0:
                self.sys.logger.info(
                    f"{player.name}: {self.name} +credit {credit} ({now_credit})"
                )

    def reduce_credit(self, player: Player, credit: float):
        o = self.sys.loaded_jobdatas[player]["credit"]
        now_credit = self.sys.loaded_jobdatas[player]["credit"] = max(
            o - credit, CREDIT_MIN
        )
        if self.sys.LOG:
            if credit > 0:
                self.sys.logger.info(
                    f"{player.name}: {self.name} -credit {credit} ({now_credit})"
                )

    def get_datas(self, player: Player) -> dict:
        return self.sys.get_job_datas(player, self.name)

    def write_datas(self, player: Player, datas):
        self.sys.write_job_datas(player, self.name, datas)

    def get_metadatas(self, player: Player):
        return self.get_datas(player).get("metadata", {})

    def write_metadatas(self, player: Player, data: dict):
        datas = self.get_datas(player)
        datas["metadata"] = data
        self.write_datas(player, datas)

    def get_skillpoints(self, player: Player):
        return self.get_metadatas(player).get("skillpoints", 0)

    def set_skillpoints(self, player: Player, skill_points: int):
        metadatas = self.get_metadatas(player)
        metadatas["skillpoints"] = skill_points
        self.write_metadatas(player, metadatas)

    def get_skill_tree_value(self, player: Player, skill_name: str):
        return self.get_metadatas(player).get("stree", {}).get(skill_name)

    def add_skill_tree_value(self, player: Player, skill_name: str):
        (d := self.get_metadatas(player)).setdefault("stree", {})
        d["stree"].setdefault(skill_name, {})
        d["stree"][skill_name] += 1
        self.write_metadatas(player, d)

    def all_employees(self):
        return self.sys.get_job_employees(self.name)

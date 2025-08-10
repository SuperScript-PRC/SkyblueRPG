from typing import Union
from time import time
from tooldelta import Player

if 0:
    from . import CustomRPGJobs

SYSTEM = Union["CustomRPGJobs"]


def int_time():
    return int(time()) - 1728000000


class Job:
    name: str
    level: int
    job_levels: tuple[int, ...]

    def __init__(self, sys: SYSTEM):
        self.sys = sys

    def calculate_level(self, exp: int):
        for i, j in enumerate(self.job_levels):
            if exp < j:
                return i
        return 1

    def get_skillpoints(self, player: Player):
        return self.sys._get_job_skillpoints(player, self.name)

    def set_skillpoints(self, player: Player, skill_points: int):
        self.sys._set_job_skillpoints(player, self.name, skill_points)

    def get_exp(self, player: Player):
        return self.sys._get_job_exp(player, self.name)

    def add_exp(self, player: Player, exp: int):
        self.sys._add_job_exp(player, self.name, exp)

    def add_credit(self, player: Player, credit: float):
        self.sys.add_credit(player, credit)

    def reduce_credit(self, player: Player, credit: float):
        self.sys.reduce_credit(player, credit)

    def read_datas(self, player: Player):
        return self.sys._read_job_datas(player, self.name)

    def write_datas(self, player: Player, kvs):
        self.sys._write_job_datas(player, self.name, kvs)

    def get_skill_tree_point(self, player: Player, skill_name: str):
        return (
            self.sys._read_job_datas(player, self.name).get("stree", {}).get(skill_name)
        )

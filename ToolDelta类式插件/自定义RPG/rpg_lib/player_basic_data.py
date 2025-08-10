from dataclasses import dataclass
from tooldelta import Player
from typing import TYPE_CHECKING

from .frame_effects import RPGEffect
from .rpg_entities import PlayerEntity
from .constants import DEFAULT_HP_MAX, DEFAULT_SPAWNPOINT

if TYPE_CHECKING:
    from .. import CustomRPG


# 玩家的基本属性
# 仅存储玩家的基本信息 (可直接导入导出到JSON, 玩家实体信息不能)
# 可以转换为玩家实体信息 (PlayerEntity)
# 也可以从玩家实体信息转换而来
@dataclass
class PlayerBasic:
    system: "CustomRPG"
    player: Player
    Level: int
    Exp: int
    original_atks: list[int]
    original_defs: list[int]
    HP: int
    HP_max: int
    SpawnPoint: list[int]
    Effects: list[RPGEffect]
    mainhand_weapons_uuid: list[str | None]
    relics_uuid: list[str | None]
    metadatas: dict

    @staticmethod
    def read_from_data_without_effects(system: "CustomRPG", player: Player, data: dict):
        return PlayerBasic(
            system,
            player,
            Level=data["Lv"],
            Exp=data["Exp"],
            original_atks=data["OrgAtks"],
            original_defs=data["OrgDefs"],
            HP=data["HP"],
            HP_max=data["HPmax"],
            SpawnPoint=data["SP"],
            Effects=[],
            mainhand_weapons_uuid=data["MH-UUID"],
            relics_uuid=data["RLC-UUID"],
            metadatas=data.get("MTDatas", {}),
        )

    def dump(self):
        return {
            "Lv": self.Level,
            "Exp": self.Exp,
            "OrgAtks": self.original_atks,
            "OrgDefs": self.original_defs,
            "HP": self.HP,
            "HPmax": self.HP_max,
            "SP": self.SpawnPoint,
            "Effs": [list(i.dump()) for i in self.Effects],
            "MH-UUID": self.mainhand_weapons_uuid,
            "RLC-UUID": self.relics_uuid,
            "MTDatas": self.metadatas,
        }

    # 转换为没有暴击的玩家实体数据类型
    # 因为玩家实体数据类型不存储暴击值
    # TODO: 执行这个方法的一些代码会再一次 update_property_from_basic
    def to_player_entity_with_orig_crit(self):
        s = PlayerEntity(
            self.system,
            self.player,
            self.HP,
            self.HP_max,
            self.original_atks,
            self.original_defs,
            0.2,
            0.2,
            self.Effects,
        )
        self.system.player_holder.player_entities[s.player] = s
        self.system.player_holder.update_property_from_basic(self, s)
        s.died_func = lambda _: self.system.player_holder._player_died_handler(s)
        return s

    # 从实体数据更新玩家基本数据
    # 因为这样才能被保存下来
    # 一般是保存玩家数据的时候先于导出Basic数据调用
    def update_from_player_property(self, prop: PlayerEntity):
        self.HP = prop.hp
        self.HP_max = prop.original_hpmax
        self.Chg = prop.weapon.chg if prop.weapon else 0
        self.Effects = prop.effects

    # 创建一个新的玩家基本信息
    @staticmethod
    def make_new(system: "CustomRPG", player: Player):
        return PlayerBasic(
            system,
            player,
            Level=1,
            Exp=0,
            original_atks=[0] * 7,
            original_defs=[0] * 7,
            HP=DEFAULT_HP_MAX,
            HP_max=DEFAULT_HP_MAX,
            SpawnPoint=DEFAULT_SPAWNPOINT,
            Effects=[],
            mainhand_weapons_uuid=[None] * 4,
            relics_uuid=[None] * 8,
            metadatas={},
        )

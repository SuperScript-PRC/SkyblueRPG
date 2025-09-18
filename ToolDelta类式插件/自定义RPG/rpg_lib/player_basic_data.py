from dataclasses import dataclass
from tooldelta import Player
from typing import TYPE_CHECKING

from .frame_effects import RPGEffect, find_effect_class
from .rpg_entities import PlayerEntity
from .constants import DEFAULT_HP_MAX, DEFAULT_SPAWNPOINT

if TYPE_CHECKING:
    from .. import CustomRPG


@dataclass
class PlayerBasic:
    """
    玩家的基本属性<br>
    仅存储玩家的基本信息 (可直接导入导出到JSON, 玩家实体信息不能)<br>
    可以转换为玩家实体信息 (PlayerEntity)<br>
    也可以从玩家实体信息转换而来<br>
    """

    system: "CustomRPG"
    player: Player
    runtime_id: int
    Level: int
    Exp: int
    original_atks: list[int]
    original_defs: list[int]
    HP: int
    HP_max: int
    SpawnPoint: list[int]
    Effects: list[tuple[str, str, str, int, int]]
    mainhand_weapons_uuid: list[str | None]
    relics_uuid: list[str | None]
    metadatas: dict

    @classmethod
    def read_from_data(cls, system: "CustomRPG", player: Player, data: dict):
        return cls(
            system,
            player,
            system.entity_holder.new_runtimeid(),
            Level=data["Lv"],
            Exp=data["Exp"],
            original_atks=data["OrgAtks"],
            original_defs=data["OrgDefs"],
            HP=data["HP"],
            HP_max=data["HPmax"],
            SpawnPoint=data["SP"],
            Effects=[tuple(i) for i in data["Effs"]],
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
            "Effs": [list(i) for i in self.Effects],
            "MH-UUID": self.mainhand_weapons_uuid,
            "RLC-UUID": self.relics_uuid,
            "MTDatas": self.metadatas,
        }

    def to_player_entity(self):
        """
        - 转换为没有暴击的玩家实体数据类型
        - 因为玩家实体数据类型不存储暴击值
        - 一般只在初始化玩家实体时调用此方法
        TODO: 执行这个方法的一些代码会再一次 update_playerentity_from_basic
        """
        entity = PlayerEntity(
            self.system,
            self.player,
            self.runtime_id,
            self.HP,
            0,
            self.HP_max,
            self.original_atks,
            self.original_defs,
            0.2,
            0.2,
            effects=[],
            died_func=lambda player,
            killer: self.system.player_holder._player_died_handler(player, killer),
        )
        self.system.player_holder._player_entities[entity.player] = entity
        self.system.player_holder.update_playerentity_from_basic(self, entity)
        # === 初始化效果
        effects: list[RPGEffect] = []
        sys = self.system
        for clsname, fromtype, fromwho_str, seconds, level in self.Effects:
            if fromtype == "Player":
                fromwho = sys.game_ctrl.players.getPlayerByXUID(fromwho_str)
                if fromwho is None:
                    fromwho = entity
                else:
                    fromwho = self.system.player_holder.get_playerinfo(fromwho)
            elif fromtype == "Mob":
                fromwho = self.system.mob_holder.load_mobinfo(fromwho_str)
                if fromwho is None:
                    fromwho = entity
            else:
                sys.print_war(f"不明效果来源: {fromwho_str}")
                continue
            effects.append(find_effect_class(clsname)(entity, fromwho, seconds, level))
        entity.effects = effects
        return entity

    def update_from_playerentity(self, entity: PlayerEntity):
        """
        - 从实体数据更新玩家基本数据
        - 因为这样才能被保存下来
        - 一般是保存玩家数据的时候先于导出Basic数据调用
        """
        self.HP = entity.hp
        self.HP_max = entity.original_hpmax
        self.Chg = entity.weapon.chg if entity.weapon else 0
        self.Effects = [i.dump() for i in entity.effects]

    # 创建一个新的玩家基本信息
    @staticmethod
    def make_new(system: "CustomRPG", player: Player):
        return PlayerBasic(
            system,
            player,
            system.entity_holder.new_runtimeid(),
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

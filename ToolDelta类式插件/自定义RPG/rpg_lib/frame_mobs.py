from typing import TYPE_CHECKING

from .constants import SrcType, AttackType

if TYPE_CHECKING:
    from .rpg_entities import MobEntity, ENTITY

ELEMENTS = tuple[int, int, int, int, int, int, int]
"""
蔚蓝空域中, 设定这些元素名称依次为:
- 火属性
- 冰属性
- 草属性
- 雷属性
- 金属性
- 虚空属性
- 末影属性
"""


class Mob:
    """
    - 火属性
    - 冰属性
    - 草属性
    - 雷属性
    - 金属性
    - 虚空属性
    - 末影属性
    """
    model_id: str
    tag_name: str
    type_id: int
    show_name: str
    max_hp: int
    atks: ELEMENTS = (0, 0, 0, 0, 0, 0, 0)
    defs: ELEMENTS = (0, 0, 0, 0, 0, 0, 0)
    effect_hit: float = 0.0
    effect_anti: float = 0.0
    drop_exp_range: tuple[int, int]
    loots: tuple[tuple[str, int, float], ...]
    harmful: bool | None = None
    tags: tuple[str, ...] = ()

    @classmethod
    def init(cls, entity: "MobEntity"):
        pass

    @classmethod
    def attack(
        cls,
        entity: "MobEntity",
        target: "ENTITY",
        src_type: SrcType,
        attack_type: AttackType,
    ):
        target.injured(entity, src_type, attack_type, entity.tmp_atks)

    # 返回: 是否拦截此次伤害
    @classmethod
    def injured(
        cls, entity: "MobEntity", fromwho: "ENTITY", damages: list[int], is_crit: bool
    ) -> bool:
        return False

    # 返回: 是否确认死亡事件
    @classmethod
    def ready_died(
        cls,
        entity: "MobEntity",
        killer: "ENTITY",
    ) -> bool:
        return True

    @classmethod
    def is_harmful(cls):
        if cls.harmful is None:
            cls.harmful = sum(cls.atks) != 0
        return cls.harmful


registered_mobs: dict[str, type[Mob]] = {}


def register_mob_module(module):
    registered_mobs.update(
        {
            j.tag_name: j
            for j in module.__dict__.values()
            if isinstance(j, type) and issubclass(j, Mob) and j != Mob
        }
    )


def find_mob_class_by_id(id: int):
    for _, cls in registered_mobs.items():
        if cls.type_id == id:
            return cls
    raise ValueError(f"No such mob id: {id}")


def find_mob_class_by_tagname(tag_name: str):
    if res := registered_mobs.get(tag_name):
        return res
    raise ValueError(f"No such mob id: {tag_name}")

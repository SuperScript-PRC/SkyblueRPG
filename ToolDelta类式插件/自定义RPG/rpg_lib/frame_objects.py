import time
from typing import ClassVar
from weakref import ref
from .constants import (
    RelicType,
    SrcType,
    AttackType,
    ModelType,
    WeaponType,
    PropVal,
    STARLEVEL,
)
from .lib_rpgitems import ItemWeapon, ItemRelic

if 0:
    from .. import entry as rpg_entry
    from .rpg_entities import PlayerEntity, ENTITY

    UpgradeConfigWeapon = rpg_entry.rpg_upgrade.WeaponUpgradeConfig
    UpgradeConfigRelic = rpg_entry.rpg_upgrade.RelicUpgradeConfig


# player.attack() => 武器确认是否 attack => player.final_attack()
# 七种基本元素属性: 火属性, 冰属性, 草属性, 雷属性, 金属性, 虚空属性, 末影属性


# 道具
class Weapon:
    # 显示名
    show_name: str = "<未命名道具>"
    # 描述
    description: str = "无描述"
    skill_description: str = "无"
    ult_description: str = "无"
    # 道具星级
    star_level: STARLEVEL = 3
    category: WeaponType = WeaponType.SWORD
    "组类"
    default_durability: int = 200
    "最大耐久度"
    cd_skill: int = 5
    "技能冷却秒数"
    cd_ult: int = 5
    "终结技冷却秒数"
    charge_ult: int = 100
    "终结技所需能量"
    need_skill_set: bool = True
    "是否需要在释放技能之前选定目标"
    need_ult_set: bool = True
    "是否需要在释放终结技之前选定目标"
    show_model: ModelType = ModelType.AXE
    "显示的主手模型"
    basic_atks: tuple[int, int, int, int, int, int, int] = (0, 0, 0, 0, 0, 0, 0)
    "武器在初始的攻击 (七种基本元素属性各自的攻击值)"
    repair_materials: ClassVar[dict[str, int]]
    "修复耐久所需材料对应的修复值"
    upgrade_mode: "UpgradeConfigWeapon | None" = None
    "升级方法"

    def __init__(
        self,
        owner: "PlayerEntity",
        level: int,
        exp: int,
        killcount: int,
        durability: int,
        skill_use_last: int,
        charge: int,
        leveled_atks: list[int],
        metadata: dict | None,
    ):
        """
        Args:
            level: 武器等级
            exp: 武器经验值
            killcount: 武器击杀数
            durability: 武器耐久度
            skill_use_last: 最后一次使用武器的时间的时间戳
            charge: 武器充能值
            my_atks: 武器的七种基本属性的攻击
            metadata: 武器额外数据
        """
        self._owner = ref(owner)
        self.level = level
        self.exp = exp
        self.killcount = killcount
        self.durability = durability
        self.metadata = metadata or {}
        self.skill_use_last = skill_use_last
        self.chg = charge
        self.current_atks = leveled_atks

    def on_skill_use(self, target: "ENTITY"):
        "技能使用(有目标), 正常情况下记得 set_cd()"
        pass

    def on_skill_set(self):
        "技能使用(无目标), 正常情况下记得 set_cd()"
        pass

    def on_ult_set(self):
        "终结技使用(无目标), 正常情况下记得 clear_charge()"
        pass

    def on_ult_use(self, target: "ENTITY | None"):
        "终结技使用(有目标), 正常情况下记得 clear_charge()"
        pass

    def set_cd(self):
        self.skill_use_last = int(time.time())

    def add_charge(self, chg: int):
        self.chg = min(self.charge_ult, self.chg + chg)

    def clear_charge(self):
        self.chg = 0

    def show_ult(self, text: str):
        gc = self.owner.sys.game_ctrl
        gc.player_subtitle(self.owner.name, f"§7终结技 §f「{text}§f」")
        gc.player_title(self.owner.name, "§a")

    def use(self):
        "使用一次该武器, 返回是否可使用"
        if self.durability > 0:
            self.durability -= 1
            return True
        else:
            return False

    def add_kill_count(self, count: int = 1):
        self.killcount += count

    def dump_to_item(self, item_weapon: ItemWeapon):
        item_weapon.durability = self.durability
        item_weapon.killcount = self.killcount
        item_weapon.last_skill_used = self.skill_use_last
        item_weapon.charge = self.chg

    @property
    def tag_name(self):
        return self.__class__.__name__

    @property
    def owner(self):
        o = self._owner()
        if o is None:
            raise ValueError("Owner ref lost")
        return o


# 饰品
class Relic:
    show_name: str = "<未命名饰品>"
    description: str = "无描述"
    star_level: STARLEVEL = 3
    category: str = ""
    suit_2nd_description: str = "无"
    suit_4th_description: str = "无"
    types: tuple[RelicType, ...]
    upgrade_mode: "UpgradeConfigRelic | None" = None
    "升级方法"

    def __init__(
        self,
        owner: "PlayerEntity",
        main_props: dict[str, float],
        sub_props: dict[str, float],
        metadata: dict | None = None,
    ):
        "初始化"
        self._owner = ref(owner)
        self.main_props = main_props
        self.sub_props = sub_props
        self.metadata = metadata or {}
        self.suits: int = 0

    def on_use(self):
        pass

    def on_attack(
        self,
        target: "ENTITY",
        src_type: SrcType,
        attack_type: AttackType,
        atks: list[int],
        is_crit: bool,
    ):
        pass

    def on_injured(
        self,
        fromwho: "ENTITY",
        src_type: SrcType,
        attack_type: AttackType,
        atks: list[int],
        is_crit: bool,
    ):
        pass

    def on_skill_use(self, target: "ENTITY | None"):
        pass

    def on_ult_use(self, target: "ENTITY | None"):
        pass

    def on_cure(self, fromwho: "PlayerEntity", cured_hp: int):
        pass

    def on_cured(self, fromwho: "PlayerEntity", cured_hp: int):
        pass

    def on_kill(self, target: "ENTITY"):
        pass

    def on_pre_died(self, killer: "ENTITY"):
        pass

    def on_died(self, killer: "ENTITY"):
        pass

    def on_break_shield(self, fromwho: "ENTITY"):
        pass

    def update_suit(self):
        self.suits = self.owner._get_category_relic_num(self.category)

    @property
    def is_suit_2(self):
        return self.suits >= 2

    @property
    def is_suit_4(self):
        return self.suits >= 4

    @property
    def owner(self):
        o = self._owner()
        if o is None:
            raise ValueError("Owner ref lost")
        return o


registered_weapons: dict[str, type[Weapon]] = {}

registered_relics: dict[str, type[Relic]] = {}


def get_registered_weapons():
    return registered_weapons


def get_registered_relics():
    return registered_relics


def find_weapon_class(name: str):
    for wp_name, wp in registered_weapons.items():
        if wp_name == name:
            return wp
    raise ValueError(f"No such weapon: {name}")


def find_relic_class(name: str):
    for rl_name, rl in registered_relics.items():
        if rl_name == name:
            return rl
    raise ValueError(f"No such weapon: {name}")


def get_weapon_instance(cls: str, owner: "PlayerEntity", item: ItemWeapon):
    return find_weapon_class(cls)(
        owner,
        item.level,
        item.exp,
        item.killcount,
        item.durability,
        item.last_skill_used,
        item.charge,
        item.atks,
        item.slotItem.metadata,
    )


def get_relic_instance(cls: str, owner: "PlayerEntity", item: ItemRelic):
    return find_relic_class(cls)(
        owner,
        PropVal.new(item.main_props),
        PropVal.new(item.sub_props),
        item.slotItem.metadata,
    )


def register_weapon_module(module):
    registered_weapons.update(
        {
            i: j
            for i, j in module.__dict__.items()
            if isinstance(j, type) and issubclass(j, Weapon) and j != Weapon
        }
    )


def register_relic_module(module):
    registered_relics.update(
        {
            i: j
            for i, j in module.__dict__.items()
            if isinstance(j, type) and issubclass(j, Relic) and j != Relic
        }
    )


def execute_on_use(playerinf: "PlayerEntity"):
    cbs = []
    for relic in playerinf.relics:
        if relic:
            cb = relic.on_use
            if cb not in cbs:
                cb()
                cbs.append(cb)


def execute_on_attack(
    playerinf: "PlayerEntity",
    target: "ENTITY",
    src_type: SrcType,
    attack_type: AttackType,
    atks: list[int],
    is_crit: bool,
):
    cbs = []
    for relic in playerinf.relics:
        if relic:
            cb = relic.on_attack
            if cb.__func__ not in cbs:
                cb(target, src_type, attack_type, atks, is_crit)
                cbs.append(cb.__func__)


def execute_on_injured(
    playerinf: "PlayerEntity",
    fromwho: "ENTITY",
    src_type: SrcType,
    attack_type: AttackType,
    atks: list[int],
    is_crit: bool,
):
    cbs = []
    for relic in playerinf.relics:
        if relic:
            cb = relic.on_injured
            if cb.__func__ not in cbs:
                cb(fromwho, src_type, attack_type, atks, is_crit)
                cbs.append(cb.__func__)


def execute_on_skill_use(playerinf: "PlayerEntity", target: "ENTITY | None"):
    cbs = []
    for relic in playerinf.relics:
        if relic:
            cb = relic.on_skill_use
            if cb.__func__ not in cbs:
                cb(target)
                cbs.append(cb.__func__)


def execute_on_ult_use(playerinf: "PlayerEntity", target: "ENTITY | None"):
    cbs = []
    for relic in playerinf.relics:
        if relic:
            cb = relic.on_ult_use
            if cb.__func__ not in cbs:
                cb(target)
                cbs.append(cb.__func__)


def execute_on_cure(playerinf: "PlayerEntity", fromwho: "PlayerEntity", cured_hp: int):
    cbs = []
    for relic in playerinf.relics:
        if relic:
            cb = relic.on_cure
            if cb.__func__ not in cbs:
                cb(fromwho, cured_hp)
                cbs.append(cb.__func__)


def execute_on_cured(playerinf: "PlayerEntity", fromwho: "PlayerEntity", cured_hp: int):
    cbs = []
    for relic in playerinf.relics:
        if relic:
            cb = relic.on_cured
            if cb.__func__ not in cbs:
                cb(fromwho, cured_hp)
                cbs.append(cb.__func__)


def execute_on_kill(playerinf: "PlayerEntity", target: "ENTITY"):
    cbs = []
    for relic in playerinf.relics:
        if relic:
            cb = relic.on_kill
            if cb.__func__ not in cbs:
                cb(target)
                cbs.append(cb.__func__)


def execute_on_pre_died(playerinf: "PlayerEntity", killer: "ENTITY"):
    cbs = []
    for relic in playerinf.relics:
        if relic:
            cb = relic.on_pre_died
            if cb.__func__ not in cbs:
                cb(killer)
                cbs.append(cb.__func__)


def execute_on_died(playerinf: "PlayerEntity", killer: "ENTITY"):
    cbs = []
    for relic in playerinf.relics:
        if relic:
            cb = relic.on_died
            if cb.__func__ not in cbs:
                cb(killer)
                cbs.append(cb.__func__)


def execute_on_break_shield(playerinf: "PlayerEntity", fromwho: "ENTITY"):
    cbs = []
    for relic in playerinf.relics:
        if relic:
            cb = relic.on_break_shield
            if cb.__func__ not in cbs:
                cb(fromwho)
                cbs.append(cb.__func__)

from enum import Enum, IntEnum
from typing import Literal


def category_join(*c: str):
    return ":".join(c)


# 星级类型
STARLEVEL = Literal[1, 2, 3, 4, 5]

# 默认玩家数据
DEFAULT_SPAWNPOINT = [0, -64, 0]
DEFAULT_HP_MAX = 100


# 伤害来源
class SrcType(IntEnum):
    # 普通伤害来源 (实体攻击)
    NORMAL = 0
    # 来自 buff
    FROM_EFFECT = 1
    # 来自道具技能
    FROM_SKILL = 2
    # 来自饰品
    FROM_RELIC = 3


# 道具显示在手上的模型
class ModelType(IntEnum):
    # 铁剑
    SWORDIRON = 3
    # 金剑
    SWORDGOLD = 4
    # 钻石剑
    SWORDDIAMOND = 5
    # 下界合金剑
    SWORDNETHERITE = 6
    # 斧头
    AXE = 7
    # 镐
    PICKAXE = 15
    # 铁斧
    AXEIRON = 17
    # 铲
    SHOVEL = 24
    # BOW = 36
    # TRIDENT = 48


class Category(str, Enum):
    MATERIAL = "材料"
    WEAPON = "武器"
    RELIC = "饰品"

    SWORD = category_join(WEAPON, "剑")
    BOW = category_join(WEAPON, "弓")
    TRIDENT = category_join(WEAPON, "戟")

    HELMET = "头盔"
    CHESTPLATE = "胸甲"
    LEGGINGS = "护腿"
    BOOTS = "护靴"

    RELICA = "天环"
    RELICB = "项链"
    RELICC = "手环"
    RELICD = "腰带"


class HiddenCategory(str, Enum):
    RELIC = "__饰品"

    HELMET = category_join(RELIC, Category.HELMET)
    CHESTPLATE = category_join(RELIC, Category.CHESTPLATE)
    LEGGINGS = category_join(RELIC, Category.LEGGINGS)
    BOOTS = category_join(RELIC, Category.BOOTS)

    RELICA = category_join(RELIC, Category.RELICA)
    RELICB = category_join(RELIC, Category.RELICB)
    RELICC = category_join(RELIC, Category.RELICC)
    RELICD = category_join(RELIC, Category.RELICD)


# 道具类型
class WeaponType(IntEnum):
    # 剑
    SWORD = 0
    # 弓
    BOW = 1
    # 戟
    TRIDENT = 2

    def to_category(self):
        return (Category.SWORD, Category.BOW, Category.TRIDENT)[self.value]


# 护甲/饰品类型
class RelicType(IntEnum):
    # 头盔
    HELMET = 0
    # 胸甲
    CHESTPLATE = 1
    # 护腿
    LEGGINGS = 2
    # 护靴
    BOOTS = 3
    # A 类 (天环)
    A = 4
    # B 类 (项链)
    B = 5
    # C 类 (手环)
    C = 6
    # D 类 (腰带)
    D = 7

    def to_category(self):
        return (
            Category.HELMET,
            Category.CHESTPLATE,
            Category.LEGGINGS,
            Category.BOOTS,
            Category.RELICA,
            Category.RELICB,
            Category.RELICC,
            Category.RELICD,
        )[self.value]

    def to_hidden_category(self):
        return category_join(HiddenCategory.RELIC, self.to_category())

    def to_full_category(self, tagname: str):
        return category_join(Category.RELIC, tagname, self.to_category())

    def to_full_display_category(self, disp_name: str):
        return category_join(Category.RELIC, disp_name, self.to_category())


class AttackType(IntEnum):
    # 普通攻击
    NORMAL = 0
    # 无视护甲的攻击
    NON_SHIELD = 1
    # 真实攻击 (无视护甲, 减伤效果等)
    REAL = 2
    # 其他类型
    OTHER = 3


# buff 的类型
class EffectType(IntEnum):
    # 中性效果
    NEUTRAL = 0
    # 有益效果
    POSITIVE = 1
    # 有害效果
    NEGATIVE = 2


class Properties(str, Enum):
    ATKBoost = "攻击力加成"
    DEFBoost = "防御力加成"
    HPBoost = "生命提升"
    HPBoostAdd = "生命提升加成"
    EffectHit = "效果命中"
    EffectRes = "效果抵抗"
    CritChance = "暴击率"
    CritDamage = "暴击伤害"
    ChargeAdd = "充能效率"

    ATK1 = "属性1攻击力"
    ATK2 = "属性2攻击力"
    ATK3 = "属性3攻击力"
    ATK4 = "属性4攻击力"
    ATK5 = "属性5攻击力"
    ATK6 = "属性6攻击力"
    ATK7 = "属性7攻击力"
    DEF1 = "属性1防御力"
    DEF2 = "属性2防御力"
    DEF3 = "属性3防御力"
    DEF4 = "属性4防御力"
    DEF5 = "属性5防御力"
    DEF6 = "属性6防御力"
    DEF7 = "属性7防御力"
    ATK1Add = "属性1攻击力加成"
    ATK2Add = "属性2攻击力加成"
    ATK3Add = "属性3攻击力加成"
    ATK4Add = "属性4攻击力加成"
    ATK5Add = "属性5攻击力加成"
    ATK6Add = "属性6攻击力加成"
    ATK7Add = "属性7攻击力加成"
    DEF1Add = "属性1防御力加成"
    DEF2Add = "属性2防御力加成"
    DEF3Add = "属性3防御力加成"
    DEF4Add = "属性4防御力加成"
    DEF5Add = "属性5防御力加成"
    DEF6Add = "属性6防御力加成"
    DEF7Add = "属性7防御力加成"

    @classmethod
    def atks(cls):
        return (
            cls.ATK1,
            cls.ATK2,
            cls.ATK3,
            cls.ATK4,
            cls.ATK5,
            cls.ATK6,
            cls.ATK7,
        )

    @classmethod
    def defs(cls):
        return (
            cls.DEF1,
            cls.DEF2,
            cls.DEF3,
            cls.DEF4,
            cls.DEF5,
            cls.DEF6,
            cls.DEF7,
        )

    @classmethod
    def atk_adds(cls):
        return (
            cls.ATK1Add,
            cls.ATK2Add,
            cls.ATK3Add,
            cls.ATK4Add,
            cls.ATK5Add,
            cls.ATK6Add,
            cls.ATK7Add,
        )

    @classmethod
    def def_adds(cls):
        return (
            cls.DEF1Add,
            cls.DEF2Add,
            cls.DEF3Add,
            cls.DEF4Add,
            cls.DEF5Add,
            cls.DEF6Add,
            cls.DEF7Add,
        )


class PropVal(float, Enum):
    "属性等级对应属性数值 乘法映射"

    GenericATK = 1.5
    GenericDEF = 1.5
    GenericATKAdd = 0.1
    GenericDEFAdd = 0.1
    ElementedATKAdd = 0.1
    ElementedDEFAdd = 0.1
    HPBoost = 10
    HPBoostAdd = 0.12
    ChargeAdd = 0.1
    Crit = 0.05
    CritAdd = 0.12
    EffectHit = 0.05
    EffectRes = 0.05

    @staticmethod
    def new(mapping: dict):
        return {k: PROPVAL_MAPPING[k] * v for k, v in mapping.items()}


PROPVAL_MAPPING = {
    Properties.ATKBoost: PropVal.GenericATK,
    Properties.DEFBoost: PropVal.GenericDEF,
    Properties.HPBoost: PropVal.HPBoost,
    Properties.HPBoostAdd: PropVal.HPBoostAdd,
    Properties.ChargeAdd: PropVal.ChargeAdd,
    Properties.CritChance: PropVal.Crit,
    Properties.CritDamage: PropVal.CritAdd,
    Properties.EffectHit: PropVal.EffectHit,
    Properties.EffectRes: PropVal.EffectRes,
}
PROPVAL_MAPPING.update(
    dict(
        (
            *((i, PropVal.GenericATK) for i in Properties.atks()),
            *((i, PropVal.GenericDEF) for i in Properties.defs()),
            *((i, PropVal.GenericATKAdd) for i in Properties.atk_adds()),
            *((i, PropVal.GenericDEFAdd) for i in Properties.def_adds()),
        )
    )
)

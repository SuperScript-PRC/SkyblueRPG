import time
from dev_rpg_lib import constants, frame_objects, rpg_entities, upgrade_lib  # type: ignore[reportMissingModuleSource]

# A: 天环
# B: 项链
# C: 手环
# D: 腰带

default_upgrade_mode = upgrade_lib.RelicUpgradeConfig(
    max_level=15,
    upgrade_exp_syntax=lambda x: int(300 * (1 + x / 20)),
    sub_prop_levels=(2, 3, 5, 7, 11, 14, 15),
    available_upgrade_materials={
        "魔金粒": 50,
        "魔钢锭": 300,
        "魔金锭": 450,
        "魔力珍珠": 750,
        "魔力砂金": 860,
        "魔力钻石": 1200,
    },
    upgrade_level_limit_materials={},
    main_props_weight={
        "生命提升": 2.5,
        "属性1攻击力": 0.15,
        "属性2攻击力": 0.15,
        "属性3攻击力": 0.15,
        "属性4攻击力": 0.15,
        "属性5攻击力": 0.15,
        "属性6攻击力": 0.15,
        "属性7攻击力": 0.15,
        "属性1防御力": 0.15,
        "属性2防御力": 0.15,
        "属性3防御力": 0.15,
        "属性4防御力": 0.15,
        "属性5防御力": 0.15,
        "属性6防御力": 0.15,
        "属性7防御力": 0.15,
    },
    sub_props_weight={
        "生命提升": 1.5,
        "生命提升加成": 1,
        "攻击力加成": 2,
        "防御力加成": 2,
        "属性1攻击力加成": 0.2,
        "属性2攻击力加成": 0.2,
        "属性3攻击力加成": 0.2,
        "属性4攻击力加成": 0.2,
        "属性5攻击力加成": 0.2,
        "属性6攻击力加成": 0.2,
        "属性7攻击力加成": 0.2,
        "属性1防御力加成": 0.15,
        "属性2防御力加成": 0.15,
        "属性3防御力加成": 0.15,
        "属性4防御力加成": 0.15,
        "属性5防御力加成": 0.15,
        "属性6防御力加成": 0.15,
        "属性7防御力加成": 0.15,
        "暴击率": 1.5,
        "暴击伤害": 1.5,
    },
    extra_materials={},
)

Relic = frame_objects.Relic
RelicType = constants.RelicType
ENTITY = rpg_entities.ENTITY
SrcType = frame_objects.SrcType


class SatelleIronHelmet(Relic):
    types = (RelicType.HELMET,)
    category = "陨铁套装"
    show_name = "陨铁头盔"
    star_level = 3
    suit_2nd_description = "生命值低于§635%§a时， 全属性防御力提高10%。"
    upgrade_mode = default_upgrade_mode

    def on_injured(self, fromwho, src_type, attack_type, atks, is_crit):
        if self.owner.hp <= self.owner.basic_hp_max * 0.35 and self.is_suit_2:
            self.owner.tmp_def_add = [0.1 + i for i in self.owner.tmp_def_add]


class SatelleIronChestplate(SatelleIronHelmet):
    types = (RelicType.CHESTPLATE,)
    show_name = "陨铁护甲"


class SatelleIronLeggings(SatelleIronHelmet):
    types = (RelicType.LEGGINGS,)
    show_name = "陨铁护腿"


class SatelleIronBoots(SatelleIronHelmet):
    types = (RelicType.BOOTS,)
    show_name = "陨铁护靴"


class GrassSeedA(Relic):
    types = (RelicType.A,)
    category = "精蕴魔法的鲜草"
    show_name = "§2蕴生木种之冠"
    star_level = 4
    suit_2nd_description = "§a生命值上限增加§67%§a。"
    suit_4th_description = (
        "§a当消灭目标后，§610§a秒内每次攻击时恢复自身§62%§a的生命值。"
    )
    upgrade_mode = default_upgrade_mode

    def on_use(self):
        self.utime = 0
        if self.is_suit_2:
            self.owner.basic_hp_max = int(self.owner.basic_hp_max * 1.07)

    def on_kill(self, target):
        if self.is_suit_4:
            self.utime = time.time()

    def on_attack(
        self, target: ENTITY, src_type, attack_type, atks: list[int], is_crit
    ):
        if (
            self.is_suit_4
            and src_type in (SrcType.NORMAL, SrcType.FROM_SKILL)
            and time.time() - self.utime <= 10
        ):
            self.owner.cured(
                self.owner, SrcType.FROM_RELIC, int(self.owner.tmp_hp_max * 0.02)
            )


class GrassSeedB(GrassSeedA):
    types = (RelicType.B,)
    show_name = "§2蕴生木种之坠"


class GrassSeedC(GrassSeedA):
    types = (RelicType.C,)
    show_name = "§2蕴生木种之戒"


class GrassSeedD(GrassSeedA):
    types = (RelicType.D,)
    show_name = "§2蕴生木种之缔"

from dev_rpg_lib import (  # type: ignore[reportMissingModuleSource]
    constants,
    frame_objects,
    frame_effects,
    upgrade_lib,
    rpg_entities,
)

# ruff: noqa: RUF012

# 1: 20

# 七种属性: 火 冰 草 雷 金 虚空 末影.

Weapon = frame_objects.Weapon
ModelType = frame_objects.ModelType
ENTITY = rpg_entities.ENTITY
SrcType = constants.SrcType
AttackType = constants.AttackType

default_upgrade_mode = upgrade_lib.WeaponUpgradeConfig(
    80,
    lambda x, y: int(x * (1 + y / 16) ** 2),
    available_upgrade_materials={"大经验书": 1000},
    upgrade_exp_syntax=lambda x: int(500 + x * 20),
    upgrade_level_limit_materials={10: {"石英晶": 5}},
    extra_materials={},
)


# 教学用剑
class SwordDemo(Weapon):
    show_name = "§f无铭剑"
    default_durability = 500
    repair_materials = {}
    need_skill_set = True
    need_ult_set = True
    cd_skill = 5
    charge_ult = 25
    show_model = ModelType.SWORDIRON
    basic_atks = (0, 4, 6, 0, 0, 0, 0)
    upgrade_mode = None

    def on_skill_use(self, target: ENTITY):
        self.owner.attack(target, atks=[int(x * 2) for x in self.owner.tmp_atks])
        self.set_cd()

    def on_ult_use(self, target: ENTITY):
        self.owner.attack(target, atks=[int(x * 3) for x in self.owner.tmp_atks])
        self.clear_charge()


# 钢刃: 无铭
# 技能: 施加 20s 的流血 I 效果
class SwordWuMing(Weapon):
    show_name = "§f钢刃 §l[§6无铭§f]"
    repair_materials = {"精炼铁锭": 80}
    need_skill_set = True
    need_ult_set = True
    cd_skill = 5
    show_model = ModelType.SWORDIRON
    basic_atks = (0, 4, 6, 0, 10, 0, 0)
    upgrade_mode = default_upgrade_mode

    def on_skill_use(self, target: ENTITY):
        # 技能使用
        # 流血
        target.add_effect(
            frame_effects.find_effect_class("Blooding"), self.owner, 20, 1
        )
        self.owner.attack(target)
        self.set_cd()


# 钢刃: 源初
# 技能: 给予敌人流血 等级: int(等级/10) 5秒
# 无终结技
class SwordYuanChu(Weapon):
    show_name = "§f钢刃 §l[§a源初§f]"
    star_level = 4
    repair_materials = {"精炼铁锭": 80}
    need_skill_set = True
    need_ult_set = True
    cd_skill = 20
    show_model = ModelType.SWORDIRON
    basic_atks = (8, 4, 4, 0, 0, 0, 0)
    upgrade_mode = default_upgrade_mode

    def on_skill_use(self, target: ENTITY):
        target.add_effect(
            frame_effects.find_effect_class("Blooding"), self.owner, 5, self.level // 10
        )
        self.owner.add_effect(
            frame_effects.find_effect_class("Shield"), self.owner, 30, 40
        )
        self.set_cd()

    def on_ult_use(self, target: ENTITY):
        self.clear_charge()


# 钢刃: 霜枫 (已完成)
# 技能: 根据目标的负面效果数造成追加伤害, 次数为负面效果数, 最多5次
# 终结技: 触发一次目标上的所有负面效果 (5次)
class SwordShuangFeng(Weapon):
    show_name = "§f钢刃 §l[§3霜枫§f]"
    star_level = 4
    repair_materials = {"精炼铁锭": 80}
    need_skill_set = True
    need_ult_set = True
    cd_skill = 20
    charge_ult = 50
    show_model = ModelType.SWORDIRON
    basic_atks = (12, 5, 7, 6, 8, 4, 6)
    upgrade_mode = default_upgrade_mode

    def on_skill_use(self, target: ENTITY):
        # 技能使用
        effects_num = 0
        for bad_eff in (
            frame_effects.find_effect_class("Slowness"),
            frame_effects.find_effect_class("Blooding"),
            frame_effects.find_effect_class("Burning"),
            frame_effects.find_effect_class("Freezing"),
            frame_effects.find_effect_class("Potion"),
            frame_effects.find_effect_class("Puzzling"),
        ):
            if frame_effects.has_effect(target, bad_eff):
                effects_num += 1
        for _ in range(min(effects_num, 5)):
            self.owner.attack(
                target,
                SrcType.FROM_SKILL,
            )
        self.set_cd()

    def on_ult_use(self, target: ENTITY):
        count = 0
        for bad_eff in target.effects:
            if count < 5:
                bad_eff.on_ticking()
                count += 1
        self.clear_charge()


# 钢刃: 炽焱
# 技能: 扣除 HP 提高攻击力
# 终结技: 根据扣除的 HP 提高攻击力 (提高等级为 int(扣除生命值百分比 * 7))
class SwordChiYan(Weapon):
    show_name = "§f钢刃 §l[§c赤焱§f]"
    star_level = 4
    repair_materials = {"精炼铁锭": 80}
    cd_skill = 15
    charge_ult = 60
    show_model = ModelType.SWORDGOLD
    basic_atks = (14, 0, 3, 0, 3, 0, 0)
    upgrade_mode = default_upgrade_mode

    def on_skill_use(self, target: ENTITY):
        sub_hp = int(self.owner.tmp_hp_max * 0.2)
        if self.owner.hp > sub_hp:
            self.owner.hp -= sub_hp
            self.owner.add_effect(
                frame_effects.find_effect_class("ATKBoost"),
                self.owner,
                10,
                self.level // 10,
                self.owner.tmp_effect_hit,
            )
        self.set_cd()

    def on_ult_use(self, target: ENTITY):
        hp_sub_percent = 1 - self.owner.hp / self.owner.tmp_hp_max
        self.owner.add_effect(
            frame_effects.find_effect_class("ATKBoost"),
            self.owner,
            30,
            int(hp_sub_percent * 7),
        )
        self.clear_charge()


# 钢刃: 极光
# 技能: 施加 30s `裂伤` 效果
# 终结技: 为周围 10 格实体引爆一次 `裂伤` 效果
class SwordJiGuang(Weapon):
    show_name = "§f钢刃 §l[§b极光§f]"
    star_level = 5
    repair_materials = {"精炼铁锭": 80}
    cd_skill = 15
    charge_ult = 45
    default_durability = 620
    show_model = ModelType.SWORDIRON
    basic_atks = (5, 2, 3, 0, 0, 7, 3)
    upgrade_mode = default_upgrade_mode

    def on_skill_use(self, target: ENTITY):
        target.add_effect(frame_effects.find_effect_class("Crackling"), self.owner, 30)
        self.set_cd()

    def on_ult_use(self, target: ENTITY):
        nearest_players, nearest_mobs = (
            self.owner.system.entity_holder.get_surrounding_entities(
                self.owner.name, "r=10"
            )
        )
        for entity in nearest_players + nearest_mobs:
            for effect in entity.effects:
                if isinstance(effect, frame_effects.find_effect_class("Crackling")):
                    effect.on_ticking()

        self.clear_charge()


# 钢刃: 吹雪
# 技能:
class SwordChuiXue(Weapon):
    cd_skill = 15
    charge_ult = 60
    basic_atks = (1, 1, 1, 1, 1, 1, 1)
    upgrade_mode = default_upgrade_mode

    def on_ult_use(self, target: "ENTITY"):
        self.owner.run_cmd(
            "execute at %t at @s run camera minecraft:free ease 0.2 linear pos ^^2^4 facing ~~2~"
        )


# 钢刃: 蔚空之蓝 (OP武器)
class SwordWeiKongZL(Weapon):
    show_name = "§f钢刃 §l[§b§l蔚空之蓝§f]"
    star_level = 5
    repair_materials = {"精炼铁锭": 80}
    cd_skill = 2
    charge_ult = 5
    show_model = ModelType.SWORDDIAMOND
    basic_atks = (1, 1, 1, 1, 1, 1, 1)
    upgrade_mode = default_upgrade_mode

    def on_skill_use(self, target: ENTITY):
        # self.tmp
        self.owner.tmp_atks = [1000, 1000, 1000, 1000, 1000, 1000, 1000]
        self.owner.final_attack(target, SrcType.FROM_SKILL, AttackType.NORMAL, True)
        self.set_cd()


# 精钢斧
class AxeRefinedIron(Weapon):
    show_name = "精炼铁斧"
    star_level = 3
    repair_materials = {"精炼铁锭": 80}
    cd_skill = 30
    charge_ult = 50
    default_durability = 200
    basic_atks = (0, 3, 4, 0, 0, 5, 8)
    show_model = ModelType.AXEIRON

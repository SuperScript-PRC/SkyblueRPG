import time as _time
from dev_rpg_lib import frame_effects, rpg_entities, constants, utils  # type: ignore[reportMissingModuleSource]

RPGEffect = frame_effects.RPGEffect
EffectType = frame_effects.EffectType
PlayerEntity = rpg_entities.PlayerEntity
MobEntity = rpg_entities.MobEntity
ENTITY = rpg_entities.ENTITY
AttackType = constants.AttackType
SrcType = constants.SrcType

# 自定义效果


class Shield(RPGEffect):
    "提供 (当前等级 * 10) 的护盾"

    icon = "§b◘"
    name = "护盾"
    type = EffectType.POSITIVE
    target_type = -1

    def __init__(self, target, fromwho, seconds: int, level: int = 1):
        super().__init__(target, fromwho, seconds, level)
        self.target.add_shield(self.level * 10)

    def __del__(self):
        self.target.remove_shield(self.level * 10)


class ATKBoost(RPGEffect):
    "全属性攻击力提升 5% * (当前等级 + 1)"

    icon = "§7†"
    name = "攻击提升"
    type = EffectType.POSITIVE
    target_type = -1

    def on_basic(self):
        self.target.tmp_atk_add = [
            x + (self.level + 1) * 0.05 for x in self.target.tmp_atk_add
        ]


class DEFBoost(RPGEffect):
    "总的防御力提升 5% * (当前等级 + 1) (ADD)"

    icon = "§b♓"
    name = "防御提升"
    type = EffectType.POSITIVE
    target_type = -1

    def on_basic(self):
        self.target.tmp_def_add = [
            x + (self.level + 1) * 0.05 for x in self.target.tmp_def_add
        ]


class HealthBoost(RPGEffect):
    # 生命提升
    icon = "§c♥"
    name = "生命提升"
    type = EffectType.POSITIVE
    target_type = -1

    def on_basic(self):
        self.target.tmp_hp_add += self.level * 0.02


class CritPerCentBoost(RPGEffect):
    icon = "§f‡"
    name = "暴击率提升"
    type = EffectType.POSITIVE
    target_type = -1

    def on_basic(self):
        if isinstance(self.target, PlayerEntity):
            self.target.tmp_crit_pc += self.level + 0.05


class KillMobCharging(RPGEffect):
    "击杀目标后回复 (当前充能上限 * 0.5) 的充能值"

    icon = "§d◎"
    name = "景星助狩月"
    type = EffectType.POSITIVE
    target_type = 0

    def on_kill(self, target):
        if (
            isinstance(target, MobEntity)
            and isinstance(self.target, PlayerEntity)
            and self.target.weapon
        ):
            self.target.weapon.chg += min(
                int(self.target.weapon.charge_ult * 0.5), self.target.weapon.charge_ult
            )


class CuredCritBoost(RPGEffect):
    # 被治疗后暴击率提高
    icon = "§7➹"
    name = "愈害"
    type = EffectType.POSITIVE
    target_type = 0

    def on_cured(self, fromwho: ENTITY, cure_type, cured_hp):
        self.target.add_effect(CritPerCentBoost, self.fromwho, 30, 1)


class CuredEach(RPGEffect):
    # 被治疗后治疗者回复治疗量的一半的生命值
    icon = "§e♥"
    name = "慈怀"
    type = EffectType.POSITIVE
    target_type = -1

    def on_cured(self, fromwho, cure_type, curehp):
        if cure_type != SrcType.FROM_EFFECT:
            self.target.cured(fromwho, SrcType.FROM_EFFECT, int(curehp / 2))


class AttackBack(RPGEffect):
    icon = "§b☯"
    name = "盾反"
    type = EffectType.NEUTRAL
    target_type = -1

    def on_injured(self, fromwho: "ENTITY", attack_type, dmgs, _):
        if attack_type == SrcType.NORMAL:
            self.target.attack(
                fromwho,
                SrcType.FROM_EFFECT,
                AttackType.NORMAL,
                [int(i * 0.2 * self.level) for i in dmgs],
            )


class WarPath(RPGEffect):
    # 加强攻击
    icon = "§c☍"
    name = "战意"
    type = EffectType.POSITIVE
    target_type = -1

    def on_basic(self):
        self.target.tmp_atk_add = utils.list_multi(
            self.target.tmp_atk_add, [1 + 0.02 * self.level] * 7
        )


class HiEnergy(RPGEffect):
    # 充能效率提高
    icon = "§e℗"
    name = "高能"
    type = EffectType.POSITIVE
    target_type = 0

    def on_basic(self):
        if isinstance(self.target, PlayerEntity):
            self.target.tmp_chg_add += 0.05 * self.level


class Invincible(RPGEffect):
    icon = "§d۞"
    name = "无敌"
    type = EffectType.POSITIVE
    target_type = -1

    def on_injured(self, _, _2, dmgs: list[int], _3):
        if sum(dmgs) <= self.target.hp:
            dmgs[:] = utils.list_multi(dmgs, [0, 0, 0, 0, 0, 0, 0])

    def on_basic(self):
        if self.level > 1:
            self.target.tmp_defs = [int(1e12) for _ in range(len(self.target.tmp_defs))]
        if self.level > 2:
            self.target.tmp_atks = [int(1e12) for _ in range(len(self.target.tmp_atks))]


class Blooding(RPGEffect):
    "每秒减去10*当前等级的生命值"

    icon = "§4♥"
    name = "流血"
    type = EffectType.NEGATIVE
    target_type = -1

    def on_ticking(self):
        self.target.real_injured(
            self.fromwho, SrcType.FROM_EFFECT, 10 * (self.level + 1)
        )
        return True


class Slowness(RPGEffect):
    icon = "§7☍"
    name = "缓慢"
    type = EffectType.NEGATIVE
    target_type = -1

    def __init__(self, target, fromwho, seconds: int, level: int = 1):
        super().__init__(target, fromwho, seconds, level)
        self.sys = self.target.system

    def on_ticking(self):
        sendcmd = self.sys.game_ctrl.sendwocmd
        if isinstance(self.target, PlayerEntity):
            sendcmd(f"effect @a[name={self.target.name}] slowness 2 {self.level - 1}")
        else:
            sendcmd(
                f"effect @e[scores={{sr:ms_uuid={(self.target.uuid)}}}] slowness 2 {self.level - 1}"
            )
        return True


class Burning(RPGEffect):
    icon = "§c♨"
    name = "灼烧"
    type = EffectType.NEGATIVE
    target_type = -1

    def __init__(self, target, giver: ENTITY, seconds: int, level: int = 1):
        super().__init__(target, giver, seconds, level)
        self.sys = self.target.system

    def on_ticking(self):
        self.target.injured(
            self.target,
            SrcType.FROM_EFFECT,
            AttackType.NON_SHIELD,
            [5 + 5 * self.level, 0, 0, 0, 0, 0, 0],
        )
        self.target.run_cmd("damage @s %t 1 entity_attack entity @s")
        return True


class Freezing(RPGEffect):
    icon = "§b☍"
    name = "冻结"
    type = EffectType.NEGATIVE
    target_type = -1

    def __init__(self, target, fromwho, seconds: int, level: int = 1):
        super().__init__(target, fromwho, seconds, level)
        self.sys = self.target.system

    def on_ticking(self):
        self.target.injured(
            self.target,
            SrcType.FROM_EFFECT,
            AttackType.NON_SHIELD,
            [0, 6 * self.level, 0, 0, 0, 0, 0],
        )
        self.target.run_cmd(f"effect %t slowness 2 {self.level - 1}")
        return True


class Potion(RPGEffect):
    icon = "§2¤"
    name = "中毒"
    type = EffectType.NEGATIVE
    target_type = -1

    def on_ticking(self):
        self.target.injured(
            self.target,
            SrcType.FROM_EFFECT,
            AttackType.NON_SHIELD,
            [5 * self.level] * 7,
        )
        return True


class Puzzling(RPGEffect):
    "当受击时, 若距上次受击不足 0.5 秒, 获得 缓慢| (等级/2+1)秒效果"

    icon = "☡"
    name = "眩晕"
    type = EffectType.NEGATIVE
    target_type = -1

    def __init__(self, target, fromwho, seconds: int, level: int = 1):
        super().__init__(target, fromwho, seconds, level)
        self.last_attack = 0

    def on_injured(self, fromwho: PlayerEntity | MobEntity, attack_type, dmgs, iscrit):
        attack_g = _time.time() - self.last_attack
        if attack_g <= 0.5:
            self.target.run_cmd(f"effect %t slowness {self.level // 2 + 1} 0 true")
            if attack_g <= 0.35:
                self.target.run_cmd(f"effect %t blindness {self.level // 3 + 1} 0 true")
        self.last_attack = _time.time()


class Reborn(RPGEffect):
    "当攻击时, 回复 (自身HP x 2% x 等级 的生命值)"

    icon = "§e♥"
    name = "复生"
    type = EffectType.POSITIVE
    target_type = -1

    def on_attack(self, target, src_type, attack_type, dmgs, iscrit):
        if src_type == SrcType.NORMAL:
            hp_max = self.target.tmp_hp_max
            self.target.cured(
                target, SrcType.FROM_EFFECT, int(hp_max * 0.02 * self.level)
            )


class Crackling(RPGEffect):
    "当受击时, 额外受到 (生命上限 * (3% + 等级%)) 的金属性伤害"

    icon = "§7Y"
    name = "裂伤"
    type = EffectType.NEGATIVE
    target_type = -1

    def on_injured(self, target, src_type, attack_type, dmgs, iscrit):
        if src_type == SrcType.NORMAL:
            sub_hp = self.target.tmp_hp_max * (0.03 + 0.02 * self.level)
            self.target.injured(
                self.fromwho,
                SrcType.FROM_EFFECT,
                AttackType.NON_SHIELD,
                [0, 0, 0, 0, int(sub_hp), 0, 0],
            )
            self.target.hp = max(0, int(self.target.hp - sub_hp * self.level))


class Weakness(RPGEffect):
    def on_basic(self):
        self.target.tmp_def_add


class Kindness(RPGEffect):
    icon = "§e㉿"
    name = "慈善"


class ColorAperture(RPGEffect):
    icon = "§e◎"
    name = "七色光圈"


class SChiYan_ATKBoost(RPGEffect):
    "攻击力提升 5% * (当前等级 + 1) (ADD)"

    icon = "§c➹"
    name = "攻击提升"
    type = EffectType.POSITIVE
    target_type = -1

    def on_basic(self):
        self.target.tmp_atk_add = [
            x + (self.level + 1) * 0.05 for x in self.target.tmp_atk_add
        ]

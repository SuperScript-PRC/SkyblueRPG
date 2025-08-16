import random
from typing import Callable, TYPE_CHECKING, Union  # noqa: UP035

from tooldelta import Player
from .constants import SrcType, AttackType
from .utils import (
    list_add,
    list_multi,
    list_sub,
    hurt_calc,
    make_entity_panel,
)
from . import frame_objects
from . import frame_effects
from . import frame_mobs
from .frame_effects import RPGEffect, EffectType, add_effect, find_effect_class

ENTITY = Union["PlayerEntity", "MobEntity"]
SWORD_ICON = ""  # ⚔

if TYPE_CHECKING:
    from rpg_lib.frame_objects import Weapon, Relic
    from .. import CustomRPG

# define: 七种基本属性: 火属性, 冰属性, 草属性, 雷属性, 金属性, 虚空属性, 末影属性

# 有关变量的说明
# original_ 开头的变量 表示属于这个实体的原生属性 不可改变
# basic_ 开头的变量 表示使用了武器和饰品后的玩家的属性
# tmp_ 开头的变量 表示在战斗中判定了效果后改变的属性
# 例如:
# original_hpmax: 玩家自身生命上限
# basic_hpmax: 玩家穿戴了饰品后的生命上限
# tmp_hpmax: 玩家穿戴了饰品和武器并判定了效果后的生命上限, 是临时的


# 玩家的数据化实体属性
# 主要记录战斗属性, 不记录等级经验值等数据
class PlayerEntity:
    def __init__(
        self,
        system: "CustomRPG",
        player: Player,  # 玩家名
        hp: int,  # 当前生命值
        original_hpmax: int,  # 玩家自身生命上限
        original_atks: list[int],  # 玩家自身攻击力, 为七种基本属性的攻击力
        original_defs: list[int],  # 玩家自身防御力, 为七种基本属性的防御力
        original_crit_pc: float,  # 暴击率
        original_crit_add: float,  # 暴击加成率
        effects: list[RPGEffect] | None = None,  # 携带的效果
        died_func: Callable[["PlayerEntity"], None] = lambda _: None,  # 死亡回调
    ):
        """
        Args:
            name: 玩家名
            hp: 当前生命值
            original_atks: 玩家自身攻击力
            original_defs: 玩家自身防御力
            original_hpmax: 玩家自身生命上限
            original_crit_pc: 玩家自身暴击率
            original_crit_add: 玩家自身暴击伤害
            chg: 当前能量
            chg_max: 充能上限
            basic_chg_add: 充能效率
            effects: 效果
            died_func: 死亡回调
        """
        self.system = system
        self.player = player
        self.name = player.name
        self.hp = hp
        self.original_atks = original_atks
        self.original_defs = original_defs
        self.original_hpmax = original_hpmax
        self.original_crit_pc = original_crit_pc
        self.original_crit_add = original_crit_add
        self.died_func = died_func
        self.effects = effects.copy() if effects else []
        self.variables = {}
        self.basic_atk_add: list = [0, 0, 0, 0, 0, 0, 0]
        self.basic_def_add: list = [0, 0, 0, 0, 0, 0, 0]
        self.basic_effect_hit = 0.0
        self.basic_effect_anti = 0.0
        self.cure_add = 0
        self.shield = 0
        self.weapon: Weapon | None = None
        self.relics: list["Relic | None"] = []
        self.is_skill_set = False
        self.is_ult_set = False
        self.pvp = False

    def init_basic(
        self,
        atks: list[int],
        defs: list[int],
        atk_add: list[float],
        def_add: list[float],
        crit_pc: float,
        crit_add: float,
        chg_add: float,
        hp_max_addition: int,
        cure_add: float,
        basic_effect_hit: float,
        basic_effect_anti: float,
    ):
        "在角色使用武器后更新角色攻击力等, 每使用一次就是刷新数据"
        self.basic_atks = list_add(self.original_atks, atks)
        self.basic_defs = list_add(self.original_defs, defs)
        self.basic_hp_max = self.original_hpmax + hp_max_addition
        self.basic_atk_add = atk_add
        self.basic_def_add = def_add
        self.basic_crit_pc = self.original_crit_pc + crit_pc
        self.basic_crit_add = self.original_crit_add + crit_add
        self.basic_chg_add = chg_add
        self.basic_cure_add = cure_add
        self.basic_effect_hit = basic_effect_hit
        self.basic_effect_anti = basic_effect_anti
        self._update()

    def set_weapon(self, weapon: "Weapon | None"):
        "设置主手武器"
        self.weapon = weapon

    def attack(
        self,
        target: ENTITY,
        src_type: SrcType = SrcType.NORMAL,
        attack_type: AttackType = AttackType.NORMAL,
        atks: list[int] | None = None,
    ):
        # 仅限普攻 技能等请不要调用
        # attack => 得出普通的ATK数据
        # atks: 如果写入, 就强制注入伤害数值 否则由系统自动按武器和效果等计算
        if self.weapon is None:
            raise ValueError(f"Weapon empty but attack: {self.name}")
        self._update()
        if atks is not None:
            self.tmp_atks = atks
        if not self.weapon.use():
            self.tmp_atks = [0, 0, 0, 0, 0, 0, 0]
        atks, is_crit, is_died = self.final_attack(target, src_type, attack_type)
        return atks, is_crit, is_died

    def final_attack(
        self,
        target: ENTITY,
        src_type: SrcType,
        attack_type: AttackType,
        must_be_crit=False,
    ):
        # 武器基本攻击应当给到了 tmp_atks
        # 判断有没有暴击
        is_crit = must_be_crit or random.random() < self.tmp_crit_pc
        if is_crit:
            # 自动加成
            self.tmp_atks = [int(x * (1 + self.tmp_crit_add)) for x in self.tmp_atks]
        # 发动攻击造成伤害
        target.injured(self, src_type, attack_type, self.tmp_atks, is_crit)
        # 圣遗物生效
        frame_objects.execute_on_attack(
            self, target, src_type, attack_type, self.tmp_atks, is_crit
        )
        # 效果生效: 玩家攻击
        # 这些效果看上去不会有增强攻击效果的, 所以放到最后
        frame_effects.execute_on_attack(
            self, target, src_type, attack_type, self.tmp_atks, is_crit
        )
        # 效果生效: 目标死亡
        if target.is_died():
            self.on_kill_target(target)
            self.add_charge(self.system.MOB_DEATH_CHARGE)
        self.show_attack(target, is_crit)
        if target.is_died() and self.weapon is not None:
            self.weapon.add_kill_count()
        return self.tmp_atks, is_crit, target.is_died()

    def on_kill_target(self, target: ENTITY):
        frame_effects.execute_on_kill(self, target)
        frame_objects.execute_on_kill(self, target)

    def injured(
        self,
        attacker: ENTITY,
        src_type: SrcType,
        attack_type: AttackType,
        dmgs: list[int],
        is_crit: bool = False,
    ):
        self._update()
        frame_effects.execute_on_injured(
            self, attacker, src_type, attack_type, dmgs, is_crit
        )
        frame_objects.execute_on_injured(
            self, attacker, src_type, attack_type, dmgs, is_crit
        )
        self.tmp_defs = list_multi(self.tmp_defs, self.tmp_def_add)
        # TODO: 盾量
        if attack_type == AttackType.NORMAL:
            hurtsum = sum(hurt_calc(dmgs, self.tmp_defs))
        else:
            hurtsum = sum(self.tmp_defs)
        if hurtsum < 0:
            raise ValueError("hurt sum < 0")
        if attack_type != AttackType.NON_SHIELD and attack_type != AttackType.REAL:
            if self.shield > 0:
                self.shield -= hurtsum
                if self.shield < 0:
                    hurtsum = -self.shield
                    self.shield = 0
                else:
                    hurtsum = 0
                if self.shield == 0:
                    # 被破盾
                    frame_effects.execute_on_break_shield(self, attacker)
                    frame_objects.execute_on_break_shield(self, attacker)
        self.hp -= hurtsum
        if self.hp <= 0:
            self.hp = 0
        self.player.setActionbar(make_entity_panel(self, attacker))
        if self.hp == 0:
            self.ready_died(attacker)

    def real_injured(
        self,
        attacker: ENTITY,
        src_type: SrcType,
        damage: int,
    ):
        self.hp -= damage
        if self.hp <= 0:
            self.hp = 0
        if isinstance(attacker, PlayerEntity):
            attacker.player.setActionbar(make_entity_panel(attacker, self))
        self.player.setActionbar(make_entity_panel(self, attacker))
        if self.hp == 0:
            self.ready_died(attacker)

    def cured(self, fromwho: ENTITY, cure_type: SrcType, cured_hp: int):
        frame_effects.execute_on_cure(fromwho, self, cured_hp)
        if isinstance(fromwho, PlayerEntity):
            frame_objects.execute_on_cure(fromwho, self, cured_hp)
        frame_effects.execute_on_cured(self, fromwho, cure_type, cured_hp)
        self.hp = min(self.hp + cured_hp, self.tmp_hp_max)
        # self.system.game_ctrl.player_actionbar(
        #     self.name, make_entity_panel(self, fromwho if self != fromwho else None)
        # )

    def skill_use(self, target: ENTITY | None):
        assert self.weapon, "Cannot use SKILL now"
        if target is None:
            self.weapon.on_skill_set()
        else:
            self.weapon.on_skill_use(target)
        frame_effects.execute_on_skill_use(self, target)
        frame_objects.execute_on_skill_use(self, target)

    def ult_use(self, target: ENTITY | None):
        assert self.weapon, "Cannot use ULT now"
        if target is None:
            self.weapon.on_ult_set()
        else:
            self.weapon.on_ult_use(target)
        frame_effects.execute_on_ult_use(self, target)
        frame_objects.execute_on_ult_use(self, target)

    def is_died(self):
        return self.hp == 0

    def ready_died(self, killer: "ENTITY"):
        frame_effects.execute_on_pre_died(self, killer)
        frame_objects.execute_on_pre_died(self, killer)
        if self.hp == 0:
            self.died(killer)

    def died(self, killer: "ENTITY"):
        self.died_func(self)
        frame_effects.execute_on_died(self, killer)
        frame_objects.execute_on_died(self, killer)
        if isinstance(killer, PlayerEntity):
            self.system.show_any(
                killer.name, "a", f"§6{SWORD_ICON} §f你击败了 {self.name}"
            )
            self.system.show_any(
                f"@a[name=!{killer.name}]",
                "6",
                f"§f{self.name} §7被 {killer.name} §7击败了..",
            )
        else:
            self.system.show_any(
                "@a", "6", f"§f{self.name} §7被 §f{killer.name} §7击败了.."
            )

    def execute_effects_ticking(self) -> bool:
        can_display_panel = False
        for effect in self.effects.copy():
            if effect.on_ticking:
                can_display_panel = effect.on_ticking() or can_display_panel
            if effect.last_time <= 0:
                self.effects.remove(effect)
        return can_display_panel

    def add_effect(
        self,
        effect: type[RPGEffect] | RPGEffect | str,
        fromwho: "ENTITY",
        sec: int = 1,
        lv: int = 1,
        hit: float = 1,
        **kwargs,
    ):
        if isinstance(effect, RPGEffect):
            eff = effect
        elif isinstance(effect, str):
            eff = find_effect_class(effect)(self, fromwho, sec, lv, **kwargs)
        else:
            eff = effect(self, fromwho, sec, lv, **kwargs)
        if fromwho != self and eff.type == EffectType.NEGATIVE:
            if random.randint(1, int(hit * 1000)) <= self.tmp_effect_hit * 1000:
                return
        add_effect(self, eff, fromwho, sec, lv, hit, **kwargs)
        if isinstance(fromwho, PlayerEntity):
            if fromwho != self:
                self.player.setActionbar(make_entity_panel(fromwho, self))
                fromwho.player.setActionbar(make_entity_panel(fromwho, self))
            else:
                self.player.setActionbar(make_entity_panel(self, None))

    def add_charge(self, charge: int):
        assert self.weapon, "主手武器为空时不能充能"
        ncharge = int(charge * (1 + self.tmp_chg_add))
        self.weapon.add_charge(ncharge)

    def add_shield(self, shield: int):
        self.shield += shield

    def remove_shield(self, shield: int):
        self.shield = max(0, self.shield - shield)

    def run_cmd(self, cmd: str):
        self.system.game_ctrl.sendwocmd(cmd.replace("%t", '"' + self.player.name + '"'))

    def get_effect(self, effect_tagname: str):
        for i in self.effects:
            if i.__class__.__name__ == effect_tagname:
                return i
        return None

    def show_attack(self, target: ENTITY, is_crit: bool):
        changed = -self.system.entity_holder.get_hp_changed(target)
        damage_num = self.system.bigchar.replaceBig(str(changed))
        self.system.game_ctrl.player_subtitle(
            self.name,
            "§c\n§c\n§c               "
            f"§6§l{damage_num}  {'§e暴击！' if is_crit else ''}",
        )
        self.player.setActionbar(make_entity_panel(self, target, is_crit))

    def recover(self):
        self.hp = self.tmp_hp_max
        self.system.entity_holder.update_last_hp(self)
        self.system.game_ctrl.sendwocmd(
            f"/scoreboard players set {self.player.safe_name} sr:pl_hp {self.hp}"
        )

    def switch_pvp(self, pvp: bool):
        self.pvp = pvp

    def _update(self):
        self.tmp_atk_add = self.basic_atk_add.copy()
        self.tmp_def_add = self.basic_def_add.copy()
        self.tmp_hp_add = 0.0
        self.tmp_hp_max = self.basic_hp_max
        self.tmp_crit_pc = self.basic_crit_pc
        self.tmp_crit_add = self.basic_crit_add
        self.tmp_chg_add = self.basic_chg_add
        self.tmp_cure_add = self.basic_cure_add
        self.tmp_effect_hit = self.basic_effect_hit
        self.tmp_effect_anti = self.basic_effect_anti
        self.shield_add = 1
        self.__update_buff()
        self.tmp_atks = [
            int(x * (1 + y)) for x, y in zip(self.basic_atks, self.tmp_atk_add)
        ]
        self.tmp_defs = [
            int(x * (1 + y)) for x, y in zip(self.basic_defs, self.tmp_def_add)
        ]
        self.tmp_hp_max = int(self.basic_hp_max * (1 + self.tmp_hp_add))
        if self.hp > self.tmp_hp_max:
            self.hp = self.tmp_hp_max

    def _get_category_relic_num(self, category: str):
        return sum(1 for i in self.relics if i and i.category == category)

    def __update_buff(self):
        for eff in self.effects:
            if eff.is_timeout():
                self.effects.remove(eff)
        for eff in self.effects:
            if eff.is_timeout():
                self.effects.remove(eff)
        frame_effects.execute_on_basic(self)

    def dump(self):
        self.__update_buff()
        return {
            "basic_atks": self.original_atks,
            "basic_defs": self.original_defs,
            "last_hp": self.hp,
            "hp_max": self.original_hpmax,
            "crit": self.original_crit_pc,
            "crit_add": self.original_crit_add,
            "last_effects": [eff.dump() for eff in self.effects],
        }


# 其他生物的数据化实体属性
class MobEntity:
    def __init__(
        self,
        system: "CustomRPG",
        mob_cls: type[frame_mobs.Mob],
        uuid: str,
        hp: int,
        effects: list[RPGEffect] | None = None,
        died_func=lambda _: None,
    ):
        """
        Args:
            name: 实体
            hp: 当前生命值
            mob_type: 实体种类ID
            uuid: 计分板UUID
            basic_atks: 自身攻击力
            basic_defs: 自身防御力
            basic_hpmax: 自身生命上限
            effects: 效果
            died_func: 死亡回调
        """
        self.system = system
        self.cls = mob_cls
        self.name = mob_cls.show_name
        self.uuid = uuid
        self.hp = hp
        self.basic_hp_max = mob_cls.max_hp
        self.basic_atks = list(mob_cls.atks)
        self.basic_defs = list(mob_cls.defs)
        self.basic_effect_hit = mob_cls.effect_hit
        self.basic_effect_anti = mob_cls.effect_anti
        self.effects = effects.copy() if effects else []
        self.died_func = died_func
        self.variables = {}
        self.shield = 0
        self._update()
        self.is_deleted = False

    def attack(
        self,
        target: ENTITY,
        src_type: SrcType,
        attack_type: AttackType,
        atks: list[int] | None = None,
    ):
        self._update()
        if atks:
            self.tmp_atks = atks
        frame_effects.execute_on_attack(
            self, target, src_type, attack_type, self.tmp_atks, False
        )
        self.final_attack(target, src_type, attack_type)
        return self.tmp_atks

    def final_attack(self, target: ENTITY, src_type: SrcType, attack_type: AttackType):
        self.cls.attack(self, target, src_type, attack_type)

    def injured(
        self,
        attacker: ENTITY,
        src_type: SrcType,
        attack_type: AttackType,
        dmgs: list[int],
        is_crit: bool = False,
    ):
        self._update()
        frame_effects.execute_on_injured(
            self, attacker, src_type, attack_type, dmgs, is_crit
        )
        if self.cls.injured(self, attacker, dmgs, is_crit):
            return
        sum_dmg = sum(hurt_calc(dmgs, self.tmp_defs))
        if sum_dmg < 0:
            raise ValueError
        if attack_type != AttackType.NON_SHIELD and attack_type != AttackType.REAL:
            if self.shield > 0:
                self.shield -= sum_dmg
                if self.shield < 0:
                    sum_dmg = -self.shield
                    self.shield = 0
                else:
                    sum_dmg = 0
                if self.shield == 0:
                    frame_effects.execute_on_break_shield(self, attacker)
        self.hp -= sum_dmg
        if self.hp < 0:
            self.hp = 0
        self.system.game_ctrl.sendwocmd(
            f"/scoreboard players set @e[scores={{sr:ms_uuid={self.uuid}}}] sr:ms_hp {max(0, self.hp)}"
        )
        if self.is_died():
            self.ready_died(attacker)

    def real_injured(
        self,
        attacker: ENTITY,
        src_type: SrcType,
        damage: int,
    ):
        self.hp -= damage
        if self.hp <= 0:
            self.hp = 0
        if isinstance(attacker, PlayerEntity):
            attacker.player.setActionbar(make_entity_panel(attacker, self))
        if self.hp == 0:
            self.ready_died(attacker)

    def cured(self, fromwho: ENTITY, cure_type: SrcType, curehp: int):
        frame_effects.execute_on_cure(fromwho, self, curehp)
        # 玩家在目前还不能给生物回血
        frame_effects.execute_on_cured(self, fromwho, cure_type, curehp)
        self.hp = min(self.hp + curehp, self.tmp_hp_max)

    def is_died(self):
        return self.hp <= 0

    def ready_died(self, killer: "ENTITY"):
        if self.hp <= 0:
            self.hp = 0
            frame_effects.execute_on_pre_died(self, killer)
            if self.hp == 0:
                frame_effects.execute_on_died(self, killer)
                if self.cls.ready_died(self, killer):
                    self.died(killer)

    def died(self, killer: "ENTITY"):
        if isinstance(killer, PlayerEntity):
            self.system.show_any(
                killer.name, "a", f"§6{SWORD_ICON} §f你击败了 {self.name}"
            )
        self.died_func(self, killer)
        self.is_deleted = True

    def execute_effect_ticking(self) -> bool:
        can_display_panel = False
        for effect in self.effects.copy():
            if effect.on_ticking:
                can_display_panel = effect.on_ticking() or can_display_panel
            if effect.last_time <= 0:
                self.effects.remove(effect)
        return can_display_panel

    def add_effect(
        self,
        effect: type[RPGEffect] | RPGEffect,
        fromwho: "ENTITY",
        sec: int = 1,
        lv: int = 1,
        hit: float = 1,
        **kwargs,
    ):
        add_effect(self, effect, fromwho, sec, lv, hit, **kwargs)
        if isinstance(fromwho, PlayerEntity):
            fromwho.player.setActionbar(make_entity_panel(fromwho, self))

    def add_shield(self, shield: int):
        self.shield += shield

    def remove_shield(self, shield: int):
        self.shield = max(0, self.shield - shield)

    def run_cmd(self, cmd: str):
        self.system.game_ctrl.sendwocmd(
            cmd.replace("%t", "@e[scores={sr:ms_uuid=" + self.uuid + "}]")
        )

    def _update(self):
        "更新, 重新计算 buff 和 攻击增加"
        self.tmp_hp_max = self.basic_hp_max
        self.tmp_atk_add = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.tmp_def_add = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.tmp_effect_hit = self.basic_effect_hit
        self.tmp_effect_anti = self.basic_effect_anti
        self.tmp_hp_add = 0.0
        self.shield_add = 1
        self.__update_buff()
        self.tmp_hp_max = int(self.tmp_hp_max * (1 + self.tmp_hp_add))
        self.tmp_atks = [
            int(x * (1 + y)) for x, y in zip(self.basic_atks, self.tmp_atk_add)
        ]

        self.tmp_defs = [
            int(x * (1 + y)) for x, y in zip(self.basic_defs, self.tmp_def_add)
        ]

    def __update_buff(self):
        for eff in self.effects:
            if eff.is_timeout():
                self.effects.remove(eff)
        for eff in self.effects:
            if eff.is_timeout():
                self.effects.remove(eff)
        frame_effects.execute_on_basic(self)


class PlayerPanel:
    def __init__(self, player_inf: PlayerEntity):
        self.p_orig_hpmax = player_inf.original_hpmax
        ##########################
        self.p_bas_hpmax = player_inf.basic_hp_max
        self.bas_hpmax = player_inf.basic_hp_max - self.p_bas_hpmax
        self.eff_hpmax = player_inf.tmp_hp_max - self.p_bas_hpmax - self.bas_hpmax
        self.bas_atks = player_inf.basic_atks
        self.bas_defs = player_inf.basic_defs
        self.eff_atks = list_sub(player_inf.tmp_atks, player_inf.basic_atks)
        self.eff_defs = list_sub(player_inf.tmp_defs, player_inf.basic_defs)
        self.p_bas_crit_pc = player_inf.original_crit_pc
        self.p_bas_crit_add = player_inf.original_crit_add
        self.bas_crit_pc = player_inf.basic_crit_pc - self.p_bas_crit_pc
        self.bas_crit_add = player_inf.basic_crit_add - self.p_bas_crit_add
        self.eff_crit_pc = (
            player_inf.tmp_crit_pc - self.p_bas_crit_pc - self.bas_crit_pc
        )
        self.eff_crit_add = (
            player_inf.tmp_crit_add - self.p_bas_crit_add - self.bas_crit_add
        )
        self.basic_chg_add = player_inf.basic_chg_add
        self.eff_chg_add = player_inf.tmp_chg_add - self.basic_chg_add
        self.bas_eff_hit = player_inf.basic_effect_hit
        self.bas_eff_anti = player_inf.basic_effect_anti
        self.eff_eff_hit = player_inf.tmp_effect_hit - self.bas_eff_hit
        self.eff_eff_anti = player_inf.tmp_effect_anti - self.bas_eff_anti

    def panel(self, elems: dict[str, str]):
        txts = []
        n_elems = [elems[f"属性{i}"] for i in range(1, len(elems) + 1)]
        append = txts.append
        if self.eff_hpmax == 0:
            append(
                f"§7 - §f生命值上限 §7{self.p_orig_hpmax}->§f{self.p_bas_hpmax}§a+{self.bas_hpmax}"
            )
        else:
            append(
                f"§7 - §f生命值上限 §f{self.p_bas_hpmax}§a+{self.bas_hpmax}§6+{self.eff_hpmax}"
            )
        for i, elem in enumerate(n_elems):
            t = ""
            bas_atk = self.bas_atks[i]
            eff_atk = self.eff_atks[i]
            bas_def = self.bas_defs[i]
            eff_def = self.eff_defs[i]
            if eff_atk > 0:
                t += f"§f{bas_atk}§6+{eff_atk}"
            else:
                t += f"§f{bas_atk}"
            t += "§f / "
            if eff_def > 0:
                t += f"§f{bas_def}§6+{eff_def}"
            else:
                t += f"§f{bas_def}"
            append(f"§7 - {elem} (攻击/防御): " + t)
        if self.eff_crit_pc > 0:
            append(
                f"§7 - §4暴击率 §f{round(self.p_bas_crit_pc * 100)}%%§a+{round(self.bas_crit_pc * 100)}%%§6+{round(self.eff_crit_pc * 100)}%%"
            )
        else:
            append(
                f"§7 - §4暴击率 §f{round(self.p_bas_crit_pc * 100)}%%§a+{round(self.bas_crit_pc * 100)}%%"
            )
        if self.eff_crit_add > 0:
            append(
                f"§7 - §4暴击伤害加成 §f{round(self.p_bas_crit_add * 100)}%%§a+{round(self.bas_crit_pc * 100)}%%§6+{round(self.eff_crit_pc * 100)}%%"
            )
        else:
            append(
                f"§7 - §4暴击伤害加成 §f{round(self.p_bas_crit_add * 100)}%%§a+{round(self.bas_crit_add * 100)}%%"
            )
        if self.eff_eff_hit > 0:
            append(
                f"§7 - §3效果命中 §f{round(self.bas_eff_hit * 100)}%%§6+{round(self.eff_eff_hit * 100)}%%"
            )
        else:
            append(f"§7 - §3效果命中 §f{round(self.bas_eff_hit * 100)}%%")
        if self.eff_eff_anti > 0:
            append(
                f"§7 - §3效果抵抗 §f{round(self.bas_eff_anti * 100)}%%§6+{round(self.eff_eff_anti * 100)}%%"
            )
        else:
            append(f"§7 - §3效果抵抗 §f{round(self.bas_eff_anti * 100)}%%")
        return txts

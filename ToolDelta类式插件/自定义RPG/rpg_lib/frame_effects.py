import random
import time
from typing import TYPE_CHECKING
from .utils import make_rome_num
from .constants import SrcType, AttackType, EffectType

if TYPE_CHECKING:
    from .rpg_entities import ENTITY


# 玩家或生物身上的 buff
class RPGEffect:
    # 显示的图标
    icon = "?"
    # 显示的名称
    name = "<?>"
    # 0 = 仅玩家; 1 = 仅生物; -1 = 玩家或生物都适用
    target_type = -1
    # 0 (NEUTRAL) = 中立效果; 1 (POSITIVE) = 有益效果; 2 (NEGATIVE) = 有害效果
    type = EffectType.NEUTRAL
    # 该 buff 的效果命中值 (实体受到此 buff 的概率为 buff的效果命中值 - 实体的效果抵抗值)
    anti = 1.0

    # 初始化 buff
    def __init__(
        self, target: "ENTITY", fromwho: "ENTITY", seconds: int, level: int = 1
    ):
        # target: 实体 (玩家或生物)
        # fromwho: buff 来源, 被哪个实体给予的
        # seconds: 持续时间
        # level: 等级
        self.target = target
        self.fromwho = fromwho
        self.seconds = seconds
        self.level = level
        self.tm = time.time()

    # 当被添加后, 每次刷新前
    def on_basic(self):
        pass

    # 当持有者发动攻击时
    def on_attack(
        self,
        target: "ENTITY",
        src_type: SrcType,
        attack_type: AttackType,
        dmgs: list[int],
        iscrit: bool,
    ):
        pass

    # 当持有者受伤时
    def on_injured(
        self,
        fromwho: "ENTITY",
        src_type: SrcType,
        attack_type: AttackType,
        dmgs: list[int],
        iscrit: bool,
    ):
        pass

    # 当持有者击杀目标时
    def on_kill(self, target: "ENTITY"):
        pass

    # 当持有者即将死亡时
    def on_pre_died(self, fromwho: "ENTITY"):
        pass

    # 当持有者死亡时
    def on_died(self, fromwho: "ENTITY"):
        pass

    # 当持有者释放技能时
    def on_skill_use(self, target: "ENTITY | None"):
        pass

    # 当持有者释放大招时
    def on_ult_use(self, target: "ENTITY | None"):
        pass

    # 当持有者施放治疗时
    def on_cure(self, target: "ENTITY", cured_hp: int):
        pass

    # 当持有者被治疗时
    def on_cured(
        self, fromwho: "ENTITY | None", cure_type: SrcType, cured_hp: int
    ):
        pass

    # 当护甲被击破时
    def on_break_shield(self, fromwho: "ENTITY | None"):
        pass

    # 每过一秒时
    def on_ticking(self) -> bool:
        return False

    # 效果是否已经结束
    def is_timeout(self):
        return self.last_time < 0

    # 格式化自身等级为罗马数字
    def self_level(self):
        return make_rome_num(self.level)

    # 格式化 buff 剩余时间为 MM:SS
    def timeleft_str(self):
        m, s = divmod(self.last_time, 60)
        return f"{m:02d}:{s:02d}"

    # 导出自身数据到 dict
    def dump(self):
        Player = get_entity_module().PlayerEntity
        fromwho = self.fromwho
        return (
            self.__class__.__name__,
            ("Mob" if isinstance(fromwho, Player) else "Player"),
            (fromwho.name if isinstance(fromwho, Player) else fromwho.uuid),
            self.last_time,
            self.level,
        )

    # 获取剩余时间
    @property
    def last_time(self):
        return int(self.tm + self.seconds - time.time())


def has_effect(entity: "ENTITY", effect_cls: type[RPGEffect]):
    for effect in entity.effects:
        if isinstance(effect, effect_cls):
            return effect
    return None


def get_entity_module():
    from . import rpg_entities

    return rpg_entities


registered_effects: dict[str, type[RPGEffect]] = {}


def find_effect_class(name: str):
    for eff_name, eff in registered_effects.items():
        if eff_name == name:
            return eff
    raise ValueError(f"No such effect: {name}")


def get_effects(effect_datas: list, target: "ENTITY"):
    effs: list[RPGEffect] = []
    for eff_dat in effect_datas:
        nam, sec, lv = eff_dat["id"], eff_dat["sec"], eff_dat["lv"]
        effs.append(find_effect_class(nam)(target, sec, lv))
    return effs


def register_effect_module(module):
    registered_effects.update(
        {
            i: j
            for i, j in module.__dict__.items()
            if isinstance(j, type) and issubclass(j, RPGEffect)
        }
    )

def add_effect(
    entity: "ENTITY",
    effect: type[RPGEffect] | RPGEffect,
    fromwho: "ENTITY",
    sec: int = 1,
    lv: int = 1,
    hit: float = 1,
    **kwargs,
):
    if isinstance(effect, RPGEffect):
        eff = effect
    else:
        eff = effect(entity, fromwho, sec, lv, **kwargs)
    if fromwho != entity and eff.type == EffectType.NEGATIVE:
        # 来源不是自己
        if random.randint(1, int(hit * 1000)) <= entity.tmp_effect_hit * 1000:
            return
    for effi in entity.effects:
        if effi.__class__ == eff.__class__:
            if effi.level == eff.level and eff.seconds > effi.seconds:
                # 等级相等, 取更多秒数的
                effi.seconds = eff.seconds
            elif effi.level < eff.level:
                # 等级更大
                effi.level = eff.level
                effi.seconds = int(effi.level / eff.level * effi.seconds + eff.seconds)
            break
    else:
        entity.effects.append(eff)


def execute_on_basic(entity: "ENTITY"):
    for effect in entity.effects:
        effect.on_basic()


def execute_on_attack(
    entity: "ENTITY",
    target: "ENTITY",
    src_type: SrcType,
    attack_type: AttackType,
    dmgs: list[int],
    iscrit: bool,
):
    for effect in entity.effects:
        effect.on_attack(target, src_type, attack_type, dmgs, iscrit)


def execute_on_injured(
    entity: "ENTITY",
    fromwho: "ENTITY",
    src_type: SrcType,
    attack_type: AttackType,
    dmgs: list[int],
    iscrit: bool,
):
    for effect in entity.effects:
        effect.on_injured(fromwho, src_type, attack_type, dmgs, iscrit)


def execute_on_kill(entity: "ENTITY", target: "ENTITY"):
    for effect in entity.effects:
        effect.on_kill(target)


def execute_on_pre_died(entity: "ENTITY", fromwho: "ENTITY"):
    for effect in entity.effects:
        effect.on_pre_died(fromwho)


def execute_on_died(entity: "ENTITY", fromwho: "ENTITY"):
    for effect in entity.effects:
        effect.on_died(fromwho)


def execute_on_skill_use(entity: "ENTITY", target: "ENTITY | None"):
    for effect in entity.effects:
        effect.on_skill_use(target)


def execute_on_ult_use(entity: "ENTITY", target: "ENTITY | None"):
    for effect in entity.effects:
        effect.on_ult_use(target)


def execute_on_cure(entity: "ENTITY", target: "ENTITY", cured_hp: int):
    for effect in entity.effects:
        effect.on_cure(target, cured_hp)


def execute_on_cured(
    entity: "ENTITY", fromwho: "ENTITY | None", cure_type: SrcType, cured_hp: int
):
    for effect in entity.effects:
        effect.on_cured(fromwho, cure_type, cured_hp)


def execute_on_break_shield(entity: "ENTITY", fromwho: "ENTITY | None"):
    for effect in entity.effects:
        effect.on_break_shield(fromwho)


def execute_on_ticking(entity: "ENTITY"):
    for effect in entity.effects:
        if effect.on_ticking():
            entity.effects.remove(effect)

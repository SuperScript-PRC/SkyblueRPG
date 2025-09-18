import time
from typing import TYPE_CHECKING
from weakref import ref
from .utils import make_rome_num
from .constants import SrcType, AttackType, EffectType, EffectTarget

if TYPE_CHECKING:
    from .rpg_entities import Entity


# 玩家或生物身上的 buff
class RPGEffect:

    def __init_subclass__(
        cls,
        icon: str,
        name: str,
        target_type: EffectTarget = EffectTarget.BOTH,
        type: EffectType = EffectType.NEUTRAL,
        tags: tuple[str, ...] = (),
        hit: float = 1.0,
    ):
        """
        效果 (Buff) 类。

        Args:
            icon (str): 显示的小图标
            name (str): 显示的名称
            target_type (EffectTarget): 效果施加的目标的类型
            type (EffectType): 效果的性质 (中立, 良性, 恶性)
            tags (tuple[str, ...]): 效果标签
            anti (float, optional): 默认效果命中. Defaults to 1.0.
        """
        cls.icon = icon
        cls.name = name
        cls.target_type = target_type
        cls.type = type
        cls.tags = tags
        cls.hit = hit

    # 初始化 buff
    def __init__(
        self, target: "Entity", fromwho: "Entity", seconds: int, level: int = 1
    ):
        # target: 实体 (玩家或生物)
        # fromwho: buff 来源, 被哪个实体给予的
        # seconds: 持续时间
        # level: 等级
        self._target = ref(target)
        self._fromwho = ref(fromwho)
        self.seconds = seconds
        self.level = level
        self.tm = time.time()

    # 当被添加后, 每次刷新前
    def on_basic(self):
        pass

    # 当持有者发动攻击时
    def on_attack(
        self,
        target: "Entity",
        src_type: SrcType,
        attack_type: AttackType,
        dmgs: list[int],
        iscrit: bool,
    ):
        pass

    # 当持有者受伤时
    def on_injured(
        self,
        fromwho: "Entity",
        src_type: SrcType,
        attack_type: AttackType,
        dmgs: list[int],
        iscrit: bool,
    ):
        pass

    # 当持有者击杀目标时
    def on_kill(self, target: "Entity"):
        pass

    # 当持有者即将死亡时
    def on_pre_died(self, fromwho: "Entity"):
        pass

    # 当持有者死亡时
    def on_died(self, fromwho: "Entity"):
        pass

    # 当持有者释放技能时
    def on_skill_use(self, target: "Entity | None"):
        pass

    # 当持有者释放大招时
    def on_ult_use(self, target: "Entity | None"):
        pass

    # 当持有者施放治疗时
    def on_cure(self, target: "Entity", cured_hp: int):
        pass

    # 当持有者被治疗时
    def on_cured(self, fromwho: "Entity | None", cure_type: SrcType, cured_hp: int):
        pass

    # 当护甲被击破时
    def on_break_shield(self, fromwho: "Entity | None"):
        pass

    # 每过一秒时
    def on_ticking(self) -> bool:
        return False

    # 效果是否已经结束
    def is_timeout(self):
        return self.last_time < 0

    def self_hurt(
        self,
        damages: list[int],
        attacker: "Entity | None" = None,
        msg: str | None = None,
    ):
        attacker = attacker or self.fromwho
        self.target.injured(
            attacker, SrcType.FROM_EFFECT, AttackType.EFFECT, damages, death_message=msg
        )

    def self_cure(self, hp: int, cure_from: "Entity | None" = None):
        cure_from = cure_from or self.fromwho
        self.target.cured(cure_from, SrcType.FROM_EFFECT, hp)

    # 格式化自身等级为罗马数字
    def self_level(self):
        return make_rome_num(self.level)

    # 格式化 buff 剩余时间为 MM:SS
    def timeleft_str(self):
        m, s = divmod(self.last_time, 60)
        return f"{m:02d}:{s:02d}"

    # 导出自身数据到 dict
    def dump(self):
        PlayerEntity = get_entity_module().PlayerEntity
        fromwho = self.fromwho
        return (
            self.__class__.__name__,
            ("Player" if isinstance(fromwho, PlayerEntity) else "Mob"),
            (
                fromwho.player.xuid
                if isinstance(fromwho, PlayerEntity)
                else getattr(fromwho, "uuid")
            ),
            self.last_time,
            self.level,
        )

    @property
    def target(self):
        t = self._target()
        if t is None:
            raise ReferenceError("目标不存在")
        return t

    @target.setter
    def target(self, target: "Entity"):
        self._target = ref(target)

    @property
    def fromwho(self):
        f = self._fromwho()
        if f is None:
            raise ReferenceError("来源不存在")
        return f

    @fromwho.setter
    def fromwho(self, who: "Entity"):
        self._fromwho = ref(who)

    # 获取剩余时间
    @property
    def last_time(self):
        return int(self.tm + self.seconds - time.time())


def has_effect(entity: "Entity", effect_cls: type[RPGEffect]):
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


def get_effects(effect_datas: list, target: "Entity"):
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
    entity: "Entity",
    effect: RPGEffect,
    fromwho: "Entity",
    sec: int = 1,
    lv: int = 1,
    hit: float = 1,
    **kwargs,
):
    for effi in entity.effects:
        if effi.__class__ == effect.__class__:
            effi.fromwho = effect.fromwho
            if effi.level == effect.level and effect.seconds > effi.last_time:
                # 等级相等, 取更多秒数的
                effi.tm = time.time()
            elif effi.level < effect.level:
                # 等级更大
                effi.level = effect.level
                effi.seconds = int(
                    effi.level / effect.level * effi.seconds + effect.seconds
                )
            break
    else:
        entity.effects.append(effect)


def execute_on_basic(entity: "Entity"):
    for effect in entity.effects:
        effect.on_basic()


def execute_on_attack(
    entity: "Entity",
    target: "Entity",
    src_type: SrcType,
    attack_type: AttackType,
    dmgs: list[int],
    iscrit: bool,
):
    for effect in entity.effects:
        effect.on_attack(target, src_type, attack_type, dmgs, iscrit)


def execute_on_injured(
    entity: "Entity",
    fromwho: "Entity",
    src_type: SrcType,
    attack_type: AttackType,
    dmgs: list[int],
    iscrit: bool,
):
    for effect in entity.effects:
        effect.on_injured(fromwho, src_type, attack_type, dmgs, iscrit)


def execute_on_kill(entity: "Entity", target: "Entity"):
    for effect in entity.effects:
        effect.on_kill(target)


def execute_on_pre_died(entity: "Entity", fromwho: "Entity"):
    for effect in entity.effects:
        effect.on_pre_died(fromwho)


def execute_on_died(entity: "Entity", fromwho: "Entity"):
    for effect in entity.effects:
        effect.on_died(fromwho)


def execute_on_skill_use(entity: "Entity", target: "Entity | None"):
    for effect in entity.effects:
        effect.on_skill_use(target)


def execute_on_ult_use(entity: "Entity", target: "Entity | None"):
    for effect in entity.effects:
        effect.on_ult_use(target)


def execute_on_cure(entity: "Entity", target: "Entity", cured_hp: int):
    for effect in entity.effects:
        effect.on_cure(target, cured_hp)


def execute_on_cured(
    entity: "Entity", fromwho: "Entity | None", cure_type: SrcType, cured_hp: int
):
    for effect in entity.effects:
        effect.on_cured(fromwho, cure_type, cured_hp)


def execute_on_break_shield(entity: "Entity", fromwho: "Entity | None"):
    for effect in entity.effects:
        effect.on_break_shield(fromwho)


def execute_on_ticking(entity: "Entity"):
    for effect in entity.effects:
        if effect.on_ticking():
            entity.effects.remove(effect)

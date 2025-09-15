from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class WeaponUpgradeConfig:
    "武器等级提升配置"

    max_level: int
    "最大等级"
    upgrade_value_syntax: Callable[[float, int], int] # lambda x, y: int(x * (1 + y / 16) // 2)
    "升级后属性数值公式 (属性初始, 道具当前等级) -> 升级后数值"
    available_upgrade_materials: dict[str, int]
    "可用升级材料及单个材料给予的经验值"
    upgrade_exp_syntax: Callable[[int], int]
    "每升一级后升级所需经验数计算公式 (道具当前等级) -> 经验值"
    upgrade_level_limit_materials: dict[int, dict[str, int]]
    "升级到这些级数的时候晋阶所需的[材料:数量]"
    extra_materials: dict[str, dict[str, int]]
    "额外升级材料(定向升级)" # 可能包含氪金内容


@dataclass
class RelicUpgradeConfig:
    "饰品等级提升配置"

    max_level: int
    "最大等级"
    sub_prop_levels: tuple[int, ...]
    "达到等级时副词条变动"
    available_upgrade_materials: dict[str, int]
    "可用升级材料及单个材料给予的经验值"
    upgrade_exp_syntax: Callable[[int], int]
    "每升一级后升级所需经验数计算公式 (道具当前等级) -> 经验值"
    upgrade_level_limit_materials: dict[int, dict[str, int]]
    "升级到这些级数的时候晋阶所需的[材料:数量]"
    main_props_weight: dict[str, float]
    "主词条数值权重"
    sub_props_weight: dict[str, float]
    "副词条数值权重"
    extra_materials: dict[str, dict[str, int]]
    "额外升级材料(定向升级)"

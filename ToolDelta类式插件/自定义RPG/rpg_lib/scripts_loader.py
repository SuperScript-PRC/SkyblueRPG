import importlib
import sys
import os
from collections.abc import Callable
from typing import TYPE_CHECKING
from types import ModuleType
from pathlib import Path
from . import (
    constants,
    frame_objects,
    frame_effects,
    frame_enchants,
    frame_mobs,
    rpg_entities,
    utils
)

if TYPE_CHECKING:
    from .. import CustomRPG
    from ...自定义RPG_升级系统 import CustomRPGUpgrade


def load_scripts(system: "CustomRPG", base_folder: Path, register: Callable[[ModuleType], None]):
    dev_rpg_lib_module.upgrade_lib = system.rpg_upgrade
    sys.path.append(str(base_folder))
    for py_file in base_folder.glob("*.py"):
        module_name = py_file.stem
        module_reloaded = module_name in sys.modules
        module = importlib.import_module(f"{module_name}")
        if module_reloaded:
            importlib.reload(module)
        register(module)
    sys.path.remove(str(base_folder))


def load_all(sys: "CustomRPG"):
    for dirname, loader in (
        ("饰品脚本", frame_objects.register_relic_module),
        ("效果脚本", frame_effects.register_effect_module),
        ("实体脚本", frame_mobs.register_mob_module),
        ("附魔脚本", frame_enchants.register_enchant_module),
        ("武器脚本", frame_objects.register_weapon_module),
    ):
        os.makedirs(sys.data_path / dirname, exist_ok=True)
        load_scripts(sys, sys.data_path / dirname, loader)


class dev_rpg_lib(ModuleType):
    name = "dev_rpg_lib"

    constants = constants
    frame_effects = frame_effects
    frame_enchants = frame_enchants
    frame_mobs = frame_mobs
    frame_objects = frame_objects
    rpg_entities = rpg_entities
    utils = utils
    upgrade_lib: "CustomRPGUpgrade"


dev_rpg_lib_module = dev_rpg_lib("dev_rpg_lib")
sys.modules[dev_rpg_lib_module.name] = dev_rpg_lib_module

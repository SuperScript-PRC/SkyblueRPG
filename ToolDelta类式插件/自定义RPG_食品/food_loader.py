import importlib
import os
import sys
from typing import TYPE_CHECKING
from types import ModuleType

from .food_frame import register_food_module, RPGFood

if TYPE_CHECKING:
    from . import CustomRPGFood


def load_scripts(system: "CustomRPGFood"):
    base_folder = system.data_path / "食品脚本"
    os.makedirs(base_folder, exist_ok=True)
    sys.path.append(str(base_folder))
    for py_file in base_folder.glob("*.py"):
        module_name = py_file.stem
        module_reloaded = module_name in sys.modules
        module = importlib.import_module(f"{module_name}")
        if module_reloaded:
            importlib.reload(module)
        register_food_module(system, module)
    sys.path.remove(str(base_folder))


class dev_rpg_food_lib(ModuleType):
    name = "dev_rpg_food_lib"

    RPGFood = RPGFood


dev_rpg_lib_module = dev_rpg_food_lib("dev_rpg_food_lib")
sys.modules[dev_rpg_lib_module.name] = dev_rpg_lib_module

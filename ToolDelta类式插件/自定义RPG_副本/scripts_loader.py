import importlib
import sys
from typing import TYPE_CHECKING
from types import ModuleType
from pathlib import Path

from .frame_dungeon import Dungeon
from .dungeon_utils import RandChoice, RandChoices

if TYPE_CHECKING:
    from . import CustomRPGDungeon


def load_scripts(base_folder: Path):
    regist_dungeons: list[Dungeon] = []
    sys.path.append(str(base_folder))
    for py_file in base_folder.glob("*.py"):
        module_name = py_file.stem
        module_reloaded = module_name in sys.modules
        module = importlib.import_module(f"{module_name}")
        if module_reloaded:
            importlib.reload(module)
        for v in module.__dict__.values():
            if isinstance(v, Dungeon):
                regist_dungeons.append(v)
    sys.path.remove(str(base_folder))
    return regist_dungeons


def load_all(sys: "CustomRPGDungeon"):
    return load_scripts(sys.data_path)


class dev_rpg_dungeons_lib(ModuleType):
    RandChoice = RandChoice
    RandChoices = RandChoices
    Dungeon = Dungeon
    system: "CustomRPGDungeon"

    def __init__(self):
        super().__init__("dev_rpg_item_lib")


dev_rpg_dungeons_lib_instance = dev_rpg_dungeons_lib()
sys.modules[dev_rpg_dungeons_lib.__name__] = dev_rpg_dungeons_lib_instance

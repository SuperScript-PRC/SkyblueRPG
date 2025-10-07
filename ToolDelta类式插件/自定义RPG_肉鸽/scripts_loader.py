import importlib
import sys
from typing import TYPE_CHECKING
from collections.abc import Callable
from types import ModuleType
from pathlib import Path
from tooldelta import Player
from .define import MobWave, FortuneEvent
from . import (
    define,
    frame_areas,
    frame_levels,
    frame_rogue,
    rogue_utils,
    storage,
    sources,
)
from .rogue import Rogue

if TYPE_CHECKING:
    from . import CustomRPGRogue, entry

    Mob = entry.rpg.frame_mobs.Mob


rogue_obj: Rogue | None = None


def load_scripts(system: "CustomRPGRogue", base_folder: Path):
    path = base_folder / "脚本文件"
    path.mkdir(exist_ok=True)
    sys.path.append(str(path))
    for py_file in path.glob("*.py"):
        module_name = py_file.stem
        module_reloaded = module_name in sys.modules
        module = importlib.import_module(f"{module_name}")
        if module_reloaded:
            importlib.reload(module)
        # load mod
        system.rpg.frame_effects.register_effect_module(module)
        system.rpg.frame_mobs.register_mob_module(module)
        get_rogue_from_module(module)
    sys.path.remove(str(path))
    if rogue_obj is None:
        raise ValueError("Rogue instance not found!")
    sources.check_safe()
    return rogue_obj


def load_all(sys: "CustomRPGRogue"):
    lib_instance.init_lib(sys)
    lib_instance.system = sys
    return load_scripts(sys, sys.data_path)


def get_rogue_from_module(module: ModuleType):
    for v in module.__dict__.values():
        if isinstance(v, Rogue):
            global rogue_obj
            if rogue_obj is not None:
                raise ValueError("Rogue instance already exists!")
            rogue_obj = v


def fortune(weight: float):
    def decorator(plotfunc: Callable[[Player], None]):
        f = FortuneEvent(lib_instance._plot()(plotfunc), weight)
        sources.add_fortune_plot(f)
        return f

    return decorator


def as_boss(cls: type["Mob"]):
    sources.add_boss_mob(cls)
    return cls


def mob_waves(level: int, *waves: tuple[tuple[str, int], ...]):
    mws = [MobWave(*w) for w in waves]
    sources.add_mob_waves(level, mws)


def pve(player: Player, mob_waves: list[MobWave]):
    rogue_utils.pve(player, mob_waves)


class dev_rpg_rogue_lib(ModuleType):
    system: "CustomRPGRogue"

    def __init__(self):
        super().__init__("dev_rpg_rogue_lib")

    def init_lib(self, sys: "CustomRPGRogue"):
        self.sys = sys
        self.rpg_constants = sys.rpg.constants
        self.rpg_mobs = sys.rpg.frame_mobs
        self.plot_utils = sys.rpg_plots.putils
        self.define = define
        self.frame_areas = frame_areas
        self.frame_levels = frame_levels
        self.frame_rogue = frame_rogue
        self.rogue_utils = rogue_utils
        self.storage = storage
        self.sources = sources
        self._plot = staticmethod(sys.rpg_plots.quest_loader.plot)
        self.fortune = staticmethod(fortune)
        self.pve = staticmethod(pve)
        self.as_boss = staticmethod(as_boss)
        self.mob_waves = staticmethod(mob_waves)
        self.RPGEffect = sys.rpg.frame_effects.RPGEffect


lib_instance = dev_rpg_rogue_lib()
sys.modules[dev_rpg_rogue_lib.__name__] = lib_instance

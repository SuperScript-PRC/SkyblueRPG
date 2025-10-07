import importlib
import sys
from typing import TYPE_CHECKING
from types import ModuleType
from pathlib import Path

from .task_frame import DailyTask, get_task_classes_from_module

if TYPE_CHECKING:
    from . import CustomRPGDailyTask


def load_scripts(system: "CustomRPGDailyTask", base_folder: Path):
    sys.path.append(str(base_folder))
    for py_file in base_folder.glob("*.py"):
        module_name = py_file.stem
        module_reloaded = module_name in sys.modules
        module = importlib.import_module(f"{module_name}")
        if module_reloaded:
            importlib.reload(module)
        ts = get_task_classes_from_module(system, module)
    sys.path.remove(str(base_folder))
    return ts


def load_all(sys: "CustomRPGDailyTask"):
    dev_rpg_tasks.system = sys
    return load_scripts(sys, sys.data_path / "任务脚本")


class dev_rpg_tasks(ModuleType):
    DailyTask = DailyTask
    system: "CustomRPGDailyTask"

    def __init__(self):
        super().__init__("dev_rpg_item_lib")


dev_rpg_tasks_instance = dev_rpg_tasks()
sys.modules[dev_rpg_tasks.__name__] = dev_rpg_tasks_instance

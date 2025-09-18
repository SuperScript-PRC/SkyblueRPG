import importlib
import sys
from collections.abc import Callable
from typing import TYPE_CHECKING
from types import ModuleType
from pathlib import Path
from tooldelta import Player

if TYPE_CHECKING:
    from . import CustomRPGItemScript, SlotItem

register_des_funcs: dict[str, Callable[["SlotItem"], str]] = {}
register_use_funcs: dict[str, Callable[["SlotItem", Player], bool]] = {}


def load_scripts(system: "CustomRPGItemScript", base_folder: Path):
    dev_rpg_item_lib_instance.SlotItem = system.backpack.SlotItem
    sys.path.append(str(base_folder))
    for py_file in base_folder.glob("*.py"):
        module_name = py_file.stem
        module_reloaded = module_name in sys.modules
        module = importlib.import_module(f"{module_name}")
        if module_reloaded:
            importlib.reload(module)
    sys.path.remove(str(base_folder))


def load_all(sys: "CustomRPGItemScript"):
    dev_rpg_item_lib_instance.system = sys
    load_scripts(sys, sys.data_path)


def name(tag_name: str):
    "物品动态名称"
    from . import entry

    def name_wrapper(func: Callable[["SlotItem"], str]):
        item = entry.backpack.get_registed_item(tag_name)
        if item is None:
            raise ValueError(f"物品不存在: {tag_name}")
        item.disp_name = func
        return func

    return name_wrapper


def description(tag_name: str):
    "物品动态描述"
    from . import entry

    def desc_wrapper(func: Callable[["SlotItem"], str]):
        item = entry.backpack.get_registed_item(tag_name)
        if item is None:
            raise ValueError(f"物品不存在: {tag_name}")
        item.description = func
        return func

    return desc_wrapper


def use(tag_name: str, text: str):
    "物品使用回调"
    from . import entry

    def use_wrapper(func: Callable[["SlotItem", Player], None]):
        item = entry.backpack.get_registed_item(tag_name)
        if item is None:
            raise ValueError(f"物品不存在: {tag_name}")
        item.on_use[text] = func
        return func

    return use_wrapper

def given(tag_name: str):
    "物品被获得回调 不允许获得则返回 False"
    from . import entry

    def use_wrapper(func: Callable[[Player], bool]):
        item = entry.backpack.get_registed_item(tag_name)
        if item is None:
            raise ValueError(f"物品不存在: {tag_name}")
        item.on_get.append(func)
        return func

    return use_wrapper


class dev_rpg_item_lib(ModuleType):
    name = staticmethod(name)
    description = staticmethod(description)
    use = staticmethod(use)
    given = staticmethod(given)
    system: "CustomRPGItemScript"
    SlotItem: type["SlotItem"]

    def __init__(self):
        super().__init__("dev_rpg_item_lib")


dev_rpg_item_lib_instance = dev_rpg_item_lib()
sys.modules[dev_rpg_item_lib.__name__] = dev_rpg_item_lib_instance

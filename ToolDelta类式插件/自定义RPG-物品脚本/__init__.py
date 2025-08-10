from importlib import reload
from typing import Callable  # noqa: UP035
from tooldelta import Plugin, Player, TYPE_CHECKING, Print, plugin_entry

from . import scripts

reload(scripts)
register_funcs: dict[str, Callable[["SlotItem", Player], bool]] = {}
for k, v in scripts.__dict__.items():
    if v.__doc__ and v.__doc__.startswith("export:"):
        register_funcs[v.__doc__[7:].strip()] = v


class CustomRPGItemScript(Plugin):
    name = "自定义RPG-物品使用脚本"
    author = "SuperScript"
    version = (0, 0, 1)

    def __init__(self, frame):
        super().__init__(frame)
        scripts.set_system(self)
        self.ListenPreload(self.on_def)
        self.ListenActive(self.on_inject)

    def on_def(self):
        global SlotItem
        self.rpg = self.GetPluginAPI("自定义RPG")
        self.backpack = self.GetPluginAPI("虚拟背包")
        if TYPE_CHECKING:
            from 自定义RPG import CustomRPG
            from 虚拟背包 import VirtuaBackpack

            self.rpg: CustomRPG
            self.backpack: VirtuaBackpack
            SlotItem = self.backpack.SlotItem

    def on_inject(self):
        self.inject_item_use_script()

    def inject_item_use_script(self):
        for tagname, func in register_funcs.items():
            if item := self.backpack.get_registed_item(tagname):
                item.on_use = func
            else:
                Print.print_war(f"物品未注册: {tagname}")


entry = plugin_entry(CustomRPGItemScript)

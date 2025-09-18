from importlib import reload
from tooldelta import Plugin, TYPE_CHECKING, plugin_entry

from . import scripts_loader

reload(scripts_loader)


class CustomRPGItemScript(Plugin):
    name = "自定义RPG-物品脚本"
    author = "SuperScript"
    version = (0, 0, 1)

    def __init__(self, frame):
        super().__init__(frame)
        self.ListenPreload(self.on_def, priority=-5)
        self.make_data_path()

    def on_def(self):
        global SlotItem
        self.rpg = self.GetPluginAPI("自定义RPG")
        self.backpack = self.GetPluginAPI("虚拟背包")
        if TYPE_CHECKING:
            global SlotItem
            from ..自定义RPG import CustomRPG
            from ..虚拟背包 import VirtuaBackpack

            self.rpg: CustomRPG
            self.backpack: VirtuaBackpack
            SlotItem = self.backpack.SlotItem
        scripts_loader.load_all(self)



entry = plugin_entry(CustomRPGItemScript)

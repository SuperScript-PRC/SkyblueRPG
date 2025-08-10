from tooldelta import Plugin, TYPE_CHECKING, plugin_entry


class CustomRPGGames(Plugin):
    name = "自定义RPG-小游戏"

    def __init__(self, frame):
        super().__init__(frame)
        self.ListenPreload(self.on_def)

    def on_def(self):
        self.intr = self.GetPluginAPI("前置-世界交互")


entry = plugin_entry(CustomRPGGames)

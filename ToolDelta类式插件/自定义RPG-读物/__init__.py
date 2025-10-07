import os
from tooldelta import Plugin, Player, TYPE_CHECKING, utils, plugin_entry
from . import event_apis

TEXTLEN = 80
CONTENT_LEN = 10


class CustomRPGItemScript(Plugin):
    name = "自定义RPG-读物"
    author = "SuperScript"
    version = (0, 0, 1)

    def __init__(self, frame):
        super().__init__(frame)
        self.ListenPreload(self.on_def)
        self.ListenActive(self.on_inject)

    def on_def(self):
        global SlotItem
        self.texts: dict[str, str] = {}
        self.rpg = self.GetPluginAPI("自定义RPG")
        self.backpack = self.GetPluginAPI("虚拟背包")
        self.sight = self.GetPluginAPI("视角菜单")
        if TYPE_CHECKING:
            from 自定义RPG import CustomRPG
            from 虚拟背包 import VirtuaBackpack, SlotItem
            from 前置_视角菜单 import SightRotation

            self.rpg: CustomRPG
            self.backpack: VirtuaBackpack
            self.sight: SightRotation
        self.make_data_path()
        self.read_texts()

    def on_inject(self):
        self.inject_item_use_script()

    def read_texts(self):
        loaded_texts = 0
        for dirs in os.listdir(self.data_path):
            for file in os.listdir(self.format_data_path(dirs)):
                with open(self.format_data_path(dirs, file), encoding="utf-8") as f:
                    self.texts[file.removesuffix(".txt")] = f.read()
                    loaded_texts += 1
        self.print(f"§a加载了 {loaded_texts} 本读物")

    def inject_item_use_script(self):
        for tagname, text in self.texts.items():
            if item := self.backpack.get_registed_item(tagname):
                # TODO: directly use Item.disp_name
                item.on_use["阅读"] = self.create_reader(
                    item.force_disp(), text, item.id
                )
            else:
                self.print_war(f"书籍未注册: {tagname}")

    def create_reader(self, title: str, text: str, text_tagname=""):
        def _reader(_, player: Player):
            self.read_by_snowmenu(player, title, text, text_tagname)

        return _reader

    def read_by_snowmenu(self, player: Player, title: str, text: str, text_tagname=""):
        cached_text = ""
        textlines: list[str] = []
        textlen = 0
        text = text.replace("[玩家名]", player.name)
        actions = self.sight.HeadAction
        for char in text + "\n":
            textlen += 2 - char.isascii()
            if char == "\n" or textlen > TEXTLEN:
                textlines.append(cached_text)
                cached_text = ""
                textlen = 0
            if char != "\n":
                cached_text += char
        content_line = 0
        content_line_max = len(textlines)
        utils.fill_list_index(textlines, [""] * CONTENT_LEN)
        finished_reading = False
        self.BroadcastEvent(
            event_apis.PlayerStartReadingEvent(player, text_tagname).to_broadcast()
        )
        max_ln = max(0, content_line_max - CONTENT_LEN)
        while True:
            content = (
                f"§b{title} §7>>> §7line {content_line + 1} of {content_line_max} §f\n§7┃§f "
                + "\n§7┃§f ".join(textlines[content_line : content_line + CONTENT_LEN])
                + "\n §3上下滑动屏幕滚动， 左滑退出"
            )
            action = self.sight.wait_next_action(player, content)
            match action:
                case actions.UP:
                    content_line = max(content_line - 1, 0)
                case actions.DOWN:
                    content_line = max(
                        0, min(content_line + 1, content_line_max - CONTENT_LEN)
                    )
                    if not finished_reading and content_line == max_ln:
                        finished_reading = True
                        self.BroadcastEvent(
                            event_apis.PlayerReadFinishedEvent(
                                player, text_tagname
                            ).to_broadcast()
                        )
                case actions.LEFT:
                    self.BroadcastEvent(
                        event_apis.PlayerExitReadingEvent(
                            player, text_tagname
                        ).to_broadcast()
                    )
                    break
                case actions.PLAYER_LEFT | actions.SNOWBALL_EXIT:
                    self.BroadcastEvent(
                        event_apis.PlayerExitReadingEvent(
                            player, text_tagname
                        ).to_broadcast()
                    )
                    raise SystemExit


entry = plugin_entry(CustomRPGItemScript)

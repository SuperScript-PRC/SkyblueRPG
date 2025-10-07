from collections.abc import Callable
from dataclasses import dataclass
from tooldelta import Plugin, Player, plugin_entry, utils, TYPE_CHECKING


@dataclass
class Setting:
    id: str
    show_name: str
    enum: list[str]
    default_value: int

    def display_from_settings(self, settings: dict):
        return self.display(settings.get(self.id, self.default_value))

    def display(self, section: int):
        count = len(self.enum)
        main_body = (
            self.show_name
            + "： "
            + ("§e< §f" if section > 0 else "§8< §f")
            + self.enum[section]
            + (" §e>" if section < count - 1 else " §8>")
        )
        if len(self.enum) == 2:
            return f"§{'c' if section == 0 else 'a'}┃ §f{main_body}"
        else:
            return f"§6┃ §f{main_body}"

    def change(self, settings: dict, mode: int):
        if mode == 1:
            last_op = settings.get(self.id, self.default_value)
            settings[self.id] = min(
                settings.get(self.id, self.default_value) + 1, len(self.enum) - 1
            )
            return settings[self.id] != last_op
        elif mode == -1:
            last_op = settings.get(self.id, self.default_value)
            settings[self.id] = max(settings.get(self.id, self.default_value) - 1, 0)
            return settings[self.id] != last_op
        else:
            return False


available_settings = [
    # Setting("auto_change_weapon", "武器耐久耗尽自动切换", ["§c关闭", "§a打开"], 1),
    Setting(
        "pvp",
        "PVP",
        ["§c关闭", "§a打开"],
        0,
    ),
    Setting(
        "plot_printer_sfx",
        "剧情打字音效",
        ["§c关闭", "§b打字机", "§6蜂鸣器", "§a村民"],
        1,
    ),
    Setting(
        "rpg_power_tips",
        "蔚源获取提示",
        ["§c关闭", "§a打开"],
        1,
    ),
    Setting(
        "rpg_qq_notify",
        "进退游戏群播报",
        ["§c关闭", "§a打开"],
        1,
    ),
    Setting(
        "rpg_plot_stereo_sfx",
        "立体声剧情背景音效",
        ["§c关闭", "§a打开"],
        1,
    ),
    # Setting("sfx", "剧情背景音效", ["§c关闭", "§a打开"], 1),
    # Setting("textfield_size", "剧情文本框尺寸", ["40", "60", "80"], 1),
]

all_settings = {i.id: i for i in available_settings}


class CustomRPGSettings(Plugin):
    name = "自定义RPG-设置"
    author = "SuperScript"
    version = (0, 0, 1)

    def __init__(self, frame):
        super().__init__(frame)
        self.ListenPreload(self.on_def)
        self.ListenActive(self.on_inject, priority=-13)
        self.settings_changed_listeners: dict[
            str, list[Callable[[Player, int], None]]
        ] = {}

    def on_def(self):
        self.snowmenu = self.GetPluginAPI("雪球菜单v3")
        self.rpg = self.GetPluginAPI("自定义RPG")
        self.sight = self.GetPluginAPI("视角菜单")
        if TYPE_CHECKING:
            from 雪球菜单v3 import SnowMenuV3
            from 自定义RPG import CustomRPG
            from 前置_视角菜单 import SightRotation

            self.snowmenu: SnowMenuV3
            self.rpg: CustomRPG
            self.sight: SightRotation

    def on_inject(self):
        self.snowmenu.register_main_page(self.on_settings, "游戏设置")

    def on_settings(self, player: Player):
        self._on_settings(player)
        return False

    def add_setting_changed_listener(
        self, setting_id: str, listener: Callable[[Player, int], None]
    ):
        self.settings_changed_listeners.setdefault(setting_id, []).append(listener)

    def _on_trig_cb(self, player: Player, setting_id: str, value: int):
        for listener in self.settings_changed_listeners.get(setting_id, []):
            listener(player, value)

    @utils.thread_func("玩家进行设置")
    def _on_settings(self, player: Player):
        sections = available_settings.copy()
        now_selected = 0
        settings = self.get_player_settings(player)
        ACTS = self.sight.HeadAction
        with self.sight.create_env(player) as e:
            self.game_ctrl.sendwocmd(f'execute as "{player.name}" at @s run tp ~~~ 0 0')
            while 1:
                output = "❁ §b§l游戏设置§r"
                now_section = sections[now_selected]
                for index in range(now_selected - 3, now_selected + 4):
                    if index < 0 or index >= len(sections):
                        output += "\n§8    ┃"
                    elif now_selected == index:
                        output += "\n§b " + sections[index].display_from_settings(
                            settings
                        )
                    else:
                        output += "\n    " + sections[index].display_from_settings(
                            settings
                        )
                output += "\n§b抬头/低头选择设置项 §a左右划动屏幕切换设置选项 §c扔雪球退出"
                resp = e.wait_next_action(output)
                match resp:
                    case ACTS.LEFT:
                        if now_section.change(settings, -1):
                            self.game_ctrl.sendwocmd(
                                f'execute as "{player.name}" at @s run playsound random.toast'
                            )
                            self._on_trig_cb(player, now_section.id, settings[now_section.id])
                    case ACTS.RIGHT:
                        if now_section.change(settings, 1):
                            self.game_ctrl.sendwocmd(
                                f'execute as "{player.name}" at @s run playsound random.toast'
                            )
                            self._on_trig_cb(player, now_section.id, settings[now_section.id])
                    case ACTS.UP:
                        now_selected = max(now_selected - 1, 0)
                    case ACTS.DOWN:
                        now_selected = min(now_selected + 1, len(sections) - 1)
                    case ACTS.SNOWBALL_EXIT:
                        self.game_ctrl.player_actionbar(player.name, "❏ §a设置已保存")
                        self.game_ctrl.sendwocmd(
                            f'execute as "{player.name}" at @s run playsound note.pling @s ~~~ 1 1.4'
                        )
                        break
                    case _:
                        return
            self.set_player_settings(player, settings)

    def get_player_settings(self, player: Player) -> dict[str, int]:
        return utils.tempjson.load_and_read(
            self.format_data_path(player.xuid + ".json"),
            need_file_exists=False,
            default={},
        )

    def set_player_settings(self, player: Player, settings: dict):
        utils.tempjson.load_and_write(
            self.format_data_path(player.xuid + ".json"),
            settings,
            need_file_exists=False,
        )

    def get_player_setting(self, player: Player, id: str) -> int:
        res = self.get_player_settings(player).get(id)
        if res is not None:
            return res
        else:
            setting = all_settings.get(id)
            if setting is None:
                raise ValueError(f"设置不存在: {id}")
            else:
                return setting.default_value


entry = plugin_entry(CustomRPGSettings, "自定义RPG-设置")

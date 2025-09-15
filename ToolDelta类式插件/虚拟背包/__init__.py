import uuid
import os
import copy
from dataclasses import dataclass, field
from tooldelta import (
    Plugin,
    utils,
    fmts,
    TYPE_CHECKING,
    Player,
    FrameExit,
    plugin_entry,
)

from typing import Callable  # noqa

item_id_map: dict[str, "Item"] = {}


def make_uuid():
    return str(uuid.uuid1())


# 去除一些常见的敏感词
def proh_repl(fmt: str):
    return fmt.replace("qq", "QX")


def in_category(_category: str, _parent_category: str):
    category = _category.split(":")
    parent_category = _parent_category.split(":")
    if len(category) < len(parent_category):
        return False
    for c, c2 in zip(parent_category, category):
        if c != c2:
            return False
    return True


class BackpackOpenEnv:
    def __init__(self, sys: "VirtuaBackpack", player: Player):
        self.sys = sys
        self.player = player

    def __enter__(self):
        self.sys.game_ctrl.sendwocmd(
            f"execute as {self.player.safe_name} at @s run tp ~~~ 0 0"
        )
        self.sys.game_ctrl.sendwocmd(
            f"execute as {self.player.safe_name} at @s run playsound armor.equip_leather @s"
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.sys.game_ctrl.sendwocmd(
            f"execute as {self.player.safe_name} at @s run playsound armor.equip_leather @s"
        )


@dataclass
class Item:
    "物品(抽象化的)"

    id: str
    "唯一标识"
    disp_name: str | Callable[["SlotItem"], str]
    "展示名"
    categories: list[str] = field(default_factory=list)
    "所属组类"
    stackable: bool = True
    "可否堆叠"
    description: str | Callable[["SlotItem"], str] = ""
    "物品简介"
    # metadata
    on_use: Callable[["SlotItem", Player], bool] | None = None
    "使用该物品时的回调 (使用者, 玩家名) -> 是否不消耗"
    on_use_extra: dict[str, Callable[["SlotItem", Player], None]] = field(
        default_factory=dict
    )

    def force_disp(self, slotitem: "SlotItem | None" = None):
        if isinstance(self.disp_name, str):
            return self.disp_name
        if slotitem is None:
            return self.disp_name(SlotItem(self))
        else:
            return self.disp_name(slotitem)


@dataclass
class SlotItem:
    "背包槽中的物品"

    item: Item
    count: int = 1
    uuid: str = field(default_factory=make_uuid)
    metadata: dict = field(default_factory=dict)

    def dump(self):
        r = {"Count": self.count, "UUID": self.uuid}
        if self.metadata:
            r["MTData"] = self.metadata
        return r

    def copy(self):
        return SlotItem(
            self.item, self.count, make_uuid(), copy.deepcopy(self.metadata)
        )

    def orig_copy(self):
        return SlotItem(self.item, self.count, self.uuid, copy.deepcopy(self.metadata))

    @staticmethod
    def make(id, data):
        return SlotItem(
            item_id_map[id], data["Count"], data["UUID"], data.get("MTData", {})
        )

    @property
    def disp_name(self):
        if callable(self.item.disp_name):
            return self.item.disp_name(self)
        else:
            return self.item.disp_name

    def force_disp(self, slotitem: "SlotItem | None" = None):
        return self.item.force_disp(self)

    @property
    def id(self):
        return self.item.id

    def __hash__(self):
        return id(self)


class Backpack:
    def __init__(self, owner: Player, datas):
        self.owner = owner
        _bag: dict[str, list[SlotItem]] = {}
        for k, v in datas.items():
            if k in item_id_map:
                _bag[k] = [SlotItem.make(k, i) for i in v]
            else:
                fmts.print_war(f"{owner.name} 背包内存在物品未被注册: {k}")
        self._bag = _bag

    def get_items(self):
        items: list["SlotItem"] = []
        for i in self._bag.values():
            items += i
        return items

    def get_item(self, item_uuid: str):
        for item_stacks in self._bag.values():
            for item in item_stacks:
                if item.uuid == item_uuid:
                    return item
        return None

    def item_count(self, item_id: str):
        item_stack = self._bag.get(item_id)
        if item_stack is None:
            return 0
        elif (item_count := len(item_stack)) != 1:
            return item_count
        else:
            return item_stack[0].count

    def find_item_stackable(self, item_id: str):
        item = self._bag.get(item_id)
        if item is None:
            return None
        elif len(item) != 1:
            raise ValueError("Item is not stackable")
        else:
            return item[0]

    def find_items(self, item_id: str):
        item = self._bag.get(item_id)
        if item is None:
            return None
        else:
            return item

    def find_item_by_category(self, categories: list[str]):
        resp: list[SlotItem] = []
        for item_stack in self._bag.values():
            for c in item_stack[0].item.categories:
                for c2 in categories:
                    if c.startswith(c2) and in_category(c, c2):
                        resp += item_stack

        return resp

    def find_item_by_metadata_key(self, key: str):
        resp: list[SlotItem] = []
        for item_stack in self.get_items():
            if key in item_stack.metadata.keys():
                resp.append(item_stack)
        return resp

    def find_item_by_metadata_property(self, key: str, value):
        resp: list[SlotItem] = []
        for item_stack in self.get_items():
            if item_stack.metadata.get(key) == value:
                resp.append(item_stack)
        return resp

    def add_item(self, item: Item | SlotItem, count: int = 1, metadata=None):
        if isinstance(item, SlotItem):
            metadata = item.metadata
            count = item.count or 1
            uuid = item.uuid
            item = item.item
        elif isinstance(item, Item):
            uuid = make_uuid()
        else:
            raise TypeError(f"Item must be Item or SlotItem, got {type(item).__name__}")
        if item.id not in self._bag.keys():
            self._bag[item.id] = [SlotItem(item, count, uuid, metadata=metadata or {})]
        else:
            if item.stackable and not metadata:
                self._bag[item.id][0].count += count
            else:
                if count != 1:
                    for _ in range(count):
                        self._bag[item.id].append(
                            SlotItem(item, 1, metadata=metadata or {})
                        )
                else:
                    self._bag[item.id].append(
                        SlotItem(item, 1, uuid, metadata=metadata or {})
                    )

    def remove_item(self, item_id: str, count: int = 1, item_uuid: str = ""):
        item_collections = self._bag[item_id]
        if item_uuid:
            for i in item_collections:
                if i.uuid == item_uuid:
                    assert i.count - count >= 0, (
                        f"Item remove overcount: now {i.count}, attempt to remove {count}"
                    )
                    i.count -= count
                    if i.count == 0:
                        item_collections.remove(i)
                    if len(item_collections) == 0:
                        del self._bag[item_id]
                    return
            raise ValueError(f"Item remove failed: not exists: {item_id}:{item_uuid}")
        else:
            oi = item_collections[0]
            if oi.item.stackable:
                if oi.count < count:
                    raise ValueError(
                        f"Item remove failed: not enough: {oi.count}<{count}"
                    )
                oi.count -= count
                if oi.count == 0:
                    del self._bag[item_id]
            else:
                if len(item_collections) < count:
                    raise ValueError(
                        f"Item remove failed: not enough: {oi.count}<{count} (not stackable)"
                    )
                else:
                    item_collections = item_collections[count:]
                    if len(item_collections) == 0:
                        del self._bag[item_id]
                    else:
                        self._bag[item_id] = item_collections

    def dump(self):
        return {k: [i.dump() for i in v] for k, v in self._bag.items()}


class VirtuaBackpack(Plugin):
    author = "SuperScript"
    name = "虚拟背包"
    version = (0, 0, 1)
    Item = Item
    Backpack = Backpack
    SlotItem = SlotItem
    PAGE_SIZE = 12

    def __init__(self, frame):
        super().__init__(frame)
        self.cached_backpacks: dict[str, Backpack] = {}
        self.ListenPreload(self.on_def)
        self.ListenActive(self.on_inject)
        self.ListenPlayerJoin(self.on_player_join)
        self.ListenPlayerLeave(self.on_player_leave)
        self.ListenFrameExit(self.on_frame_exit)

    def on_def(self):
        snowmenu = self.GetPluginAPI("雪球菜单v3")
        self.game_intr = self.GetPluginAPI("前置-世界交互")
        self.sight = self.GetPluginAPI("视角菜单")
        self.act = self.GetPluginAPI("行为监测")
        self.crpg = self.GetPluginAPI("自定义RPG", force=False)
        if TYPE_CHECKING:
            global HeadActionEnv
            from 雪球菜单v3 import SnowMenuV3
            from 前置_世界交互 import GameInteractive
            from 前置_视角菜单 import SightRotation, HeadActionEnv
            from 前置_行为监测 import ActionListener

            snowmenu: SnowMenuV3
            self.game_intr: GameInteractive
            self.sight: SightRotation
            self.act: ActionListener
        self.make_data_path()
        snowmenu.register_main_page(
            lambda player: self.skim_bag(player), "背包", priority=2
        )

    def on_player_join(self, playerf: Player):
        player = playerf.name
        self.game_ctrl.sendwocmd(f"/tag @a[name={player}] remove bagdetect")

    def on_player_leave(self, playerf: Player):
        player = playerf.name
        if player in self.cached_backpacks.keys():
            self.save_backpack(self.cached_backpacks[player])
            del self.cached_backpacks[player]

    def on_frame_exit(self, e: FrameExit):
        fmts.print_suc("虚拟背包: 所有人背包物品已保存")
        for player in self.game_ctrl.allplayers:
            if player in self.cached_backpacks.keys():
                self.save_backpack(self.cached_backpacks[player])
                del self.cached_backpacks[player]

    def regist_item(self, item: Item):
        item_id_map[item.id] = item

    def get_registed_items(self):
        return item_id_map

    def get_registed_item(self, id: str):
        return item_id_map.get(id)

    def load_backpack(self, player: Player, is_temp: bool = True) -> Backpack:
        backpack_path = self.format_data_path(player.xuid + ".json")
        if is_temp and player.name in self.cached_backpacks.keys():
            return self.cached_backpacks[player.name]
        else:
            if not os.path.isfile(backpack_path):
                backpack = Backpack(player, {})
            else:
                backpack = Backpack(
                    player, utils.safe_json.safe_json_load(backpack_path)
                )
            if is_temp:
                self.cached_backpacks[player.name] = backpack
                return self.cached_backpacks[player.name]
            else:
                return backpack

    def select_item(self, player: Player, bp: Backpack):
        # 从背包选择一个物品
        backpack_items: list[SlotItem] = []
        for v in bp._bag.values():
            backpack_items += v
        return self.select_item_special(player, backpack_items)

    def select_item_special(self, player: Player, backpack_items: list[SlotItem]):
        HeadAction = self.sight.HeadAction
        # 从背包类似物里选择一个物品
        page = 0
        sel_len = len(backpack_items)
        # format
        items_pages = utils.split_list(backpack_items, self.PAGE_SIZE)
        item_selected = None
        # items_starlevel
        with self.sight.create_env(player):
            while 1:
                item_page = items_pages[page // self.PAGE_SIZE]
                pointer = page % self.PAGE_SIZE
                format_txt = "§7--------<§f背包物品选择§7>--------"
                for i, item in enumerate(item_page):
                    starlevel_color = "§7"
                    if self.crpg:
                        if item.item.id in self.crpg.items_starlevel:
                            starlevel = self.crpg.items_starlevel[item.item.id]
                            starlevel_color = ("§7", "§3", "§9", "§d", "§e")[
                                starlevel - 1
                            ]
                    if i == pointer:
                        fronter = "§r§e> "
                    else:
                        fronter = "§r  "
                    format_txt += (
                        "\n" + fronter + starlevel_color + "┃ " + item.disp_name
                    )
                for i in range(8 - len(item_page)):
                    format_txt += "\n§r§8  ┃"
                format_txt += "\n§a\n§a\n§a"
                item_selected = item_page[pointer]
                resp = self.sight.wait_next_action(player, proh_repl(format_txt))
                if resp == HeadAction.PLAYER_LEFT:
                    raise SystemExit
                match resp:
                    case HeadAction.UP:
                        page -= 1
                    case HeadAction.DOWN:
                        page += 1
                    case HeadAction.LEFT:
                        ...
                    case HeadAction.RIGHT:
                        break
                    case _:
                        return
                if page >= sel_len:
                    page = 0
        return item_selected

    def skim_bag(self, player: Player):
        HeadAction = self.sight.HeadAction

        def _skim_specified_items(items: list[SlotItem]):
            page = 0
            sel_len = len(items)
            items_pages = utils.split_list(items, self.PAGE_SIZE)
            self.game_ctrl.sendwocmd(
                f"execute as {player.safe_name} at @s run tp ~~~ 0 0"
            )
            while True:
                if page >= sel_len:
                    page = 0
                elif page < 0:
                    page = sel_len - 1
                pointer = page % self.PAGE_SIZE
                item_page = items_pages[page // self.PAGE_SIZE]
                item_selected = item_page[pointer]
                format_txt = f"§7------<§f[背包 §6{(page // self.PAGE_SIZE) + 1}§f/§6{len(items_pages)} §f潜行可翻整页]§7>------"
                for i, item in enumerate(item_page):
                    starlevel_color = "§7"
                    if self.crpg:
                        if item.item.id in self.crpg.item_holder.items_starlevel:
                            starlevel = self.crpg.item_holder.get_item_starlevel(
                                item.item.id
                            )
                            starlevel_color = ("§7", "§3", "§9", "§d", "§e")[
                                starlevel - 1
                            ]
                    if i == pointer:
                        fronter = "§e> "
                    else:
                        fronter = "  "
                    format_txt += (
                        "\n"
                        + fronter
                        + starlevel_color
                        + "┃ "
                        + item.disp_name
                        + f"§r§7 x {item.count}"
                    )
                for i in range(len(item_page), 8):
                    format_txt += "\n§r§8  ┃"
                format_txt += "\n§r§c扔雪球返回 §f| §a右转查看 §f| §b上下滑动切换"
                format_txt += "\n§a\n§a\n§a"
                resp = self.sight.wait_next_action(player, proh_repl(format_txt))
                if resp == HeadAction.PLAYER_LEFT:
                    break
                match resp:
                    case HeadAction.SNOWBALL_EXIT:
                        break
                    case HeadAction.UP:
                        if self.act.is_shifting(player):
                            page -= self.PAGE_SIZE
                        else:
                            page -= 1
                        self.game_ctrl.sendwocmd(
                            f"execute as {player.safe_name} at @s run playsound dig.sand @s"
                        )
                    case HeadAction.DOWN:
                        if self.act.is_shifting(player):
                            page += self.PAGE_SIZE
                        else:
                            page += 1
                        self.game_ctrl.sendwocmd(
                            f"execute as {player} at @s run playsound dig.stone @s"
                        )
                    case HeadAction.LEFT:
                        return
                    case HeadAction.RIGHT:

                        def _on_use(slotitem: SlotItem, player: Player):
                            on_use_func = slotitem.item.on_use
                            if on_use_func is None:
                                return
                            resp = on_use_func(slotitem, player)
                            if not resp:
                                self.load_backpack(player).remove_item(
                                    item_selected.item.id, 1, item_selected.uuid
                                )

                        x_section = 0
                        all_sections: list[
                            tuple[str, Callable[[SlotItem, Player], None]]
                        ] = (
                            [("使用", _on_use)]
                            if item_selected.item.on_use is not None
                            else []
                        )
                        all_sections.extend(
                            list(item_selected.item.on_use_extra.items())
                        )
                        self.game_ctrl.sendwocmd(
                            f"execute as {player} at @s run playsound note.bit @s ~~~ 1 1.41"
                        )
                        while True:
                            desc = item_selected.item.description
                            if not isinstance(desc, str):
                                desc = desc(item_selected)
                            desc = desc.replace("[玩家名]", player.name)
                            section_texts = "§r§f"
                            for i, (disp_name, _) in enumerate(all_sections):
                                section_texts += "§8["
                                if i == x_section:
                                    section_texts += "§b"
                                else:
                                    section_texts += "§7"
                                section_texts += f"{disp_name}§8]  "
                            format_txt = (
                                f"{item_selected.disp_name} §7x {item_selected.count}\n"
                                "§r§f"
                                + "一" * 30
                                + "\n"
                                + "\n".join(self._cut_long_str(desc))
                            )
                            for i in range(8 - len(format_txt.split("\n"))):
                                format_txt += "\n§r"
                            format_txt += "\n" + section_texts
                            if all_sections:
                                format_txt += "\n§c左划退出 §6右划切换功能 §a扔雪球确认功能\n§a\n§a"
                            else:
                                format_txt += "\n§c左划退出\n§a\n§a"
                            resp = self.sight.wait_next_action(
                                player, proh_repl(format_txt)
                            )
                            match resp:
                                case HeadAction.PLAYER_LEFT:
                                    return
                                case HeadAction.LEFT:
                                    x_section -= 1
                                    if x_section < 0:
                                        break
                                case HeadAction.RIGHT:
                                    x_section += 1
                                    if x_section >= len(all_sections):
                                        x_section = 0
                                case HeadAction.SNOWBALL_EXIT:
                                    if all_sections == []:
                                        pass
                                    else:
                                        all_sections[x_section][1](
                                            item_selected, player
                                        )

                    case other:
                        fmts.print_war(
                            f"虚拟背包: 玩家 {player} 的菜单响应退出: {other}"
                        )
                        raise SystemExit

        def _skim_categories(
            current_levels: list[str], d: dict[str, dict], e: "HeadActionEnv"
        ):
            if "" in d:
                d = d.copy()
                del d[""]
            index = 0
            sections = list(d.keys())
            self.game_ctrl.sendwocmd(f"execute as {player} at @s run tp ~~~ 0 0")
            while 1:
                output_text = f"选择分组 §l{'>'.join(current_levels)}"
                for i, category in enumerate(d.keys()):
                    is_current_section = index == i
                    if is_current_section:
                        fronter = "§r§e>§f"
                    else:
                        fronter = "§r§7|"
                    output_text += f"\n{fronter} {category}"
                output_text += "\n§r§c扔雪球返回 §f| §a右转进入 §f| §b上下滑动切换"
                resp = e.wait_next_action(output_text)
                match resp:
                    case HeadAction.SNOWBALL_EXIT:
                        return None
                    case HeadAction.UP:
                        index = max(index - 1, 0)
                        self.game_ctrl.sendwocmd(
                            f"execute as {player} at @s run playsound dig.sand @s"
                        )
                    case HeadAction.DOWN:
                        index = min(index + 1, len(sections) - 1)
                        self.game_ctrl.sendwocmd(
                            f"execute as {player} at @s run playsound dig.stone @s"
                        )
                    case HeadAction.LEFT:
                        return None
                    case HeadAction.RIGHT:
                        section = d[sections[index]]
                        if "" in section:
                            _skim_specified_items(section[""])
                        else:
                            resp1 = _skim_categories(
                                [*current_levels, sections[index]], section, e
                            )
                            if resp1 is not None:
                                return resp1
                            else:
                                continue
                    case _:
                        return

        @utils.thread_func("玩家查看背包")
        def _skim_bag_thread():
            if len((bp := self.load_backpack(player))._bag.values()) < 1:
                player.setActionbar("§6背包空空如也...")
                return
            bp_items = self.divide_items_by_category_deeply(bp.get_items())
            with BackpackOpenEnv(self, player), self.sight.create_env(player) as env:
                _skim_categories([], bp_items, env)
            player.setActionbar("§7<§a背包已关闭§7>")

        _skim_bag_thread()
        return False

    def divide_items_by_category_deeply(self, items: list["SlotItem"]):
        def recursive_divide(items_and_current_level):
            sub_levels = {}
            for item, levels in items_and_current_level:
                if levels == []:
                    sub_levels.setdefault("", [])
                    sub_levels[""].append(item)
                else:
                    this_level = levels[0]
                    sub_levels.setdefault(this_level, [])
                    sub_levels[this_level].append((item, levels[1:]))
            for k, v in sub_levels.items():
                if k != "":
                    sub_levels[k] = recursive_divide(v)
            return sub_levels

        items_cached = []
        for item in items:
            for category in item.item.categories:
                if category.startswith("__"):
                    # ignore hidden categories
                    continue
                category_levels = category.split(":")
                items_cached.append((item, category_levels))
        return recursive_divide(items_cached)

    def save_backpack(self, bp: Backpack):
        backpack_path = self.format_data_path(bp.owner.xuid + ".json")
        utils.safe_json.safe_json_dump(bp.dump(), backpack_path)

    @utils.timer_event(150, "定时保存背包数据")
    def save_backpack_timer(self):
        for backpack in self.cached_backpacks.values():
            self.save_backpack(backpack)

    def on_inject(self):
        self.game_ctrl.sendwocmd("/tag @a remove bagdetect")
        self.save_backpack_timer()

    def divide_items_by_category(self, items: list["SlotItem"]):
        o: dict[str, list["SlotItem"]] = {}
        for item in items:
            for category in item.item.categories:
                o.setdefault(category, [])
                o[category].append(item)
        return o

    def _cut_long_str(self, s: str) -> list[str]:
        strlen = 0
        output = []
        cached_str = ""
        for c in s:
            if c != "|":
                strlen += (not c.isascii()) + 1
            cached_str += c
            if c == "\n":
                strlen = 0
            elif c == "§":
                strlen -= 1
            if strlen >= 60:
                strlen = 0
                output.append(cached_str)
                cached_str = ""
        output.append(cached_str)
        return output


entry = plugin_entry(VirtuaBackpack, "虚拟背包")

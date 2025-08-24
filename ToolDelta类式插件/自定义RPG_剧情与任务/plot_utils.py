import time
from typing import TYPE_CHECKING
from tooldelta import utils, Player
from .event_apis import PlayerTradingWithNPCEvent
from .define import ShopSellMeta, ShopSell

if TYPE_CHECKING:
    from . import CustomRPGPlotAndTask
    from .quest_loader import RegisteredPlot

SYSTEM: "CustomRPGPlotAndTask | None" = None


class MovementLimiter:
    def __init__(self, player: Player):
        self.player = player

    def __enter__(self):
        disable_movement(self.player)

    def __exit__(self, exc_type, exc_val, exc_tb):
        enable_movement(self.player)


class RotationCtrl:
    def __init__(self, player: Player):
        self.player = player
        self.m = MovementLimiter(player)

    def __enter__(self):
        self.m.__enter__()
        get_system().game_ctrl.sendwocmd(
            f"execute as {self.player.safe_name} at @s run tp ~~~ facing @e[c=1,tag=npc]"
        )
        get_system().game_ctrl.sendwocmd(
            f"execute as {self.player.safe_name} at @s run camera @s set minecraft:free ease 0.5 linear pos ^^3^-3 facing ~~1.7~"
        )

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.m.__exit__(exc_type, exc_val, exc_tb)
        get_system().game_ctrl.sendwocmd(
            f"execute as {self.player.safe_name} at @s run tp ~~~ facing @e[c=1,tag=npc]"
        )
        get_system().game_ctrl.sendwocmd(
            f"execute as {self.player.safe_name} at @s run camera @s set minecraft:free ease 0.5 linear pos ~~1.7~ facing ~~1.7~"
        )
        time.sleep(0.5)
        get_system().game_ctrl.sendwocmd(f"camera {self.player.safe_name} clear")


class Dialogue:
    def __init__(self, player: Player, npc_name: str):
        self.player = player
        self.npc_name = npc_name
        self.text = "..."

    def pprint(
        self,
        plot_text: str,
        spd: float = 8,
        delay: float = 3,
    ):
        self.text = pprint(self.player, self.npc_name, plot_text, spd, delay)

    def choice(
        self,
        sections: list[str],
        extra_insertion_sections: list["RegisteredPlot"] = [],
    ):
        return choice(self.player, self.text, sections, extra_insertion_sections)

    def show_buy_and_sell(self, *buys_and_sells: ShopSell | ShopSellMeta):
        return show_buy_and_sell(self.player, self.npc_name, *buys_and_sells)

    def enter(self):
        return RotationCtrl(self.player)


def set_system(sys: "CustomRPGPlotAndTask"):
    global SYSTEM
    SYSTEM = sys


def get_system() -> "CustomRPGPlotAndTask":
    if SYSTEM is None:
        raise RuntimeError("SYSTEM is not initialized")
    return SYSTEM


def simple_actionbar_print(
    player: Player,
    plot_texts: str,
    speed: float = 8,
    delay: float = 3,
) -> str:
    lettok = ""
    c = 0
    self = get_system()
    with self.create_plotskip_detector(player) as ps:
        jumping = 0
        for char in plot_texts:
            c += 0.5 + 0.5 * (not char.isascii())
            lettok += char
            if char == "§":
                continue
            if c > 25:
                c = 0
                lettok += "\n"
            if jumping > 0:
                jumping -= 1
                continue
            if ps.plot_skip():
                jumping += 20
                continue
            time.sleep(round(1 / speed, 3))
            player.setActionbar(lettok)

        if delay == -1:
            for _ in range(0, 2):
                player.setActionbar(lettok)
                if ps.plot_skip():
                    break
                time.sleep(0.5)
            self.snowmenu.simple_select_dict(
                player, {0: lettok + "\n§r§7抬头/低头以继续 >"}
            )
            self.game_ctrl.sendwocmd(f'/execute as "{player.name}" at @s run tp ~~~~ 0')
        else:
            for _ in range(0, int(delay * 2)):
                player.setActionbar(lettok)
                if ps.plot_skip():
                    break
                time.sleep(0.5)
    return lettok


def plot_box_print(
    player: Player,
    character_name: str,
    plot_text: str,
    spd: float = 8,
    delay: float = 2,
):
    self = get_system()
    plot_refmt = ""
    lntime = 0
    jumping = 0
    plot_printer_sfx = (None, "note.hat", "note.bit", "mob.villager.idle")[
        self.settings.get_player_setting(player, "plot_printer_sfx")
    ]
    with self.create_plotskip_detector(player) as ps:
        for char in plot_text:
            plot_refmt += char
            if char == "§":
                continue
            if char.isascii():
                lntime += 0.5
            else:
                lntime += 1
            if (
                lntime > self.cfg["剧情设置"]["剧情对话框每行的最多字符数"]
                and char not in ".，。？！（）"
            ):
                lntime = 0
                plot_refmt += "\n "
            if jumping:
                jumping -= 1
                continue
            show_text = utils.simple_fmt(
                {"[角色名]": character_name, "[内容]": "§r§f" + plot_refmt},
                self.cfg["剧情设置"]["剧情对话框显示格式"],
            )
            player.setActionbar(show_text)
            if plot_printer_sfx is not None:
                self.game_ctrl.sendwocmd(
                    f'execute as "{player.name}" at @s run playsound {plot_printer_sfx} @s'
                )
            if ps.plot_skip():
                jumping += 20
                continue
            time.sleep(round(1 / spd, 3))
        show_text = utils.simple_fmt(
            {"[角色名]": character_name, "[内容]": "§r§f" + plot_refmt},
            self.cfg["剧情设置"]["剧情对话框显示格式"],
        )
        if delay == -1:
            self.snowmenu.simple_select_dict(
                player, {0: show_text + "\n§r§7抬头/低头以继续 >"}
            )
            self.game_ctrl.sendwocmd(f'execute as "{player.name}" at @s run tp ~~~~ 0')
        else:
            for _ in range(0, int(delay * 2)):
                if ps.plot_skip():
                    break
                player.setActionbar(show_text)
                time.sleep(0.5)
    return show_text


def plot_box_print_with_choice(
    player: Player,
    prev_plot_text: str,
    sections: list[str],
    extra_insertion_sections: list["RegisteredPlot"] = [],
):
    self = get_system()
    extra_sections = [i._section_text or "???" for i in extra_insertion_sections]
    shift = len(extra_insertion_sections)
    all_sections = extra_sections + sections

    def _menu(_, page: int):
        if page < len(all_sections):
            menu_ptext = prev_plot_text + "\n"
            for i, txt in enumerate(all_sections):
                if len(txt) > 0 and txt[0] == "$":
                    sign = "㉿"
                    txt = txt[1:]
                else:
                    sign = "➡"
                if i == page:
                    chostext = f"§b{sign} | §f" + txt
                else:
                    chostext = f"§7{sign} | §f" + txt
                menu_ptext += "\n" + chostext
            return menu_ptext + "\n§7 - <扔雪球切换 抬头确认> - "
        else:
            return None

    res = 0
    while 1:
        resp = self.snowmenu.simple_select(player, _menu)
        if resp is None:
            if player.name not in self.game_ctrl.allplayers:
                raise self.PlotPlayerExit
            else:
                self.rpg.show_warn(player, "请选择一个选项")
                sleep(player, 0.2)
                continue
        res = resp
        break
    if res < shift:
        ex = extra_insertion_sections[res].run(player)
        raise self.PlotExit(ex)
    else:
        res -= shift
    return res


def show_buy_and_sell(
    player: Player,
    shop_name: str,
    *orig_buys_and_sells: ShopSell | ShopSellMeta,
):
    sys = get_system()
    last_page = 0
    page_max = len(orig_buys_and_sells) - 1
    bought: list[ShopSell | ShopSellMeta] = []
    playerinf = sys.rpg.player_holder.get_playerinfo(player)
    new_buys_and_sells = list(orig_buys_and_sells)
    if eff := playerinf.get_effect("Kindness"):
        level = eff.level
        for i, bs in enumerate(orig_buys_and_sells):
            if bs.cost_item.id == "蔚蓝点":
                if bs.cost_count < 30:
                    new_buycount = int(
                        max(bs.cost_count // 2, bs.cost_count * (1 - level / 10))
                    )
                else:
                    new_buycount = int(
                        max(bs.cost_count // 2, bs.cost_count - level * 6)
                    )
                new_buys_and_sells[i].cost_count = new_buycount
    while 1:
        fmt_strings = []
        for i, bs in enumerate(new_buys_and_sells):
            left, cdmin_time = sys.get_shop_left2cd(player, shop_name, bs.tag)
            if left is None or cdmin_time == 0:
                left = bs.once_limit
            left_str = " 售罄" if left == 0 else f" 剩余{left}件"
            cd_str = (
                (sys.format_timer_zhcn(int(cdmin_time)) + "后补货")
                if not cdmin_time == 0
                else ""
            )
            old_buycount = orig_buys_and_sells[i].cost_count
            sellcount = (
                bs.sell_count if isinstance(bs, ShopSell) else bs.sell_item.count
            )
            if old_buycount > bs.cost_count:
                fmt_strings.append(
                    f"§f{bs.cost_item.disp_name}§r§ex§8{old_buycount}§e§l[{bs.cost_count}]§r §f➭ {bs.sell_item.disp_name}§r§ex{sellcount}§7{left_str} {cd_str} §c§l（折!）§r"
                )
            elif old_buycount < bs.cost_count:
                fmt_strings.append(
                    f"§f{bs.cost_item.disp_name}§r§ex§8{old_buycount}§e§l[{bs.cost_count}]§r §f➭ {bs.sell_item.disp_name}§r§ex{sellcount}§7{left_str} {cd_str} §c§4（涨!）§r"
                )
            else:
                fmt_strings.append(
                    f"§f{bs.cost_item.disp_name}§r§ex{bs.cost_count} §f➭ {bs.sell_item.disp_name}§r§ex{sellcount}§7{left_str} {cd_str}"
                )

        def _page_cb(_, page: int):
            if page > page_max:
                return None
            fmt_strings1 = fmt_strings.copy()
            fmt_strings1[page] = "§e> " + fmt_strings1[page]
            for _ in range(8 - len(fmt_strings1)):
                fmt_strings1.append("§7")
            shop_text = "\n".join(fmt_strings1)
            return (
                "§6"
                + shop_name
                + "\n§7"
                + "-" * 60
                + "\n§f"
                + shop_text
                + "\n§7"
                + "-" * 60
                + "\n§r§b扔雪球切换 §f| §a抬头购买 §f| §c低头退出"
            )

        res = sys.snowmenu.simple_select(player, _page_cb, last_page)
        if res is None:
            break
        last_page = res
        buy_arg = new_buys_and_sells[res]
        left, cdmin_time = sys.get_shop_left2cd(player, shop_name, buy_arg.tag)
        if left is None or cdmin_time == 0:
            left = buy_arg.once_limit
        if cdmin_time > 0 and left <= 0:
            sys.rpg.show_fail(player, "无法购买未补货或售罄的商品")
            continue
        elif (
            player_have := sys.rpg.backpack_holder.getItemCount(
                player, buy_arg.cost_item.id
            )
        ) < buy_arg.cost_count:
            sys.rpg.show_fail(
                player,
                f"需要的物品不足 §6（§f{buy_arg.cost_item.disp_name}§6： §c{player_have}§7/§f{buy_arg.cost_count}§6）",
            )
            continue
        sys.rpg.backpack_holder.clearItem(
            player, buy_arg.cost_item.id, buy_arg.cost_count
        )
        if isinstance(buy_arg, ShopSellMeta):
            sys.rpg.backpack_holder.giveItem(player, buy_arg.sell_item.copy())
        else:
            sys.rpg.backpack_holder.giveItems(
                player,
                sys.rpg.item_holder.createItems(
                    buy_arg.sell_item.id, buy_arg.sell_count
                ),
            )
        left -= 1
        if cdmin_time > 0:
            buycd = cdmin_time
        else:
            buycd = buy_arg.cooldown_min
        sys.set_shop_left2cddata(player, shop_name, buy_arg.tag, left, buycd)
        bought.append(buy_arg.copy())
        get_system().BroadcastEvent(
            PlayerTradingWithNPCEvent(player, buy_arg).to_broadcast()
        )
    return bought


def set_movement(
    player: Player,
    enabled: bool,
):
    get_system().game_ctrl.sendwocmd(
        f"inputpermission set {player.getSelector()} movement "
        + ("disabled", "enabled")[enabled]
    )


def enable_movement(player: Player):
    set_movement(player, True)


def disable_movement(player: Player):
    set_movement(player, False)


def is_plot_completed(player: Player, plot_name: str):
    self = get_system()
    return plot_name in self.check_plot_record(player).keys()


def start_quest(player: Player, quest_name: str):
    q = get_system().get_quest(quest_name)
    if q is None:
        player.show(f"§c无法开始任务 {quest_name}， 请告知管理员")
    else:
        get_system().add_quest(player, q)


def finish_quest(player: Player, quest_name: str):
    q = get_system().get_quest(quest_name)
    if q is None:
        player.show(f"§c无法结束任务 {quest_name}， 请告知管理员")
    else:
        get_system().finish_quest(player, q)


def tp(
    player: Player,
    pos: tuple[int, int, int],
    facing: tuple[int, int, int] | None = None,
    record: bool = False,
):
    x, y, z = pos
    if facing is None:
        get_system().game_ctrl.sendwocmd(f"tp {player.safe_name} {x} {y} {z}")
    else:
        fx, fy, fz = facing
        get_system().game_ctrl.sendwocmd(
            f"tp {player.safe_name} {x} {y} {z} facing {fx} {fy} {fz}"
        )
    if record:
        get_system().save_player_last_plot_position(player, (0, *pos))


def trans(player: Player, fadeIn: int, keep: int, fadeOut: int, color: int):
    r = (color & 0xFF0000) >> 16
    g = (color & 0x00FF00) >> 8
    b = color & 0x0000FF
    get_system().game_ctrl.sendwocmd(
        f"camera {player.safe_name} fade time {fadeIn} {keep} {fadeOut} color {r} {g} {b}"
    )


# def trans_clear(player: Player):
#     get_system().game_ctrl.sendwocmd(
#         f"camera {player.safe_name} clear"
#     )


def sleep(player: Player, t: float):
    with snowball_ignorer(player):
        time.sleep(t)


def snowball_ignorer(player: Player):
    return get_system().create_plotskip_detector(player)


def quest_is_finished(player: Player, quest_name: str):
    return quest_name in (i.tag_name for i in get_system().read_quests_finished(player))


def player_is_in_quest(player: Player, quest_name: str):
    return quest_name in (i.tag_name for i in get_system().read_quests(player))


# alias


def pprint(
    player: Player,
    character_name: str,
    plot_text: str,
    spd: float = 8,
    delay: float = 3,
) -> str:
    return plot_box_print(player, character_name, plot_text, spd, delay)


def choice(
    player: Player,
    prev_plot_text: str,
    sections: list[str],
    extra_insertion_sections: list["RegisteredPlot"] = [],
):
    return plot_box_print_with_choice(
        player, prev_plot_text, sections, extra_insertion_sections
    )


def createItem(tag_name: str, amount: int, metadata=None):
    return get_system().rpg.item_holder.createItem(tag_name, amount, metadata)


def createOrigItem(tag_name: str):
    item = get_system().rpg.backpack.get_registed_item(tag_name)
    if item is None:
        raise ValueError(f"物品不存在: {tag_name}")
    return item


def giveItem(player: Player, slotitem, amount=1, metadata=None):
    Item = get_system().rpg.backpack.Item
    SlotItem = get_system().rpg.backpack.SlotItem
    if isinstance(slotitem, SlotItem):
        get_system().rpg.backpack_holder.giveItem(player, slotitem)
    elif isinstance(slotitem, Item):
        get_system().rpg.backpack_holder.giveItem(
            player, SlotItem(slotitem, amount, metadata=metadata or {})
        )


def run_plot(player: Player, plot: "RegisteredPlot"):
    sys = get_system()
    sys.running_plot_threads[player] = _run_plot(player, plot)


def get_favor(player: Player, plot_linkname: str):
    return get_system().get_quest_point_data(player, plot_linkname).get("__favor", 0)


def set_favor(player: Player, plot_linkname: str, favor: int):
    old = get_system().get_quest_point_data(player, plot_linkname)
    old["__favor"] = favor
    get_system().set_quest_point_data(player, plot_linkname, old)


# 增加某个剧情点对应的好感度 (例如这个剧情节点对应一个 NPC)
def add_favor(player: Player, plot_linkname: str, favor: int):
    set_favor(player, plot_linkname, get_favor(player, plot_linkname) + favor)


@utils.thread_func("剧情执行")
def _run_plot(player: Player, plot: "RegisteredPlot"):
    sys = get_system()
    _d, _x, _y, _z = player.getPos()
    sys.snowmenu.set_player_page(player, None)
    sys.save_player_last_plot_position(player, (_d, int(_x), int(_y), int(_z)))
    exit_normal = False
    running_plot_final = None
    with utils.ChatbarLock(
        player.name, oth_cb=lambda _: print(f"{player} is using plot") and None
    ):
        sys.running_plots[player] = plot
        try:
            running_plot_final = plot.run(player)
            exit_normal = True
        except sys.PlotExit as err:
            exit_normal = True
            if err.extra:
                running_plot_final = err.extra
        except SystemExit:
            sys.print(f"§6{player.name} 的剧情被中断")
        if exit_normal:
            sys.add_plot_record(player, (running_plot_final or plot).tagname)
            sys.save_player_last_plot_position(player, None)
        del sys.running_plots[player]
        del sys.running_plot_threads[player]
        if running_plot_final:
            return running_plot_final
        else:
            return running_plot_final

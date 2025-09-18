import time
from pathlib import Path
from typing import TypeVar, TYPE_CHECKING
from tooldelta import cfg, Print

if TYPE_CHECKING:
    from .rpg_entities import Entity, PlayerEntity
    from .. import CustomRPG

SYS: "CustomRPG"


def set_system(sys: "CustomRPG"):
    global SYS
    SYS = sys


_LT = TypeVar("_LT", int, float)
ELEM_TYPE = tuple[int, int, int, int, int, int, int]
"七元素数值组"


def category_join(*args: str):
    return ":".join(args)


def real_any(args: list[_LT]) -> _LT | None:
    for arg in args:
        if arg:
            return arg


def hurt_calc(atks: list[int], defs: list[int]):
    # 按防御值计算受伤
    return [
        int(_atk**2 / (_atk + _def)) if _atk != 0 else 0
        for _atk, _def in zip(atks, defs)
    ]


def list_add(lst1: list[_LT], lst2: list[_LT]) -> list[_LT]:
    return [x + y for x, y in zip(lst1, lst2)]


def list_sub(lst1: list[_LT], lst2: list[_LT]) -> list[_LT]:
    return [x - y for x, y in zip(lst1, lst2)]


def list_multi(lst: list[float | int], mul: list[float | int]) -> list[float]:
    return [x * y for x, y in zip(lst, mul)]


def list_multi_int(lst: list[int], mul: list[int]) -> list[int]:
    return [x * y for x, y in zip(lst, mul)]


def list_multi_to_int(lst: list[int], mul: list[float]) -> list[int]:
    return [int(x * y) for x, y in zip(lst, mul)]


def fill_list_index(lst: list[str], default: list[str]):
    if len(lst) < len(default):
        lst.extend(default[len(lst) :])
    return lst


def make_rome_num(num: int):
    _M, sig = divmod(num, 1000)
    _D, sig = divmod(sig, 500)
    _C, sig = divmod(sig, 100)
    _L, sig = divmod(sig, 50)
    _X, sig = divmod(sig, 10)
    ll = "", "I", "II", "III", "IV", "V", "VI", "VI", "VIII", "IX"
    return "M" * _M + "D" * _D + "C" * _C + "L" * _L + "X" * _X + ll[sig]
    # 125 12 1
    # # █ ▉▊▋ࡇ


def make_hp_bar(curr_hp: int, max_hp: int, last_hp: int) -> str:
    pc = curr_hp / max_hp
    if pc < 0.2:
        hp_color = "§c"
    elif pc < 0.4:
        hp_color = "§e"
    else:
        hp_color = "§b"
    return render_bar_old(
        curr_hp / max_hp, last_hp / max_hp, hp_color, "§6", "§a", "§8"
    )


def make_number_color(num: float):
    if num > 0:
        return f"§a+{num}"
    elif num < 0:
        return f"§c{num}"
    else:
        return "0"


def int_time():
    return int(time.time())


def make_subscript_number(num: int):
    if num == 0:
        return ""
    chars = "₀₁₂₃₄₅₆₇₈₉"
    output = ""
    while num >= 10:
        tenth, num = divmod(num, 10)
        output += chars[tenth]
    return output + chars[num]


def make_effect_icons(who: "Entity"):
    return " ".join(
        [i.icon + "§r§f" + make_subscript_number(i.level) for i in who.effects]
    )


def makeUUID():
    return hex(int(time.time() * 100)).strip("0x")


def props_to_list(prop_dic):
    "only to 7"
    l1: list[int] = []
    for i in range(7):
        l1.append(prop_dic.get(f"属性{i + 1}", 0))
    return l1


def make_entity_panel(
    playerinf: "PlayerEntity",
    otherinf: "Entity | None",
    player_crit=False,
):
    if playerinf is otherinf:
        raise ValueError("playerinf and otherinf can't be the same")
    playerhp_last, is_new = SYS.entity_holder.get_last_hp(playerinf)
    playerhp_change = playerinf.hp - playerhp_last
    if playerhp_change != 0:  # or not is_new:
        chgtext1 = f"{['§a+', '§c'][playerhp_change < 0]}{playerhp_change}"
    else:
        chgtext1 = ""
    if otherinf:
        otherhp_last, is_new = SYS.entity_holder.get_last_hp(otherinf)
        otherhp_change = otherinf.hp - otherhp_last
        if otherhp_change != 0:  # or not is_new:
            chgtext2 = f"{['§a+', '§c'][otherhp_change < 0]}{otherhp_change}"
        else:
            chgtext2 = ""
    crit_text = " §c暴击！" if player_crit else ""
    # TODO: 显示武器耐久
    if otherinf:
        # 显示战斗面板
        return (
            f"§e§l{otherinf.name}§r\n"
            "玩家HP "
            + make_hp_bar(playerinf.hp, playerinf.tmp_hp_max, playerhp_last)
            + f"§r§f - {playerinf.hp}§7/{playerinf.tmp_hp_max} {chgtext1}{crit_text}\n§l"
            + make_effect_icons(playerinf)
            + "\n"
            "§r§f对方HP "
            + make_hp_bar(otherinf.hp, otherinf.tmp_hp_max, otherhp_last)
            + f"§r§f - {otherinf.hp}§7/{otherinf.tmp_hp_max} {chgtext2}\n§l"
            + make_effect_icons(otherinf)
        )
    else:
        # 显示平常面板
        return (
            f"§e§l{playerinf.name}§r\n"
            "玩家HP "
            + make_hp_bar(playerinf.hp, playerinf.tmp_hp_max, playerhp_last)
            + f"§r§f - {playerinf.hp}§7/{playerinf.tmp_hp_max} {chgtext1}{crit_text}\n§l"
            + make_effect_icons(playerinf)
        )


def get_cfg(fn: str, path: str | Path, std):
    try:
        return cfg.get_cfg(str(path), std)
    except cfg.ConfigError as err:
        Print.print_err(f"配置文件 {fn} 不正确: {err}")
        raise SystemExit


@staticmethod
def get_str_display_len(string: str):
    length = 0
    for i in string:
        c = ord(i)
        if i == "§":
            length -= 1
        elif i.isascii():
            length += 1
        else:
            if c in range(19968, 40960):
                length += 2
            else:
                length += 1
    return length


@staticmethod
def cut_str_by_len(string: str, length: int):
    outputs: list[str] = []
    cache_len = 0
    cache_str = ""
    for i in string:
        c = ord(i)
        if i == "§":
            cache_len -= 1
        elif i.isascii():
            cache_len += 1
        else:
            if c in range(19968, 40960):
                cache_len += 2
            else:
                cache_len += 1
        if cache_len >= length:
            outputs.append(cache_str)
            cache_str = ""
            cache_len = 0
        else:
            cache_str += i
    if cache_str.strip():
        outputs.append(cache_str)
    return outputs


def align_left(left_str: str, string: str, length: int) -> str:
    return left_str + " " * (length - get_str_display_len(left_str)) + string


def get_last_color(string: str):
    i = string.rfind("§")
    if i == -1:
        return ""
    elif i + 1 >= len(string):
        return "§"
    else:
        return string[i : i + 2]


def split_by_display_len(string: str, length: int):
    res: list[str] = []
    now_len = 0
    cached_str = ""
    for c in string:
        if c == "§":
            now_len -= 1
        elif c.isascii():
            now_len += 1
        else:
            if ord(c) in range(19968, 40960):
                now_len += 2
            else:
                now_len += 1
        cached_str += c
        if now_len >= length:
            res.append(cached_str)
            cached_str = ""
            now_len = 0
    if cached_str.strip():
        res.append(cached_str)
    return res


# █ ▉▊▋ࡇ

# ࡇ▉

# █▉▊▋▌▍ࡇ


def render_bar_old(
    progress1: float,
    progress2: float,
    left_color: str,
    mid_color1: str,
    mid_color2: str,
    right_color: str,
):
    BAR_LEN = 60
    if progress1 > progress2:
        use_color_mid = mid_color2
    else:
        use_color_mid = mid_color1
    progress1, progress2 = min(progress1, progress2), max(progress1, progress2)
    prgs1 = int(BAR_LEN * progress1)
    prgs2 = int(BAR_LEN * progress2) - prgs1
    prgs_rest = BAR_LEN - prgs1 - prgs2
    return (
        left_color
        + "|" * prgs1
        + use_color_mid
        + "|" * prgs2
        + right_color
        + "|" * prgs_rest
    )


def render_bar(
    current: float, total: float, left_color: str, right_color: str, length: int = 90
):
    render_blocks = ["", "▍", "▌", "▋", "▊", "▉"]  # "▍", "▌", "▋", "▊", "▉"
    biggest_block_len_max = length // 6
    biggest_block_eq = len(render_blocks) - 1
    progress1 = current / total
    prgs = int(biggest_block_len_max * biggest_block_eq * progress1)
    prgs_rest = biggest_block_len_max * biggest_block_eq - prgs
    square_count, render_block_index = divmod(prgs, biggest_block_eq)
    square_rest_count, render_block_rest_index = divmod(prgs_rest, biggest_block_eq)
    output_1 = "ࡇ" * square_count + render_blocks[render_block_index]
    output_rest = "ࡇ" * square_rest_count + render_blocks[render_block_rest_index]
    final_output = left_color + output_1 + right_color + output_rest
    return final_output


def render_bar_multiple(
    progress1: float,
    progress2: float,
    left_color: str,
    mid_color1: str,
    mid_color2: str,
    right_color: str,
):
    render_blocks = ["", "▍", "▌", "▋", "▊", "▉"]  # "▍", "▌", "▋", "▊", "▉"
    biggest_block_len_max = 20
    biggest_block_eq = len(render_blocks) - 1
    if progress1 > progress2:
        use_color_mid = mid_color2
    else:
        use_color_mid = mid_color1
    progress1, progress2 = min(progress1, progress2), max(progress1, progress2)
    # progress1 < progress2
    prgs1 = int(biggest_block_len_max * biggest_block_eq * progress1)
    prgs2 = int(biggest_block_len_max * biggest_block_eq * progress2) - prgs1
    prgs_rest = biggest_block_len_max * biggest_block_eq - prgs1 - prgs2
    square_1_count, render_block_1_index = divmod(prgs1, biggest_block_eq)
    square_2_count, render_block_2_index = divmod(prgs2, biggest_block_eq)
    square_rest_count, render_block_rest_index = divmod(prgs_rest, biggest_block_eq)
    output_1 = "ࡇ" * square_1_count + render_blocks[render_block_1_index]
    output_2 = "ࡇ" * square_2_count + render_blocks[render_block_2_index]
    output_rest = "ࡇ" * square_rest_count + render_blocks[render_block_rest_index]
    final_output = (
        left_color + output_1 + use_color_mid + output_2 + right_color + output_rest
    )
    if output_1 == "":
        final_output += "▍"
    if output_2 == "":
        final_output += "▍"
    if output_rest == "":
        final_output += "▍"
    return final_output

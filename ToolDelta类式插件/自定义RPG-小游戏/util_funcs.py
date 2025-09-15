from pathlib import Path
from tooldelta import Player


def select_levels(player: Player, level_path: Path):
    loaded_levels = [
        i.name.removesuffix(".json")
        for i in level_path.iterdir()
        if i.name.endswith(".json")
    ]
    player.show("已存在关卡如下：")
    for i, level_name in enumerate(loaded_levels):
        player.show(f" {i}. {level_name}")
    while True:
        resp = player.input("请选择多个关卡（输入序号以+隔开）：")
        if resp is None:
            return None
        try:
            sections = list(map(int, resp.split("+")))
        except Exception:
            player.show("§c输入错误， 请重新输入")
            continue
        try:
            levels = [loaded_levels[i] for i in sections]
        except IndexError:
            player.show("§c输入错误， 请重新输入")
            continue
        break
    player.show(f"已选择关卡： {', '.join(levels)}")
    return levels


def cut_string(string: str, length: int):
    outputs: list[str] = []
    strlen = 0
    cached_str = ""
    for char in string:
        o = ord(char)
        if o >= 0x4E00 and o <= 0x9FFF:
            strlen += 2
        elif char == "§":
            strlen -= 1
        else:
            strlen += 1
        cached_str += char
        if strlen > length:
            outputs.append(cached_str)
            cached_str = ""
            strlen = 0
    if cached_str.strip():
        outputs.append(cached_str)
    return outputs

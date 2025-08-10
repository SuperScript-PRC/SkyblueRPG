import random
import time
from tooldelta import Plugin, utils, plugin_entry


def unpack(ab: list[tuple[int, int]]) -> tuple[list[int], list[int]]:
    res1 = []
    res2 = []
    for i, j in ab:
        res1.append(i)
        res2.append(j)
    return res1, res2


class CustomRPGMiner(Plugin):
    name = "自定义RPG-矿区"
    author = "SuperScript"
    version = (0, 0, 1)

    def __init__(self, frame):
        super().__init__(frame)

    def spawn_mine(
        self,
        pos: tuple[int, int, int],
        size: tuple[int, int, int],
        mine_rand: float,
        texture: str,
        mines_and_weights: list[tuple[int, int]],
    ):
        x, y, z = pos
        dx, dy, dz = size
        mines, wts = unpack(mines_and_weights)
        for y1 in range(y, y + dy + 1):
            self.game_ctrl.sendwocmd(
                f"fill {x} {y1} {z} {x + dx} {y1} {z + dz} {texture}"
            )
            for x1 in range(x, x + dx + 1):
                for z1 in range(z, z + dz + 1):
                    if random.random() <= mine_rand:
                        mine_id = random.choices(mines, wts, k=1)[0]
                        self.game_ctrl.sendwocmd(f"setblock {x1} {y1} {z1} {mine_id}")


# 0000000 000000
# LLLLLL000LLLLL
# LLLLLM000LLMLL
# LLLLLLLLLLMLLL
entry = plugin_entry(CustomRPGMiner)

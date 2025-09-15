import time
import random
from tooldelta import Player


class SightCtrl:
    def __init__(self, player: Player, center_pos: tuple[int, int, int]):
        self.player = player
        self.center_pos = center_pos
        self.dont_clears = False

    def __enter__(self):
        from . import entry

        x, y, z = self.center_pos
        entry.game_ctrl.sendwocmd(
            f"inputpermission set {self.player.safe_name} movement disabled"
        )
        entry.game_ctrl.sendwocmd(
            f"execute as {self.player.safe_name} at @s run tp ~~~ facing {x} {y} {z}"
        )
        entry.game_ctrl.sendwocmd(
            f"execute as {self.player.safe_name} at @s run camera @s set minecraft:free ease 0.5 linear pos ^^1.5^-3 facing {x} {y} {z}"
        )
        return self

    def dont_clear(self):
        self.dont_clears = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        from . import entry

        x, y, z = self.center_pos
        entry.game_ctrl.sendwocmd(
            f"inputpermission set {self.player.safe_name} movement enabled"
        )
        if not self.dont_clears:
            entry.game_ctrl.sendwocmd(
                f"execute as {self.player.safe_name} at @s run tp ~~~ facing {x} {y} {z}"
            )
            entry.game_ctrl.sendwocmd(
                f"execute as {self.player.safe_name} at @s run camera @s set minecraft:free ease 0.5 linear pos ~~1.7~ facing {x} {y} {z}"
            )
            time.sleep(0.5)
            entry.game_ctrl.sendwocmd(f"camera {self.player.safe_name} clear")


def merge(dict1: dict[str, int], dict2: dict[str, int]):
    for key, value in dict2.items():
        if key in dict1:
            dict1[key] += value
        else:
            dict1[key] = value


class RandChoice:
    def __init__(self, item_id: str, amount: int, rand: float):
        self.item_id = item_id
        self.amount = amount
        self.rand = rand

    def pick(self):
        if random.random() < self.rand:
            return {self.item_id: self.amount}
        else:
            return {}


class RandChoices:
    def __init__(
        self,
        item_ids: list[str],
        k: int,
        amount: int | None = None,
        amount_2: int | None = None,
    ):
        self.item_ids = item_ids
        self.k = k
        self.amount = amount or k
        self.amount_2 = amount_2
        if len(item_ids) < k:
            raise ValueError("k > len(item_ids)")
        elif k > self.amount:
            raise ValueError("k > amount")
        elif self.amount_2 is not None and self.amount_2 <= self.amount:
            raise ValueError("amount_2 <= amount")

    def picks(self):
        if len(self.item_ids) == self.k:
            can_pick_items = self.item_ids.copy()
        else:
            p = self.item_ids.copy()
            can_pick_items: list[str] = []
            for _ in range(self.k):
                item_id = random.choice(p)
                can_pick_items.append(item_id)
                p.remove(item_id)
        final_result: dict[str, int] = dict.fromkeys(can_pick_items, 1)
        pick_amount = (
            random.randint(self.amount, self.amount_2)
            if self.amount_2 is not None
            else self.amount
        )
        for item_id in random.choices(can_pick_items, k=pick_amount - self.k):
            final_result[item_id] += 1
        return final_result


def render_bar(curr: float, prog: float, length: int):
    progress = round(curr / prog * length)
    return "§d" + "|" * progress + "§8" + "|" * (length - progress)

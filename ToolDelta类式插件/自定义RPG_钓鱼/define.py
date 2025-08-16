from dataclasses import dataclass


def _cmp(x, y):
    return (x, y) if x < y else (y, x)


class Cube:
    def __init__(
        self, sx: float, sy: float, sz: float, ex: float, ey: float, ez: float
    ):
        self.sx, self.ex = _cmp(sx, ex)
        self.sy, self.ey = _cmp(sy, ey)
        self.sz, self.ez = _cmp(sz, ez)

    def __contains__(self, inc: tuple[float, float, float]):
        x, y, z = inc
        return (
            self.sx <= x <= self.ex
            and self.sy <= y <= self.ey
            and self.sz <= z <= self.ez
        )


@dataclass
class FishingArea:
    hook: float
    time_range: tuple[int, int]
    area: Cube
    fish_and_weight: dict[str, float]
    treasure_and_weight: dict[str, float]


@dataclass
class Bait:
    name: str
    not_empty: float = 0.5
    speed_up: float = 0
    treasure: float = 0.1
    fish: float = 0.1
    reduce: float = 0.9

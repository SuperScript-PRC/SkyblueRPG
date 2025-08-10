anti_areas: list["AntiArea"] = []


def cmp(a1, a2):
    return (a1, a2) if a1 < a2 else (a2, a1)


class AntiArea:
    def __init__(
        self,
        startx: int,
        startz: int,
        endx: int,
        endz: int,
        allowlist: list[str],
    ):
        self.startx, self.endx = cmp(startx, endx)
        self.startz, self.endz = cmp(startz, endz)
        self.allowlist = allowlist

    def can_cut(self, x: int, y: int, z: int, blockid_simp: str):
        return (
            self.in_area(x, y, z)
            and blockid_simp.removeprefix("minecraft:") in self.allowlist
        )

    def in_area(self, x: int, y: int, z: int):
        return x in range(self.startx, self.endx) and z in range(self.startz, self.endz)


anti_areas.append(AntiArea(131, -154, 226, -95, ["oak_log"]))
anti_areas.append(AntiArea(948, -2576, 1241, -2442, ["oak_log"]))

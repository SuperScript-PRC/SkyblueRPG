from .define import AreaType
from .sources import areas, uniqueID2areas


class Area:
    def __init__(
        self,
        type: AreaType,
        pos: tuple[int, int, int],
        safe_pos: tuple[int, int, int],
        extra_id: int = 0,
    ):
        self.type = type
        self.pos = pos
        self.safe_pos = safe_pos
        self.extra_id = extra_id
        self._locked = False

    def lock(self):
        self._locked = True

    def locked(self):
        return self._locked

    def release(self):
        self._locked = False

    @property
    def unique_id(self):
        x, y, z = self.pos
        return f"{x}:{y}:{z}"

    @property
    def npc_1_pos(self):
        x, y, z = self.pos
        return x + 14, y - 2, z + 3

    @property
    def npc_2_pos(self):
        x, y, z = self.pos
        return x + 14, y - 2, z + 6

    @property
    def npc_3_pos(self):
        x, y, z = self.pos
        return x + 14, y - 2, z + 10


def allocate_area(type: AreaType, specific_id: int = -1):
    """
    Raises:
        ValueError: 可请求区域不足
    """
    typed_areas = areas[type]
    if specific_id == -1:
        _areas: list[Area] = []
        for vs in typed_areas.values():
            _areas += vs
    else:
        _areas = typed_areas[specific_id]
    for area in _areas:
        if not area.locked():
            return area
    raise ValueError(f"Failed to allocate area for {type.name}")


def all_areas_empty_one():
    return all(
        all(any(not k.locked() for k in j) for j in i.values()) for i in areas.values()
    )


LOCK_DATA = list[str]


def dump_locks() -> LOCK_DATA:
    return [k for k, v in uniqueID2areas.items() if v.locked()]


def load_locks(datas: LOCK_DATA):
    for data in datas:
        if data in uniqueID2areas:
            uniqueID2areas[data].lock()

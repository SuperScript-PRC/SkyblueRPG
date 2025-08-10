from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .frame_objects import Weapon

# 附魔
class Enchant:
    name: str = ""
    max_level: int = 1

    def __init__(self, on_weapon: "Weapon", level: int):
        self.on_weapon = on_weapon
        self.level = level

    def on_use(self, **kwargs):
        pass

registered_enchants: dict[str, type[Enchant]] = {}

def register_enchant_module(module):
    registered_enchants.update(
        {
            i: j
            for i, j in module.__dict__.items()
            if isinstance(j, type) and issubclass(j, Enchant)
        }
    )

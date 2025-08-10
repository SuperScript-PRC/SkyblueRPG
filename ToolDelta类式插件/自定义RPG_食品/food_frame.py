from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from 自定义RPG.rpg_lib.rpg_entities import PlayerProperties
    from . import CustomRPGFood

SYSTEM: "CustomRPGFood | None" = None


def set_system(sys: "CustomRPGFood"):
    global SYSTEM
    SYSTEM = sys


def get_system():
    assert SYSTEM
    return SYSTEM


def effect_cls(clsname: str):
    return get_system().rpg.find_effect_class(clsname)


class RPGFood:
    tag_name: str = "???"
    show_name: str = "<食品???>"
    description: str = "<简介???>"
    stackable: bool = True
    model_id: str = "apple"
    model_data: int = 0
    cure_hp: int = 0
    cure_hp_percent: float = 0

    def __init__(self, user: "PlayerProperties"):
        self.user = user
        self.sys = get_system()


    def eat(self) -> bool:
        "食用此食品, 返回是否消耗该食品。"
        self.user._update()
        hp_added = int(self.user.tmp_hp_max * self.cure_hp_percent + self.cure_hp)
        self.user.cured(self.user, self.sys.rpg.constants.SrcType.FROM_SKILL, hp_added)
        return True

    def add_effect(
        self, effect_name: str, seconds: int = 30, level: int = 0, visible=False
    ):
        get_system().game_ctrl.sendwocmd(
            f'effect @a[name="{self.user}"] {effect_name} {seconds} {level} {"false" if visible else "true"}'
        )

    def add_rpg_effect(self, effect_name: str, seconds: int, level: int):
        self.user.add_effect(effect_cls(effect_name), self.user, seconds, level)

    def revert_effect(self, effect_name: str):
        get_system().game_ctrl.sendwocmd(
            f'effect @a[name="{self.user}"] {effect_name} 0 0'
        )


registered_foods: dict[str, type[RPGFood]] = {}
registered_foods_tagname: dict[str, type[RPGFood]] = {}


def get_food_cls_by_clsname(clsname: str) -> type[RPGFood]:
    if food := registered_foods.get(clsname):
        return food
    else:
        raise ValueError(f"没有这种食物类: {clsname}")


def get_food_cls_by_tagname(food_name: str) -> type[RPGFood]:
    if food := registered_foods_tagname.get(food_name):
        return food
    else:
        raise ValueError(f"没有这种食物类: {food_name}")


def register_food_module(sys: "CustomRPGFood", module):
    for k, v in module.__dict__.items():
        # if isinstance(v, type) and not issubclass(v, RPGFood):
        #     print(v)
        #     if k == "CookedChicken":
        #         print(v, issubclass(v, RPGFood), RPGFood, v.__base__, v.__base__ == RPGFood, dir(RPGFood), dir(v.__base__))
        #         raise ValueError
        if isinstance(v, type) and issubclass(v, RPGFood) and v != RPGFood:
            registered_foods[k] = v
            registered_foods_tagname[v.tag_name] = v
            sys.backpack.regist_item(
                sys.backpack.Item(
                    v.tag_name, v.show_name, ["食品"], v.stackable, v.description
                )
            )
            # print(f"added: {k}")
    # raise ValueError("END of the test")

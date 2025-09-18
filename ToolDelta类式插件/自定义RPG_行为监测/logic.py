from tooldelta import TYPE_CHECKING, utils
from .define import Event

if TYPE_CHECKING:
    from . import CustomRPGActionListener, Entity


class LogicCore:
    def __init__(self, system: "CustomRPGActionListener"):
        self.sys = system

    def get_effect(self, effect_id: str):
        return self.sys.rpg.find_effect_class(effect_id)

    def basic_effect_get(self):
        self.BURNING = self.get_effect("Burning")
        self.WET = self.get_effect("Wet")
        self.CURED = self.get_effect("Cured")

    def basic_event_regist(self):
        self.sys.add_event_listener(Event.INTO_LAVA, self.on_into_lava)
        self.sys.add_event_listener(Event.INTO_WATER, self.on_into_water)
        self.sys.add_event_listener(Event.INTO_SNOW, self.on_into_snow)

    def activate(self):
        self.basic_effect_get()
        self.basic_event_regist()
        self.on_time()

    @utils.timer_event(1, "自定义RPG-行为检测:场地buff效果")
    def on_time(self):
        for entity, status in self.sys.statuses.items():
            if status.in_lava:
                self.on_into_lava(entity)
            if status.in_water:
                self.on_into_water(entity)
            if status.in_snow:
                self.on_into_snow(entity)

    def on_into_lava(self, entity: "Entity", first_add=True):
        entity.add_effect(self.BURNING, sec=8)

    def on_into_water(self, entity: "Entity", first_add=True):
        entity.add_effect(self.WET, sec=4)

    def on_into_snow(self, entity: "Entity", first_add=True):
        entity.add_effect(self.CURED, sec=2)

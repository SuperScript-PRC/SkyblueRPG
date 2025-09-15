from collections.abc import Callable
from weakref import WeakKeyDictionary
from sys import getrefcount
from importlib import reload
from tooldelta import Plugin, TYPE_CHECKING, plugin_entry, utils, InternalBroadcast
from . import logic
from .define import Event

reload(logic)


class EntityStatus:
    def __init__(self):
        self.in_water = False
        self.in_fire = False
        self.in_lava = False
        self.in_deep_water = False
        self.in_snow = False


class CustomRPGActionListener(Plugin):
    name = "自定义RPG-行为监测"
    author = "SuperScript"
    version = (0, 0, 1)

    Event = Event

    def __init__(self, frame):
        super().__init__(frame)
        self.logic_core = logic.LogicCore(self)
        self.clear_timeoutfn = None
        self.ListenPreload(self.on_def)
        self.ListenActive(self.on_active)

    def on_def(self):
        self.cb2bot = self.GetPluginAPI("Cb2Bot通信")
        self.rpg = self.GetPluginAPI("自定义RPG")
        if TYPE_CHECKING:
            global ENTITY, MobInitedEvent
            from ..前置_Cb2Bot通信 import TellrawCb2Bot
            from ..自定义RPG import CustomRPG
            from ..自定义RPG.rpg_lib.rpg_entities import ENTITY
            from ..自定义RPG.event_apis import MobInitedEvent

            self.cb2bot: TellrawCb2Bot
            self.rpg: CustomRPG
        for evt in Event:
            get_handler = lambda evt: (lambda args: self.handler(evt, args))  # noqa: E731
            self.cb2bot.regist_message_cb(evt.value, get_handler(evt))
        self.statuses: WeakKeyDictionary["ENTITY", EntityStatus] = WeakKeyDictionary()
        self.statuses_pending: dict[int, EntityStatus] = {}
        self.status_changed_listeners: dict[
            Event, list[Callable[["ENTITY"], None]]
        ] = {}
        self.frame.add_console_cmd_trigger(["rs"], None, self.name, self.check_refs)
        self.ListenInternalBroadcast(
            self.rpg.event_apis.BroadcastType.MOB_INITED, self.on_init_entity
        )

    def on_active(self):
        self.logic_core.activate()

    def check_refs(self, _):
        for k in self.statuses:
            self.print(k.name, k.runtime_id, f"refs={getrefcount(k)}")

    def get_status(self, entity: "ENTITY") -> EntityStatus:
        if entity not in self.statuses:
            self.statuses[entity] = EntityStatus()
        return self.statuses[entity]

    def add_event_listener(self, evt: Event, cb: Callable[["ENTITY"], None]):
        if evt not in self.status_changed_listeners:
            self.status_changed_listeners[evt] = []
        self.status_changed_listeners[evt].append(cb)

    def temp_get_entity(self, runtime_id: int, mob_uuid: str):
        e = self.rpg.entity_holder.get_entity_by_runtimeid(runtime_id)
        if e is None:
            if mob_uuid == "":
                self.print_war(f"runtime_id={runtime_id} 未找到 && mob_uuid 为空 已反初始化")
                self.rpg.mob_holder.uninit_runtime_only_mob(runtime_id)
                return None
            e = self.rpg.mob_holder.load_mobinfo(mob_uuid)
        return e

    def on_init_entity(self, data: InternalBroadcast) -> None:
        dat: "MobInitedEvent" = data.data
        e = dat.mob
        if e.runtime_id in self.statuses_pending:
            self.statuses[e] = self.statuses_pending.pop(e.runtime_id)
            self.print(f"生物状态反挂起: {e.runtime_id}")

    @utils.thread_func("自定义RPG-行为监测:handler")
    def handler(self, evt: Event, args: list[str]):
        runtime_id = int(args[0])
        if len(args) > 1:
            mob_uuid = args[1]
        else:
            mob_uuid = ""
        entity = self.temp_get_entity(runtime_id, mob_uuid)
        if entity is None:
            self.print_war(f"RuntimeID 对应实体无效: {runtime_id}")
            if runtime_id not in self.statuses_pending:
                status = self.statuses_pending[runtime_id] = EntityStatus()
            else:
                status = self.statuses_pending[runtime_id]
            self.print(f"挂起生物状态: {runtime_id}: {evt.name}")
            self.ready_clear_pending()
        else:
            if entity not in self.statuses:
                status = self.statuses[entity] = EntityStatus()
            else:
                status = self.statuses[entity]
        # self.print(evt.name, entity.name)
        match evt:
            case Event.INTO_WATER:
                status.in_water = True
            case Event.OUT_WATER:
                status.in_water = False
            case Event.INTO_FIRE:
                status.in_fire = True
            case Event.OUT_FIRE:
                status.in_fire = False
            case Event.INTO_LAVA:
                status.in_lava = True
            case Event.OUT_LAVA:
                status.in_lava = False
            case Event.INTO_DEEPWATER:
                status.in_deep_water = True
            case Event.OUT_DEEPWATER:
                status.in_deep_water = False
            case Event.INTO_SNOW:
                status.in_snow = True
            case Event.OUT_SNOW:
                status.in_snow = False
            case _:
                pass
        if entity:
            for cb in self.status_changed_listeners.get(evt, []):
                cb(entity)

    @utils.timeout_func(5, "自定义RPG-行为监测:清除挂起的生物状态")
    def clear_pending(self):
        if self.statuses_pending:
            self.print_war(
                f"存在挂起的 RuntimeID > 生物状态: {', '.join(str(i) for i in self.statuses_pending.keys())}"
            )
        self.statuses_pending.clear()

    def ready_clear_pending(self):
        if self.clear_timeoutfn is None:
            self.clear_timeoutfn = self.clear_pending()
        elif self.clear_timeoutfn.finished:
            self.clear_timeoutfn = self.clear_pending()
        else:
            self.clear_timeoutfn.add_time(5)


entry = plugin_entry(CustomRPGActionListener, "自定义RPG-行为监测")

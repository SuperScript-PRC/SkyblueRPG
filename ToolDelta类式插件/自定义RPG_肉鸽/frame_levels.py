import time
from collections.abc import Callable
from .define import LevelType, AreaType
from .sources import get_fortune_plot, get_mob_waves_by_level, pick_boss

if 0:
    from . import entry
    from .frame_areas import Area
    from .storage import RogueStatusStorage

    RPGEffect = entry.rpg.frame_effects.RPGEffect


def get_level_classes():
    return {
        i.__name__: i
        for i in globals().values()
        if isinstance(i, type) and issubclass(i, Level)
    }


class Level:
    def __init_subclass__(
        cls,
        name: str,
        type: LevelType,
        area_type: AreaType,
        shake_value: int,
        weight: float,
        *,
        final=False,
    ):
        cls.name = name
        cls.type = type
        cls.area_type = area_type
        cls.shake_value = shake_value
        cls.weight = weight
        cls.final = final

    def __init__(
        self,
        storage: "RogueStatusStorage",
        area: "Area",
        *,
        on_finished: Callable[["Level"], None] | None = None,
    ):
        self.storage = storage
        self.sys = storage.sys
        self.area = area
        self.player = self.sys.rpg.api_holder.get_player_entity(storage.player)
        self.win = False
        self.interrupted = False
        if on_finished is not None:
            self._on_finished_func = on_finished
        else:
            self._on_finished_func = self._default_on_finished

    def activate(self):
        self.area.lock()
        self.sys.executor.link_player_to_level(self.player.player, self)

    def destroy(self):
        self.area.release()

    def dump(self):
        return f"{self.__class__.__name__}::{self.area.unique_id}"

    def on_finished(self):
        self._on_finished_func(self)

    def on_player_exit(self):
        self.win = False
        self.interrupted = True
        self.destroy()
        self.on_finished()

    def set_win(self):
        self.win = True

    def _default_on_finished(self, _):
        if self.win:
            self.storage.executor.rogue.level_finished(self.storage, self)

    @classmethod
    def load(cls, storage: "RogueStatusStorage", dump_data: str):
        from .sources import get_area_by_uqid

        clsname, area_uqid = dump_data.split("::")
        return get_level_classes()[clsname](storage, get_area_by_uqid(area_uqid))


class EntranceLevel(
    Level,
    name="入口",
    type=LevelType.Entrance,
    area_type=AreaType.Entrance,
    shake_value=0,
    weight=0,
):
    def __init__(self, storage, area, *, on_finished=None):
        super().__init__(storage, area, on_finished=on_finished)

    def activate(self):
        super().activate()
        self.set_win()
        self.on_finished()


class PVELevel(
    Level,
    name="战斗",
    type=LevelType.PVE,
    area_type=AreaType.PVE,
    shake_value=10,
    weight=2,
):
    "所有战斗关卡的基类。"

    def __init__(self, storage, area, *, on_finished=None):
        super().__init__(storage, area, on_finished=on_finished)
        self.phase = -1
        self.mob_waves = get_mob_waves_by_level(storage.passed_levels_num)
        self.mob_runtimeids: set[int] = set()
        self.end = False

    def activate(self):
        super().activate()
        self.on_next_wave()

    def destroy(self):
        for rtid in self.mob_runtimeids.copy():
            self.sys.rpg.mob_holder.kill_mob_by_runtimeid(rtid)
        return super().destroy()

    def on_next_wave(self):
        end = self.next_wave()
        if end:
            self.set_win()
            self.player.player.setTitle("§a战斗结束")
            self.on_finished()
            return
        mob_wave = self.mob_waves[self.phase]
        for mob_id, amount in mob_wave.mob_and_amount:
            for _ in range(amount):
                rtid = self.sys.rpg_mob.summon(mob_id, *self.area.safe_pos)
                self.mob_runtimeids.add(rtid)
                self.sys.executor.link_mob_runtimeid_to_level(rtid, self)

    def on_mob_died(self, mob_runtimeid: int):
        if self.end:
            return
        self.mob_runtimeids.remove(mob_runtimeid)
        if not self.mob_runtimeids:
            self.on_next_wave()

    def on_player_died(self):
        self.player.player.setTitle("§c战斗结束")
        self.on_finished()
        self.end = True

    def next_wave(self):
        self.phase += 1
        return self.phase >= len(self.mob_waves)


class FortuneLevel(
    Level,
    name="机遇",
    type=LevelType.Fortune,
    area_type=AreaType.Fortune,
    shake_value=15,
    weight=1,
):
    def __init__(self, storage, area, *, on_finished=None):
        super().__init__(storage, area, on_finished=on_finished)
        self.event = get_fortune_plot()

    def activate(self):
        super().activate()

        def cb(ok: bool):
            if not ok:
                self.on_player_exit()
            else:
                self.set_win()
                self.on_finished()

        self.sys.rpg_plots.putils.run_plot(self.player.player, self.event.plot, cb)


class RestLevel(
    Level,
    name="休憩",
    type=LevelType.Rest,
    area_type=AreaType.Rest,
    shake_value=10,
    weight=0.5,
):
    def __init__(self, storage, area, *, on_finished=None):
        super().__init__(storage, area, on_finished=on_finished)
        self.health_supplied = False

    def activate(self):
        super().activate()
        self.set_win()
        self.on_finished()

    def supply_health(self):
        if self.health_supplied:
            return
        self.health_supplied = True
        self.player.cured(
            self.player,
            self.player.sys.constants.SrcType.FROM_EFFECT,
            self.player.tmp_hp_max - self.player.hp,
        )
        self.player.player.setTitle("§a", "§a你将生命值补充至回满状态。")


class BossLevel(
    Level,
    name="头头",
    type=LevelType.Boss,
    area_type=AreaType.Boss,
    shake_value=0,
    weight=0.001,
    final=True,
):
    def __init__(self, storage, area, *, on_finished=None):
        super().__init__(storage, area, on_finished=on_finished)
        self.phase = 0
        self.boss_rtid = 0
        self.boss_tagname = pick_boss().tag_name

    def activate(self):
        self.boss_rtid = self.sys.rpg_mob.summon(self.boss_tagname, *self.area.safe_pos)
        self.sys.executor.link_mob_runtimeid_to_level(self.boss_rtid, self)

    def destroy(self):
        self.sys.rpg.mob_holder.kill_mob_by_runtimeid(self.boss_rtid)
        return super().destroy()

    def on_open_chest(self):
        x, y, z = self.area.safe_pos
        self.sys.game_ctrl.sendwocmd(
            f'/setblock {x + 25} {y} {z + 9} wooden_button ["facing_direction"=1]'
        )
        time.sleep(0.5)
        self.sys.game_ctrl.sendwocmd(
            f'/setblock {x + 25} {y} {z + 9} trapped_chest ["minecraft:cardinal_direction"="west"]'
        )

    def on_mob_died(self, mob_runtimeid: int):
        self.win = True
        self.player.player.setTitle("§a战斗结束")
        self.on_finished()

    def on_player_died(self):
        self.player.player.setTitle("§c战斗结束")
        self.on_finished()

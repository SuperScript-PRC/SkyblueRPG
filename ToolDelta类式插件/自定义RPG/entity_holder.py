from typing import TYPE_CHECKING
from weakref import WeakKeyDictionary
from tooldelta import utils, Player
from tooldelta.game_utils import getTarget
from .rpg_lib.rpg_entities import PlayerEntity, MobEntity, Entity
from .rpg_lib.utils import make_entity_panel

if TYPE_CHECKING:
    from . import CustomRPG


class EntityRuntimeIDCounter:
    def __init__(self, n: int):
        self.n = n

    def __next__(self):
        self.n += 1
        return self.n


class EntityHolder:
    def __init__(self, sys: "CustomRPG"):
        self.sys = sys
        # HP 缓存, 用于计算变化差值
        self.cached_hp: WeakKeyDictionary[Entity, int] = WeakKeyDictionary()
        # 盾量缓存, 用于计算变化查值
        self.cached_shield: WeakKeyDictionary[Entity, int] = WeakKeyDictionary()
        # 主要敌人目标
        self.main_target: WeakKeyDictionary[Entity, Entity] = WeakKeyDictionary()
        self.runtimeid_to_entity: dict[int, Entity] = {}
        self.runtime_id_counter = EntityRuntimeIDCounter(0)

    def new_runtimeid(self):
        return next(self.runtime_id_counter)

    def player_in_battle(self, player: Player):
        return self.main_target.get(self.sys.player_holder.get_playerinfo(player))

    def activate(self):
        self.rpg_effect_ticking_activate()

    def load_player(self, player: PlayerEntity):
        self.runtimeid_to_entity[player.runtime_id] = player
        self.update_last_hp(player)

    def load_mob(self, mob: MobEntity):
        self.runtimeid_to_entity[mob.runtime_id] = mob
        self.update_last_hp(mob)

    def unload_player(self, player: Player):
        playerinf = self.sys.player_holder.get_playerinfo(player)
        # # this is weakref dict
        # if playerinf in self.cached_hp:
        #     del self.cached_hp[playerinf]
        # if playerinf in self.cached_shield:
        #     del self.cached_shield[playerinf]
        if playerinf.runtime_id in self.runtimeid_to_entity:
            del self.runtimeid_to_entity[playerinf.runtime_id]
        self.unload_main_target(playerinf)

    def unload_mob(self, mob: MobEntity):
        "清除怪物缓存数据"
        # # this is weakref dict
        # if mob in self.cached_hp:
        #     self.cached_hp[mob]
        # if mob in self.cached_shield:
        #     self.cached_shield[mob]
        if mob.runtime_id in self.runtimeid_to_entity:
            del self.runtimeid_to_entity[mob.runtime_id]
        self.unload_main_target(mob)

    def get_entity_by_runtimeid(self, runtimeid: int):
        return self.runtimeid_to_entity.get(runtimeid)

    # 获取玩家 / 怪物的上一次 HP 值
    def get_last_hp(self, entity: Entity):
        "-> last_hp, is_new"
        old = self.cached_hp.get(entity)
        # if old != entity.hp:
        #     import traceback
        #     self.sys.print_war("\n".join(traceback.format_stack()))
        return old or entity.hp, old is None

    # 获取玩家 / 怪物的 HP 值变化
    def get_hp_changed(self, entity: Entity):
        old = self.cached_hp.get(entity)
        if old is not None:
            return entity.hp - old
        else:
            return 0

    # 更新玩家 / 怪物的上一次 HP 值
    def update_last_hp(self, entity: Entity):
        self.check_exists(entity)
        # old = self.cached_hp.get(entity, entity.hp)
        # import traceback
        # self.sys.print_suc("\n".join(traceback.format_stack()))
        # if old == entity.hp:
        #     print(f"update_last_hp: {entity.name}: Old == new")
        # else:
        #     print(f"update_last_hp: {entity.name}: Old != new")
        self.cached_hp[entity] = entity.hp

    # 获取最后一次的护盾值
    def get_last_shield(self, entity: Entity):
        old = self.cached_shield.get(entity)
        return old or entity.shield

    # 更新最后一次的护盾值
    def update_last_shield(self, entity: Entity):
        self.check_exists(entity)
        if isinstance(entity, PlayerEntity):
            self.cached_shield[entity] = entity.shield
        else:
            self.cached_shield[entity] = entity.shield

    # 设定实体的目标对手
    def set_main_target(self, entity: "Entity", other: "Entity"):
        self.check_exists(entity, other)
        if entity is other:
            raise ValueError("Cannot set main target to self")
        self.main_target[entity] = other
        self.main_target[other] = entity

    # 清除实体的目标对手
    def unload_main_target(self, entity: "Entity"):
        if entity in self.main_target.keys():
            del self.main_target[entity]
        if entity in self.main_target.values():
            for k, v in self.main_target.copy().items():
                if v is entity:
                    del self.main_target[k]

    # 获取实体的战斗目标对手
    def get_main_target(self, entity: "Entity"):
        return self.main_target.get(entity)

    # 在某人附近获取符合选择器条件的所有实体 -> (玩家名列表, 生物 UUID 列表)
    # 适合在 AOE 时作为检测
    def player_get_surrounding_entities(self, fromwho: Player, selector_mid: str):
        """ """
        dim, x, y, z = fromwho.getPos()
        if dim != 0:
            raise ValueError("只能在主世界调用")
        # self.game_ctrl.say_to("@a", "pos get ok")
        player_selector = (
            f"@a[x={x},y={y},z={z},m=!1,rm=0.1"
            + ("," if selector_mid else "")
            + selector_mid
            + "]"
        )
        mob_selector = (
            f"@e[x={x},y={y},z={z},tag=sr.mob"
            + ("," if selector_mid else "")
            + selector_mid
            + "]"
        )
        # self.game_ctrl.say_to("@a", "getting res..")
        _player_res, _mob_res = utils.thread_gather(
            [
                (getTarget, (player_selector,)),
                (
                    self.sys.game_ctrl.sendwscmd_with_resp,
                    (f"scoreboard players test {mob_selector} sr:ms_uuid -2 -1",),
                ),
            ]
        )
        # self.game_ctrl.say_to("@a", "res get ok")
        assert isinstance(_player_res, list)
        assert not isinstance(_mob_res, list)
        player_res = [
            self.sys.player_holder.get_playerinfo(self.sys.getPlayer(i))
            for i in _player_res
        ]
        if any(
            i.Message == "commands.scoreboard.players.score.notFound"
            for i in _mob_res.OutputMessages
        ):
            # 出现了诡异的 sr:mob_uuid 不存在的现象
            # 那我们就需要去反初始化生物
            self.sys.mob_holder.uninit_uuid_lost_mob()
            _mob_res.OutputMessages = [
                i
                for i in _mob_res.OutputMessages
                if i.Message != "commands.scoreboard.players.test.failed"
            ]
        if (
            len(_mob_res.OutputMessages) > 1
            or _mob_res.OutputMessages[0].Message
            == "commands.scoreboard.players.test.failed"
        ):
            __mob_res = utils.thread_gather(
                [
                    (self.sys.mob_holder.load_mobinfo, (i.Parameters[0],))
                    for i in _mob_res.OutputMessages
                ]
            )
            mob_res: list[MobEntity] = list(filter(lambda i: i is not None, __mob_res))  # type: ignore
        else:
            mob_res = []
        return player_res, mob_res

    @utils.timer_event(1, "RPG效果定时执行")
    def rpg_effect_ticking_activate(self):
        # 效果 on_ticking 生效
        # 效果每秒生效一次
        # 对于显示实时面板方面:
        # 先列出所有需要显示实时战斗面板的实体 (这些实体的主要战斗目标为玩家)
        # 然后根据玩家的主要战斗目标是否需要显示实时战斗面板以对玩家进行显示
        can_display_panels: list["Entity"] = []
        for mob in self.sys.mob_holder.mob_data_cache.copy().values():
            can_display_panel = mob.execute_effects_ticking()
            if mob.is_died():
                # Can this make sense?
                continue
            if can_display_panel:
                self.update_last_hp(mob)
                # 如果该生物正在与某玩家战斗
                if (target := self.get_main_target(mob)) and isinstance(
                    target, PlayerEntity
                ):
                    can_display_panels.append(mob)
        for playerinf in self.sys.player_holder._player_entities.copy().values():
            can_display_panel = playerinf.execute_effects_ticking()
            if playerinf.is_died():
                # Can this make sense?
                continue
            if can_display_panel:
                # 如果该玩家正在与某生物战斗
                if target := self.get_main_target(playerinf):
                    playerinf.player.setActionbar(make_entity_panel(playerinf, target))
                    if isinstance(target, PlayerEntity):
                        can_display_panels.append(playerinf)
                else:
                    if not self.sys.player_holder.displayed_effect_last(playerinf):
                        # 可能之前进行的 add_effect() 向玩家展示了状态栏
                        playerinf.player.setActionbar(
                            make_entity_panel(playerinf, None)
                        )
                        self.update_last_hp(playerinf)
        for playerinf in self.sys.player_holder._player_entities.values():
            target = self.get_main_target(playerinf)
            if target in can_display_panels:
                playerinf.player.setActionbar(make_entity_panel(playerinf, target))

    def check_exists(self, *entities: Entity):
        for entity in entities:
            if not entity.exists:
                raise ValueError(
                    f"实体 {entity.name}(runtimeid:{entity.runtime_id}) 不存在"
                )

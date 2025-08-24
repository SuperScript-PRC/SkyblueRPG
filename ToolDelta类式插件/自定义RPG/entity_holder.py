from typing import TYPE_CHECKING

from tooldelta import utils, Player
from tooldelta.game_utils import getPosXYZ, getTarget
from .rpg_lib.rpg_entities import PlayerEntity, MobEntity, ENTITY
from .rpg_lib.utils import make_entity_panel

if TYPE_CHECKING:
    from . import CustomRPG


class EntityHolder:
    def __init__(self, sys: "CustomRPG"):
        self.sys = sys
        # HP 缓存, 用于计算变化差值
        self.cached_hp: dict[str, int] = {}
        # 盾量缓存, 用于计算变化查值
        self.cached_shield: dict[str, int] = {}
        # 主要敌人目标
        self.main_target: dict[str, "ENTITY"] = {}

    def player_in_battle(self, player: Player):
        return self.main_target.get(player.name)

    def activate(self):
        self.rpg_effect_ticking_activate()

    def load_player(self, player: PlayerEntity):
        self.update_last_hp(player)

    def load_mob(self, mob: MobEntity):
        self.update_last_hp(mob)

    def unload_player(self, player: Player):
        playerinf = self.sys.player_holder.get_playerinfo(player)
        if player in self.cached_hp:
            del self.cached_hp[player.name]
        if player in self.cached_shield:
            del self.cached_shield[player.name]
        self.unload_main_target(playerinf)

    def unload_mob(self, mob: MobEntity):
        "清除怪物缓存数据"
        ud = mob.uuid
        if ud in self.cached_hp:
            self.cached_hp[ud]
        if ud in self.cached_shield:
            self.cached_shield[ud]
        self.unload_main_target(mob)

    # 获取玩家 / 怪物的上一次 HP 值
    def get_last_hp(self, entity: ENTITY):
        if isinstance(entity, PlayerEntity):
            old = self.cached_hp.get(entity.name)
            return old or entity.hp
        else:
            old = self.cached_hp.get(entity.uuid)
            return old or entity.hp

    # 获取玩家 / 怪物的 HP 值变化
    def get_hp_changed(self, entity: ENTITY):
        if isinstance(entity, PlayerEntity):
            old = self.cached_hp.get(entity.name)
        else:
            old = self.cached_hp.get(entity.uuid)
        if old is not None:
            return entity.hp - old
        else:
            return 0

    # 更新玩家 / 怪物的上一次 HP 值
    def update_last_hp(self, entity: ENTITY):
        if isinstance(entity, PlayerEntity):
            self.cached_hp[entity.name] = entity.hp
        else:
            self.cached_hp[entity.uuid] = entity.hp

    # 获取最后一次的护盾值
    def get_last_shield(self, entity: ENTITY):
        if isinstance(entity, PlayerEntity):
            old = self.cached_shield.get(entity.name)
            return old or entity.shield
        else:
            old = self.cached_shield.get(entity.uuid)
            return old or entity.shield

    # 更新最后一次的护盾值
    def update_last_shield(self, entity: ENTITY):
        if isinstance(entity, PlayerEntity):
            self.cached_shield[entity.name] = entity.shield
        else:
            self.cached_shield[entity.uuid] = entity.shield

    # 设定实体的目标对手
    def set_main_target(self, entity: "ENTITY", other: "ENTITY"):
        self.main_target[
            entity.name if isinstance(entity, PlayerEntity) else entity.uuid
        ] = other
        self.main_target[
            other.name if isinstance(other, PlayerEntity) else other.uuid
        ] = entity

    # 清除实体的目标对手
    def unload_main_target(self, entity: "ENTITY"):
        k = entity.name if isinstance(entity, PlayerEntity) else entity.uuid
        if k in self.main_target.keys():
            del self.main_target[k]
        if entity in self.main_target.values():
            for k, v in self.main_target.copy().items():
                if v == entity:
                    del self.main_target[k]

    # 获取实体的战斗目标对手
    def get_main_target(self, entity: "ENTITY"):
        return self.main_target.get(
            entity.name if isinstance(entity, PlayerEntity) else entity.uuid
        )

    # 在某人附近获取符合选择器条件的所有实体 -> (玩家名列表, 生物 UUID 列表)
    # 适合在 AOE 时作为检测
    def get_surrounding_entities(self, fromwho: str, selector_mid: str):
        """ """
        x, y, z = getPosXYZ(fromwho)
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
        assert isinstance(_player_res, list) and not isinstance(_mob_res, list)  # noqa: PT018
        player_res = [
            self.sys.player_holder.get_playerinfo(self.sys.getPlayer(i))
            for i in _player_res
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
        can_display_panels: list["ENTITY"] = []
        for mob in self.sys.mob_holder.mob_data_cache.copy().values():
            can_display_panel = mob.execute_effect_ticking()
            if can_display_panel:
                self.update_last_hp(mob)
                # 如果该生物正在与某玩家战斗
                if (target := self.get_main_target(mob)) and isinstance(
                    target, PlayerEntity
                ):
                    can_display_panels.append(mob)
        for playerinf in self.sys.player_holder.player_entities.copy().values():
            can_display_panel = playerinf.execute_effects_ticking()
            if can_display_panel:
                self.update_last_hp(playerinf)
                # 如果该玩家正在与某生物战斗
                if target := self.get_main_target(playerinf):
                    playerinf.player.setActionbar(make_entity_panel(playerinf, target))
                    if isinstance(target, PlayerEntity):
                        can_display_panels.append(playerinf)
                else:
                    playerinf.player.setActionbar(make_entity_panel(playerinf, None))
        for playerinf in self.sys.player_holder.player_entities.values():
            target = self.get_main_target(playerinf)
            if target in can_display_panels:
                playerinf.player.setActionbar(make_entity_panel(playerinf, target))

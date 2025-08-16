from collections.abc import Callable
from typing import TYPE_CHECKING

import time
import random
from tooldelta import fmts, utils
from tooldelta.game_utils import getTarget
from tooldelta.game_utils import getScore
from .rpg_lib.frame_mobs import find_mob_class_by_id, find_mob_class_by_tagname
from .rpg_lib.frame_effects import RPGEffect
from .rpg_lib.rpg_entities import MobEntity, PlayerEntity
from .rpg_lib.utils import int_time

if TYPE_CHECKING:
    from . import CustomRPG


class MobHolder:
    def __init__(self, sys: "CustomRPG"):
        self.sys = sys
        # 实体缓存池
        self.mob_data_cache: dict[str, MobEntity] = {}
        # 实体缓存刷新时间
        self.mob_data_cache_time: dict[str, int] = {}
        self.mob_death_handlers: list[Callable[[PlayerEntity, int, str], None]] = []

    def activate(self):
        self._clear_mob_data_cache()
        self.sys.cb2bot.regist_message_cb(r"sr.mob.spawn", self._handle_mob_spawn)

    def add_mob(self, mob: MobEntity):
        self.mob_data_cache[mob.uuid] = mob
        self.mob_data_cache_time[mob.uuid] = int_time()
        self.sys.entity_holder.load_mob(mob)
        fmts.print_inf(
            f"自定义RPG: 怪物 {mob.cls.tag_name}(ud={mob.uuid}) 生成",
            end="\r",
            need_log=False,
        )

    # 清除怪物缓存数据
    def remove_mob(self, mob: MobEntity):
        ud = mob.uuid
        del self.mob_data_cache[ud]
        del self.mob_data_cache_time[ud]
        self.sys.entity_holder.unload_mob(mob)

    # 通过生物的 uuid 和种类生成其信息
    def make_mobinfo(
        self,
        mob_uuid: str,
        mob_type: int,
        effects: list[RPGEffect] = [],
    ):
        if not isinstance(mob_type, int):
            raise ValueError(mob_type.__class__.__name__)
        ms = find_mob_class_by_id(mob_type)
        if ms is None:
            return None
        m = MobEntity(
            self.sys,
            ms,
            mob_uuid,
            ms.max_hp,
            effects,
            lambda s, k: self._mob_died_handler(k, s),
        )
        return m

    # 通过在线的生物的 UUID 获取怪物信息
    def load_mobinfo(self, mob_uuid: str) -> MobEntity | None:
        mob = self.mob_data_cache.get(mob_uuid)
        if mob is None:
            # 尝试生成一个新的 mob_info
            try:
                mob_type = getScore(
                    "sr:ms_type", "@e[scores={sr:ms_uuid=" + mob_uuid + "},c=1]"
                )
            except ValueError:
                fmts.print_war(f"无法获取 UUID 为 {mob_uuid} 的生物的信息")
                self.sys.game_ctrl.sendwocmd(
                    f"kill @e[scores={{sr:ms_uuid={mob_uuid}}}]"
                )
                return
            mob = self.make_mobinfo(mob_uuid, mob_type)
            if mob is None:
                return None
            # 尝试获取其血量信息
            try:
                mob_hp = getScore(
                    "sr:ms_hp", "@e[scores={sr:ms_uuid=" + mob_uuid + "},c=1]"
                )
            # 如果不行
            except Exception:
                mob_hp = mob.basic_hp_max
            mob.hp = mob_hp
            self.add_mob(mob)
            return mob
        else:
            return mob

    def get_mob_class(self, mob_tagname: str):
        try:
            return find_mob_class_by_tagname(mob_tagname)
        except ValueError:
            return None

    def mob_spawn(self, ms_uuid: str, ms_id: int):
        mob = self.make_mobinfo(ms_uuid, ms_id)
        if mob is None:
            raise ValueError(f"Failed to make mob: {ms_id} not registered")
        self.sys.game_ctrl.sendwocmd(
            "scoreboard players set @e[scores={sr:ms_uuid="
            + ms_uuid
            + "}] sr:ms_type "
            + str(ms_id)
        )
        self.sys.game_ctrl.sendwocmd(
            "replaceitem entity @e[scores={sr:ms_uuid="
            + ms_uuid
            + "}] slot.armor.head 0 leather_helmet 1 1000"
        )
        self.add_mob(mob)

    # 获取所有在世界内的数据化实体的 UUID
    def get_inworld_mobs_uuids(self):
        try:
            res = self.sys.game_ctrl.sendwscmd_with_resp(
                "scoreboard players test @e[tag=sr.mob] sr:ms_uuid 0 0"
            )
            if (
                len(res.OutputMessages) > 1
                or res.OutputMessages[0].Message
                == "commands.scoreboard.players.test.failed"
            ):
                return [i.Parameters[0] for i in res.OutputMessages]
            else:
                return []
        except TimeoutError:
            return None

    # 确认单个怪物是否存在于世界内
    def check_mob_inworld(self, mob: MobEntity):
        try:
            res = getTarget(f"@e[scores={{sr:ms_uuid={mob.uuid}}}]")
        except TimeoutError:
            # 一是真的超时了, 二是有敏感词
            fmts.print_war(f"怪物UUID {mob.uuid} 为敏感词, 予以清除")
            res = []
        if res == []:
            return False
        return True

    # 清除实体缓存
    @utils.timer_event(60, "清除实体的缓存")
    @utils.thread_func("清除实体缓存线程")
    def _clear_mob_data_cache(self):
        inworld_mobs = self.get_inworld_mobs_uuids()
        if inworld_mobs is not None:
            for k, tim in self.mob_data_cache_time.copy().items():
                if k in inworld_mobs:
                    self.mob_data_cache_time[k] = int_time()
                else:
                    self.remove_mob(self.mob_data_cache[k])
        else:
            fmts.print_war("无法获取世界实体, 尝试挨个获取")
            for k, tim in self.mob_data_cache_time.copy().items():
                if time.time() - tim > 60:
                    if self.check_mob_inworld(mob := self.mob_data_cache[k]):
                        self.mob_data_cache_time[k] = int_time()
                    else:
                        self.sys.game_ctrl.sendwocmd(
                            f"kill @e[scores={{sr:ms_uuid={mob.uuid}}}]"
                        )
                        self.remove_mob(self.mob_data_cache[k])

    @utils.thread_func("自定义RPG-怪物生成处理")
    def _handle_mob_spawn(self, dats: list[str]):
        # with RPG_Lock:
        if len(dats) == 0:
            raise ValueError("Fuck 怪物生成")
        if len(dats) == 1:
            self.sys.print("出现 UUID 为空的怪物; 正在处理")
            self.sys.game_ctrl.sendwocmd(
                "scoreboard players add @e[tag=sr.mob] sr:ms_uuid 0"
            )
            time.sleep(0.5)
            self.sys.game_ctrl.sendwocmd(
                r"tag @e[tag=sr.mob,scores={sr:ms_uuid=0,sr:ms_type=1..}] add sr.mob_uninited"
            )
            time.sleep(0.5)
            self.sys.game_ctrl.sendwocmd(
                r"tag @e[tag=sr.mob,scores={sr:ms_uuid=0,sr:ms_type=1..}] remove sr.mob"
            )
            return
        self.mob_spawn(dats[1], int(dats[0]))

    def _mob_died_handler(self, killer: PlayerEntity, mob: MobEntity):
        """
        实体死亡处理方法
        只能用于注册进实体死亡回调
        """
        if mob.is_deleted:
            return
        for func in self.mob_death_handlers:
            func(killer, mob.cls.type_id, mob.uuid)
        expdrag_min, expdrag_max = mob.cls.drop_exp_range
        exp_added = random.choice(range(expdrag_min, expdrag_max))
        self.sys.rpg_upgrade.add_player_exp(killer.player, exp_added)
        self.sys.game_ctrl.sendwscmd(
            f"/execute as @e[scores={{sr:ms_uuid={mob.uuid}}}] at @s run kill"
        )
        for item_id, count, p in mob.cls.loots:
            if p >= random.randint(1, 100) / 100:
                self.sys.backpack_holder.giveItems(
                    killer.player,
                    items := self.sys.item_holder.createItems(item_id, count),
                    False,
                )
                self.sys.display_holder.display_items_added(killer.player, items)
        basic = self.sys.player_holder.get_player_basic(killer.player)
        self.sys.show_any(
            killer.player.name,
            "e",
            f"§7 + §e{exp_added} 经验 §7(§f{basic.Exp}§7/{self.sys.rpg_upgrade.get_levelup_exp(basic)})",
        )
        self.remove_mob(mob)

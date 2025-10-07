import time
import random
import importlib
from enum import IntEnum
from typing import TYPE_CHECKING
from tooldelta import Player, utils
from . import dungeon_utils

importlib.reload(dungeon_utils)
from .dungeon_utils import SightCtrl, RandChoice, RandChoices, merge
from . import event_apis

if TYPE_CHECKING:
    from . import CustomRPGDungeon
    from . import rpg_event_apis

POWER_ITEM = "蔚源"
TIMEOUT_SECONDS = 60
MAX_TIME_SECONDS = 60 * 5


class DungeonFinishType(IntEnum):
    FINISH_WIN = 0
    FINISH_FAIL = 1
    FINISH_PLAYEREXIT = 2
    MAX_TIME_EXCEEDED = 3
    TIMEOUT_EXCEEDED = 4
    FRAME_EXIT = 5

    @property
    def win(self):
        return self.value == DungeonFinishType.FINISH_WIN


class Dungeon:
    def __init__(
        self,
        id: str,
        disp_name: str,
        limited_level: int,
        power_cost: int,
        entrance_pos: tuple[int, int, int],
        center_pos: tuple[int, int, int],
        summoned_mobs: tuple[tuple[str, ...], ...],
        awards: tuple[tuple[str, int] | RandChoice | RandChoices, ...],
        award_exp: int,
        *,
        exit_pos: tuple[int, int, int] | None = None,
        max_challenge_time: int = MAX_TIME_SECONDS,
    ):
        self.id = id
        self.disp_name = disp_name
        self.limited_level = limited_level
        self.power_cost = power_cost
        self.entrance_pos = entrance_pos
        self.center_pos = center_pos
        self.summoned_mobs = summoned_mobs
        self.awards = awards
        self.award_exp = award_exp
        self.in_dungeon_players: list[Player] = []
        self.stage: "DungeonStage | None" = None
        self.max_challenge_time = max_challenge_time
        if exit_pos is None:
            ex, ey, ez = self.entrance_pos
            cx, _, cz = self.center_pos
            dx = (1 if ex - cx > 0 else -1) * (abs(ex - cx) > abs(ez - cz))
            dz = (1 if ez - cz > 0 else -1) * (abs(ez - cz) > abs(ex - cx))
            self.exit_pos = (ex + dx, ey, ez + dz)
        else:
            self.exit_pos = exit_pos

    def player_enter(self, sys: "CustomRPGDungeon", player: Player):
        playerbas = sys.rpg.player_holder.get_player_basic(player)
        mobs = {
            m
            for ts in set(self.summoned_mobs)
            for t in ts
            if (m := sys.rpg.mob_holder.get_mob_class(t))
        }
        awards_fixed, awards_rand = self.get_awards(sys)
        if awards_fixed:
            awards_fixed_disp = "§r§7， ".join(awards_fixed)
        else:
            awards_fixed_disp = "§7无"
        if awards_rand:
            awards_rand_disp = "§r§7， ".join(awards_rand)
        else:
            awards_rand_disp = "§7无"
        can_start = (
            player_power := sys.rpg.backpack_holder.getItemCount(player, POWER_ITEM)
        ) >= self.power_cost

        def _menu_disp(_, page: int):
            if page >= 2:
                return None
            level_str = "§c" if playerbas.Level < self.limited_level else "§a"
            status = (
                "§c正在开启中"
                if not self.empty()
                else "§a可开启"
                if can_start
                else f"§4蔚源不足 §c{player_power}§7/{self.power_cost}"
            )
            line = "~" * 30
            spaces = " " * 6
            extra_spaces = spaces + "    "
            sep = "§r\n" + spaces
            return (
                f"§8✙ {line}| §f异穴挑战§8 |{line} ✙"
                + f"\n      §7[§fLv.{level_str}{self.limited_level}§7] | {self.disp_name} §r§7| {status}"
                + sep
                + "§7[§b◆§7] §b增益效果： 无"
                + sep
                + f"§7[§e◔§7] §e挑战限时： {self.max_challenge_time // 60}分钟 {self.max_challenge_time % 60}秒"
                + sep
                + "§7[§6!§7] §6可能遭遇：§f\n"
                + extra_spaces
                + "§r§f、 ".join(i.show_name for i in mobs)
                + sep
                + "§7[§d?§7] §d回馈预览：§f\n"
                + extra_spaces
                + "§f必定获取： "
                + awards_fixed_disp
                + "\n"
                + extra_spaces
                + "§d额外概率获取： §f"
                + awards_rand_disp
                + sep
                + "§f选择功能：\n"
                + extra_spaces
                + (
                    "§b❖ 进入异穴  §7|  ❖ 离开"
                    if page == 0
                    else "§7❖ 进入异穴  |§b  ❖ 离开"
                )
            )

        sys.game_ctrl.sendwocmd(
            f"execute as {player.safe_name} at @s run playsound block.end_portal.spawn"
        )
        with SightCtrl(player, self.center_pos) as s:
            resp = sys.rpg.snowmenu.simple_select(player, _menu_disp)
            if resp is None or resp == 1:
                return
            s.dont_clear()
        if not self.empty():
            sys.rpg.show_fail(player, "副本正在开启中， 请等待当前玩家退出")
            sys.game_ctrl.sendwocmd(f"camera {player.safe_name} clear")
        elif not can_start:
            sys.rpg.show_fail(player, "开启所需蔚源不足")
            sys.game_ctrl.sendwocmd(f"camera {player.safe_name} clear")
        else:
            self.stage = DungeonStage(sys, self, player)
            sys.game_ctrl.sendwocmd(
                f"camera {player.safe_name} fade time 0.5 0 0.5 color 0 0 0"
            )
            time.sleep(0.5)
            x, y, z = self.center_pos
            tpx = x + random.randint(-3, 3)
            tpz = z + random.randint(-3, 3)
            sys.game_ctrl.sendwocmd(
                f"execute as {player.safe_name} at @s run spawnpoint"
            )
            sys.game_ctrl.sendwocmd(f"tp {player.safe_name} {tpx} {y} {tpz}")
            sys.game_ctrl.sendwocmd(f"camera {player.safe_name} clear")
            player.setActionbar("§o§7<§c!§7> §r§c准备战斗...")
            time.sleep(3)
            player.setActionbar("§o§7<§c!§7> §r§c挑战开始！")
            self.stage.activate()
            sys.BroadcastEvent(
                event_apis.PlayerStartDungeonEvent(player, self).to_broadcast()
            )

    def player_finish(
        self, sys: "CustomRPGDungeon", player: Player, fntype: DungeonFinishType
    ):
        if self.stage is None:
            player.setActionbar("§c挑战异常")
            return
        sys.game_ctrl.sendwocmd(
            f"camera {player.safe_name} fade time 0.5 3 0.5 color 255 255 255"
        )
        cost_time = self.stage.since()
        if fntype.win:
            player.setTitle("§a挑战完成！")
            player_power = sys.rpg.backpack_holder.getItemCount(player, POWER_ITEM)
            if player_power < self.power_cost:
                sys.rpg.show_fail(player, "您的蔚源发生变动， 不足以扣除")
            else:
                sys.rpg.show_succ(player, f"❀ {self.disp_name}")
                sys.rpg.show_succ(player, "异穴挑战成功， 奖励结算：")
                sys.rpg.backpack_holder.clearItem(
                    player, POWER_ITEM, self.power_cost, False
                )
                items: dict[str, int] = {}
                for award in self.awards:
                    if isinstance(award, tuple):
                        item_id, amount = award
                        items[item_id] = items.get(item_id, 0) + amount
                    elif isinstance(award, RandChoice):
                        merge(items, award.pick())
                    else:
                        merge(items, award.picks())
                for item_id, amount in items.items():
                    slotitem = sys.rpg.item_holder.createItem(item_id, amount)
                    sys.rpg.backpack_holder.addPlayerStore(player, slotitem)
                    sys.rpg.show_any(
                        player, "d", f"§7◈ §f{slotitem.disp_name} §7x {amount}"
                    )
                sys.rpg.show_any(player, "b", f"§7+ {self.award_exp} §b经验")
                sys.rpg.rpg_upgrade.add_player_exp(player, self.award_exp)
                sys.rpg.show_any(
                    player,
                    "e",
                    "挑战耗时 " + time.strftime("%M分 %S秒", time.gmtime(cost_time)),
                )
        elif fntype == DungeonFinishType.FINISH_PLAYEREXIT:
            sys.print(f"§6{self.id}: 玩家 {player.name} 中途退出挑战")
        elif fntype == DungeonFinishType.TIMEOUT_EXCEEDED:
            sys.rpg.show_fail(player, "战斗超时， 异穴挑战已退出。")
        elif fntype == DungeonFinishType.MAX_TIME_EXCEEDED:
            sys.rpg.show_fail(player, "已超过挑战时间限制， 异穴挑战已退出。")
        else:
            sys.rpg.show_fail(player, "挑战失败..")
        sys.rpg.player_holder.get_playerinfo(player).add_effect("Immortal", sec=5)
        time.sleep(0.5)
        if fntype.win:
            sys.game_ctrl.sendwocmd(
                f"execute as {player.safe_name} at @s run playsound portal.travel @s ~~~ 1 0.5"
            )
        else:
            sys.game_ctrl.sendwocmd(
                f"execute as {player.safe_name} at @s run playsound random.totem @s ~~~ 0.4 2"
            )
        x, y, z = self.exit_pos
        time.sleep(0.5)
        sys.game_ctrl.sendwocmd(f"tp @a[name={player.safe_name}] {x} {y} {z}")
        self.stage = None
        sys.BroadcastEvent(
            event_apis.PlayerFinishDungeonEvent(
                player, self, fntype, cost_time
            ).to_broadcast()
        )

    def on_player_leave(self, player: Player):
        if self.stage and self.stage.player is player:
            self.stage.on_player_leave()

    def on_event(self, evt):
        if self.stage:
            self.stage.on_event(evt)

    def get_awards(self, sys: "CustomRPGDungeon"):
        awards_fixed: set[str] = set()
        awards_rand: set[str] = set()
        for award in self.awards:
            if isinstance(award, tuple):
                awards_fixed.add(
                    str(sys.rpg.item_holder.getOrigItem(award[0]).disp_name)
                )
            elif isinstance(award, RandChoice):
                awards_rand.add(
                    str(sys.rpg.item_holder.getOrigItem(award.item_id).disp_name)
                )
            else:
                for item_id in award.item_ids:
                    awards_rand.add(
                        str(sys.rpg.item_holder.getOrigItem(item_id).disp_name)
                    )
        return awards_fixed, awards_rand

    def empty(self):
        return self.stage is None

    def ticking(self, ntime: float):
        if self.stage:
            self.stage.ticking(ntime)

    def exit(self):
        if self.stage is not None:
            self.stage.finish(DungeonFinishType.FRAME_EXIT)


# ...


class DungeonStage:
    def __init__(self, sys: "CustomRPGDungeon", dungeon: "Dungeon", player: Player):
        self.sys = sys
        self.d = dungeon
        self.player = player
        self.apis = sys.rpg.event_apis
        self.start_time = time.time()
        self.last_flush_time = time.time()
        self.instage_mob_rtids: set[int] = set()
        self.phase = 1
        self.phase_mobs_amount = 0
        self.final_phase = len(self.d.summoned_mobs)

    def activate(self):
        x, y, z = self.d.center_pos
        self.player.setTitle(f"波次 {self.phase}/{self.final_phase}")
        # TODO: summon 可能报错
        rtids = utils.thread_gather(
            [
                (self.sys.rpg_mobs.summon, (mt, x, y, z))
                for mt in self.d.summoned_mobs[self.phase - 1]
            ]
        )
        self.instage_mob_rtids = set(rtids)
        self.phase_mobs_amount = len(rtids)

    def finish_current_phase(self):
        if self.phase < self.final_phase:
            self.player.setActionbar(
                f"§7[§ai§7] §a{self.phase}/{self.final_phase} 波次已完成"
            )
        else:
            self.player.setActionbar("§7[§a√§7] §a全部挑战波次已完成")
        self.phase += 1
        if self.phase > self.final_phase:
            self.finish(DungeonFinishType.FINISH_WIN)
        else:
            self.activate()

    def finish(self, fntype: DungeonFinishType):
        if not fntype.win:
            for mob_runtimeid in self.instage_mob_rtids:
                mob = self.sys.rpg.mob_holder.get_mob_by_runtimeid(mob_runtimeid)
                if mob:
                    mob.ready_died(mob, self.sys.rpg.constants.AttackData())
                else:
                    self.sys.print_war(
                        f"无法通过 RuntimeID {mob_runtimeid} 找到并清除怪物"
                    )
        if fntype is not DungeonFinishType.FRAME_EXIT:
            self.d.player_finish(self.sys, self.player, fntype)

    def on_player_leave(self):
        self.finish(DungeonFinishType.FINISH_PLAYEREXIT)

    def on_event(
        self,
        evt: "rpg_event_apis.PlayerAttackMobEvent | rpg_event_apis.MobAttackPlayerEvent | rpg_event_apis.MobDiedEvent | rpg_event_apis.PlayerDiedEvent",
    ):
        a = self.apis
        if isinstance(evt, a.PlayerDiedEvent):
            if evt.player.player is not self.player:
                return
        elif isinstance(evt, a.MobDiedEvent):
            if evt.mob.runtime_id not in self.instage_mob_rtids:
                return
        elif (
            evt.player.player is not self.player
            or evt.mob.runtime_id not in self.instage_mob_rtids
        ):
            return
        if isinstance(evt, a.PlayerAttackMobEvent | a.MobAttackPlayerEvent):
            self.last_flush_time = time.time()
        elif isinstance(evt, a.MobDiedEvent):
            evt.cancel_drop()
            self.instage_mob_rtids.remove(evt.mob.runtime_id)
            self.sys.rpg.show_any(
                self.player,
                "6",
                f"§c剩余§e{len(self.instage_mob_rtids)}/{self.phase_mobs_amount}§c个怪物",
            )
            if not self.instage_mob_rtids:
                self.finish_current_phase()
        elif isinstance(evt, a.PlayerDiedEvent):
            self.finish(DungeonFinishType.FINISH_FAIL)

    def ticking(self, ntime: float):
        if ntime - self.start_time > self.d.max_challenge_time:
            self.finish(DungeonFinishType.MAX_TIME_EXCEEDED)
        elif ntime - self.last_flush_time > TIMEOUT_SECONDS:
            self.finish(DungeonFinishType.TIMEOUT_EXCEEDED)

    def since(self):
        return time.time() - self.start_time

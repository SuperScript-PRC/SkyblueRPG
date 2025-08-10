from collections.abc import Callable
from typing import TYPE_CHECKING

from tooldelta import fmts, utils, InternalBroadcast, Player
from .rpg_lib import constants, event_apis
from .rpg_lib.rpg_entities import PlayerEntity, MobEntity, ENTITY

if TYPE_CHECKING:
    from . import CustomRPG


class CombatHandler:
    def __init__(self, sys: "CustomRPG"):
        self.sys = sys
        self.game_ctrl = sys.game_ctrl
        self.display_holder = sys.display_holder
        self.player_holder = sys.player_holder
        self.entity_holder = sys.entity_holder
        self.mob_holder = sys.mob_holder
        self.BroadcastEvent = sys.BroadcastEvent
        self.weapon_use_listener: dict[str, Callable[[PlayerEntity], None]] = {}

    def activate(self):
        cb2bot = self.sys.cb2bot
        cb2bot.regist_message_cb(r"sr.skill.loaded", self._handle_player_set_skill)
        cb2bot.regist_message_cb(r"sr.ult.loaded", self._handle_player_set_ult)
        cb2bot.regist_message_cb(
            r"sr.player.use.weapon", self._handle_player_use_weapon_only
        )
        cb2bot.regist_message_cb(
            r"sr.player.attack.mob", self._handle_player_attack_mob
        )
        cb2bot.regist_message_cb(
            r"sr.mob.attack.player", self._handle_mob_attack_player
        )
        cb2bot.regist_message_cb(
            r"sr.player.attack.player", self._handle_player_attack_player
        )
        cb2bot.regist_message_cb(
            r"sr.player.switch.weapon", self._handle_player_switch_weapon
        )

    # 玩家预设技能
    def player_set_skill(self, playerinf: PlayerEntity):
        if playerinf.weapon is None:
            self.game_ctrl.player_title(playerinf.name, "§c")
            self.game_ctrl.player_subtitle(playerinf.name, "§c\n§c目前无法使用技能")
            return
        weapon = playerinf.weapon
        if not weapon.need_skill_set:
            playerinf.skill_use(None)
        else:
            if playerinf.is_ult_set:
                playerinf.is_ult_set = False
                self.sys.show_warn(playerinf.player, "终结技准备已被技能准备取消")
                self.game_ctrl.sendwocmd(
                    f"/replaceitem entity {playerinf.player.safe_name} slot.hotbar 2 gold_ingot 1 755 "
                    + r'{"item_lock":{"mode":"lock_in_slot"}}'
                )
            self.game_ctrl.player_title(playerinf.name, "§a")
            self.game_ctrl.player_subtitle(
                playerinf.name, "§a\n§a技能已准备, 请攻击以选定目标"
            )
            playerinf.is_skill_set = True
            self.sys.tutor.check_point("自定义RPG:选中技能", playerinf.player)
        self.display_holder.display_charge_to_player(playerinf)

    # 玩家预设终结技
    def player_set_ult(self, playerinf: PlayerEntity):
        if playerinf.weapon is None:
            self.game_ctrl.player_title(playerinf.name, "§c")
            self.game_ctrl.player_subtitle(playerinf.name, "§c\n§c目前无法使用终结技")
            return
        weapon = playerinf.weapon
        if not weapon.need_ult_set:
            playerinf.ult_use(None)
        else:
            if playerinf.is_skill_set:
                playerinf.is_skill_set = False
                self.sys.show_warn(playerinf.player, "技能准备已被终结技准备取消")
                self.game_ctrl.sendwocmd(
                    f"/replaceitem entity {playerinf.player.safe_name} slot.hotbar 1 iron_ingot 1 755 "
                    + r'{"item_lock":{"mode":"lock_in_slot"}}'
                )
            self.game_ctrl.player_title(playerinf.name, "§c")
            self.game_ctrl.player_subtitle(
                playerinf.name, "§d\n§d终结技已准备, 请攻击以选定目标"
            )
            playerinf.is_ult_set = True
            self.sys.tutor.check_point("自定义RPG:选中终结技", playerinf.player)
        # self.show_charge_to_player(playerinf)

    # 玩家使用技能
    def player_use_skill(self, playerinf: PlayerEntity, target: ENTITY | None):
        if not (item_hot := playerinf.weapon):
            self.sys.show_fail(playerinf.player, "目前无法使用技能")
            return
        if cd_time := self.sys.item_holder.get_weapon_skill_cd(item_hot):
            self.sys.show_fail(playerinf.player, f"技能正在冷却 ({cd_time}s)")
        else:
            playerinf.skill_use(target)
            self.sys.tutor.check_point("自定义RPG:使用技能", playerinf.player)
        self.display_holder.display_charge_to_player(playerinf)
        self.entity_holder.update_last_hp(playerinf)
        if target is not None:
            self.entity_holder.update_last_hp(target)
            self.ensure_kill_handler(playerinf, target)

    # 玩家使用终结技
    def player_use_ult(self, playerinf: PlayerEntity, target: ENTITY | None):
        if not (item_hot := playerinf.weapon):
            self.sys.show_fail(playerinf.player, "目前无法使用终结技")
            return
        if item_hot.chg == item_hot.charge_ult:
            playerinf.ult_use(target)
            self.sys.tutor.check_point("自定义RPG:使用终结技", playerinf.player)
        else:
            self.sys.show_fail(playerinf.player, "充能不足")
        self.display_holder.display_charge_to_player(playerinf)
        self.entity_holder.update_last_hp(playerinf)
        if target is not None:
            self.entity_holder.update_last_hp(target)
            self.ensure_kill_handler(playerinf, target)

        # 玩家攻击实体

    def player_attack_mob(self, playerinf: PlayerEntity, mob: MobEntity):
        playerinf.attack(mob)
        self.ensure_kill_handler(playerinf, mob)
        playerinf.player.setTitle("§a")
        self.display_holder.display_charge_to_player(playerinf)
        self.entity_holder.update_last_hp(playerinf)
        self.entity_holder.update_last_hp(mob)

    # 实体攻击玩家
    def mob_attack_player(self, player: Player, mob_uuid: str):
        mob = self.mob_holder.load_mobinfo(mob_uuid)
        if mob is None:
            fmts.print_war(
                f"SkyblueRPG: 实体 [{mob_uuid}] 所属实体类型未知, 无法初始化"
            )
            return
        playerinf = self.player_holder.get_playerinfo(player)
        self.entity_holder.set_main_target(playerinf, mob)
        mob.attack(playerinf, constants.SrcType.NORMAL, constants.AttackType.NORMAL)
        self.entity_holder.update_last_hp(playerinf)
        self.entity_holder.update_last_hp(mob)
        self.ensure_kill_handler(mob, playerinf)

    # 玩家攻击玩家
    def player_attack_player(self, playerinf: PlayerEntity, playerinf_2: PlayerEntity):
        playerinf.attack(playerinf_2)
        self.entity_holder.update_last_hp(playerinf)
        self.entity_holder.update_last_hp(playerinf_2)
        self.ensure_kill_handler(playerinf, playerinf_2)
        self.ensure_kill_handler(playerinf_2, playerinf)

    # 在每个有可能造成目标死亡的事件下调用
    def ensure_kill_handler(self, killer: "ENTITY", killed: "ENTITY"):
        if isinstance(killer, PlayerEntity):
            if killed.is_died():
                if isinstance(killed, MobEntity):
                    self.sys.tutor.check_point(
                        "自定义RPG:击杀生物", killer.player, killed
                    )
                    evt = event_apis.PlayerKillMobEvent(killer, killed)
                    self.BroadcastEvent(InternalBroadcast(evt.type, evt))
                elif isinstance(killed, PlayerEntity):
                    self.sys.tutor.check_point(
                        "自定义RPG:击杀玩家", killer.player, killed
                    )
                    evt = event_apis.PlayerKillPlayerEvent(killer, killed)
                    self.BroadcastEvent(InternalBroadcast(evt.type, evt))
                    killed.recover()
        elif isinstance(killer, MobEntity):
            if killed.is_died():
                if isinstance(killed, PlayerEntity):
                    evt = event_apis.MobKillPlayerEvent(killed, killer)
                    self.BroadcastEvent(InternalBroadcast(evt.type, evt))
                    killed.recover()

    # 处理玩家设置技能
    def _handle_player_set_skill(self, dats: list[str]):
        target = self.player_holder.get_playerinfo(self.sys.getPlayer(dats[0]))
        self.player_set_skill(target)
        self.game_ctrl.sendwocmd(
            f"scoreboard players set @a[name={target.name}] sr:skillmode 0"
        )
        self.game_ctrl.sendwocmd(
            "replaceitem entity @a[name="
            + target.name
            + r'] slot.hotbar 1 netherite_ingot 1 754 {"item_lock":{"mode":"lock_in_slot"}}'
        )

    # 处理玩家切换武器
    def _handle_player_switch_weapon(self, dats: list[str]):
        self.sys.menu_gui._player_switch_weapon(self.sys.getPlayer(dats[0]))

    # 处理玩家设置终结技
    def _handle_player_set_ult(self, dats: list[str]):
        target = self.player_holder.get_playerinfo(self.sys.getPlayer(dats[0]))
        self.player_set_ult(target)
        self.game_ctrl.sendwocmd(
            f"scoreboard players set @a[name={target.name}] sr:skillmode 0"
        )
        self.game_ctrl.sendwocmd(
            "replaceitem entity @a[name="
            + target.name
            + r'] slot.hotbar 2 netherite_ingot 1 754 {"item_lock":{"mode":"lock_in_slot"}}'
        )

    @utils.thread_func("自定义RPG-玩家攻击生物")
    def _handle_player_attack_mob(self, dats: list[str]):
        if len(dats) != 2:
            if len(dats) == 1:
                # 没在使用武器打怪
                playerinf = self.player_holder.get_playerinfo(
                    self.sys.getPlayer(dats[0])
                )
                if (
                    playerinf.weapon
                    and (tagname := playerinf.weapon.tag_name)
                    in self.weapon_use_listener.keys()
                ):
                    self.weapon_use_listener[tagname](playerinf)
                else:
                    fmts.print_war(f"异常玩家攻击实体通信数据: {dats}")
                return
            else:
                return
        player = self.sys.game_ctrl.players.getPlayerByName(dats[0])
        if player is None:
            fmts.print_war(f"无法获取玩家: {dats[0]}")
            return
        if player not in self.player_holder.player_entities.keys():
            fmts.print_war(
                f"SkyblueRPG: {dats[0]} 的信息还未加载完成, 无法处理攻击实体信息"
            )
            return
        playerinf = self.player_holder.get_playerinfo(self.sys.getPlayer(dats[0]))
        mob = self.mob_holder.load_mobinfo(dats[1])
        if mob is None or mob.is_died():
            fmts.print_war(f"实体 {dats[1]} 不存在但是仍然受攻击, 已忽略")
            self.game_ctrl.sendwocmd(f"kill @e[scores={{sr:ms_uuid={dats[1]}}}]")
            return
        if mob is None:
            fmts.print_war(f"无法处理怪物 {mob} 的数据")
            return
        self.entity_holder.set_main_target(playerinf, mob)
        if playerinf.is_skill_set:
            playerinf.is_skill_set = False
            self.game_ctrl.player_title(playerinf.name, "§a技能已发动\n\n§a")
            self.player_use_skill(playerinf, mob)
        elif playerinf.is_ult_set:
            playerinf.is_ult_set = False
            self.game_ctrl.player_title(playerinf.name, "§d终结技已发动\n\n§a")
            self.player_use_ult(playerinf, mob)
        else:
            self.player_attack_mob(playerinf, mob)
        self.display_holder.display_charge_to_player(playerinf)

    @utils.thread_func("自定义RPG-生物攻击玩家")
    def _handle_mob_attack_player(self, dats: list[str]):
        player = self.sys.game_ctrl.players.getPlayerByName(dats[0])
        if player is None:
            fmts.print_war(f"无法获取玩家: {dats[0]}")
            return
        if player in self.player_holder.player_entities.keys():
            if len(dats) == 2:
                self.mob_attack_player(self.sys.getPlayer(dats[0]), dats[1])
        else:
            fmts.print_war(
                f"SkyblueRPG: {dats[0]} 的信息还未加载完成, 无法处理受伤信息"
            )

    @utils.thread_func("自定义RPG-玩家攻击玩家")
    def _handle_player_attack_player(self, dats: list[str]):
        if len(dats) != 2:
            fmts.print_war(f"玩家 PVP 攻击数据错误: {dats}")
            return
        p_1 = self.game_ctrl.players.getPlayerByName(dats[0])
        p_2 = self.game_ctrl.players.getPlayerByName(dats[1])
        if p_1 is None or p_2 is None:
            fmts.print_war(f"SkyblueRPG: 玩家 {dats[0]} 或 {dats[1]} 不存在")
            return
        p1 = self.player_holder.player_entities.get(p_1)
        p2 = self.player_holder.player_entities.get(p_2)
        if p1 is None or p2 is None:
            fmts.print_war(
                f"SkyblueRPG: {dats[0]}/{dats[1]} 的信息还未加载完成, 无法处理受伤信息"
            )
            return
        self.player_attack_player(p2, p1)

    @utils.thread_func("自定义RPG-玩家使用主手道具")
    def _handle_player_use_weapon_only(self, dats: list[str]):
        playerinf = self.player_holder.get_playerinfo(self.sys.getPlayer(dats[0]))
        if (
            playerinf.weapon
            and (tagname := playerinf.weapon.tag_name)
            in self.weapon_use_listener.keys()
        ):
            self.weapon_use_listener[tagname](playerinf)

from time import time
from typing import TYPE_CHECKING
from weakref import WeakKeyDictionary
from tooldelta import Player
from tooldelta.utils import tempjson
from . import event_apis
from .rpg_lib import constants, utils as rpg_utils
from .rpg_lib.rpg_entities import PlayerEntity, MobEntity, Entity
from .rpg_lib.player_basic_data import PlayerBasic
from .rpg_lib.frame_objects import Relic
from .rpg_lib.lib_rpgitems import (
    convert_item_to_relic,
    convert_item_to_weapon,
    ItemWeapon,
)

if TYPE_CHECKING:
    from . import CustomRPG


class PlayerHolder:
    def __init__(self, sys: "CustomRPG"):
        self.sys = sys
        # 玩家实体缓存数据
        self._player_entities: dict[Player, PlayerEntity] = {}
        self.loaded_player_basic_data: dict[Player, PlayerBasic] = {}
        # 玩家上一次的武器冷却
        self.player_last_weapon_cd: dict[Player, float] = {}
        # 玩家上一次的武器终结技充能
        self.player_last_weapon_chg: dict[Player, int] = {}
        self.player_last_display_effect: WeakKeyDictionary[PlayerEntity, int] = (
            WeakKeyDictionary()
        )
        self.sys.rpg_settings.add_setting_changed_listener(
            "pvp", self._on_change_pvp_mode
        )
        self.initialized = False

        if False:
            from .ref_saver import save_ref, read_ref

            def check_ref(_):
                import sys

                for k, v in self._player_entities.items():
                    self.sys.print(f"ref of {k.name} is {sys.getrefcount(v)}")

            def set_ref(_):
                save_ref(list(self._player_entities.values()))
                self.sys.print("ref saved")

            def get_ref(_):
                refs = read_ref()
                for rname, rcount in refs:
                    self.sys.print(f"ref of {rname} is {rcount}")

            self.sys.frame.add_console_cmd_trigger(
                ["gref"], None, self.sys.name, check_ref
            )
            self.sys.frame.add_console_cmd_trigger(
                ["ssr"], None, self.sys.name, set_ref
            )
            self.sys.frame.add_console_cmd_trigger(
                ["ggr"], None, self.sys.name, get_ref
            )

    def activate(self):
        self.initialized = True

    def add_player(self, player: Player, init=False, is_creative=False):
        path = self.sys.path_holder.format_player_basic_path(player)
        data = tempjson.load_and_read(path, need_file_exists=False, default=None)
        if data is None:
            basic_data = PlayerBasic.make_new(self.sys, player)
            data = basic_data.dump()
        basic_data = PlayerBasic.read_from_data(self.sys, player, data)
        # 加载基础数据
        self.loaded_player_basic_data[player] = basic_data
        entity = basic_data.to_player_entity()
        # self._player_entities[player] = (
        #     entity := basic_data.to_player_entity()
        # )
        entity.switch_gamemode(1 if is_creative else 2)
        entity.switch_pvp(bool(self.sys.rpg_settings.get_player_setting(player, "pvp")))
        self.sys.game_ctrl.sendwocmd(
            f"scoreboard players set {player.safe_name} sr:ms_rtid {basic_data.runtime_id}"
        )
        self.sys.entity_holder.load_player(entity)
        if init:
            self.sys.qq_holder.on_player_join(basic_data)
        return entity

    # 玩家退出处理
    def remove_player(self, player: Player, normal=False):
        if (playerinf := self._player_entities.get(player)) is None:
            self.sys.print_war(
                f"玩家移除: 玩家 {player.name} 没有被加载到 RPG 系统, 忽略移除"
            )
            return
        if normal:
            self.sys.qq_holder.on_player_leave(self.get_player_basic(player))
        playerinf.set_removed()
        self.save_game_player_data(player, unload_path=True)
        self.sys.entity_holder.unload_player(player)
        if player in self._player_entities.keys():
            del self._player_entities[player]
        if player in self.loaded_player_basic_data:
            del self.loaded_player_basic_data[player]
        if player in self.player_last_weapon_cd:
            del self.player_last_weapon_cd[player]
        if player in self.player_last_weapon_chg:
            del self.player_last_weapon_chg[player]

    def get_playerinfo(self, player: Player):
        return self._player_entities[player]

    def get_player_basic(self, player: Player):
        return self.loaded_player_basic_data[player]

    # 获取玩家身上的饰品二件套和四件套
    def get_player_suites(self, playerinf: PlayerEntity):
        armor_suits_2nd: dict[str, Relic] = {}
        armor_suits_4th: dict[str, Relic] = {}
        relic_suits_2nd: dict[str, Relic] = {}
        relic_suits_4th: dict[str, Relic] = {}
        for relic in playerinf.relics:
            if relic:
                if relic.is_suit_2:
                    if relic.types[0] in range(4):
                        armor_suits_2nd[relic.category] = relic
                    else:
                        relic_suits_2nd[relic.category] = relic
                if relic.is_suit_4:
                    if relic.types[0] in range(4):
                        armor_suits_4th[relic.category] = relic
                    else:
                        relic_suits_4th[relic.category] = relic
        return armor_suits_2nd, armor_suits_4th, relic_suits_2nd, relic_suits_4th

    def update_playerentity_from_basic(self, basic: PlayerBasic, prop: PlayerEntity):
        """
        - 从 PlayerBasic 中获取内容并更新到 PlayerEntity 上
        - 当饰品改变等造成 Basic 数据改变时调用
        - 从 basic_data 更新武器
        """
        weapon_uuid = basic.mainhand_weapons_uuid[0]
        if weapon_uuid is None:
            weapon = None
        elif not (
            weapon := self.sys.backpack_holder.getItem(basic.player, weapon_uuid)
        ):
            basic.mainhand_weapons_uuid[0] = None
            self.sys.print_war(
                f"玩家 {basic.player.name} 所持主手物品 UUID 无法对应背包物品 UUID"
            )
        else:
            weapon = convert_item_to_weapon(weapon, prop)
        prop.set_weapon(weapon)
        # 从 basic_data 更新饰品
        relics: list[Relic | None] = []
        for relic_uuid in basic.relics_uuid:
            if relic_uuid is None:
                relic = None
            elif not (
                relic := self.sys.backpack_holder.getItem(basic.player, relic_uuid)
            ):
                self.sys.print_war(
                    f"玩家 {basic.player} 所持饰品UUID无法对应背包物品UUID: {relic_uuid}"
                )
                basic.relics_uuid[basic.relics_uuid.index(relic_uuid)] = None
            else:
                relic = convert_item_to_relic(relic, prop)
            relics.append(relic)
        prop.relics = relics
        self._update_player_properties(basic.player)

    def update_playerentity_from_basic_easy(self, player: Player):
        self.update_playerentity_from_basic(
            self.get_player_basic(player), self.get_playerinfo(player)
        )

    # 更新玩家数据至磁盘 同时刷新Basic数据
    def save_game_player_data(self, player: Player, unload_path=False):
        if player in self.loaded_player_basic_data.keys():
            path = self.sys.path_holder.format_player_basic_path(player)
            playerinf = self.get_playerinfo(player)
            self.get_player_basic(player).update_from_playerentity(playerinf)
            self.dump_mainhand_weapon_datas_to_slotitem(playerinf)
            tempjson.load_and_write(path, self.get_player_basic(player).dump())
            if unload_path:
                tempjson.unload_to_path(path)
        else:
            self.sys.print_war(
                f"save_game_player_data: 玩家 {player.name} 没有被加载到 RPG 系统"
            )

    def get_player_last_weapon_charge(self, player: PlayerEntity):
        return self.player_last_weapon_chg.get(player.player)

    def set_player_last_weapon_charge(self, player: PlayerEntity, charge: int):
        self.player_last_weapon_chg[player.player] = charge

    def dump_mainhand_weapon_datas_to_slotitem(self, playerinf: PlayerEntity):
        "将武器数据格式化为可保存内容"
        if (weapon := playerinf.weapon) is None:
            return
        player_basic = self.get_player_basic(playerinf.player)
        mainhand_weapon_uuid = player_basic.mainhand_weapons_uuid[0]
        if mainhand_weapon_uuid is None:
            self.sys.print_war(
                f"异常: 玩家主手有道具, 实际上基础信息内没有 ({player_basic.mainhand_weapons_uuid})"
            )
            return
        mainhand_weapon_slot = self.sys.backpack_holder.getItem(
            playerinf.player, mainhand_weapon_uuid
        )
        if mainhand_weapon_slot is None:
            self.sys.print_war(
                f"异常: 玩家主手有道具(uuid={mainhand_weapon_uuid}), 实际上背包内没有"
            )
            return
        # Danger Zone! 需要 mainhand_weapon_slot 为 _bag 内 SlotItem, 不能为 copy
        item_weapon = ItemWeapon.load_from_item(mainhand_weapon_slot)
        weapon.dump_to_item(item_weapon)
        mainhand_weapon_slot.metadata.update(item_weapon.dump_item().metadata)

    # 更新玩家数据 (更新 basic 数据 到 玩家属性)
    def _update_player_properties(self, player: Player):
        playerinf = self.get_playerinfo(player)
        playerinf.basic_chg_add = 0.0
        atks = [0] * 7
        atks_add_default = 0.0
        atks_add = [0.0] * 7
        defs = [0] * 7
        defs_add_default = 0.0
        defs_add = [0.0] * 7
        hp_max_boost = 0
        hp_max_booost_add = 0.0
        crit = 0
        crit_add = 0
        chg_add = 0.0
        cure_add = 0.0
        effect_hit = 0.0
        effect_anti = 0.0
        weapon_mainhand_model = 0
        if weapon := playerinf.weapon:
            atks = rpg_utils.list_add(atks, list(weapon.current_atks))
            weapon_mainhand_model = weapon.show_model
        # 饰品数值
        for relic in playerinf.relics:
            if relic is None:
                continue
            metadata = {}
            metadata.update(relic.metadata["Main"])
            metadata.update(relic.metadata["Sub"])
            PROPs = constants.Properties
            PVAL = constants.PropVal
            for i, prop in enumerate(PROPs.atks()):
                atks[i] += metadata.get(prop, 0) * PVAL.GenericATK
            for i, prop in enumerate(PROPs.defs()):
                defs[i] += metadata.get(prop, 0) * PVAL.GenericDEF
            for i, prop in enumerate(PROPs.atk_adds()):
                atks_add[i] += metadata.get(prop, 0) * PVAL.ElementedATKAdd
            for i, prop in enumerate(PROPs.def_adds()):
                defs_add[i] += metadata.get(prop, 0) * PVAL.ElementedDEFAdd
            atks_add_default += metadata.get(PROPs.ATKBoost, 0) * PVAL.GenericATKAdd
            defs_add_default += metadata.get(PROPs.DEFBoost, 0) * PVAL.GenericDEFAdd
            hp_max_boost = metadata.get(PROPs.HPBoost, 0) * PVAL.HPBoost
            hp_max_booost_add += metadata.get(PROPs.HPBoostAdd, 0.0) * PVAL.HPBoostAdd
            chg_add += metadata.get(PROPs.ChargeAdd, 0) * PVAL.ChargeAdd
            crit += metadata.get(PROPs.CritChance, 0) * PVAL.Crit
            crit_add += metadata.get(PROPs.CritDamage, 0) * PVAL.CritAdd
            effect_hit += metadata.get(PROPs.EffectHit, 0) * PVAL.EffectHit
            effect_anti += metadata.get(PROPs.EffectRes, 0) * PVAL.EffectRes
        playerinf.init_basic(
            atks,
            defs,
            rpg_utils.list_multi(atks_add, [atks_add_default] * len(atks_add)),
            rpg_utils.list_multi(defs_add, [defs_add_default] * len(defs_add)),
            round(crit, 3),
            round(crit_add, 3),
            chg_add,
            int(playerinf.original_hpmax * hp_max_booost_add) + hp_max_boost,
            cure_add,
            effect_hit,
            effect_anti,
        )
        self.sys.game_ctrl.sendwocmd(
            f"scoreboard players set {player.safe_name} sr:mh_weapon {weapon_mainhand_model}"
        )
        # 饰品N件套刷新
        for relic in playerinf.relics:
            if relic:
                relic.update_suit()
                relic.on_use()
        self.sys.display_holder.display_charge_to_player(playerinf)

    # 玩家死亡处理方法
    def _player_died_handler(self, player: PlayerEntity, killer: Entity | None):
        assert isinstance(player, PlayerEntity)
        if isinstance(killer, PlayerEntity):
            self.sys.BroadcastEvent(
                event_apis.PlayerKillPlayerEvent(killer, player).to_broadcast()
            )
        elif isinstance(killer, MobEntity):
            self.sys.BroadcastEvent(
                event_apis.MobKillPlayerEvent(player, killer).to_broadcast()
            )
        self.sys.game_ctrl.sendwocmd(f"/kill {player.name}")
        player.hp = player.tmp_hp_max
        self.sys.player_holder.get_player_basic(player.player).update_from_playerentity(
            player
        )
        player.effects.clear()

    # 监听玩家设置更改 pvp 模式
    def _on_change_pvp_mode(self, player: Player, mode: int):
        self.get_playerinfo(player).switch_pvp(bool(mode))

    def player_online(self, player: Player):
        return player in self._player_entities.keys()

    def update_last_display_effect_time(self, playerinf: PlayerEntity):
        self.player_last_display_effect[playerinf] = int(time())

    def displayed_effect_last(self, playerinf: PlayerEntity):
        return time() - self.player_last_display_effect.get(playerinf, 0) < 0.5

    def player_change_gamemode(self, player: Player, mode: int):
        self.get_playerinfo(player).gamemode = mode

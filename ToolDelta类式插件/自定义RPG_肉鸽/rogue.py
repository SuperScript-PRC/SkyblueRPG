from typing import TYPE_CHECKING
from weakref import WeakValueDictionary
from tooldelta import Player, utils
from .define import CBEvent
from .frame_areas import all_areas_empty_one
from .frame_levels import Level, PVELevel, BossLevel, RestLevel
from .frame_rogue import Rogue
from .rogue_utils import copy_weapons_and_relics_to_virtual
from .storage import RogueStatusStorage

if TYPE_CHECKING:
    from . import CustomRPGRogue, entry

    evtapi = entry.rpg.event_apis


class Executor:
    def __init__(self, sys: "CustomRPGRogue", rogue: Rogue):
        self.sys = sys
        self.rogue = rogue
        self.player_linked_levels: WeakValueDictionary[Player, Level] = (
            WeakValueDictionary()
        )
        self.mob_linked_levels: WeakValueDictionary[int, PVELevel | BossLevel] = (
            WeakValueDictionary()
        )
        e = self.sys.rpg.event_apis
        self.sys.cb2bot.regist_message_cb(
            CBEvent.PlayerStartRogue.value, self._on_enter_rogue
        )  # tellraw @a[tag=sr.rpg_bot] {"rawtext":[{"text":"rogue.start_game"},{"selector":"@p"}]}
        self.sys.cb2bot.regist_message_cb(
            CBEvent.PlayerSelectNextLevel.value, self._on_select_nextlevel
        )  # tellraw @a[tag=sr.rpg_bot] {"rawtext":[{"text":"rogue.player_select_nextlevel"},{"selector":"@p"},{"text":"0"}]}
        self.sys.cb2bot.regist_message_cb(
            CBEvent.PlayerSupplyHealth.value,
            self._on_rest_level_supply_health,
        )  # tellraw @a[tag=sr.rpg_bot] {"rawtext":[{"text":"rogue.player_supply_health"},{"selector":"@p"}]}
        self.sys.cb2bot.regist_message_cb(
            CBEvent.PlayerGameCompletion.value,
            self._on_player_game_completion,
        )  # tellraw @a[tag=sr.rpg_bot] {"rawtext":[{"text":"rogue.player_game_completion"},{"selector":"@p"}]}
        self.sys.ListenInternalBroadcast(
            e.PlayerDiedEvent.type, lambda evt: self._on_player_died(evt.data)
        )
        self.sys.ListenInternalBroadcast(
            e.MobDiedEvent.type, lambda evt: self._on_mob_died(evt.data)
        )
        self.sys.ListenInternalBroadcast(
            e.PlayerModifyWeaponEvent.type,
            lambda evt: self._on_player_modify_weapon(evt.data),
        )
        self.sys.ListenInternalBroadcast(
            e.PlayerModifyRelicEvent.type,
            lambda evt: self._on_player_modify_relic(evt.data),
        )
        self.sys.menu.add_new_trigger(
            ["reflect-exit"],
            [],
            "强制退出反射世界",
            self.on_force_exit_rogue,
            op_only=True,
        )
        self.sys.menu.add_new_trigger(
            ["reflect-start"],
            [],
            "强制开启反射世界关卡",
            self.on_force_start_level,
            op_only=True,
        )
        self.sys.snowmenu.register_mainpage_blocker(self._snowmenu_blocker)

    def enter_rogue(self, player: Player):
        can_enter = all_areas_empty_one()
        align = self.sys.bigchar.mctext.align
        pad = self.sys.bigchar.mctext.pad

        def _disp_cb(_, page: int):
            if page > 2:
                return None
            dsp = ["§" + ("f" if page == i else "8") for i in range(3)]
            title = align.align_center(
                "§9❈ §bＲｅｆｌｅｃｔ Ｗｏｒｌｄ Ｅｍｕｌａｔｏｒ §f| §s反射世界§f ", 60
            )
            sp = "§7" + pad.pad_with_length(60 * 12, "一")
            output = "\n".join(
                (
                    title,
                    sp,
                    "§d • 当前状态： "
                    + f"§f【{('§a空闲§f' if can_enter else '§c忙碌§f')}§f】",
                    "§e • 初始效果： "
                    + ("， ".join(x.name for x in self.rogue.initial_effects) or "无"),
                    f"§c • 振荡阈值： {self.sys.bigchar(self.rogue.shake_value_threshold)}",
                    sp,
                    f"§7〈{dsp[0]}进入世界§7〉  〈{dsp[1]}排行榜§7〉  〈{dsp[2]}离开§7〉",
                )
            )
            return output

        with utils.ChatbarLock(player.name):
            section = self.sys.snowmenu.simple_select(player, _disp_cb)
            if section is None:
                return
            elif section == 0:
                if not can_enter:
                    self.sys.rpg.show_fail(player, "无法进入")
                    return
                elif (
                    self.sys.rpg.api_holder.get_player_basic(
                        player
                    ).mainhand_weapons_uuid[0]
                    is None
                ):
                    self.sys.rpg.show_fail(player, "进入前请先在槽位 1 装备武器")
                    return
                storage = RogueStatusStorage.default(self.sys, player)
                self.sys.set_storage(player, storage)
                self.rogue.enter_rogue(storage)
                copy_weapons_and_relics_to_virtual(player)

    def link_mob_runtimeid_to_level(
        self, mob_runtimeid: int, level: PVELevel | BossLevel
    ):
        self.mob_linked_levels[mob_runtimeid] = level

    def link_player_to_level(self, player: Player, level: Level | None):
        if level:
            self.player_linked_levels[player] = level
        else:
            del self.player_linked_levels[player]

    def on_force_exit_rogue(self, player: Player, _):
        if not self.sys.pdstore.get_property(player, "srpg:in_rogue", False):
            self.sys.rpg.show_fail(player, "您未处在反射世界中")
            return
        storage = self.sys.get_storage(player)
        if not storage.current_level:
            self.sys.rpg.show_fail(player, "退出映象世界出错： 当前关卡不存在")
            return
        storage.current_level.destroy()
        self.rogue._clear_display_levels(self.sys, storage.current_level)
        self.rogue.player_leave_rogue(self.sys, storage, display_scb=False)
        self.rogue.remove_player(self.sys, player)
        self.sys.rpg.show_succ(player, "已退出当前的映象世界")

    def on_force_start_level(self, player: Player, _):
        if not self.sys.pdstore.get_property(player, "srpg:in_rogue", False):
            self.sys.rpg.show_fail(player, "您未处在反射世界中")
            return
        storage = self.sys.get_storage(player)
        if storage.current_level:
            storage.current_level.activate()
        else:
            self.sys.rpg.show_fail(player, "退出映象世界出错： 当前关卡不存在")

    def _snowmenu_blocker(self, player: Player):
        if self.sys.pdstore.get_property(player, "srpg:in_rogue", False):
            self._on_open_rogue_menu(player)
            return True
        return False

    def _on_open_rogue_menu(self, player: Player):
        output = ""
        last_page = -1
        a = self.sys.bigchar.mctext.align
        p = self.sys.bigchar.mctext.pad
        s = self.sys.get_storage(player)

        def update_disp(page: int):
            nonlocal output
            output = ""
            ybp = "§9▁▂▃▄▅▆▇▉ §b§l仪表盘§r §9▉▇▆▅▄▃▂▁"
            length = a.get_line_width(ybp)
            dsp = ["§" + ("f" if page == i else "8") for i in range(3)]
            output = "\n".join(
                (
                    ybp,
                    a.align_simple(
                        " ",
                        ("§b振荡值", 12),
                        (8, str(s.shake_value)),
                        ("", 16),
                        ("§e金粒数量", 12),
                        (8, str(s.money)),
                    ),
                    a.align_simple(
                        " ",
                        ("§s效果数", 12),
                        (8, str(s.effects_amount)),
                        ("", 16),
                        ("§p当前得分", 12),
                        (8, str(s.score)),
                    ),
                    f"§8{p.pad_with_length(length, '一', _round=True)}§r",
                    a.align_simple(
                        (f"{dsp[0]}效果详情", 20),
                        (f"{dsp[1]}属性面板", 20),
                        (f"{dsp[2]}退出世界", 20),
                    ),
                )
            )

        def disp(_, page: int):
            nonlocal last_page, output
            if page > 2:
                return None
            if page != last_page:
                update_disp(page)
                last_page = page
            return output

        while True:
            match self.sys.snowmenu.simple_select(player, disp):
                case None:
                    return
                case 0:
                    self._on_player_skim_effects(player)
                case 2:
                    self._on_player_exit(player)
                    return

    def _on_player_init(self, player: Player):
        if self.sys.pdstore.get_property(player, "srpg:in_rogue", False):
            self.rogue.add_player(self.sys, player)

    def _on_enter_rogue(self, args: list[str]):
        target = args[0]
        player = self.sys.game_ctrl.players.getPlayerByName(target)
        if player is None:
            return
        self.enter_rogue(player)

    def _on_select_nextlevel(self, args: list[str]):
        target, level = args[0:2]
        player = self.sys.game_ctrl.players.getPlayerByName(target)
        if player is None:
            return
        self.rogue.select_and_goto_next_level(self.sys.get_storage(player), int(level))

    def _on_rest_level_supply_health(self, args: list[str]):
        target = args[0]
        player = self.sys.game_ctrl.players.getPlayerByName(target)
        if player is None:
            return
        storage = self.sys.get_storage(player)
        if isinstance(storage.current_level, RestLevel):
            storage.current_level.supply_health()

    @utils.thread_func("玩家完成映像世界")
    def _on_player_game_completion(self, args: list[str]):
        target = args[0]
        player = self.sys.game_ctrl.players.getPlayerByName(target)
        if player is None:
            return
        storage = self.sys.get_storage(player)
        if not isinstance(storage.current_level, BossLevel):
            self.sys.rpg.show_fail(player, "非法访问映像内存")
        elif not storage.current_level_passed:
            self.sys.rpg.show_fail(player, "访问映像数组越界")
        else:
            self.rogue.player_complete_rogue(self.sys, storage, storage.current_level)

    def _on_mob_died(self, evt: "evtapi.MobDiedEvent"):
        # 将生物死亡事件广播到需要监听该生物的关卡中
        if level := self.mob_linked_levels.get(evt.mob.runtime_id):
            level.on_mob_died(evt.mob.runtime_id)
            evt.cancel_drop()

    def _on_player_died(self, evt: "evtapi.PlayerDiedEvent"):
        # 将玩家死亡事件广播到需要监听该玩家关卡中
        if isinstance(
            level := self.player_linked_levels.get(evt.player.player), PVELevel
        ):
            level.on_player_died()

    def _on_player_exit(self, player: Player):
        if level := self.player_linked_levels.get(player):
            level.on_player_exit()
        if player in self.sys.storages:
            s = self.sys.storages.pop(player)
            s.interrupt()
            s.save()
            if s.current_level is not None:
                s.current_level.destroy()
                self.rogue._clear_display_levels(self.sys, s.current_level)
            self.rogue.player_leave_rogue(self.sys, s, display_scb=False)
            self.rogue.remove_player(self.sys, player)
            self.sys.rpg.show_succ(player, "已退出当前的映象世界")
            self.rogue.remove_player(self.sys, player)
            # TODO: 退出时显示计分板数据

    def _on_player_skim_effects(self, player: Player):
        sys = self.sys
        entity = self.sys.rpg.api_holder.get_player_entity(player)
        align = sys.bigchar.mctext.align
        pad = sys.bigchar.mctext.pad
        entity = sys.rpg.api_holder.get_player_entity(player)
        snowmenu = sys.snowmenu
        output = ""
        effects = entity.get_effects_by_tag("reflect_world")

        output = ""
        if effects:
            effect_names = [f"【{e.name}】  " for e in effects]
            prefix_length = align.get_lines_width(effect_names) // 12
            prefix_spaces = align.get_specific_length_spaces(prefix_length * 12)
            for i, effect in enumerate(effects):
                docs = align.cut_by_length(effect.doc(), 40)
                prefix = f"【{effect.name}】 "
                body = align.align_left("§6" + prefix, prefix_length) + "§7" + docs[0]
                if len(docs) > 1:
                    body += ("\n" + prefix_spaces).join("§7" + i for i in docs[1:])
                output += "\n" + body
        else:
            output += "§a\n    §7暂无任何效果"
        for _ in range(12 - output.count("\n")):
            output += "\n§a"
        title_length = max(480, align.get_lines_width(output.split("\n")))
        output = (
            "§7"
            + pad.pad_with_length(title_length // 2, "一")
            + "§e❃ §l效果详情§r§7"
            + pad.pad_with_length(title_length // 2, "一")
        ) + output

        def disp(_, page: int):
            if page >= 1:
                return None
            return output

        snowmenu.simple_select(player, disp)

    def _on_player_modify_weapon(self, evt: "evtapi.PlayerModifyWeaponEvent"):
        if self.sys.pdstore.get_property(evt.player, "srpg:in_rogue", False):
            return "映像世界内不可配置武器"

    def _on_player_modify_relic(self, evt: "evtapi.PlayerModifyRelicEvent"):
        if self.sys.pdstore.get_property(evt.player, "srpg:in_rogue", False):
            return "映像世界内不可配置饰品"

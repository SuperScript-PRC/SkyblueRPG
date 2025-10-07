from collections.abc import Callable
from typing import TYPE_CHECKING
from tooldelta import utils, Player
from . import event_apis
from .rpg_lib import constants, utils as rpg_utils

if TYPE_CHECKING:
    from . import CustomRPG, SlotItem


page_descriptions = tuple(
    (
        (string := "\n".join(rpg_utils.cut_str_by_len(i, 46)))
        + "\n" * (3 - string.count("\n"))
    )
    for i in (
        "查看和配置当前装备的武器， 其中§a第一个槽位§7的武器作为§a主手武器§7。",
        "查看和配置当前佩戴的饰品， 同类饰品可组合为§a二件套§7或§a四件套§7。",
        "查看你的角色的各项基本战斗数据。",
        "",
    )
)


class SnowmenuGUI:
    def __init__(self, sys: "CustomRPG"):
        self.sys = sys
        self.game_ctrl = sys.game_ctrl
        self.gui = sys.snowmenu
        MultiPage = sys.snowmenu.MultiPage
        self.main_page = MultiPage(
            "sr.rpg_menu",
            self._menu_main_page,
            self._menu_confirm,
            parent_page_id="default",
        )
        sys.snowmenu.add_page(self.main_page)

    def enable_snowmenu(self):
        self.gui.register_main_page(self.main_page, "战斗终端")

    def _menu_main_page(self, _: Player, page: int):
        if page in range(4):
            page_chg = ["7"] * 4
            page_chg[page] = "b"
            p1, p2, p3, p4 = page_chg
            return (
                "§8========§7=====§f=====｛|§bTerminal§f|｝=====§7=====§8========\n"
                + f"  §{p1}➭ 武器配置\n"
                + f"  §{p2}➭ 饰品配置\n"
                + f"  §{p3}➭ 角色数据\n"
                + f"  §{p4}➭ 敬请期待\n"
                + "§8一一一一一一一一一一一一一一一一一一一一一一\n§7"
                + page_descriptions[page]
                + "§8========§7=====§f=====================§7=====§8========\n§a"
            )
        else:
            return None

    def _menu_confirm(self, player: Player, page: int):
        (
            self._player_config_mainhand_weapon,
            self._player_config_armors_and_relics,
            self._player_check_panel_simple,
            lambda _: None,
        )[page](player)

    ##### 菜单内配置物品等 #####
    @utils.thread_func("玩家配置主手物品")
    def _player_config_mainhand_weapon(self, player: Player):
        def _modify_test(
            index: int, slotitem: "SlotItem | None", err_fmt="无法切换武器: %s"
        ):
            cant_modify: str | None = rpg_utils.real_any(
                self.sys.BroadcastEvent(
                    event_apis.PlayerModifyWeaponEvent(
                        player, index, slotitem
                    ).to_broadcast()
                )
            )
            if cant_modify:
                self.sys.show_fail(player, err_fmt % cant_modify)
            return cant_modify is not None

        old_mainhand_weapons_uuid = self.sys.player_holder.get_player_basic(
            player
        ).mainhand_weapons_uuid.copy()
        items: list["SlotItem | None"] = []
        items_hs = {}
        self.game_ctrl.sendwscmd(f"/execute as {player.safe_name} at @s run tp ~~~ ~ 0")
        self.sys.player_holder.dump_mainhand_weapon_datas_to_slotitem(
            self.sys.player_holder.get_playerinfo(player)
        )
        # 更新主手物品信息到虚拟背包
        self.sys.player_holder.save_game_player_data(player)
        try:
            for item in (
                self.sys.backpack_holder.getItem(player, i) if i is not None else i
                for i in old_mainhand_weapons_uuid
            ):
                if item is None:
                    items.append(None)
                else:
                    items.append(item)
                    items_hs[item.uuid] = item
            l_menu = {}
            for ind, _ in enumerate(items):
                single = (
                    "§8········§7---===§f===<|§c§l配置武器槽§r§f|>===§7===---§8········"
                )
                for ind2, slotitem in enumerate(items):
                    if slotitem is None:
                        single += (
                            f"\n§r§f➣ §f§l[{ind2 + 1}] 空"
                            if ind == ind2
                            else f"\n§r§8➣ §7[{ind2 + 1}] 空"
                        )
                    else:
                        single += (
                            f"\n§r§f➣ §f§l[{ind2 + 1}] {slotitem.disp_name}"
                            if ind == ind2
                            else f"\n§r§8➣ §7[{ind2 + 1}] {slotitem.disp_name}"
                        )
                selected_item = items[ind]
                if selected_item is not None:
                    single += (
                        "\n§r§f"
                        + self.sys.item_holder.get_weapon_minimal_description(
                            selected_item
                        )
                    )
                else:
                    single += "\n\n§r§7[§bi§7] §b选中武器以查看属性。\n\n"
                l_menu[ind] = single + "\n§r§6§l在切换武器时， 会按从上到下顺序切换武器"
            res_slot: int | None = self.gui.simple_select_dict(player, l_menu)
            if res_slot is None:
                raise SystemExit
            else:
                item_sel = old_mainhand_weapons_uuid[res_slot]
                if item_sel is None:
                    res = self.gui.simple_select_dict(
                        player,
                        {
                            0: f"§7槽位 [§f{res_slot + 1}§7] §6空槽位\n §f➣ §l装备武器§r§f"
                            + " " * 30
                            + "\n§7   ..."
                            + "\n§a" * 6
                            + "§a抬头确认 §7| §c低头取消"
                        },
                    )
                    if res is not None:
                        swap_item_uuids = [i for i in old_mainhand_weapons_uuid if i]
                        changable_items = (
                            self.sys.backpack_holder.list_player_store_with_filter(
                                player,
                                [i.to_category() for i in constants.WeaponType],
                            )
                        )
                        if changable_items == []:
                            self.sys.show_fail(player, "无可切换的道具")
                            raise SystemExit

                        def _cb1(x: "SlotItem"):
                            return (
                                f"◈ {x.disp_name} §r§7(交换)"
                                if x.uuid in swap_item_uuids
                                else "◈ " + x.disp_name
                            )

                        res1 = self.check_items(
                            player, changable_items, display_column_cb=_cb1
                        )
                        if res1 is None:
                            raise SystemExit
                        if not _modify_test(res_slot, res1, "无法装备武器： %s"):
                            return
                        if res1.uuid in swap_item_uuids:
                            target_slot = old_mainhand_weapons_uuid.index(res1.uuid)
                            old_mainhand_weapons_uuid[target_slot] = None
                            if target_slot == 0:
                                # 将主手的武器交换至此, 目前主手为空时
                                for _slotid in range(3):
                                    self.game_ctrl.sendwocmd(
                                        f"replaceitem entity {player.safe_name} slot.hotbar {_slotid} air"
                                    )
                        old_mainhand_weapons_uuid[res_slot] = res1.uuid
                        self.sys.show_succ(
                            player,
                            f"已将 §f<{res1.disp_name}§r§f> §a放入主手槽位",
                        )
                        self.sys.display_holder.display_weapon_to_player(player, res1)
                    else:
                        raise SystemExit
                else:
                    item_sel = self.sys.backpack_holder.getItem(player, item_sel)
                    if item_sel is None:
                        orig_uuid = old_mainhand_weapons_uuid[res_slot]
                        old_mainhand_weapons_uuid[res_slot] = None
                        raise AssertionError(f"物品选择错误: 物品丢失: {orig_uuid}")

                    def _cb(_, page: int):
                        if page > 1:
                            return None
                        header = f"§7槽位 [§f{res_slot + 1}§7]  §f{item_sel.disp_name}"
                        if page > 1:
                            return None
                        match page:
                            case 0:
                                content = " §r§f<卸下道具> §8<切换道具>"
                            case 1:
                                content = " §r§8<卸下道具> §f<切换道具>"
                        return (
                            header
                            + content
                            + "\n"
                            + item_sel.item.description(item_sel)  # type: ignore
                        )

                    res = self.gui.simple_select(player, _cb)
                    if res is not None:
                        match res:
                            case 0:
                                # unload armor
                                if not _modify_test(
                                    res_slot, None, "无法卸下武器： %s"
                                ):
                                    return
                                old_mainhand_weapons_uuid[res_slot] = None
                                self.sys.show_succ(player, "已卸下槽位武器")
                                if res_slot == 0:
                                    for _slotid in range(3):
                                        self.game_ctrl.sendwocmd(
                                            f"replaceitem entity {player.safe_name} slot.hotbar {_slotid} air"
                                        )
                            case 1:
                                # change armor
                                swap_item_uuids = [
                                    i for i in old_mainhand_weapons_uuid if i
                                ]
                                changable_items = self.sys.backpack_holder.list_player_store_with_filter(
                                    player,
                                    [i.to_category() for i in constants.WeaponType],
                                    [item_sel.uuid],
                                )
                                if changable_items == []:
                                    self.sys.show_fail(
                                        player,
                                        "无可切换的道具",
                                    )
                                    raise SystemExit

                                def _cb1(x: "SlotItem"):
                                    return (
                                        f"◈ {x.disp_name} §r§7(交换)"
                                        if x.uuid in swap_item_uuids
                                        else "◈ " + x.disp_name
                                    )

                                res1 = self.check_items(
                                    player, changable_items, display_column_cb=_cb1
                                )
                                if res1 is None:
                                    raise SystemExit
                                if not _modify_test(res_slot, res1):
                                    return
                                if res1.uuid in swap_item_uuids:
                                    old_mainhand_weapons_uuid[
                                        old_mainhand_weapons_uuid.index(res1.uuid)
                                    ] = item_sel.uuid
                                old_mainhand_weapons_uuid[res_slot] = res1.uuid
                                self.sys.show_succ(
                                    player,
                                    f"已更改槽位道具至 {res1.disp_name}",
                                )
                                self.game_ctrl.sendwocmd(
                                    f"replaceitem entity {player.safe_name} slot.hotbar 0 air"
                                )
                                self.sys.display_holder.display_weapon_to_player(
                                    player, res1
                                )
                    else:
                        raise SystemExit
        except SystemExit:
            pass
        except Exception as err:
            player.show(f"§c{err}")
            raise
        finally:
            if not self.sys.player_holder.player_online(player):
                return
            playerinf = self.sys.player_holder.get_playerinfo(player)
            self.sys.player_holder.get_player_basic(
                player
            ).mainhand_weapons_uuid = old_mainhand_weapons_uuid
            self.sys.player_holder.update_playerentity_from_basic(
                self.sys.player_holder.get_player_basic(player), playerinf
            )
            self.sys.player_holder.save_game_player_data(player)
            # 手动更新玩家的CD显示
            if (
                weapon := playerinf.weapon
            ) and self.sys.item_holder.get_weapon_skill_cd(weapon) <= 0:
                self.game_ctrl.sendwocmd(
                    "replaceitem entity @a[name="
                    + playerinf.name
                    + r'] slot.hotbar 1 iron_ingot 1 755 {"item_lock":{"mode":"lock_in_slot"}}'
                )
            self.gui.set_player_page(player, self.main_page)

    # 配置饰品
    @utils.thread_func("玩家配置饰品")
    def _player_config_armors_and_relics(self, player: Player):
        enum = constants.ConfigPanelEnum
        self.game_ctrl.sendwscmd(f"/execute as {player.safe_name} at @s run tp ~~~ ~ 0")

        def _modify_test(
            index: int, slotitem: "SlotItem | None", err_fmt="无法切换饰品: %s"
        ):
            cant_modify: str | None = rpg_utils.real_any(
                self.sys.BroadcastEvent(
                    event_apis.PlayerModifyRelicEvent(
                        player, index, slotitem
                    ).to_broadcast()
                )
            )
            if cant_modify:
                self.sys.show_fail(player, err_fmt % cant_modify)
            return cant_modify is not None

        def config_panel(
            player: Player, nowitem: "SlotItem | None", items: list["SlotItem"]
        ):
            self.game_ctrl.sendwscmd(
                f"execute as {player.safe_name} at @s run playsound note.pling @s ~~~ 1 1.4"
            )
            if nowitem is None:
                res = self.gui.simple_select_dict(
                    player,
                    {
                        0: "| §7<§o§c!§r§7>§6槽位为空 §f|\n  §f<装备道具>\n  §7<...>\n§a抬头选择 §f| §c低头退出"
                    },
                )
                if res is None:
                    return enum.NULL, None
                else:
                    res = self.check_items(player, items)
                    if res is None:
                        return enum.NULL, None
                    return enum.NEW_SLOTITEM, res
            else:
                desc_format = nowitem.item.description(nowitem)  # type: ignore
                opt_menu_pages = [
                    nowitem.disp_name
                    + " §r§f➭卸下道具 §8➭切换道具  §a抬头选择 §f| §c低头退出\n"
                    + desc_format,
                    nowitem.disp_name
                    + " §r§8➭卸下道具 §f➭切换道具  §a抬头选择 §f| §c低头退出\n"
                    + desc_format,
                ]
                real_menu_pages = dict(enumerate(opt_menu_pages))
                res = self.gui.simple_select_dict(player, real_menu_pages)
                if res is None:
                    return enum.NULL, None
                elif res == 0:
                    return enum.UNEQUIP_SLOTITEM, nowitem
                elif res == 1:
                    res = self.check_items(player, items)
                    if res is None:
                        return enum.NULL, None
                    return enum.MODIFY_SLOTITEM, res
                else:
                    raise ValueError("Invalid menu page")

        try:
            last_page = 0
            while True:
                player_basic = self.sys.player_holder.get_player_basic(player)
                shead, schest, slegs, sfeet = (
                    self.sys.backpack_holder.getItem(player, i)
                    if i is not None
                    else None
                    for i in player_basic.relics_uuid[:4]
                )
                slA, slB, slC, slD = (
                    self.sys.backpack_holder.getItem(player, i)
                    if i is not None
                    else None
                    for i in player_basic.relics_uuid[4:]
                )
                suit2_fmt = "§6%s §e二件套： §a%s"
                suit4_fmt = "§6%s §e四件套： §a%s"
                a2data, a4data, r2data, r4data = (
                    self.sys.player_holder.get_player_suites(
                        self.sys.player_holder.get_playerinfo(player)
                    )
                )
                armor_txts = (
                    [suit2_fmt % (i, j.suit_2nd_description) for i, j in a2data.items()]
                    + [
                        suit4_fmt % (i, j.suit_4th_description)
                        for i, j in a4data.items()
                    ]
                ) or ["§7无二件套效果和四件套效果"]
                relic_txts = (
                    [suit2_fmt % (i, j.suit_2nd_description) for i, j in r2data.items()]
                    + [
                        suit4_fmt % (i, j.suit_4th_description)
                        for i, j in r4data.items()
                    ]
                ) or ["§7无二件套效果和四件套效果"]
                utils.fill_list_index(armor_txts, ["", ""])
                utils.fill_list_index(relic_txts, ["", ""])

                output = ""
                _last_page = -1

                def _update(page: int):
                    nonlocal output
                    empty = "§7空"
                    a0 = shead.disp_name if shead else empty
                    a1 = schest.disp_name if schest else empty
                    a2 = slegs.disp_name if slegs else empty
                    a3 = sfeet.disp_name if sfeet else empty
                    a4 = slA.disp_name if slA else empty
                    a5 = slB.disp_name if slB else empty
                    a6 = slC.disp_name if slC else empty
                    a7 = slD.disp_name if slD else empty

                    algn = self.sys.bigchar.mctext.align.align_simple

                    glc = rpg_utils.get_last_color
                    T = 50
                    T2 = 25
                    S = 16
                    format_dict = {
                        f"a{i}": "§b" if page == i else "§7" for i in range(8)
                    }
                    output = (
                        "§8··················§7------------========§f========"
                        "<|§c§l配置饰品槽§r§f|>"
                        "========§7========------------§8··················\n"
                        "§8۞ §6护甲:§r\n"
                        + algn(
                            ("§7 {a0}➭ 头盔 §f", S), (a0, T2), armor_txts[0][:T]
                        ).removesuffix("§")
                        + "\n"
                        + algn(
                            ("§7 {a1}➭ 胸甲 §f", S),
                            (a1, T2),
                            glc(armor_txts[0][:T]) + armor_txts[0][T:],
                        ).removesuffix("§")
                        + "\n"
                        + algn(
                            ("§7 {a2}➭ 护腿 §f", S), (a2, T2), armor_txts[1][:T]
                        ).removesuffix("§")
                        + "\n"
                        + algn(
                            ("§7 {a3}➭ 护靴 §f", S),
                            (a3, T2),
                            glc(armor_txts[1][:T]) + armor_txts[1][T:],
                        ).removesuffix("§")
                        + "\n§7§8۞ §d饰品:§r\n"
                        + algn(
                            ("§7 {a4}➭ 天环 §f", S), (a4, T2), relic_txts[0][:T]
                        ).removesuffix("§")
                        + "\n"
                        + algn(
                            ("§7 {a5}➭ 项链 §f", S),
                            (a5, T2),
                            glc(relic_txts[0][:T]) + relic_txts[0][T:],
                        ).removesuffix("§")
                        + "\n"
                        + algn(
                            ("§7 {a6}➭ 戒指 §f", S), (a6, T2), relic_txts[1][:T]
                        ).removesuffix("§")
                        + "\n"
                        + algn(
                            ("§7 {a7}➭ 腰带 §f", S),
                            (a7, T2),
                            glc(relic_txts[1][:T]) + relic_txts[1][T:],
                        ).removesuffix("§")
                        + " §r\n"
                        "§a抬头选择 §f| §c低头退出 §f| §b扔雪球切换\n"
                    ).format(**format_dict)

                def _disp(_, page: int):
                    nonlocal output, _last_page
                    if page >= 8:
                        return None
                    elif page != _last_page:
                        _update(page)
                        _last_page = page
                    return output

                res = self.gui.simple_select(player, _disp, default_page=last_page)
                match res:
                    case 0 | 1 | 2 | 3:
                        temp_slots = [shead, schest, slegs, sfeet]
                        avaliable_items = (
                            self.sys.backpack_holder.list_player_store_with_filter(
                                player,
                                [
                                    [
                                        constants.HiddenCategory.HELMET,
                                        constants.HiddenCategory.CHESTPLATE,
                                        constants.HiddenCategory.LEGGINGS,
                                        constants.HiddenCategory.BOOTS,
                                    ][res]
                                ],
                                [i.uuid for i in temp_slots if i],
                            )
                        )
                        _choice = config_panel(player, temp_slots[res], avaliable_items)
                        if _choice[0] is enum.NULL:
                            last_page = res
                            continue
                        choice, item_need_op = _choice
                        if choice is enum.NEW_SLOTITEM:
                            if not _modify_test(res, item_need_op, "无法装备护甲： %s"):
                                continue
                            temp_slots[res] = item_need_op
                            self.sys.show_succ(
                                player, f"已装备 {item_need_op.disp_name}"
                            )
                        elif choice is enum.UNEQUIP_SLOTITEM:
                            if not _modify_test(res, None, "无法卸下护甲： %s"):
                                continue
                            temp_slots[res] = None
                            self.sys.show_succ(
                                player, f"已卸下 {item_need_op.disp_name}"
                            )
                        elif choice is enum.MODIFY_SLOTITEM:
                            if not _modify_test(res, item_need_op, "无法切换护甲： %s"):
                                continue
                            self.sys.show_succ(
                                player,
                                f"已将 {temp_slots[res].disp_name}§r§a 更换成 {item_need_op.disp_name}",  # type: ignore (always a item)
                            )
                            temp_slots[res] = item_need_op
                        player_basic.relics_uuid[:4] = [
                            i.uuid if i else i for i in temp_slots
                        ]
                    case 4 | 5 | 6 | 7:
                        temp_slots = [slA, slB, slC, slD]
                        avaliable_items = (
                            self.sys.backpack_holder.list_player_store_with_filter(
                                player,
                                [
                                    [
                                        constants.HiddenCategory.RELICA,
                                        constants.HiddenCategory.RELICB,
                                        constants.HiddenCategory.RELICC,
                                        constants.HiddenCategory.RELICD,
                                    ][res - 4]
                                ],
                                [i.uuid for i in temp_slots if i],
                            )
                        )
                        _choice = config_panel(
                            player, temp_slots[res - 4], avaliable_items
                        )
                        if _choice[0] is enum.NULL:
                            last_page = res
                            continue
                        choice, item_need_op = _choice
                        if choice is enum.NEW_SLOTITEM:
                            if not _modify_test(res, item_need_op, "无法装备饰品： %s"):
                                continue
                            temp_slots[res - 4] = item_need_op
                            self.sys.show_succ(
                                player, f"已装备 {item_need_op.disp_name}"
                            )
                        elif choice is enum.UNEQUIP_SLOTITEM:
                            if not _modify_test(res, None, "无法卸下饰品： %s"):
                                continue
                            temp_slots[res - 4] = None
                            self.sys.show_succ(
                                player, f"已卸下 {item_need_op.disp_name}"
                            )
                        elif choice is enum.MODIFY_SLOTITEM:
                            if not _modify_test(res, item_need_op, "无法切换饰品： %s"):
                                continue
                            self.sys.show_succ(
                                player,
                                f"已将 {temp_slots[res - 4].disp_name}§r§a 更换成 {item_need_op.disp_name}",  # type: ignore
                            )
                            temp_slots[res - 4] = item_need_op
                        player_basic.relics_uuid[4:] = [
                            i.uuid if i else i for i in temp_slots
                        ]
                    case None:
                        break
                last_page = res
                self.sys.player_holder.update_playerentity_from_basic(
                    player_basic, self.sys.player_holder.get_playerinfo(player)
                )
                self.sys.player_holder.save_game_player_data(player)
                self.game_ctrl.sendwocmd(
                    f"/execute as {player.safe_name} at @s run playsound armor.equip_diamond @s"
                )
        except SystemExit:
            self.game_ctrl.sendwscmd(
                f"execute as {player.safe_name} at @s run playsound note.pling"
            )
        finally:
            self.gui.set_player_page(player, self.main_page)

    # 玩家切换主手武器
    @utils.thread_func("玩家轮换武器")
    def _player_switch_weapon(self, player: Player):
        entity = self.sys.player_holder.get_playerinfo(player)
        playerbas = self.sys.player_holder.get_player_basic(player)
        self.sys.player_holder.dump_mainhand_weapon_datas_to_slotitem(entity)
        self.sys.player_holder.save_game_player_data(player)
        weapons_uuid = playerbas.mainhand_weapons_uuid.copy()
        avali_weapons_count = sum(i is not None for i in weapons_uuid)
        if weapons_uuid[0] is None:
            player.setActionbar("§7[§6!§7] §6无法在未使用武器情况下切换武器")
            return
        if avali_weapons_count < 2:
            player.setActionbar("§7[§6!§7] §6没有武器可供切换")
            return
        while True:
            # 使用第一个可用武器
            weapons_uuid.append(weapons_uuid.pop(0))
            if weapons_uuid[0] is not None:
                break
        playerbas.mainhand_weapons_uuid = weapons_uuid
        self.sys.player_holder.update_playerentity_from_basic(playerbas, entity)
        self.game_ctrl.sendwocmd(
            f"replaceitem entity {player.safe_name} slot.hotbar 0 air"
        )
        if wp_uuid := playerbas.mainhand_weapons_uuid[0]:
            weapon_item = self.sys.backpack_holder.getItem(entity.player, wp_uuid)
            assert weapon_item, f"{player.name}的主手物品未找到: {wp_uuid}"
            player.setActionbar(f"§7武器已切换为 {weapon_item.disp_name}")
        else:
            # will never happen?
            player.setActionbar("§7武器已切换为 §6无")
        self.sys.display_holder.display_skill_cd_to_player(entity, force_update=True)

    @utils.thread_func("玩家检查面板")
    def _player_check_panel_simple(self, player: Player, return_mainpage=True):
        playerinf = self.sys.player_holder.get_playerinfo(player)
        playerinf._update()
        hp_pc = playerinf.hp / playerinf.tmp_hp_max
        page = (
            "§8==========§7====§f｛§l§e属性面板§r§f｝§7====§8==========\n"
            "§4❤§r §7生命值： "
            f"{rpg_utils.render_bar(playerinf.hp, playerinf.tmp_hp_max, '§b' if hp_pc > 0.4 else '§e' if hp_pc > 0.25 else '§c', '§8', 60)}"
            f"  §f{playerinf.hp}§7/{playerinf.tmp_hp_max}\n"
            f"§c➚§r §7攻击力： §f{sum(playerinf.tmp_atks)}\n"
            f"§l§9▣§r §7防御力： §f{sum(playerinf.tmp_defs)}\n"
            f"§l§c➹§r §7暴击率： §f{round(playerinf.tmp_crit_pc * 100, 2)}%\n"
            f"§l§c➹§r §7暴击伤害： §f{round(playerinf.tmp_crit_add * 100 + 100, 2)}%\n"
            f"§l§b℗§r §7充能效率： §f{round(playerinf.tmp_chg_add * 100 + 100, 2)}%\n"
            f"§s✞ §7效果命中： §f{round(playerinf.tmp_effect_hit * 100, 2)}%\n"
            f"§u✽ §7效果抵抗： §f{round(playerinf.tmp_effect_anti * 100, 2)}%\n"
            "§r§6抬头或低头退出面板\n"
            "§r\n§a"
        )
        self.gui.simple_select_dict(player, {0: page})
        player.setActionbar("§a")
        if return_mainpage:
            self.gui.set_player_page(player, self.main_page)

    # 向玩家发出物品选择请求并获取返回
    def check_items(
        self,
        player: Player,
        items: list["SlotItem"],
        menu_header: str = "§7§l[§6■§7] §r§6请选择物品§f\n",
        display_column_cb: Callable[["SlotItem"], str] = lambda x: "- " + x.disp_name,
    ) -> "SlotItem | None":
        menu_pgs = {}
        items_selects_list: list["SlotItem"] = []
        for i, item in enumerate(items):
            txt = menu_header
            for _, item_2 in enumerate(items):
                item_inshow = (
                    f"§f {display_column_cb(item_2)}§r"
                    if item == item_2
                    else f"§8 {display_column_cb(item_2)}§r"
                ) + "\n"
                txt += item_inshow
            menu_pgs[i] = txt + "\n§a抬头选择 §f| §c低头退出 §f| §6扔雪球切换"
            items_selects_list.append(item)
        if menu_pgs == {}:
            self.sys.show_fail(player, "没有可选择的物品")
            return None
        res: int | None = self.gui.simple_select_dict(player, menu_pgs)
        if res is None:
            return None
        return items_selects_list[res]

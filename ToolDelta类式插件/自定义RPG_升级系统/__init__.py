import random
import time
from dataclasses import dataclass
from types import CodeType
from typing import TYPE_CHECKING, Any
from tooldelta import Plugin, Player, cfg, utils, plugin_entry

from . import event_apis
from .upgrade_cfg import RelicUpgradeConfig, WeaponUpgradeConfig


# @dataclass
# class UpgradePropMode:
#     weight: float


@dataclass
class DirectUpgrade:
    "定向升级的物品的信息"

    item_id: str
    prop: str
    add: int


# class CustomRPGUpgradeGroup_Weapon:
#     def __init__(
#         self,
#         avaliable_materials: dict[str, int],
#         upgrade_exp_syntax: str,
#         extra_materials_when_spec_level: dict[str, dict[str, int]],
#         upgrade_syntax: str,
#         max_level: int,
#     ):
#         self.avaliable_materials = avaliable_materials
#         self.upgrade_exp_syntax = compile(upgrade_exp_syntax, "None", "eval")
#         self.extra_materials = extra_materials_when_spec_level
#         self.upgrade_syntax = compile(upgrade_syntax, "None", "eval")
#         self.max_level = max_level


# class CustomRPGUpgradeGroup_Relic:
#     def __init__(
#         self,
#         avaliable_materials: dict[str, int],
#         upgrade_exp_syntax: str,
#         extra_materials_when_spec_level: dict[str, dict[str, int]],
#         main_prop_syntax: dict[str, float],
#         sub_prop_syntax: dict[str, float],
#         max_level: int,
#         sub_props_change_when_level: list[int],
#     ):
#         assert main_prop_syntax, "main prop syntax can't be empty"
#         assert sub_prop_syntax, "sub prop syntax can't be empty"
#         self.avaliable_materials = avaliable_materials
#         self.upgrade_exp_syntax = compile(upgrade_exp_syntax, "None", "eval")
#         self.extra_materials = extra_materials_when_spec_level
#         self.main_prop_syntax = {
#             k: UpgradePropMode(v) for k, v in main_prop_syntax.items()
#         }
#         self.sub_prop_syntax = {
#             k: UpgradePropMode(v) for k, v in sub_prop_syntax.items()
#         }
#         self.max_level = max_level
#         self.sub_props_change_when_level = sub_props_change_when_level


def replace_chars_with_white(n: str):
    for i in "0123456789abcdefghijklmnopqrstu":
        n = n.replace("§" + i, "")
    return n


class CustomRPGUpgrade(Plugin):
    version = (0, 0, 1)
    author = "SuperScript"
    name = "自定义RPG-升级系统"

    event_apis = event_apis

    WeaponUpgradeConfig = WeaponUpgradeConfig
    RelicUpgradeConfig = RelicUpgradeConfig

    def __init__(self, frame):
        super().__init__(frame)
        self.print_inf("§b自定义RPG-升级系统 已加载.")
        self.print_inf(
            "§b想要为你的租赁服量身定制各种提示文本, 可以找SuperScript QQ:2528622340"  # ??
        )
        CFG_STD = {
            "玩家升级所需经验值的计算公式": str,
            "玩家晋阶时执行的指令": cfg.JsonList(str),
            "饰品可用定向升级材料": cfg.AnyKeyValue(
                {"属性": str, "最小权重": float, "最大权重": float}
            ),
        }
        CFG_DEFAULT = {
            "玩家升级所需经验值的计算公式": "500+玩家等级*40",
            "玩家晋阶时执行的指令": [
                '/tellraw @a {"rawtext":[{"text": "§7玩家§f[玩家名]§7等级提升至§e[等级]§7级!"}]}',
                "/title [玩家名] title §a世界等级: [等级]\n§a\n§a\n§a",
            ],
        }
        self.cfg, _ = cfg.get_plugin_config_and_version(
            self.name, CFG_STD, CFG_DEFAULT, self.version
        )
        self.direct_ups: dict[str, DirectUpgrade] = {}
        try:
            for k, v in self.cfg["饰品可用定向升级材料"].items():
                self.direct_ups[k] = DirectUpgrade(k, v["属性"], v["概率增益"])
            self.player_levelup = compile(
                self.cfg["玩家升级所需经验值的计算公式"], "None", "eval"
            )
        except SyntaxError:
            self.print_err("自定义RPG-升级系统: 计算公式不合法")
            raise SystemExit
        self.ListenPreload(self.on_def)

    def on_def(self):
        self.rpg = self.GetPluginAPI("自定义RPG")
        self.menu = self.GetPluginAPI("聊天栏菜单", (0, 0, 1))
        self.funclib = self.GetPluginAPI("基本插件功能库", (0, 0, 2))
        self.bigchar = self.GetPluginAPI("大字替换")
        self.snowmenu = self.GetPluginAPI("雪球菜单v3")
        cb2bot = self.GetPluginAPI("Cb2Bot通信")
        if TYPE_CHECKING:
            global SlotItem, Item, ItemWeapon, ItemRelic
            from ..自定义RPG import CustomRPG, ItemRelic, ItemWeapon
            from ..前置_聊天栏菜单 import ChatbarMenu
            from ..前置_基本插件功能库 import BasicFunctionLib
            from ..前置_大字替换 import BigCharReplace
            from ..前置_Cb2Bot通信 import TellrawCb2Bot
            from ..虚拟背包 import SlotItem, Item
            from ..雪球菜单v3 import SnowMenuV3

            self.rpg: CustomRPG
            self.menu: ChatbarMenu
            self.funclib: BasicFunctionLib
            self.bigchar: BigCharReplace
            self.snowmenu: SnowMenuV3
            cb2bot: TellrawCb2Bot
        cb2bot.regist_message_cb(
            "sr.anvil.upgrade", lambda x: self.choose_upgrade(self.rpg.getPlayer(x[0]))
        )
        # tellraw @a[tag=sr.rpg_bot] {"rawtext":[{"text":"sr.anvil.upgrade"},{"selector":"@p"}]}

    @utils.thread_func("选择升级样式")
    def choose_upgrade(self, player: Player):
        def _cb(_, page: int):
            if page > 2:
                return None
            return (
                "§d✳ §6升级选项选择 §7>>\n"
                f"§{'b' if page == 0 else '7'}> 升级武器  §{'b' if page == 1 else '7'}> 升级饰品  §{'b' if page == 2 else '7'}> 退出"
            )

        match self.snowmenu.simple_select(player, _cb):
            case 0:
                self.upgrade_weapon(player)
            case 1:
                self.upgrade_relic(player)
            case 2:
                return

    def make_inited_relic_metadata(self, item: "Item", mainprops_num=1, subprops_num=5):
        "初始化饰品信息, 随机词条(默认5条)"
        upgrade_config = self.rpg.find_relic_class(item.id).upgrade_mode
        if upgrade_config is None:
            raise ValueError(f"无法从配置文件找到升级样式: {item.id}")
        main_props_keys: list[str] = []
        main_props_weights: list[float] = []
        sub_props_keys: list[str] = []
        sub_props_weights: list[float] = []
        metadata: dict[str, Any] = {"Main": {}, "Sub": {}}

        # 初始化主词条
        for k, w in upgrade_config.main_props_weight.items():
            main_props_keys.append(k)
            main_props_weights.append(w)
        props = random.choices(
            main_props_keys, k=mainprops_num, weights=main_props_weights
        )
        for prop in props:
            metadata["Main"][prop] = 1
        # 初始化副词条
        for k, w in upgrade_config.sub_props_weight.items():
            sub_props_keys.append(k)
            sub_props_weights.append(w)
        props: list[str] = []
        while len(props) < subprops_num:
            c = random.choices(
                list(range(len(sub_props_keys))), k=1, weights=sub_props_weights
            )[0]
            props.append(sub_props_keys[c])
            sub_props_keys.pop(c)
            sub_props_weights.pop(c)
        for prop in props:
            metadata["Sub"][prop] = 1
        return metadata

    def on_upgrade_weapon(self, player: Player):
        self.upgrade_weapon(player)
        self.rpg.player_holder.update_property_from_basic(
            self.rpg.player_holder.get_player_basic(player),
            self.rpg.player_holder.get_playerinfo(player),
        )

    def on_upgrade_relic(self, player: Player):
        self.upgrade_relic(player)
        self.rpg.player_holder.update_property_from_basic(
            self.rpg.player_holder.get_player_basic(player),
            self.rpg.player_holder.get_playerinfo(player),
        )

    def upgrade_weapon(self, player: Player) -> None:
        rpg = self.rpg
        constants = rpg.constants
        rpg.player_holder.dump_mainhand_weapon_datas_to_slotitem(
            rpg.player_holder.get_playerinfo(player)
        )
        storlist = rpg.backpack_holder.list_player_store_with_filter(
            player, [constants.Category.SWORD, constants.Category.BOW]
        )
        if storlist:
            section = rpg.snowmenu_gui.check_items(
                player, storlist, "§7§l[§6■§7] §r§6请选择待升级的武器\n"
            )
            if section is None:
                rpg.show_fail(player, "选项被取消， 已退出")
                return
        else:
            rpg.show_fail(player, "背包内没有任何可升级的武器..")
            return
        # 选择了需要升级的物品
        item_orig = section
        item_weapon = rpg.ItemWeapon.load_from_item(item_orig)
        upgrade_cofig = rpg.find_weapon_class(item_orig.item.id).upgrade_mode
        if upgrade_cofig is None:
            rpg.show_warn(
                player,
                f"§c该物品的组类 ({item_orig.item.categories[0]}) 无对应升级方式， 请告知管理",
            )
            return
        # 选择了用于升级的材料
        materials_select: list["SlotItem"] = []
        update_avaliable_materials = upgrade_cofig.available_upgrade_materials.keys()
        for i in update_avaliable_materials:
            res = rpg.backpack_holder.getItems(player, i)
            if res is not None:
                materials_select.append(res[0])
        exp_proved = {
            i: upgrade_cofig.available_upgrade_materials[i.item.id]
            for i in materials_select
        }
        # 如果暂时不需要特殊晋级物品
        spec_update_items = self.check_spec_item_upgrade(
            upgrade_cofig, item_weapon.level
        )
        if materials_select == []:
            rpg.show_fail(player, "你没有可用于升级此武器的材料")
            rpg.show_any(player, "6", "推荐材料：")
            for material, exp in upgrade_cofig.available_upgrade_materials.items():
                item = rpg.item_holder.getOrigItem(material)
                rpg.show_any(player, "6", f"  {item.disp_name}")
            return
        if item_weapon.level >= upgrade_cofig.max_level:
            rpg.show_fail(player, "该物品已达到最大等级")
            return
        if spec_update_items is None:
            material = rpg.snowmenu_gui.check_items(
                player,
                materials_select,
                "§7§l[§6■§7] §r§6选择一份升级材料以用于升级\n",
                lambda x: f"• {x.disp_name}§r§7x§f{x.count} §7+§f{exp_proved[x]}§eExp",
            )
            if material is None:
                if material is None:
                    rpg.show_fail(player, "选项被取消， 已退出")
                    return
            material_count_left = material.count
            # 开始升级
            while 1:
                output_text = ""
                material_count = 0
                # 用于展示升级前后的物品
                item_weapon_upgrade_fake = rpg.ItemWeapon.load_from_item(
                    item_orig.orig_copy()
                )
                while 1:
                    # 单次循环使用1个材料提供经验值
                    # 直到物品消耗完或者等级无法再提升
                    breakMode = False
                    if material_count_left <= 0:
                        break
                    material_count_left -= 1
                    material_count += 1
                    # 升级后的经验值
                    exp_boost = (
                        item_weapon_upgrade_fake.exp
                        + upgrade_cofig.available_upgrade_materials[material.item.id]
                    )
                    while 1:
                        # 检测经验增加后等级是否可以晋阶
                        # 晋阶导需要特殊物品晋阶时即停止
                        # 或者等级达到最大值时停止
                        upgrade_need_exp_fake = upgrade_cofig.upgrade_exp_syntax(
                            item_weapon_upgrade_fake.level
                        )
                        if exp_boost < upgrade_need_exp_fake:
                            break
                        if self.check_spec_item_upgrade(
                            upgrade_cofig, item_weapon_upgrade_fake.level
                        ) is not None or (
                            item_weapon_upgrade_fake.level >= upgrade_cofig.max_level
                        ):
                            breakMode = True
                            break
                        item_weapon_upgrade_fake.level += 1
                        exp_boost -= upgrade_need_exp_fake
                    item_weapon_upgrade_fake.exp = min(exp_boost, upgrade_need_exp_fake)
                    if breakMode:
                        break
                item_upgrade_fake = self.update_weapon_by_level(
                    item_weapon_upgrade_fake
                )
                output_text += f"{item_orig.disp_name}§r §7Lv.§f{self.bigchar.replaceBig(str(item_weapon.level))} §7> §fLv.§e{self.bigchar.replaceBig(str(item_weapon_upgrade_fake.level))}"
                output_text += self.format_weapon_data_compared(
                    item_weapon, item_weapon_upgrade_fake, upgrade_need_exp_fake
                )
                output_text += (
                    f"\n§7目前将使用§f{material_count}§7份材料进行升级\n"
                    "扔雪球选择: §%s确定升级 §%s取消 §%s更改花费的材料数量\n§a\n§a"
                )

                def _menu_section(_, page: int):
                    if page > 2:
                        return None
                    return output_text % tuple(("b77", "7b7", "77b")[page])

                resp = self.snowmenu.simple_select(player, _menu_section)
                if resp is None:
                    rpg.show_fail(player, "已取消升级.")
                    return
                if resp == 0:
                    # 升级物品
                    rpg.backpack_holder.removePlayerStore(
                        player, material, material_count
                    )
                    rpg.backpack_holder.removePlayerStore(player, item_orig, 1)
                    rpg.backpack_holder.addPlayerStore(
                        player, item_upgrade_fake.dump_item()
                    )
                    rpg.show_succ(player, f"{item_orig.disp_name} §a升级成功")
                    self.game_ctrl.sendwocmd(
                        f"/execute as {player.safe_name} run playsound random.levelup @s"
                    )
                    item_name_disp = (
                        item_upgrade_fake.slotItem.disp_name + " §a升级完成"
                    )
                    for i in range(len(item_name_disp)):
                        if item_name_disp[i] == "§":
                            continue
                        n_name = (
                            item_name_disp[: i + 1]
                            + "§r"
                            + replace_chars_with_white(item_name_disp[i + 1 :])
                        )
                        player.setActionbar(n_name)
                        time.sleep(0.2)
                    self.BroadcastEvent(
                        event_apis.PlayerUpgradeObjectEvent(
                            player, item_orig
                        ).to_broadcast()
                    )
                    break
                elif resp == 2:
                    while 1:
                        player.show("§7请重新输入§f花费材料的数量§7:")
                        resp = utils.try_int(player.input())
                        if resp is None or resp == 0:
                            rpg.show_fail(player, "无效选项, 已退出")
                            return
                        else:
                            if resp < 0 or resp > material.count:
                                rpg.show_fail(player, "你没有这么多材料")
                            else:
                                material_count_left = resp
                                break
                elif resp == 1:
                    rpg.show_inf(player, "已取消升级.")
                    return
                else:
                    rpg.show_fail(player, "无效选项, 已退出")
                    return
        else:
            # 需要特殊物品
            need_items = {}
            enable_to_upgrade = True
            output_text = ""
            for tag_name, count in spec_update_items.items():
                _player_have = rpg.backpack_holder.getItems(player, tag_name)
                starlevel_text = rpg.item_holder.make_item_starlevel(tag_name)
                if _player_have is None:
                    _player_have = 0
                else:
                    _player_have = _player_have[0].count
                need_items[rpg.item_holder.getOrigItem(tag_name).disp_name] = [
                    starlevel_text,
                    count,
                    _player_have,
                ]
            output_text += (
                f"{item_weapon.slotItem.disp_name}§r§7已达到当前最大等级, 需要晋阶材料:"
            )
            for itemshowname, (
                starlevel_text,
                count_need,
                player_have,
            ) in need_items.items():
                if count_need > player_have:
                    color_chr = "§c"
                    enable_to_upgrade = False
                else:
                    color_chr = "§f"
                output_text += f"\n - {itemshowname}§r {starlevel_text} {color_chr}{player_have}§f/{count_need}"
            if not enable_to_upgrade:
                output_text += "\n§7[§cx§7]§c 材料不足， 无法晋阶 §f| §c抬头/低头以退出"
                self.snowmenu.simple_select_dict(player, {0: output_text})
                return
            output_text += "\n§a抬头确认 §f| §c低头退出"
            if self.snowmenu.simple_select_dict(player, {0: output_text}) is None:
                rpg.show_fail(player, "已取消晋阶操作.")
                return
            for tag_name, count in spec_update_items.items():
                material_item = rpg.backpack_holder.getItems(player, tag_name)
                # dangerous: must stackable
                assert material_item, (
                    f"material {tag_name}->material can't be None or empty"
                )
                rpg.backpack_holder.removePlayerStore(player, material_item[0], count)
            rpg.backpack_holder.removePlayerStore(player, item_orig, 1)
            item_orig.metadata["Lv"] += 1
            rpg.backpack_holder.addPlayerStore(player, item_orig)
            self.game_ctrl.sendwocmd(
                f"/execute as {player.safe_name} run playsound random.levelup @s"
            )
            rpg.show_succ(player, "物品晋阶成功， 可以继续升级")

    def upgrade_relic(self, player: Player) -> None:
        rpg = self.rpg
        constants = rpg.constants
        storlist = rpg.backpack_holder.list_player_store_with_filter(
            player,
            [
                constants.HiddenCategory.HELMET,
                constants.HiddenCategory.CHESTPLATE,
                constants.HiddenCategory.LEGGINGS,
                constants.HiddenCategory.BOOTS,
                constants.HiddenCategory.RELICA,
                constants.HiddenCategory.RELICB,
                constants.HiddenCategory.RELICC,
                constants.HiddenCategory.RELICD,
            ],
        )
        if storlist:
            section = rpg.snowmenu_gui.check_items(
                player,
                storlist,
                "§7§l[§6■§7] §r§6请选择待升级的物品\n",
                lambda x: "- " + x.disp_name + f" §r§f<Lv.§e{x.metadata['Lv']}§f>",
            )
            if section is None:
                self.rpg.show_fail(player, "选项被取消， 已退出")
                return
        else:
            self.rpg.show_fail(player, "背包内没有任何可升级的饰品..")
            return
        # 选择了需要升级的物品
        item_orig = section
        item_relic = self.rpg.ItemRelic.load_from_item(item_orig)
        # upgrade_mode = self.relic_update.get(item_orig.item.categories[0])
        upgrade_cofig = self.rpg.find_relic_class(item_orig.item.id).upgrade_mode
        if upgrade_cofig is None:
            self.rpg.show_warn(
                player,
                f"§c该物品的组类 ({item_orig.item.categories[0]}) 无对应升级方式， 请告知管理",
            )
            return
        if item_relic.level >= upgrade_cofig.max_level:
            self.rpg.show_fail(player, "该物品已达到最大等级")
            return
        # 选择了用于升级的材料
        materials_select: list["SlotItem"] = []
        update_avaliable_materials = upgrade_cofig.available_upgrade_materials.keys()
        for i in update_avaliable_materials:
            res = self.rpg.backpack_holder.getItems(player, i)
            if res is not None:
                materials_select.append(res[0])
        exp_proved = {
            i: upgrade_cofig.available_upgrade_materials[i.item.id]
            for i in materials_select
        }
        # 如果暂时不需要特殊晋级物品
        spec_update_items = self.check_spec_item_upgrade(
            upgrade_cofig, item_relic.level
        )
        if materials_select == []:
            rpg.show_fail(player, "你没有可用于升级此饰品的物品")
            rpg.show_any(player, "6", "推荐材料：")
            for material, exp in upgrade_cofig.available_upgrade_materials.items():
                item = self.rpg.item_holder.getOrigItem(material)
                self.rpg.show_any(player, "6", f"  {item.disp_name}")
            return
        if spec_update_items is None:
            material = rpg.snowmenu_gui.check_items(
                player,
                materials_select,
                "§7§l[§6■§7] §r§6选择一份升级材料以用于升级\n",
                lambda x: f"• {x.disp_name}§r§7x§f{x.count} §7+§f{exp_proved[x]}§eExp",
            )
            if material is None:
                if material is None:
                    rpg.show_fail(player, "选项被取消， 已退出")
                    return
            material_count_left = material.count
            # 开始升级
            # 统计各词条升级次数
            subprops_upgrade_total = {}
            while 1:
                material_count = 0
                upgrade_need_exp_fake = 0
                item_relic_upgrade_fake = self.rpg.ItemRelic.load_from_item(
                    item_orig.copy()
                )
                output_text = ""
                # 额外材料
                extra_mateterials: tuple["Item", int] | None = None
                while 1:
                    # 使用1个材料提供经验值
                    breakMode = False
                    if material_count_left <= 0:
                        break
                    material_count_left -= 1
                    material_count += 1
                    exp_boost = (
                        item_relic_upgrade_fake.exp
                        + upgrade_cofig.available_upgrade_materials[material.item.id]
                    )
                    while 1:
                        # 检测经验增加后等级是否可以晋阶
                        upgrade_need_exp_fake = upgrade_cofig.upgrade_exp_syntax(
                            item_relic_upgrade_fake.level
                        )
                        if exp_boost < upgrade_need_exp_fake:
                            break
                        if self.check_spec_item_upgrade(
                            upgrade_cofig, item_relic_upgrade_fake.level
                        ) is not None or (
                            item_relic_upgrade_fake.level >= upgrade_cofig.max_level
                        ):
                            breakMode = True
                            break
                        item_relic_upgrade_fake.level += 1
                        item_relic_upgrade_fake, upgrade_subprops = (
                            self.relic_upgrade_once(
                                item_relic_upgrade_fake,
                                upgrade_cofig,
                                extra_mateterials,
                            )
                        )
                        if upgrade_subprops:
                            subprops_upgrade_total[upgrade_subprops] = (
                                subprops_upgrade_total.get(upgrade_subprops, 0) + 1
                            )
                        exp_boost -= upgrade_need_exp_fake
                    item_relic_upgrade_fake.exp = min(exp_boost, upgrade_need_exp_fake)
                    if breakMode:
                        break
                output_text += f"饰品升级： §7Lv.§f{self.bigchar.replaceBig(str(item_relic.level))} §7> §fLv.§e{self.bigchar.replaceBig(str(item_relic_upgrade_fake.level))}"
                output_text += f"\n§e经验值 {self.make_progress_bar(20, upgrade_need_exp_fake, item_relic_upgrade_fake.exp)} §f{item_relic_upgrade_fake.exp}§7/{upgrade_need_exp_fake}\n"
                output_text += (
                    f"\n§7目前将使用§f{material_count}§7份材料进行升级\n"
                    "扔雪球选择: §%s确定升级 §%s取消\n§%s更改花费的材料数量 §%s使用/切换定向强化材料"
                )

                def _menu_section(_, page: int):
                    if page > 3:
                        return None
                    return output_text % tuple(("b777", "7b77", "77b7", "777b")[page])

                resp = self.snowmenu.simple_select(player, _menu_section)
                if resp is None:
                    rpg.show_fail(player, "已取消升级.")
                    return
                if resp is None:
                    rpg.show_fail(player, "选项超时, 已退出")
                    return
                if resp == 0:
                    rpg.backpack_holder.removePlayerStore(
                        player, material, material_count
                    )
                    rpg.backpack_holder.removePlayerStore(player, item_orig, 1)
                    rpg.backpack_holder.addPlayerStore(
                        player, item_relic_upgrade_fake.dump_item()
                    )
                    rpg.show_succ(
                        player,
                        f"{item_relic_upgrade_fake.slotItem.disp_name} §r§a升级成功",
                    )
                    player.show(
                        self.format_relic_data_compared(
                            item_relic,
                            item_relic_upgrade_fake,
                            upgrade_need_exp_fake,
                            subprops_upgrade_total,
                        ),
                    )
                    self.game_ctrl.sendwocmd(
                        f"/execute as {player.safe_name} run playsound random.levelup @s"
                    )
                    item_name_disp = (
                        item_relic_upgrade_fake.slotItem.disp_name + " §a升级完成"
                    )
                    for i in range(len(item_name_disp)):
                        if item_name_disp[i] == "§":
                            continue
                        n_name = (
                            item_name_disp[: i + 1]
                            + "§r§7"
                            + replace_chars_with_white(item_name_disp[i + 1 :])
                        )
                        player.setActionbar(n_name)
                        time.sleep(0.1)
                    self.BroadcastEvent(
                        event_apis.PlayerUpgradeObjectEvent(
                            player, item_orig
                        ).to_broadcast()
                    )
                    break
                elif resp == 1:
                    rpg.show_inf(player, "已取消升级")
                    return
                elif resp == 2:
                    while 1:
                        player.show("§7请重新输入§f花费材料的数量§7:")
                        resp = utils.try_int(player.input())
                        if resp is None or resp == 0:
                            rpg.show_fail(player, "需要输入纯数字")
                        else:
                            if resp < 0 or resp > material.count:
                                rpg.show_fail(player, "你没有这么多材料")
                            else:
                                material_count_left = resp
                                rpg.show_succ(player, "设定成功， 请退出聊天栏")
                                break
                elif resp == 3:
                    # 材料id: 属性
                    bp_sys = rpg.backpack
                    # 允许使用的属性
                    allowed_direct_props = upgrade_cofig.sub_props_weight.keys()
                    # 允许使用的模式
                    allowed_direct_modes = [
                        i
                        for i in self.direct_ups.values()
                        if i.prop in allowed_direct_props
                    ]
                    # 允许使用的物品
                    allowed_direct_items: list["SlotItem"] = []
                    for i in allowed_direct_modes:
                        if getting_item := bp_sys.get_registed_item(i.item_id):
                            allowed_direct_items.append(
                                SlotItem(
                                    getting_item,
                                    rpg.backpack_holder.getItemCount(
                                        player, getting_item.id
                                    ),
                                )
                            )
                    while 1:
                        item_selected = rpg.snowmenu_gui.check_items(
                            player,
                            allowed_direct_items,
                            "§7§l[§6■§7] §r§6请选择定向升级材料§f\n",
                            lambda x: (" > " if x.count > 0 else " > §7")
                            + x.disp_name
                            + f" §e({self.direct_ups[x.item.id].prop})§r"
                            + " §6(你没有该物品)"
                            if x.count
                            else "",
                        )
                        if item_selected is None:
                            rpg.show_fail(player, "已退出")
                            return
                        if item_selected.count < 1:
                            rpg.show_fail(player, "你没有该物品")
                            continue
                        break
                    while 1:
                        resp = self.funclib.waitMsg_with_actbar(
                            player.name,
                            f"§7§l[§6!§7] §r§6请在聊天栏输入使用 {item_selected.item.id} §6的数量",
                        )
                        if (num := utils.try_int(resp)) is not None:
                            if num <= 0:
                                rpg.show_warn(
                                    player, "使用材料的数量必须大于0, 请重新输入"
                                )
                            elif num > item_selected.count:
                                rpg.show_warn(
                                    player,
                                    f"你只有 {item_selected.count} 个该种材料， 请重新输入",
                                )
                            else:
                                _num = num
                                break
                        else:
                            rpg.show_warn(player, "请重新输入纯数字")
                    extra_mateterials = (item_selected.item, _num)
                    rpg.show_succ(
                        player,
                        f"已选定升级材料 {item_selected.disp_name}§r§ex{num}§a， 请退出聊天栏",
                    )
            return
        else:
            need_items = {}
            enable_to_upgrade = True
            for tag_name, count in spec_update_items.items():
                _player_have = self.rpg.backpack_holder.getItems(player, tag_name)
                starlevel_text = self.rpg.item_holder.make_item_starlevel(tag_name)
                if _player_have is None:
                    _player_have = 0
                else:
                    # TODO: 对于不可堆叠的物品, 这样做会出问题
                    _player_have = _player_have[0].count
                need_items[self.rpg.item_holder.getOrigItem(tag_name).disp_name] = [
                    starlevel_text,
                    count,
                    _player_have,
                ]
            self.rpg.show_inf(
                player,
                f"{item_relic.slotItem.disp_name}§r§7已达到当前最大等级, 需要晋阶材料:",
            )
            for itemshowname, (
                starlevel_text,
                count_need,
                player_have,
            ) in need_items.items():
                if count_need > player_have:
                    color_chr = "§c"
                    enable_to_upgrade = False
                else:
                    color_chr = "§f"
                player.show(
                    f" - {itemshowname}§r {starlevel_text} {color_chr}{player_have}§f/{count_need}",
                )
            if not enable_to_upgrade:
                self.rpg.show_fail(player, "材料不足， 无法晋阶")
                return
            player.show("§7输入§a[Y]确定晋阶 §c[N]取消:")
            resp = player.input()
            if resp not in ["Y", "y", "N", "n"]:
                self.rpg.show_fail(player, "无效选项， 已退出")
                return
            elif resp is None:
                self.rpg.show_fail(player, "选项超时， 已退出")
                return
            elif resp.replace("y", "Y") == "Y":
                for tag_name, count in spec_update_items.items():
                    material_item = self.rpg.backpack_holder.getItems(player, tag_name)
                    assert material_item, "material can't be None"
                    self.rpg.backpack_holder.removePlayerStore(
                        player, material_item[0], count
                    )
                self.rpg.backpack_holder.removePlayerStore(player, item_orig, 1)
                item_orig.metadata["Lv"] += 1
                self.rpg.backpack_holder.addPlayerStore(player, item_orig)
                self.game_ctrl.sendwocmd(
                    f"/execute as {player.safe_name} run playsound random.levelup @s"
                )
                self.rpg.show_succ(player, "物品晋阶成功， 可以继续升级")
                return
            else:
                self.rpg.show_inf(player, "已取消晋阶.")
                return

    def make_progress_bar(self, long: int, total: int, current: int):
        act = round(current / total * long)
        char = "="
        return "§a§l" + char * act + "§7" + char * (long - act) + "§r"

    def calc(self, cmp: CodeType, variables: dict):
        variables.update({"取整": int, "四舍五入": round})
        try:
            return int(eval(cmp, variables))
        except NameError as err:
            self.game_ctrl.say_to("@a", "§4插件 自定义RPG 出现问题：")
            self.game_ctrl.say_to(
                "@a", f"§c公式中的变量 {err.name} 不可用， 请将此条信息发送至管理员"
            )
            raise SystemExit

    def update_weapon_by_level(
        self,
        item: "ItemWeapon",
    ):
        weapon = self.rpg.find_weapon_class(item.slotItem.item.id)
        upgrade_mode = weapon.upgrade_mode
        if upgrade_mode is None:
            return item
        item_level = item.level
        item.atks = [
            upgrade_mode.upgrade_value_syntax(atk, item_level)
            for atk in weapon.basic_atks
        ]
        return item

    def relic_upgrade_once(
        self,
        item: "ItemRelic",
        upgrade_mode: RelicUpgradeConfig,
        ext_add: tuple["SlotItem", int] | None,
    ):
        """饰品升级一级
        Args:
            ext_add (tuple[str, int] | None): 额外强化材料, 数量
        """
        # 主词条照样升级
        prop_to_upgrade = random.choice(list(item.main_props.keys()))
        prop_info = upgrade_mode.main_props_weight.get(prop_to_upgrade)
        if prop_info is None:
            raise ValueError(f"无法读取主属性 {prop_to_upgrade} 因为其不在配置中")
        item.main_props[prop_to_upgrade] += 1
        # 给定等级升级副词条
        if item.level in upgrade_mode.sub_prop_levels:
            # 副词条, 升级最小值, 升级最大值
            former_props = list(item.sub_props.keys())
            # 只对原有的副词条进行升级
            props_weight = [1 / len(former_props)] * len(former_props)
            if ext_add is not None:
                ext_item, count = ext_add
                # 如果是定向升级
                # 那么就加大该词条权重
                avali_up = self.direct_ups[ext_item.item.id]
                i = former_props.index(avali_up.prop)
                props_weight[i] += avali_up.add * count
            prop_to_upgrade = random.choices(former_props, weights=props_weight)[0]
            prop_info = upgrade_mode.sub_props_weight.get(prop_to_upgrade)
            if prop_info is None:
                raise ValueError(f"无法读取副属性 {prop_to_upgrade} 因为其不在配置中")
            item.sub_props[prop_to_upgrade] = item.sub_props.get(prop_to_upgrade, 0) + 1
            return item, prop_to_upgrade
        else:
            return item, None

    def format_weapon_data_compared(
        self, item: "ItemWeapon", new_item: "ItemWeapon", total_exp
    ):
        assert item.__class__ == new_item.__class__
        elements = [self.rpg.elements[i] for i in self.rpg.Types.AllElemTypes]
        output_text = f"\n§e|§8 §e经验值 {self.make_progress_bar(20, total_exp, item.exp)} §f{new_item.exp}§7/{total_exp}"
        for index, (val, val2) in enumerate(zip(item.atks, new_item.atks)):
            if val2 > val:
                output_text += f"\n§c|§8 - {elements[index][:2]}⚔ §f{val} §7> §a{val2} {'§6[New!]' if val == 0 else ''}"
            elif val2 < val:
                output_text += f"\n§c|§8 - {elements[index]}攻击 §f{val} §7> §c{val2}"
        return output_text

    def format_relic_data_compared(
        self,
        item: "ItemRelic",
        new_item: "ItemRelic",
        total_exp: int,
        upgrade_subprops: dict[str, int],
    ):
        assert item.__class__ == new_item.__class__
        prop_formatter = self.rpg.formatter.format_prop

        def _format(prop: str, level: int):
            return prop_formatter(self.rpg, prop, level)

        output_text = f"§e|§8 §e经验值 {self.make_progress_bar(20, total_exp, new_item.exp)} §f{new_item.exp}§7/{total_exp}\n"
        cached_text = []
        # TODO: 写死的七元素属性
        for main_prop, level_2 in new_item.main_props.items():
            level = item.main_props.get(main_prop, 0)
            prop_showname, level_str = _format(main_prop, level)
            _, level_2_str = _format(main_prop, level_2)
            if level_2 > level:
                cached_text.insert(
                    0,
                    f"§6|§8 §e§lMain§r {prop_showname} §f{level_str} §7> §a{level_2_str}{' §6[New!]' if level == 0 else ''}",
                )
            elif level_2 < level:
                cached_text.insert(
                    0,
                    f"§6|§8 §e§lMain§r {prop_showname} §f{level_str} §7> §c{level_2_str}",
                )
        for sub_prop, level_2 in new_item.sub_props.items():
            level = item.sub_props.get(sub_prop, 0)
            prop_showname, level_str = _format(sub_prop, level)
            _, level_2_str = _format(sub_prop, level_2)
            if level_2 > level:
                cached_text.append(
                    f"§6|§8 - {prop_showname} §f{level_str} §7> §a{level_2_str} {'§6[New!]' if level == 0 else ''}{f' §b({upgrade_subprops[sub_prop]})'}"
                )
            elif level_2 < level:
                cached_text.append(
                    f"§6|§8 - {prop_showname} §f{level_str} §7> §c{level_2_str}"
                )
        output_text += "\n".join(cached_text)
        return output_text

    def check_spec_item_upgrade(
        self, rule: WeaponUpgradeConfig | RelicUpgradeConfig, level
    ):
        spec_item = rule.upgrade_level_limit_materials
        if level in spec_item.keys():
            return spec_item[level]
        else:
            return None

    def add_player_exp(self, player: Player, exp: int):
        dat_now = self.rpg.player_holder.get_player_basic(player)
        now_exp = dat_now.Exp
        now_lv = dat_now.Level
        now_exp += exp
        while 1:
            levelup_exp = self.get_levelup_exp(dat_now)
            if now_exp >= levelup_exp:
                now_lv += 1
                now_exp -= levelup_exp
                for cmd in self.cfg["玩家晋阶时执行的指令"]:
                    self.game_ctrl.sendwocmd(
                        utils.simple_fmt(
                            {"[玩家名]": player.name, "[等级]": now_lv}, cmd
                        )
                    )
                    self.game_ctrl.sendwocmd(f"xp -10000L {player.safe_name}")
                    self.game_ctrl.sendwocmd(f"xp {now_lv}L {player.safe_name}")
            else:
                break
            time.sleep(0.05)
        dat_now.Exp = now_exp
        dat_now.Level = now_lv

    def get_levelup_exp(self, player_basic_dat):
        return self.calc(self.player_levelup, {"玩家等级": player_basic_dat.Level})


entry = plugin_entry(CustomRPGUpgrade, "自定义RPG-升级系统")

from typing import TYPE_CHECKING

import os
from .rpg_lib import constants, default_cfg, formatter, utils as rpg_utils
from .rpg_lib.frame_objects import (
    get_registered_weapons,
    get_registered_relics,
    find_weapon_class,
    Weapon,
    Relic,
)
from .rpg_lib.utils import render_bar, split_by_display_len, int_time


if TYPE_CHECKING:
    from . import CustomRPG, SlotItem, Item


class ItemHolder:
    def __init__(self, sys: "CustomRPG"):
        self.sys = sys
        self.backpack = sys.backpack

    def init(self):
        (
            self.loaded_weapons,
            self.loaded_relics,
            self.loaded_materials,
            self.items_starlevel,
        ) = self.load_items()

    def get_weapon_minimal_description(self, weapon_item: "SlotItem"):
        weapon_clss = get_registered_weapons()
        cls = weapon_clss.get(weapon_item.item.id)
        if cls is None:
            return f"§c无法找到关于武器 <{weapon_item.item.id}> 的描述"
        output = (
            self.sys.bigchar.replaceBig("$Lv. !" + str(weapon_item.metadata["Lv"]))
            .replace("$", "§7")
            .replace("!", "§f")
        )
        atks = []
        for i, elem in enumerate(self.sys.Types.AllElemTypes):
            atk = cls.basic_atks[i]
            color = self.sys.element_colors[elem]
            if atk > 0:
                atks.append(f"{color}{atk}")
        output += (
            "\n§4攻击力： "
            + " §f/ ".join(atks)
            + f"\n§c击杀数： {weapon_item.metadata.get('KC', 0)}"
        )
        durability = weapon_item.metadata["DBL"]
        max_durability = cls.default_durability
        durability_pc = durability / max_durability
        dur_color = (
            "§a"
            if durability_pc >= 0.6
            else (
                "§2"
                if durability_pc >= 0.4
                else ("§e" if durability_pc >= 0.25 else "§c")
            )
        )
        return output + (
            "\n§6耐久： "
            + render_bar(durability, max_durability, dur_color, "§8")
            + f"  §7(§f{durability}§7/{max_durability})"
        )

    # 注册物品
    def load_items(self):
        loaded_weapons: dict[str, "Item"] = {}
        loaded_relics: dict[str, "Item"] = {}
        loaded_materials: dict[str, "Item"] = {}
        items_starlevel: dict[str, int] = {}

        def get_weapon_description_wrapper(desc: str):
            def _weapon_description_wrapper(weapon: "SlotItem"):
                max_durability = find_weapon_class(weapon.item.id).default_durability
                metadata = weapon.metadata
                atks = metadata["ATKs"]
                lv = metadata["Lv"]
                killcount = metadata.get("KC", 0)
                durability = metadata.get("DBL", max_durability)
                elements = self.sys.elements
                elem_list = self.sys.Types.AllElemTypes
                fmt_element_atks = "\n".join(
                    f"§f +{atks[i]} {elements[elem_list[i]]}攻击"
                    for i in range(len(elem_list))
                    if atks[i] > 0
                )
                progress = durability / max_durability
                if progress > 0.6:
                    dur_color = "§a"
                elif progress > 0.4:
                    dur_color = "§2"
                elif durability > 0.25:
                    dur_color = "§e"
                else:
                    dur_color = "§c"
                durability_bar = render_bar(durability, max_durability, dur_color, "§8")
                return (
                    self.sys.bigchar.replaceBig(f"$Lv.!{lv}")
                    .replace("$", "§7")
                    .replace("!", "§f")
                    + "\n"
                    + fmt_element_atks
                    + f"\n§r§c击杀数： {killcount}\n"
                    f"§r§6耐久： {durability_bar}  §7(§f{durability}§7/{max_durability})\n§7"
                    + desc
                )

            return _weapon_description_wrapper

        def get_relic_name_wrapper(name: str):
            def _relic_name_wrapper(slotitem: "SlotItem"):
                o = f"{name}§r§f<Lv.{slotitem.metadata.get('Lv', '???')}>"
                if slotitem.metadata.get("trash", False):
                    o += "§7<§c☒§7>"
                return o

            return _relic_name_wrapper

        def get_relic_description_wrapper(cls: type[Relic], desc: str):
            suit_2nd_fmt_pre = split_by_display_len(
                "§6二件套： " + cls.suit_2nd_description or "无", 40
            )
            suit_4th_fmt_pre = split_by_display_len(
                "§6四件套： " + cls.suit_4th_description or "无", 40
            )

            def _relic_description_wrapper(weapon: "SlotItem"):
                metadata = weapon.metadata
                lv = metadata["Lv"]
                main_props = metadata["Main"].items()
                sub_props = metadata["Sub"].items()
                fmt_props = ""
                for prop, val in main_props:
                    show_name, level_str = formatter.format_prop(self.sys, prop, val)
                    fmt_props += f"§6|§8 §e§lMain§r {show_name} §f{level_str}\n"
                for prop, val in sub_props:
                    show_name, level_str = formatter.format_prop(self.sys, prop, val)
                    fmt_props += f"§6|§8 - {show_name} {level_str}\n"
                return (
                    self.sys.bigchar.replaceBig(f"$Lv.!{lv}")
                    .replace("$", "§7")
                    .replace("!", "§f")
                    + "\n"
                    + fmt_props
                    + "§r"
                    + "\n        ".join(suit_2nd_fmt_pre)
                    + "\n"
                    + "\n        ".join(suit_4th_fmt_pre)
                    + "\n§7"
                    + desc
                )

            return _relic_description_wrapper

        # 材料物品
        std_cfg = default_cfg.get_material_cfg_standard()
        for filename in os.listdir(self.sys.path_holder.material_cfg_path):
            content = rpg_utils.get_cfg(
                filename, self.sys.path_holder.material_cfg_path / filename, std_cfg
            )
            for tag_name, item_json in content.items():
                category = item_json.get("组类", constants.Category.MATERIAL)
                item = self.sys.backpack.Item(
                    tag_name,
                    item_json["显示名"],
                    [category],
                    description=item_json["描述"],
                    stackable=not tag_name.startswith("$"),
                )
                loaded_materials[tag_name] = item
                items_starlevel[tag_name] = item_json["星级"]
                self.backpack.regist_item(item)
        # 武器
        for weapon_name, weapon_cls in get_registered_weapons().items():
            item = self.sys.backpack.Item(
                weapon_name,
                weapon_cls.show_name,
                [weapon_cls.category.to_category()],
                description=get_weapon_description_wrapper(weapon_cls.description),
                stackable=False,
            )
            loaded_weapons[weapon_name] = item
            items_starlevel[weapon_name] = weapon_cls.star_level
            self.backpack.regist_item(item)
        # 护甲 / 饰品
        for relic_name, relic_cls in get_registered_relics().items():
            item = self.sys.backpack.Item(
                id=relic_name,
                disp_name=get_relic_name_wrapper(relic_cls.show_name),
                categories=[
                    t.to_full_display_category(relic_cls.category)
                    for t in relic_cls.types
                ]
                + [t.to_hidden_category() for t in relic_cls.types],
                stackable=False,
                description=get_relic_description_wrapper(
                    relic_cls, relic_cls.description
                ),
            )
            loaded_relics[relic_name] = item
            items_starlevel[relic_name] = relic_cls.star_level
            self.backpack.regist_item(item)
        return loaded_weapons, loaded_relics, loaded_materials, items_starlevel

    def LoadExtraItem(self, item: "Item", star_level: int):
        self.loaded_materials[item.id] = item
        self.items_starlevel[item.id] = star_level

    # 生成一个或多个物品
    def createItems(
        self, item_tag_name: str, count: int = 1, metadata: dict | None = None
    ):
        res: list["SlotItem"] = []
        if item_tag_name in self.loaded_materials.keys():
            res.append(
                self.sys.backpack.SlotItem(
                    self.get_material_info(item_tag_name),
                    count,
                    metadata=metadata or {},
                )
            )
        elif item_tag_name in self.loaded_weapons.keys():
            if count > 10:
                raise ValueError("单次最多只能给予10个武器类物品")
            wpcls = find_weapon_class(item_tag_name)
            for _ in range(count):
                res.append(
                    self.sys.backpack.SlotItem(
                        self.loaded_weapons[item_tag_name],
                        1,
                        metadata=metadata
                        or {
                            "ATKs": list(wpcls.basic_atks),
                            "LSU": 0,
                            "Chg": 0,
                            "Lv": 1,
                            "Exp": 0,
                            "KC": 0,
                            "DBL": wpcls.default_durability,
                            "Enchs": {},
                        },
                    )
                )
        elif item_tag_name in self.loaded_relics.keys():
            relic_item = self.loaded_relics[item_tag_name]
            if count > 10:
                raise ValueError("单次最多只能给予10个饰品类物品")
            for _ in range(count):
                if metadata is None:
                    new_metadata = self.sys.rpg_upgrade.make_inited_relic_metadata(
                        relic_item
                    )
                    new_metadata.update({"Lv": 1, "Exp": 0})
                    res.append(
                        self.sys.backpack.SlotItem(relic_item, 1, metadata=metadata or new_metadata)
                    )
        else:
            item = self.backpack.get_registed_item(item_tag_name)
            if item is None:
                raise ValueError(f"物品不存在: {item_tag_name}")
            return [self.sys.backpack.SlotItem(item, count)]
        return res

    def createItem(self, tag_name: str, count: int = 1, metadata: dict | None = None):
        items = self.createItems(tag_name, count, metadata)
        if len(items) > 1:
            raise ValueError("无法创建这么多物品, 请改为使用 createItems")
        return items[0]

    # 根据标签名获取原生物品属性类
    def getOrigItem(self, tag_name: str):
        if res := self.loaded_materials.get(tag_name):
            return res
        elif res := self.loaded_weapons.get(tag_name):
            return res
        elif res := self.loaded_relics.get(tag_name):
            return res
        raise ValueError(f"物品标签名不存在: {tag_name}")

    # 根据标签名查找物品的所属种类 (材料/武器/饰品)
    def getItemType(self, tag_name: str):
        if self.loaded_materials.get(tag_name):
            return "Material"
        elif self.loaded_weapons.get(tag_name):
            return "Weapon"
        elif self.loaded_relics.get(tag_name):
            return "Relic"
        else:
            return None

    # 物品是否存在 (被注册)
    def item_exists(self, tag_name: str):
        return (
            tag_name in self.loaded_materials.keys()
            or tag_name in self.loaded_materials.keys()
            or tag_name in self.loaded_relics.keys()
        )

    # 获取物品星级
    def get_item_starlevel(self, tag_name: str):
        ""
        return self.items_starlevel[tag_name]

    def make_item_starlevel(self, item_tag_name: str) -> str:
        return self.sys.star_light * self.get_item_starlevel(item_tag_name)

    # 通过材料标签名获取材料的物品信息
    def get_material_info(self, tag_name: str):
        return self.loaded_materials[tag_name]

    def get_weapon_skill_cd(self, weapon: Weapon):
        return max(0, weapon.skill_use_last + weapon.cd_skill - int_time())

from dataclasses import dataclass


if 0:
    from .rpg_entities import PlayerEntity
    from .. import SlotItem


@dataclass
# 一个中转类, 专门描述一个武器类物品。
class ItemWeapon:
    slotItem: "SlotItem"
    level: int
    exp: int
    killcount: int
    durability: int
    enchants: dict
    atks: list[int]
    last_skill_used: int
    charge: int

    @classmethod
    def load_from_item(cls, item: "SlotItem"):
        return cls(
            item,
            item.metadata["Lv"],
            item.metadata["Exp"],
            item.metadata.get("KC", 0),
            item.metadata.get("DBL", 200),
            item.metadata.get("Enchs", {}),
            [0, 0, 0, 0, 0, 0, 0],
            item.metadata["LSU"],
            item.metadata["Chg"],
        )

    def dump_item(self):
        s = self.slotItem
        s.metadata["Lv"] = self.level
        s.metadata["Exp"] = self.exp
        s.metadata["KC"] = self.killcount
        s.metadata["DBL"] = self.durability
        s.metadata["Enchs"] = self.enchants
        s.metadata["LSU"] = self.last_skill_used
        s.metadata["Chg"] = self.charge
        return s


@dataclass
# 一个中转类, 专门描述一个饰品类物品。
class ItemRelic:
    slotItem: "SlotItem"
    level: int
    exp: int
    main_props: dict[str, int]
    sub_props: dict[str, int]

    @classmethod
    def load_from_item(cls, item: "SlotItem"):
        return cls(
            item,
            item.metadata["Lv"],
            item.metadata["Exp"],
            item.metadata["Main"],
            item.metadata["Sub"],
        )

    def dump_item(self):
        s = self.slotItem
        s.metadata["Lv"] = self.level
        s.metadata["Exp"] = self.exp
        s.metadata["Main"] = self.main_props
        s.metadata["Sub"] = self.sub_props
        return s


def convert_item_to_weapon(item: "SlotItem", owner: "PlayerEntity"):
    "将物品转化为 Weapon 实例"
    from .frame_objects import get_weapon_instance
    from .. import entry

    return get_weapon_instance(
        item.item.id,
        owner,
        entry.rpg_upgrade.update_weapon_by_level(ItemWeapon.load_from_item(item)),
    )


def convert_item_to_relic(item: "SlotItem", owner: "PlayerEntity"):
    "将物品转化为 Relic 实例"
    from .frame_objects import get_relic_instance

    return get_relic_instance(item.item.id, owner, ItemRelic.load_from_item(item))

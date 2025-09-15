from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import entry

    Item = entry.rpg.backpack.Item
    SlotItem = entry.rpg.backpack.SlotItem


@dataclass
class ShopSell:
    tag: str
    cost_item: "Item"
    cost_count: int
    sell_item: "Item"
    sell_count: int
    once_limit: int
    cooldown_min: int

    @property
    def cost_item_dispname(self):
        return self.cost_item.force_disp()

    @property
    def sell_item_dispname(self):
        return self.sell_item.force_disp()

    def copy(self):
        return ShopSell(
            self.tag,
            self.cost_item,
            self.cost_count,
            self.sell_item,
            self.sell_count,
            self.once_limit,
            self.cooldown_min,
        )


@dataclass
class ShopSellMeta:
    tag: str
    cost_item: "Item"
    cost_count: int
    sell_item: "SlotItem"
    once_limit: int
    cooldown_min: int

    @property
    def sell_count(self):
        return self.sell_item.count

    @property
    def cost_item_dispname(self):
        return self.cost_item.force_disp()

    @property
    def sell_item_dispname(self):
        return self.sell_item.force_disp()

    def copy(self):
        return ShopSellMeta(
            self.tag,
            self.cost_item,
            self.cost_count,
            self.sell_item,
            self.once_limit,
            self.cooldown_min,
        )


ShopSellSuperMeta = NotImplemented


@dataclass
class RealItemSell:
    tag: str
    cost_item: "Item"
    cost_count: int
    sell_item_dispname: str
    sell_item_id: str
    sell_item_data: int
    sell_count: int
    once_limit: int
    cooldown_min: int

    @property
    def cost_item_dispname(self):
        return self.cost_item.force_disp()

    def copy(self):
        return RealItemSell(
            self.tag,
            self.cost_item,
            self.cost_count,
            self.sell_item_dispname,
            self.sell_item_id,
            self.sell_item_data,
            self.sell_count,
            self.once_limit,
            self.cooldown_min,
        )

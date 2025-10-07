from typing import TYPE_CHECKING

from tooldelta import Player

if TYPE_CHECKING:
    from . import CustomRPG, SlotItem


class BackpackHolder:
    def __init__(self, sys: "CustomRPG"):
        self.sys = sys
        self.backpack = sys.backpack

    def list_player_store_with_filter(
        self, player: Player, item_filter: list[str], antis_uuid: list[str] = []
    ):
        "使用过滤器列出玩家背包内符合条件的物品 (过滤器1: 物品分组, 过滤器2: 黑名单UUID)"
        items = self.backpack.load_backpack(player).find_item_by_categories(item_filter)
        if antis_uuid == []:
            return items
        for i in items.copy():
            if i.uuid in antis_uuid and i in items:
                items.remove(i)
        return items

    # 向玩家的虚拟背包中静默添加物品
    def addPlayerStore(self, player: Player, item: "SlotItem"):
        self.backpack.load_backpack(player).add_item(item)

    # 向玩家的虚拟背包中静默移除物品
    def removePlayerStore(self, player: Player, item: "SlotItem", count: int):
        self.backpack.load_backpack(player).remove_item(item.item.id, count, item.uuid)

    # 根据物品UUID获取玩家背包内物品
    def getItem(self, player: Player, item_uuid: str):
        return self.backpack.load_backpack(player).get_item(item_uuid)

    def giveItem(self, player: Player, item: "SlotItem", show_to_player=True):
        "给予单个物品"
        self.addPlayerStore(player, item)
        if show_to_player:
            self.sys.show_inf(player, f"§7+ {item.disp_name} §fx {item.count}")

    def giveItems(self, player: Player, items: list["SlotItem"], show_to_player=True):
        "给予多个物品"
        for item in items:
            self.addPlayerStore(player, item)
            if show_to_player:
                self.sys.show_inf(player, f"§7+ {item.disp_name} §fx {item.count}")

    # 根据标签名获取玩家背包内物品
    def getItems(self, player: Player, tag_name: str):
        return self.backpack.load_backpack(player).find_items(tag_name)

    # 根据标签名获取玩家背包内物品的数量
    def getItemCount(self, player: Player, tag_name: str):
        return self.backpack.load_backpack(player).item_count(tag_name)

    def clearItem(self, player: Player, tag_name: str, count=1, show_to_player=True):
        "根据标签名清除物品"
        player_have = self.getItemCount(player, tag_name)
        if count > player_have or count == -1:
            count = player_have
        if count > 0:
            item = self.getItems(player, tag_name)
            assert item is not None
            item = item[0]
            self.backpack.load_backpack(player).remove_item(tag_name, count)
            if show_to_player:
                self.sys.show_inf(player, f"§7- {item.disp_name} §r§fx {count}")
            if item.count == 1:
                # 清除特殊槽位
                need_update = False
                playerbas = self.sys.player_holder.get_player_basic(player)
                if item.uuid in playerbas.mainhand_weapons_uuid:
                    playerbas.mainhand_weapons_uuid[
                        playerbas.mainhand_weapons_uuid.index(item.uuid)
                    ] = None
                    need_update = True
                else:
                    self.sys.print(
                        f"item not exists in mainhand_weapon: {playerbas.mainhand_weapons_uuid}"
                    )
                if item.uuid in playerbas.relics_uuid:
                    playerbas.relics_uuid[playerbas.relics_uuid.index(item.uuid)] = None
                    need_update = True
                if need_update:
                    self.sys.show_warn(
                        player, "物品栏道具发生变动， 将更新个人战斗数据"
                    )
                    self.sys.player_holder.update_playerentity_from_basic(
                        playerbas, self.sys.player_holder.get_playerinfo(player)
                    )
        return count


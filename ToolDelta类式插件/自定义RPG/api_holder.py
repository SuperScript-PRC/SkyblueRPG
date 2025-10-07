from typing import TYPE_CHECKING
from tooldelta import Player

if TYPE_CHECKING:
    from . import CustomRPG, SlotItem


class APIHolder:
    def __init__(self, sys: "CustomRPG"):
        self.sys = sys

    def change_player_weapon_slot(
        self, player: Player, slot: int, slotitem: "SlotItem"
    ):
        entity = self.sys.player_holder.get_playerinfo(player)
        playerbas = self.sys.player_holder.get_player_basic(player)
        self.sys.player_holder.dump_mainhand_weapon_datas_to_slotitem(entity)
        self.sys.player_holder.save_game_player_data(player)
        playerbas.mainhand_weapons_uuid[slot] = slotitem.uuid
        self.sys.player_holder.update_playerentity_from_basic(playerbas, entity)
        self.sys.display_holder.display_skill_cd_to_player(entity, force_update=True)

    def get_player_basic(self, player: Player):
        return self.sys.player_holder.get_player_basic(player)

    def get_player_entity(self, player: Player):
        return self.sys.player_holder.get_playerinfo(player)

    def giveItem(self, player: Player, item: "SlotItem"):
        return self.sys.backpack_holder.giveItem(player, item)

    def clearItem(self, player: Player, tag_name: str, count: int, show_to_player=True):
        return self.sys.backpack_holder.clearItem(
            player, tag_name, count, show_to_player
        )

    def getItemCount(self, player: Player, tag_name: str):
        return self.sys.backpack_holder.getItemCount(player, tag_name)

    def giveItems(self, player: Player, items: list["SlotItem"], show_to_player=True):
        return self.sys.backpack_holder.giveItems(player, items, show_to_player)

    def createItem(self, tag_name: str, count: int, metadata: dict | None = None):
        return self.sys.item_holder.createItem(tag_name, count, metadata)

    def getOrigItem(self, tag_name: str):
        return self.sys.item_holder.getOrigItem(tag_name)

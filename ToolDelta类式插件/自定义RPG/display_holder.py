from typing import TYPE_CHECKING

from tooldelta import utils, Player
from .rpg_lib.rpg_entities import PlayerEntity

if TYPE_CHECKING:
    from . import CustomRPG, SlotItem


class DisplayHolder:
    def __init__(self, sys: "CustomRPG"):
        self.sys = sys

    def activate(self):
        self._display_skill_cd_to_player_thread()

    # 给予物品提示
    def display_items_added(self, player: Player, items: list["SlotItem"]):
        for item in items:
            self.sys.show_inf(player, f" ◈ §7{item.count}x §f{item.disp_name}")

    # 向玩家在聊天栏展示主手道具
    def display_weapon_to_player(self, player: Player, item: "SlotItem"):
        assert not isinstance(item.item.description, str)
        descs = (
            "§e┃ §f"
            + item.disp_name
            + " §r§7| "
            + self.sys.item_holder.make_item_starlevel(item.item.id)
            + " §7| §r"
        )
        descs += "\n§r┃§7§o ".join(item.item.description(item).split("\n"))
        player.show(descs)

    # 更新终结技充能显示
    def display_charge_to_player(self, playerinf: PlayerEntity, force_update=False):
        if playerinf.weapon is None:
            return
        elif (
            playerinf.weapon.chg
            == self.sys.player_holder.get_player_last_weapon_charge(playerinf)
            and not force_update
        ):
            return
        if playerinf.weapon.chg == playerinf.weapon.charge_ult:
            self.sys.game_ctrl.sendwocmd(
                f"replaceitem entity {playerinf.player.safe_name}"
                " slot.hotbar 2 gold_ingot 1 755 "
                r'{"item_lock":{"mode":"lock_in_slot"}}'
            )
        else:
            self.display_progress_by_durability_bar(
                playerinf.player,
                "slot.hotbar 2",
                "golden_helmet",
                1,
                77,
                (playerinf.weapon.chg / playerinf.weapon.charge_ult)
                if playerinf.weapon
                else 0,
            )
        self.sys.player_holder.set_player_last_weapon_charge(
            playerinf, playerinf.weapon.chg
        )

    def display_skill_cd_to_player(self, playerinf: PlayerEntity, force_update=False):
        if weapon := playerinf.weapon:
            weapon_cd = self.sys.item_holder.get_weapon_skill_cd(weapon)
            if weapon_cd > 1:
                prog = weapon_cd / weapon.cd_skill
                self.display_progress_by_durability_bar(
                    playerinf.player,
                    "slot.hotbar 1",
                    "iron_helmet",
                    1,
                    165,
                    prog,
                )
            elif weapon_cd == 1 or (force_update and weapon_cd == 0):
                # 刚刚好准备退出cd模式
                self.sys.game_ctrl.sendwocmd(
                    f"/replaceitem entity {playerinf.player.safe_name} slot.hotbar 1 iron_ingot 1 755 "
                    + r'{"item_lock":{"mode":"lock_in_slot"}}'
                )

    # 物品栏进度条
    def display_progress_by_durability_bar(
        self,
        player: Player,
        slot_and_pos: str,
        item: str,
        pmin: float,
        pmax: float,
        pnow: float,
    ):
        durability = int((pmax - pmin) * (1 - pnow)) + pmin
        self.sys.game_ctrl.sendwocmd(
            f"/replaceitem entity {player.safe_name} {slot_and_pos} {item} 1 {durability} "
            r'{"item_lock":{"mode":"lock_in_slot"}}'
        )

    @utils.timer_event(1, "数据化显示武器CD值")
    def _display_skill_cd_to_player_thread(self):
        for playerinf in self.sys.player_holder._player_entities.values():
            self.display_skill_cd_to_player(playerinf)

    def clear_player_skill_and_ult_setter(self, player: Player):
        self.sys.game_ctrl.sendwocmd(
            f"replaceitem entity {player.safe_name} slot.hotbar 1 air"
        )
        self.sys.game_ctrl.sendwocmd(
            f"replaceitem entity {player.safe_name} slot.hotbar 2 air"
        )

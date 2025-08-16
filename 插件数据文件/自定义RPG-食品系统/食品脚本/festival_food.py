import random
from dev_rpg_food_lib import RPGFood  # type: ignore[reportMissingModuleSource]


class RedPacketFruit(RPGFood):
    tag_name = "红包果"
    model_id = "beetroot"
    cure_hp_percent = 0

    def eat(self):
        money = random.randint(50, 100)
        rpg_sys = self.user.system
        money_item = rpg_sys.item_holder.createItems("蔚蓝点", money)
        rpg_sys.backpack_holder.giveItems(self.user.player, money_item)
        rpg_sys.show_any(self.user.player, "e", f"红包果掉落了 {money} 蔚蓝点。")

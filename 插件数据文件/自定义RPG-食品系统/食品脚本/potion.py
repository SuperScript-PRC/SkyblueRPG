import random
from dev_rpg_food_lib import RPGFood  # type: ignore[reportMissingModuleSource]


class OrangeJuice(RPGFood):
    tag_name = "苏打橙汁"
    show_name = "§6苏打橙汁"
    description = "由糖果城-枫糖特区的甜橙制成的冒泡橙汁。\n§e饮用后获得 1 分钟的 速度I 效果。\n\n§7§o橙色夏日， 美味连橙！"
    star_level = 2
    model_id = "potion"
    cure_hp = 8

    def eat(self):
        super().eat()
        self.revert_effect("fire_resistance")
        self.add_effect("speed", 1, 0)
        if random.random() > 0.8:
            self.sys.rpg.show_succ(self.user.player, "恭喜你, 喝到了 §7[§e再来一瓶§7]")
            return True


class BobbleBubble(RPGFood):
    tag_name = "泡泡龙汽水"
    show_name = "§a泡泡龙汽水"
    description = (
        "由 Taito 公司出品的汽水。\n§e听说饮用后会令人头大！\n\n§7§oBobble Bubble!"
    )
    star_level = 2
    model_id = "potion"
    model_data = 9
    cure_hp = 10

    def eat(self):
        super().eat()
        self.revert_effect("jump_boost")
        self.user.run_cmd('playanimation %t animation.chicken.baby_transform "" 3')


class QingdaoBeer(RPGFood):
    tag_name = "青岛啤酒"
    show_name = "§e青岛啤酒"
    description = "一小瓶啤酒。\n§e饮用后随机获得以下效果中的一个： 冒热气、 眼冒爱心、 眼冒裂心和喝醉。\n\n§7§o可以喝的。 ————普罗米修斯\n你个人机， 我当然知道。 ————SuperScript"
    model_id = "honey_bottle"
    star_level = 2
    cure_hp = 10

    def eat(self):
        rand = random.randint(1, 10)
        if rand < 3:
            self.user.run_cmd(
                "execute as %t at @s run particle minecraft:death_explosion_emitter ~~~"
            )
        elif rand < 6:
            self.user.run_cmd(
                "execute as %t at @s run particle minecraft:heart_particle ~~2~"
            )
        elif rand <= 9:
            self.user.run_cmd("execute as %t at @s run particle minecraft:bleach ~~2~")
        else:
            self.user.run_cmd("title %t title §6你感觉自己醉醺醺地...")
            self.add_effect("nausea", 30, 1, True)


class ShengXueJin(RPGFood):
    tag_name = "生血津"
    show_name = "§c生血津"
    model_id = "potion"
    model_data = 21
    cure_hp = 20
    cure_hp_percent = 0.15

    def eat(self):
        super().eat()


class YiYunWater(RPGFood):
    tag_name = "依云矿泉水"
    show_name = "§f[§b依云§f] 矿泉水"
    description = "来自雪川顶的富含微量矿物质的水。\n§e饮用后获得 1 分钟的 慈善I 效果。\n\n§7§o水也有生命吗？ ————《水知道》"
    model_id = "potion"
    star_level = 4
    model_data = 17
    cure_hp = 0
    cure_hp_percent = 0

    def eat(self):
        self.revert_effect("slowness")
        self.user.add_effect("Kindness", self.user, 60)
        self.sys.rpg.show_any(self.user.player, "e", "你感觉自己非常自信..")
        self.sys.rpg.show_any(self.user.player, "e", "商人都可能会被你的魅力“折”服。")


class ClearPotion(RPGFood):
    tag_name = "复原茗"
    show_name = "§2复原茗"
    description = "淡如白开水.. 等等， 它甚至能让刚喝完的饮料的滋味消失？\n§e可以清除大头等效果， 使一切恢复如初。\n\n§r§o没滋没味... ————大顽固美食评价。"
    model_id = "potion"
    model_data = 7

    def eat(self):
        self.revert_effect("invisibility")
        self.user.run_cmd("playanimation %t animation.agent.swing_arms  1")

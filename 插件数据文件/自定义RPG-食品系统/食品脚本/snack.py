from dev_rpg_food_lib import RPGFood  # type: ignore[reportMissingModuleSource]
import random


class Chips(RPGFood):
    tag_name = "薯条"
    show_name = "§6薯条"
    description = "外焦里脆（不一定）的薯条。\n食用后恢复 8%+10 点生命值并获得一分钟夜视。\n\n§7§o嚼嚼嚼... ————大顽固美食评论\n别光顾着吃， 美食评论呢？ ————小顽皮\n嚼嚼嚼... ————大顽固"
    star_level = 2
    model_id = "baked_potato"
    cure_hp_percent = 0.8
    cure_hp = 10

    def eat(self):
        super().eat()
        self.add_effect("night_vision", 60)


class KelpChips(RPGFood):
    tag_name = "海带片"
    show_name = "§3海带片"
    description = (
        "咸咸脆脆的大块海带片。\n\n§7§o海的味道我..我哪知道？这东西是水培床培养的。"
    )
    star_level = 1
    model_id = "dried_kelp"
    cure_hp = 0
    cure_hp_percent = 0

    def eat(self):
        super().eat()
        if random.random() > 0.75:
            self.add_effect("speed", 60, 1)

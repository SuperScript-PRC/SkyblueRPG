from dev_rpg_food_lib import RPGFood  # type: ignore[reportMissingModuleSource]


class CookedChicken(RPGFood):
    tag_name = "烤全鸡"
    show_name = "§6§l烤全鸡"
    description = "不加调料的烤全鸡， 外焦里嫩。\n食用后恢复 15%+10 点生命值。\n\n§7§o肥美多汁， 也许是油。 ————大顽固美食评价"
    model_id = "cooked_chicken"
    cure_hp_percent = 0.15
    cure_hp = 10


class BerryBall(RPGFood):
    tag_name = "野球果"
    show_name = "§c野§2球果"
    description = "森林中常见的灌木果实。\n食用后恢复少许生命值。\n\n§7§o甜甜的， 像爱情。 ————小顽皮"
    model_id = "sweet_berries"
    cure_hp = 5
    cure_hp_percent = 0.04


class HardBread(RPGFood):
    tag_name = "粗麦面包"
    show_name = "§6粗麦面包"
    description = "使用大麦粉烘焙而成。\n食用后获得 10%+8 点生命值。\n\n§7§o对胃部不好， 别吃太多。 ————普罗米修斯"
    model_id = "bread"
    cure_hp = 8
    cure_hp_percent = 0.1


class ChiliBread(RPGFood):
    tag_name = "孜然麦包"
    show_name = "§c孜然麦包"
    description = "使用大麦粉混合少量孜然粉烘焙而成。 \n食用后可获得攻击提升效果。\n\n§7§o我再说一次， 把面包从烤架上拿下来。 ————枫"
    model_id = "bread"
    cure_hp = 12

    def eat(self):
        self.add_rpg_effect("ATKBoost", 20, 1)
        super().eat()


class FruitSalad(RPGFood):
    tag_name = "水果沙拉"
    show_name = "§c水§e果§a沙拉"
    description = "含有多种水果， 富含糖类和膳食纤维。\n食用后可恢复6点能量。\n\n§7§o枫， 给我递瓶沙拉酱！ ————莉莉"
    model_id = "suspicious_stew"
    cure_hp_percent = 0.15
    cure_hp = 40

    def eat(self):
        self.revert_effect("weakness")
        self.user.add_charge(6)
        super().eat()


class CookedFish(RPGFood):
    tag_name = "烤鱼"
    show_name = "§6烤鱼"
    model_id = "cooked_fish"
    description = "不加调料的烤鱼，外焦里嫩。"
    cure_hp_percent = 0.15
    cure_hp = 40


# 蔚蓝空域/路人-麦当劳店外

import time
from tooldelta import Player
from dev_customrpg_plot import plot, get_system  # type: ignore

sys = get_system()
p = sys.putils

BOUND_OUTSIDE_MCDONALD = "麦当劳店外路人", "蔚蓝空域-路人-麦当劳店外"
BOUND_INSIDE_MCDONALD_CUSTOMER1 = "麦当劳店外路人", "蔚蓝空域-顾客1-麦当劳店内"
BOUND_MCDOLALD_EMPLOYEE = "麦当劳店内员工", "蔚蓝空域-员工-麦当劳店内"
BOUND_RAID_SHOP = "莱德奇物店", "蔚蓝空域-莱德奇物店"
BOUND_AIRSHIP = "蔚蓝空域大汽艇", "蔚蓝空域-大汽艇"
BOUND_PVE_TEACHER = "蔚蓝空域pve教练", "蔚蓝空域-武术教练"

REPAIR_SHOP_ASSISTANT = "蔚蓝空域-五金店掌柜"
GAS_STATION_STORE = "蔚蓝空域-加油站便利店店员"
DRINK_SHOP_ASSISTANT = "蔚蓝空域-饮料店掌柜"
CAKE_SHOP_ASSISTANT = "蔚蓝空域-蛋糕店掌柜"
S711_SHOP = "蔚蓝空域-711店-店员"


@plot(*BOUND_OUTSIDE_MCDONALD)
def mcdonald_outside(player: Player):
    dialog = p.Dialogue(player, "正在自拍的大妈")
    with p.RotationCtrl(player):
        dialog.pprint("凌晨三点， 我把七十五岁的老爸赶出了家门。 ")
        match dialog.choice(
            ["（尝试打断视频的拍摄。）", "是人我吃...", "别再误导大众了！"],
        ):
            case 0:
                dialog.pprint("别打扰我拍视频， 一边去！ ")
            case 1:
                dialog.pprint(
                    "什么意思？ 阿姨听不懂你们小孩子说的话， 这是骂人的吧？ 你们年轻人天天上网学了这么多脏东西， 可不了得！",
                )
            case 2:
                dialog.pprint(
                    "小伙子， 阿姨拍视频关你什么事？ 一边去一边去！",
                )


mcdonald_outside.set_as_main()


蔚蓝点 = p.createOrigItem("蔚蓝点")
烤全鸡 = p.createOrigItem("烤全鸡")
薯条 = p.createOrigItem("薯条")


@plot(*BOUND_MCDOLALD_EMPLOYEE)
def mcdolald_employee(player: Player):
    dialog = p.Dialogue(player, "店员")
    with p.RotationCtrl(player):
        dialog.pprint("欢迎光临麦当当连锁店！ 请问您要买点什么呢？")
        match dialog.choice(["我要购物。", "（离开。）"]):
            case 0:
                dialog.show_buy_and_sell(
                    [
                        (蔚蓝点, 35, 烤全鸡, 1, 3, 1200),
                        (蔚蓝点, 16, 薯条, 1, 4, 1200),
                    ],
                )
                dialog.pprint("欢迎下次光临！")
            case 1:
                dialog.pprint("欢迎下次光临！")


mcdolald_employee.set_as_main()


# 莱德奇物店, 老板性格沉稳,
@plot(*BOUND_RAID_SHOP)
def raid_shop(player: Player):
    dialog = p.Dialogue(player, "莱德")
    with p.RotationCtrl(player):
        dialog.pprint("欢迎光临， 这里是莱德奇物店。 ")
        match dialog.choice(
            ["买点什么..", "我来典当些东西.."],
            raid_shop.get_available_choices_insertions(player),
        ):
            case 1:
                ...
            case 2:
                ...
            case 3:
                ...


raid_shop.set_as_main()


@plot(*BOUND_INSIDE_MCDONALD_CUSTOMER1)
def kfc_customer1(player: Player):
    with p.RotationCtrl(player):
        NAME = "满足的顾客"
        t = time.localtime().tm_hour
        if t in range(0, 6):
            text = "凌晨"
        elif t in range(6, 11):
            text = "早上"
        elif t in range(11, 14):
            text = "中午"
        elif t in range(14, 17):
            text = "下午"
        elif t in range(17, 25):
            text = "晚上"
        p.pprint(player, NAME, f"{text}现做的手扒鸡真好吃..", delay=2)


kfc_customer1.set_as_main()


@plot(*BOUND_AIRSHIP)
def big_airship(player: Player):
    with p.MovementLimiter(player):
        section = p.choice(
            player,
            p.pprint(player, "汽艇用户交互面板", "请选择前往的目的地：", delay=1),
            ["（离开。）"],
            big_airship.get_available_choices_insertions(player),
        )
        match section:
            case 0:
                return


big_airship.set_as_main()


@plot(*BOUND_PVE_TEACHER)
def pve_teacher(player: Player):
    dialog = p.Dialogue(player, "武术师傅")
    with p.RotationCtrl(player):
        dialog.pprint("中气还是不足啊！", delay=2)
        match dialog.choice(["我想学习战斗技巧.."]):
            case 0:
                if sys.rpg.player_holder.get_playerinfo(player).weapon is None:
                    dialog.pprint("你还没拿出你的武器呢？")
                    match dialog.choice(
                        ["怎样取出武器？", "稍等， 我立刻拿。", "我还是想听取一下。"]
                    ):
                        case 0:
                            dialog.pprint(
                                "用雪球打开终端菜单， 选择§e战斗配置§f， 然后选择§e武器配置§f， 选择第一个槽位， 然后再选择§e装备武器§f， 选择背包里一个武器装配上来就好了。"
                            )
                            return
                        case 1:
                            return
                dialog.pprint(
                    "一般的战斗分为§e普攻§f、 §e技能释放§f和§e终结技释放§f， 你具体要学哪个？",
                )
                match dialog.choice(["普攻。", "技能释放。", "终结技释放。"]):
                    case 0:
                        dialog.pprint(
                            "只要使用§e物品栏第一格的武器§f攻击目标就可以施放最简单的普攻了。",
                        )
                    case 1:
                        dialog.pprint(
                            "只要拿着§e物品栏第二格的铁锭§f就可以进入技能目标选定模式， 这时候再释放一次普攻就可以施放技能了。"
                        )
                        dialog.pprint(
                            "技能的释放有冷却， 冷却进度可以通过物品栏第二格的耐久条查看。"
                        )
                    case 2:
                        dialog.pprint(
                            "只要拿着§e物品栏第三格的金锭§f就可以进入终结技目标选定模式， 这时候再释放一次普攻就可以施放终结技了。"
                        )
                        dialog.pprint(
                            "终结技的释放需要能量， 充能进度可以通过物品栏第三格的耐久条查看。 等到它变成金锭的时候， 即代表充能已完成， 可以释放终结技。 通过击败目标可获得能量。 另外， 一些效果或者饰品能使得你充能速度变快。"
                        )


精炼铁锭 = p.createOrigItem("精炼铁锭")
蔚蓝点 = p.createOrigItem("蔚蓝点")
松香 = p.createOrigItem("松香")


@plot(linked_to=REPAIR_SHOP_ASSISTANT)
def repair_shop_customer(player: Player):
    dialog = p.Dialogue(player, "五金店掌柜")
    with dialog.enter():
        dialog.pprint("...", delay=0)
        match dialog.choice(
            [
                "我想修补和升级我的装备...",
            ]
        ):
            case 0:
                dialog.pprint(
                    "这里都是自助服务， 要§e修补§f或者§e升级§f你的武器之类的， 到左侧或者右侧点击对应的§e按钮§f就可以了。"
                )
                while True:
                    match dialog.choice(
                        [
                            "我想修补我的工具和武器。",
                            "我想升级我的饰品。",
                            "购买修补材料。",
                            "（离开。）",
                        ]
                    ):
                        case 0:
                            dialog.pprint(
                                "看到§a墙面挂满了合金剑§f的一侧了吗， 按下这边的按钮可以§e修理你的工具和武器§f， 不过修补材料是要自备的， 也可以直接找我买些修补材料。"
                            )
                        case 1:
                            dialog.pprint(
                                "看到§a墙面挂满了各种盔甲§f的一侧了吗， 按下这边的按钮可以§e升级你的饰品§f， 记得拿好你的升级所需材料。"
                            )
                        case 2:
                            dialog.show_buy_and_sell(
                                [
                                    (蔚蓝点, 60, 松香, 1, 5, 1440),
                                    (蔚蓝点, 100, 精炼铁锭, 1, 5, 1440),
                                ]
                            )
                        case _:
                            break


repair_shop_customer.set_as_main()


@plot(linked_to=GAS_STATION_STORE)
def gas_station_store(player: Player):
    dialog = p.Dialogue(player, "便利店店员")
    with dialog.enter():
        dialog.pprint("您好， 欢迎光临蔚蓝石化便利店。")


苏打橙汁 = p.createOrigItem("苏打橙汁")
青岛啤酒 = p.createOrigItem("青岛啤酒")
泡泡龙汽水 = p.createOrigItem("泡泡龙汽水")
复原茗 = p.createOrigItem("复原茗")


@plot(linked_to=DRINK_SHOP_ASSISTANT)
def drink_shop_store(player: Player):
    dialog = p.Dialogue(player, "饮料店店员")
    with dialog.enter():
        dialog.pprint("您好， 买点什么饮料？", delay=2)
        dialog.show_buy_and_sell(
            [
                (蔚蓝点, 10, 苏打橙汁, 1, 12, 1440),
                (蔚蓝点, 14, 青岛啤酒, 1, 16, 1000),
                (蔚蓝点, 20, 泡泡龙汽水, 1, 8, 1000),
                (蔚蓝点, 6, 复原茗, 1, 30, 1000),
            ]
        )


drink_shop_store.set_as_main()


粗麦面包 = p.createOrigItem("粗麦面包")
孜然麦包 = p.createOrigItem("孜然麦包")


@plot(linked_to=CAKE_SHOP_ASSISTANT)
def cake_shop_store(player: Player):
    dialog = p.Dialogue(player, "蛋糕店店员")
    with dialog.enter():
        dialog.pprint("欢迎光临~", delay=2)
        dialog.show_buy_and_sell(
            [
                (蔚蓝点, 6, 粗麦面包, 1, 20, 800),
                (蔚蓝点, 14, 孜然麦包, 1, 10, 1440),
            ]
        )


cake_shop_store.set_as_main()

海带片 = p.createOrigItem("海带片")


@plot(linked_to=S711_SHOP)
def s_711_shop(player: Player):
    dialog = p.Dialogue(player, "711店店员")
    with dialog.enter():
        dialog.pprint("欢迎光临七仔店~", delay=2)
        dialog.show_buy_and_sell([(蔚蓝点, 1, 海带片, 6, 40, 1440)])


s_711_shop.set_as_main()

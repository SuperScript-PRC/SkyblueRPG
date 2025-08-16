from tooldelta import Player
from dev_customrpg_plot import plot, get_system  # type: ignore

sys = get_system()

BOUND_FISHING_PORT = "渔人码头渔夫", "渔人码头-渔夫"


蔚蓝点 = sys.putils.createOrigItem("蔚蓝点")
金枪鱼 = sys.putils.createOrigItem("金枪鱼")
鳕鱼 = sys.putils.createOrigItem("鳕鱼")
鲑鱼 = sys.putils.createOrigItem("鲑鱼")
石斑鱼 = sys.putils.createOrigItem("石斑鱼")
鲈鱼 = sys.putils.createOrigItem("鲈鱼")
海马 = sys.putils.createOrigItem("海马")
乌贼 = sys.putils.createOrigItem("乌贼")


@plot(*BOUND_FISHING_PORT)
def fishing_port(player: Player):
    p = sys.putils
    dialog = p.Dialogue(player, "渔夫")
    with p.RotationCtrl(player):
        dialog.pprint(
            "欢迎来到渔人码头。 在这里你可以钓鱼， 烧烤， 或者和朋友一起开Party哦！",
            delay=1,
        )
        match dialog.choice(["我钓到了一些鱼..", "这里怎么钓鱼呢？", "（离开。）"]):
            case 0:
                dialog.pprint("游客钓到的鱼可以在这里出售给我们哦！", delay=1)
                dialog.show_buy_and_sell(
                    [
                        (金枪鱼, 1, 蔚蓝点, 20, 20, 1440),
                        (鳕鱼, 1, 蔚蓝点, 12, 20, 1440),
                        (鲑鱼, 1, 蔚蓝点, 14, 20, 1440),
                        (石斑鱼, 1, 蔚蓝点, 15, 20, 1440),
                        (鲈鱼, 1, 蔚蓝点, 12, 20, 1440),
                        (海马, 1, 蔚蓝点, 24, 20, 1440),
                        (乌贼, 1, 蔚蓝点, 16, 20, 1440),
                    ]
                )
            case 1:
                dialog.pprint("向水域抛出§e鱼钩§f， 等待鱼竿§6自动收回§f即可。")


fishing_port.set_as_main()

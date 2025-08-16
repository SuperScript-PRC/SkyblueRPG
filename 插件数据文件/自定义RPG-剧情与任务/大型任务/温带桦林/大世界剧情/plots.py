from tooldelta import Player
from dev_customrpg_plot import plot, get_system  # type: ignore

BOUND_FISHERMAN = "温带桦林渔民1", "温带桦林-担心的渔民1"
BOUND_DIGGER = "温带桦林开采工1", "温带桦林林座:开采工1"

ITEM_FISH = "浅水鱼肉块"
ITEM_MONEY = "蔚蓝点"

sys = get_system()


@plot(*BOUND_FISHERMAN)
def fisherman(player: Player):
    p = sys.putils
    NAME = "担心的渔民"
    with p.RotationCtrl(player):
        p.pprint(player, NAME, "怎么还没钓上鱼..", delay=2)
        text = p.pprint(
            player, NAME, "今天又空军的话， 这婆娘又要说我不务正业了..", delay=1
        )
        p.choice(player, text, ["我来帮你吧。"])
        p.pprint(player, NAME, "你有鲜鱼或者肉块吗？我可以出钱！", delay=1)
        FISH = sys.rpg.backpack.get_registed_item(ITEM_FISH)
        MONEY = sys.rpg.backpack.get_registed_item(ITEM_MONEY)
        if FISH is None or MONEY is None:
            p.pprint(
                player,
                NAME,
                f"§c找不到物品 {ITEM_FISH} 或 {ITEM_MONEY}， 请上报至管理员！",
            )
            return
        boughts = p.show_buy_and_sell(player, NAME, [(FISH, 1, MONEY, 10, 5, 600)])
        had_bought = any(i[0].id == ITEM_FISH for i in boughts)
        if had_bought:
            p.pprint(player, NAME, "谢谢啊， 这样也能骗一下老婆子说钓到鱼了。")
        else:
            p.pprint(player, NAME, "哎.. 没有鱼吗？ 那我问问其他人吧..")


fisherman.set_as_main()


@plot(*BOUND_DIGGER)
def digger(player: Player):
    p = sys.putils
    p.pprint


digger.set_as_main()

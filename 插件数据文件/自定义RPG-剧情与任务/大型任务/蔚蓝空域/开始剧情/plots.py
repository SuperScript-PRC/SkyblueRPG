# 蔚蓝空域/路人-麦当劳店外

from tooldelta import Player
from dev_customrpg_plot import plot, get_system  # type: ignore

BOUND_REGISTER = "登记员", "蔚蓝空域-成员登记处"
BOUND_REGISTER_START = "登记员-开始剧情", "蔚蓝空域-成员登记处"

Q_MEMBER_REGISTRATION = "未知空间/intro:成员登记"
Q_START_FIND_JOB = "蔚蓝空域/职业入门:前往人力资源部"

S_MEMBER_REGISTERED = "蔚蓝空域/开始剧情:已登记成员"

ITEM_MONEY = "蔚蓝点"

sys = get_system()


@plot(*BOUND_REGISTER)
def register(player: Player):
    p = sys.putils
    p.disable_movement(player)
    text = p.plot_box_print(player, "登记员", "请问您需要办理什么业务？", delay=0)
    section = p.plot_box_print_with_choice(
        player,
        text,
        ["想了解一些信息.."],
        register.get_available_choices_insertions(player),
    )
    match section:
        case 0:
            section = p.plot_box_print_with_choice(
                player,
                text,
                ["每次进出都需要办理签证吗？", "想查询一下档案.."],
            )
            match section:
                case 0:
                    p.plot_box_print(
                        player,
                        "登记员",
                        "不需要， 每次出入境时蔚蓝空域会自动根据入库档案进行登记处理。",
                    )
                case 1:
                    p.plot_box_print(
                        player,
                        "登记员",
                        f"{player.name}.. 咦， 后面的信息怎么都是 undefined？",
                    )
                    p.simple_actionbar_print(
                        player, "看来蔚蓝空域还需要找人维护一下他们的居民数据库。"
                    )
    p.enable_movement(player)


register.set_as_main()


@plot(*BOUND_REGISTER_START)
def register_start(player: Player):
    p = sys.putils
    p.disable_movement(player)
    p.plot_box_print(player, "登记员", "好的， 请您伸出右手..")
    p.simple_actionbar_print(player, "登记员把你的手放到附近的面板上按了一下。")
    text = p.plot_box_print(
        player,
        "登记员",
        "您在之前没有在这里进行任何访客记录， 您是直接注册为居民呢， 还是仅登记访客？",
        delay=1,
    )
    section = p.plot_box_print_with_choice(
        player, text, ["注册为居民。", "登记为访客。"]
    )
    if section == 1:
        p.simple_actionbar_print(
            player, "如果不登记为居民， 按你现在的情况， 还能去哪里呢？"
        )
        text = p.simple_actionbar_print(player, "还是进行居民登记吧。")
        p.plot_box_print_with_choice(player, text, ["注册为居民。"])
    text = p.plot_box_print(
        player,
        "登记员",
        "您的名字是？",
    )
    retries = 0
    easter_egg = False
    while 1:
        resp = p.plot_box_print_with_choice(
            player, text, s := [player.name + "。", "无名客。", "吉米克。", "旅行者。"]
        )
        if resp == 0:
            break
        elif retries >= 4:
            text = p.plot_box_print(
                player,
                "登记员",
                "青天老大爷， 登记结束之后我给您 100 蔚蓝点， 您就别再开玩笑了！ 您的名字是？",
            )
            resp = p.plot_box_print_with_choice(player, text, [player.name + "。"])
            easter_egg = True
            break
        else:
            retries += 1
            text = p.plot_box_print(
                player,
                "登记员",
                f"{s[resp][:3]}？ 正经场合您就别开这种玩笑了， 您的名字是？",
            )
    text = p.plot_box_print(
        player,
        "登记员",
        "您的住所是？",
    )
    p.plot_box_print_with_choice(player, text, ["暂无。", "居无定所。"])
    text = p.plot_box_print(
        player,
        "登记员",
        "那住址字段就留空吧， 这不算必要填写项。 您需要绑定亲属关系吗？",
    )
    p.plot_box_print_with_choice(player, text, ["暂时不用了。"])
    p.plot_box_print(player, "登记员", "奇怪， 第二次遇到不绑定亲属关系的..", delay=0.5)
    p.plot_box_print(
        player, "登记员", "您的身份已经入库了， 欢迎入驻蔚蓝空域！", delay=0.5
    )
    p.plot_box_print(
        player, "登记员", "对了， 蔚蓝空域对于最近注册的新成员有 200 蔚蓝点的补助， 稍后也会一并下发。", delay=0.5
    )
    p.simple_actionbar_print(
        player, "你刚要转过身去， 登记员偷偷将一张招pin传单塞给了你。"
    )
    p.plot_box_print(
        player, player.name, "（这是什么.. 他不会以为我是来打工的吧..）", delay=2
    )
    p.plot_box_print(
        player,
        player.name,
        "（但是我身上确实分文没有..根据他说的，这里的货币应该是蔚蓝点吧。）",
        delay=2,
    )
    sys.game_ctrl.sendwocmd(f"execute as {player.safe_name} at @s run spawnpoint")
    if easter_egg:
        sys.rpg.backpack_holder.giveItem(player, sys.rpg.item_holder.createItem(ITEM_MONEY, 100))
    p.finish_quest(player, Q_MEMBER_REGISTRATION)
    p.start_quest(player, Q_START_FIND_JOB)
    p.enable_movement(player)
    sys.set_state(player, S_MEMBER_REGISTERED, True)


register_start.set_choice_insertion(
    "§e成员登记。", lambda player: not sys.get_state(player, S_MEMBER_REGISTERED)
)
# ...

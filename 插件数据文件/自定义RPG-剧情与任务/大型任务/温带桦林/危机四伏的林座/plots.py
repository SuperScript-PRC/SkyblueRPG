from tooldelta import Player
from dev_customrpg_plot import (  # type: ignore
    plot,
    as_broadcast_listener,
    get_system,
    plotpath,
)

sys = get_system()
p = sys.putils
evt_apis = sys.rpg.event_apis

BOUND_PLOT_RAID_SHOP_TASK1 = "莱德奇物店:任务1", "蔚蓝空域-莱德奇物店"
BOUND_PLOT_AIRSHIP = "危机四伏的林座:汽艇", "蔚蓝空域-大汽艇"
BOUND_PANICED_EMPLOYEE = "危机四伏的林座:雇员1", "温带桦林林座:开采工1"

Q_NAME = "危机四伏的林座"


@plot(*BOUND_PLOT_RAID_SHOP_TASK1)
def raid_shop_task1(player: Player) -> None:
    NAME = "莱德"
    p.pprint(player, NAME, "噢， 那堆水晶..存量不多了， 货源中断了。", delay=2)
    text = p.pprint(
        player,
        NAME,
        "最近我雇的那位采掘工被派去林座开采紫水晶， 但是不知道为什么他每次去开采都空手而归。 要不你帮我去林地慰问一下他？ ",
    )
    section = p.choice(
        player, text, ["辛苦费...", "我可不白干哦。", "行， 我待会就去看看。"]
    )
    match section:
        case 0 | 1:
            p.pprint(player, NAME, "你放心， 干好了之后报酬少不了你的。")
        case 2:
            p.pprint(player, NAME, "那可太好了， 到时候酬劳少不了你的。")
    p.pprint(
        player,
        NAME,
        "对了， 机票也帮你报销好了， 你可以直接去最近的飞艇接驳站坐到林座。",
    )
    sys.add_quest(player, Q_goto_birch)


raid_shop_task1.set_choice_insertion(
    "§e你店里的紫水晶堆真漂亮。",
    lambda player: not sys.putils.is_plot_completed(player, raid_shop_task1.tagname),
)


@plot(*BOUND_PLOT_AIRSHIP)
def big_airship_task1(player: Player):
    NAME = "汽艇用户交互面板"
    p.pprint(player, NAME, "即将前往林座， 请系好安全带..")
    p.trans(player, 2, 4, 2, 0xFFFFFF)
    p.sleep(player, 4)
    p.tp(player, (155, 74, -151))
    p.sleep(player, 4)
    sys.finish_quest(player, Q_goto_birch)
    sys.add_quest(player, Q_cometo_digger)


big_airship_task1.set_choice_insertion(
    "§e前往桦林林座。",
    lambda player: sys.putils.player_is_in_quest(player, Q_goto_birch.tag_name),
)


@plot(*BOUND_PANICED_EMPLOYEE)
def paniced_employee(player: Player):
    dialog = p.Dialogue(player, "慌张的采掘工")
    dialog.pprint("...", delay=2)
    dialog.choice(["你怎么啦？", "你怎么呆在这不动了？", "你看起来很害怕.."])
    dialog.pprint("附近的山洞里..又出现辐化僵尸了..", delay=1)
    dialog.choice(["怪不得莱德说你什么也没挖到。"])
    dialog.pprint(
        "我也实在打不过那几只僵尸啊..听说它们只要一伤人， 人就会立刻被辐射化..",
        delay=2,
    )
    dialog.pprint("您就是莱德派来的打手吗？求您帮忙解决那几只僵尸，感激不尽啊！")
    dialog.choice(["这就来！", "我可什么都没说啊.."])
    dialog.pprint("感激不尽啊！您记得拿好武器， 它们好像不好对付！")
    sys.finish_quest(player, Q_cometo_digger)
    sys.add_quest(player, Q_kill_mobs)


paniced_employee.set_insertion(
    lambda player: sys.putils.player_is_in_quest(player, Q_cometo_digger.tag_name)
)

蔚蓝点 = sys.putils.createOrigItem("蔚蓝点")


@plot(linked_to=BOUND_PANICED_EMPLOYEE[1])
def paniced_employee_quest1_end(player: Player):
    dialog = p.Dialogue(player, "慌张的采掘工")
    with dialog.enter():
        dialog.pprint("啊.. 里面应该没有怪物了.. 太感谢您了！")
        dialog.pprint("以后要是再遇到僵尸之类的我就联系您了， 小小心意不成敬意！")
        p.giveItem(player, 蔚蓝点, 200)
        p.add_favor(player, paniced_employee_quest1_end.linked_to, 5)
    sys.finish_quest(player, Q_return_to_digger)
    sys.add_quest(player, Q_return_to_raid)


paniced_employee_quest1_end.set_insertion(
    lambda player: sys.putils.player_is_in_quest(player, Q_return_to_digger.tag_name)
)


@plot(linked_to=BOUND_PLOT_RAID_SHOP_TASK1[1])
def paniced_employee_quest1_back_end(player: Player):
    dialog = p.Dialogue(player, "莱德")
    with dialog.enter():
        dialog.pprint("干得不错， 刚刚他打电话跟我说了。", delay=1)
        dialog.choice(["你怎么知道我能打？", "我好像没跟你说过我会战斗啊.."])
        dialog.pprint("有一些能力， 是可以立刻从一个人身上看出来的..", delay=1)
        dialog.pprint(
            "好了， 不开玩笑了， 现在的事实证明你确实很能打。 拿好你的报酬喽。", delay=1
        )
        dialog.pprint(
            "对了， 如果以后你通过战斗获得了战利品， 也可以卖给我喔。 我对这些稀奇物品都很感兴趣。",
            delay=1,
        )
        p.giveItem(player, 蔚蓝点, 300)
        p.add_favor(player, paniced_employee_quest1_back_end.tagname, 3)
    sys.finish_quest(player, Q_return_to_raid)


paniced_employee_quest1_back_end.set_insertion(
    lambda player: sys.putils.player_is_in_quest(player, Q_return_to_raid.tag_name)
)


def dangerous_birch_quest_detect(player: Player, data_dict):
    killcount = data_dict.get("k", 0)
    if killcount < 3:
        return False, "有僵尸未击杀完"
    else:
        return True, ""


def dangerous_birch_quest_description(player: Player, data_dict):
    return f"击杀隧洞里的 {data_dict.get('k', 0)}/3 只辐化僵尸"


Q_goto_birch = sys.LegacyQuest(
    tag_name=plotpath / "前往林座",
    disp_name=Q_NAME,
    priority=2,
    description="乘坐飞艇前往桦林林座寻找雇工",  # 温带桦林/危机四伏的林座:前往林座
    position=(310, 206, 263),
    cooldown=None,
    add_quest_cb=None,
    detect_cb=dangerous_birch_quest_detect,
    finish_cb=None,
)
sys.regist_quest(Q_goto_birch)

Q_cometo_digger = sys.LegacyQuest(
    tag_name=plotpath / "寻找雇工",  # 温带桦林/危机四伏的林座:寻找雇工
    disp_name=Q_NAME,
    priority=2,
    description="找到雇工并询问状况",
    position=(145, 55, -120),
    cooldown=None,
    add_quest_cb=None,
    detect_cb=None,
    finish_cb=None,
)
sys.regist_quest(Q_cometo_digger)

Q_kill_mobs = sys.LegacyQuest(
    tag_name=plotpath / "击杀僵尸",  # 温带桦林/危机四伏的林座:击杀僵尸
    disp_name=Q_NAME,
    priority=2,
    description=dangerous_birch_quest_description,
    position=(181, 45, -115),
    cooldown=None,
    add_quest_cb=None,
    detect_cb=dangerous_birch_quest_detect,
    finish_cb=None,
)
sys.regist_quest(Q_kill_mobs)

Q_return_to_digger = sys.LegacyQuest(
    tag_name=plotpath / "返回",  # 温带桦林/危机四伏的林座:返回
    disp_name=Q_NAME,
    priority=2,
    description="返回并告知采掘工",
    position=(145, 55, -120),
    cooldown=None,
    add_quest_cb=None,
    detect_cb=None,
    finish_cb=None,
)
sys.regist_quest(Q_return_to_digger)

Q_return_to_raid = sys.LegacyQuest(
    tag_name=plotpath / "返回奇物店",
    disp_name=Q_NAME,
    priority=2,
    description="返回蔚蓝空域并找到莱德",
    position=(378, 198, 412),
    cooldown=None,
    add_quest_cb=None,
    detect_cb=None,
    finish_cb=None,
)
sys.regist_quest(Q_return_to_raid)


@as_broadcast_listener(Q_kill_mobs, evt_apis.PlayerKillMobEvent.type)
def dangerous_birch_listener1(
    player: Player, event: evt_apis.PlayerKillMobEvent, data_dict
):
    if event.mob.cls.tag_name == "辐化僵尸" and event.player.player is player:
        count = data_dict.get("k", 0) + 1
        data_dict["k"] = count
        sys.rpg.show_inf(player, f"击杀进度： §e{count}/3")
        if data_dict["k"] >= 3:
            sys.putils.run_plot(player, dangerous_birch_plot1)


@as_broadcast_listener(Q_kill_mobs, evt_apis.MobKillPlayerEvent.type)
def dangerous_birch_listener2(
    player: Player, event: evt_apis.MobKillPlayerEvent, data_dict
):
    if event.mob.cls.tag_name == "辐化僵尸" and event.player.player is player:
        data_dict["kc"] = data_dict.get("kc", 0) + 1
        sys.putils.run_plot(player, dangerous_birch_plot2)


@plot()
def dangerous_birch_plot1(player: Player):
    playerinf = sys.rpg.player_holder.get_playerinfo(player)
    health = playerinf.hp / playerinf.tmp_hp_max
    if health == 1:
        sys.putils.pprint(player, player.name, "（僵尸甚至没有伤我一根毫毛。）")
    elif health > 0.8:
        sys.putils.pprint(player, player.name, "（这些僵尸对付起来真是轻轻松松啊。）")
    elif health > 0.6:
        sys.putils.pprint(player, player.name, "（这些僵尸对付起来还是要些手法啊。）")
    elif health > 0.4:
        sys.putils.pprint(player, player.name, "（这些僵尸不太好对付啊..）")
    else:
        sys.putils.pprint(player, player.name, "（这些僵尸真难对付啊..）")
    sys.putils.pprint(
        player, player.name, "（那个采掘工好像在叫我名字？回去找找他吧。）"
    )
    sys.finish_quest(player, Q_kill_mobs)
    sys.add_quest(player, Q_return_to_digger)


@plot()
def dangerous_birch_plot2(player: Player):
    sys.putils.pprint(
        player, player.name, "（...它们真不好对付啊， 差点把命搭进去..）", delay=0
    )

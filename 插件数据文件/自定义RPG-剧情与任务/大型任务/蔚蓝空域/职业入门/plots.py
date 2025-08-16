from tooldelta import Player
from dev_customrpg_plot import plot, get_system, plotpath  # type: ignore

sys = get_system()

GLOBAL_NAME = "蔚蓝空域职业入门"

BOUND_HR_FRONT = "人力资源前台", "蔚蓝空域-人力资源前台"
BOUND_HR_FRONT_START = "人力资源前台-开始找工作", "蔚蓝空域-人力资源前台"
BOUND_MAIL_CONSULTANT = "邮政站咨询员", "蔚蓝空域-邮政站咨询员"
BOUND_MAIL_CONSULTANT_WORK = "邮政站-入职", "蔚蓝空域-邮政站咨询员"
BOUND_CLEANER = "回收站", "蔚蓝空域-回收站工人"
BOUND_CLEANER_WORK = "回收站-入职", "蔚蓝空域-回收站工人"
BOUND_CARRIER = "建筑工地包工头", "蔚蓝空域-建筑工地包工头"
BOUND_CARRIER_WORK = "建筑工地包工头-入职", "蔚蓝空域-建筑工地包工头"


S_JOB_CHOOSE_READY = "蔚蓝空域/职业入门:准备选职业"
S_JOB_SELECTED = "蔚蓝空域/职业入门:选好初始职业"

ITEM_JOB_DESC = "蔚蓝空域职业大纲"
ITEM_JOB_DESC_OTHER = "蔚蓝空域职业大纲-附录"


@plot(*BOUND_HR_FRONT)
def hr_front(player: Player) -> None:
    p = sys.putils
    with p.RotationCtrl(player):
        NAME = "前台"
        text = p.plot_box_print(
            player, NAME, "您好， " + player.name + "。有什么可以帮您的吗？", delay=0
        )
        section = p.plot_box_print_with_choice(
            player,
            text,
            ["我想来办理工作手续。"],
            hr_front.get_available_choices_insertions(player),
        )
        match section:
            case 0:
                p.plot_box_print(player, NAME, "目前手续办理还未开放哦。")


hr_front.set_as_main()


@plot(*BOUND_HR_FRONT_START)
def hr_front_start(player: Player) -> None:
    NAME = "咨询员"
    p = sys.putils
    if not sys.get_state(player, S_JOB_SELECTED):
        p.plot_box_print(player, NAME, "稍等， 正在查询您的档案...")
        p.plot_box_print(
            player, NAME, "看起来您之前并没有任何在岗档案， 正在帮您寻找空缺的职位..."
        )
        ptext = p.plot_box_print(
            player,
            NAME,
            "当前正在招pin且适合的岗位有§6邮递员§f、 §6环卫工§f和§6建材搬运工§f...",
        )
        p.plot_box_print_with_choice(player, ptext, ["想看看职业简要说明。"])
        p.plot_box_print(
            player,
            NAME,
            "这是这三份职业的职业手册。 您可以详细查看后再决定需要选择哪一个。",
        )
        sys.rpg.backpack_holder.giveItem(
            player, sys.rpg.item_holder.createItem("蔚蓝空域职业大纲")
        )
        p.simple_actionbar_print(
            player, "一张小纸条从手册的背面脱落了下来， 你拾起了它..."
        )
        sys.rpg.backpack_holder.giveItem(
            player, sys.rpg.item_holder.createItem("蔚蓝空域职业大纲-附录")
        )
        sys.set_state(player, S_JOB_SELECTED, True)
    else:
        ptext = p.plot_box_print(
            player, NAME, "做好打算了吗？ 如果没有， 可以再查看一下手册。"
        )
        resp = p.plot_box_print_with_choice(
            player, ptext, ["邮递员。", "环卫工。", "建材搬运工。", "我再想想。"]
        )
        if resp == 0:
            sys.game_ctrl.sendwocmd(
                f"execute as {player.safe_name} run tellraw @a[tag=sr.rpg_bot] "
                '{"rawtext":[{"text":"career.madd"},{"selector":"@s"},{"text":"邮递员"}]}'
            )
            sys.add_quest(player, Q_mail_deliver_recv)
        elif resp == 1:
            sys.game_ctrl.sendwocmd(
                f"execute as {player.safe_name} run tellraw @a[tag=sr.rpg_bot] "
                '{"rawtext":[{"text":"career.madd"},{"selector":"@s"},{"text":"环卫工"}]}'
            )
            sys.add_quest(player, Q_cleaner_recv)
        elif resp == 2:
            sys.game_ctrl.sendwocmd(
                f"execute as {player.safe_name} run tellraw @a[tag=sr.rpg_bot] "
                '{"rawtext":[{"text":"career.madd"},{"selector":"@s"},{"text":"建材搬运工"}]}'
            )
            sys.add_quest(player, Q_carrier_recv)
        elif resp == 3:
            p.plot_box_print(player, NAME, "好的， 这确实需要您慎重选择。")
        if resp in range(3):
            p.plot_box_print(
                player,
                NAME,
                "已经为您在数据库登记好职业， 自动分配工位了， 您现在可以立刻就职。",
            )
            sys.finish_quest(player, Q_goto_hr)
            sys.set_state(player, S_JOB_SELECTED, True)
    p.enable_movement(player)


hr_front_start.set_insertion(
    lambda player: sys.putils.player_is_in_quest(player, Q_goto_hr.tag_name)
)


@plot(*BOUND_MAIL_CONSULTANT)
def mail_manager(player: Player):
    p = sys.putils
    NAME = "邮政咨询员"
    with p.RotationCtrl(player):
        text = p.plot_box_print(
            player,
            NAME,
            "您需要购买邮票、寄送邮件还是查询邮政编号？",
        )
        section = p.plot_box_print_with_choice(
            player,
            text,
            ["我还有点事， 先走了。"],
            mail_manager.get_available_choices_insertions(player),
        )
        match section:
            case 0:
                p.enable_movement(player)
                return


mail_manager.set_as_main()


@plot(*BOUND_MAIL_CONSULTANT_WORK)
def mail_manager_work(player: Player):
    p = sys.putils
    p.disable_movement(player)
    NAME = "邮政咨询员"
    p.plot_box_print(
        player,
        NAME,
        "啊..欢迎！新来的派送员吗？可以到我的左手边， 在那块§6绿色地板§f上按动按钮就可以领取需要配送的邮件了。",
    )
    p.plot_box_print(
        player, NAME, "噢， 还有， 别一次性领取太多邮件， 负重太多配送起来很不方便的。"
    )
    p.plot_box_print(
        player,
        NAME,
        "如果你不知道你还有多少邮件需要配送， 你可以在终端上打开§6职业菜单>邮递员§f，就可以看到你需要配送的邮件和地址了。",
    )
    sys.finish_quest(player, Q_mail_deliver_recv)
    sys.add_quest(player, Q_mail_deliver_work)
    p.enable_movement(player)


mail_manager_work.set_choice_insertion(
    "§e我是新来的邮递员。",
    lambda player: sys.putils.player_is_in_quest(player, Q_mail_deliver_recv.tag_name),
)


@plot(*BOUND_CLEANER)
def recycle_station(player: Player):
    p = sys.putils
    with p.RotationCtrl(player):
        NAME = "回收站工人"
        ptext = p.plot_box_print(
            player, NAME, "收购~电视机~冰箱~洗衣机~烂拖鞋~大平卖...", delay=1
        )
        section = p.plot_box_print_with_choice(
            player,
            ptext,
            ["回收垃圾。"],
            recycle_station.get_available_choices_insertions(player),
        )
        if section == 0:
            sys.game_ctrl.sendwocmd(
                f'tellraw @a[tag=sr.rpg_bot] {{"rawtext":[{{"text":"job.garbage.submit"}},{{"selector":"{player.name}"}}]}}'
            )


recycle_station.set_as_main()


@plot(*BOUND_CLEANER_WORK)
def recycle_station_working(player: Player):
    p = sys.putils
    NAME = "回收站工人"
    p.disable_movement(player)
    p.plot_box_print(
        player,
        NAME,
        "我知道你想问什么——域内分布着很多§6垃圾桶§f， 在街道上， 或者一些大型商场之类的。 ",
    )
    p.plot_box_print(
        player,
        NAME,
        "如果你看到一个木桶上面摆着一个§6烟熏炉§f一样的东西， 你就需要§6点击木桶§f来拾走里面的垃鸡。 你可以把回收的垃鸡都交给我， 我会给你相应的报酬。先去旁边的商场里拿走些垃鸡交给我吧！",
    )
    sys.finish_quest(player, Q_cleaner_recv)
    sys.add_quest(player, Q_cleaner_work)
    p.enable_movement(player)


recycle_station_working.set_choice_insertion(
    "§e我来入职..",
    lambda player: sys.putils.player_is_in_quest(player, Q_cleaner_recv.tag_name),
)


@plot(*BOUND_CARRIER)
def carrier(player: Player):
    p = sys.putils
    with p.RotationCtrl(player):
        NAME = "慵懒的监工"
        p.disable_movement(player)
        text = p.pprint(player, NAME, "呼..呼...", 1, 1)
        p.choice(
            player,
            text,
            ["（离开。）"],
            carrier.get_available_choices_insertions(player),
        )


carrier.set_as_main()


@plot(*BOUND_CARRIER_WORK)
def carrier_start(player: Player):
    p = sys.putils
    NAME = "懒惰的监工"
    p.pprint(player, NAME, "嗯..", delay=1)
    p.pprint(
        player,
        NAME,
        "新来的啊， 看到我左边的这个§6竹块§f了吗？ 上面有一个按钮， 点击按钮就可以得到需要搬运的建材了。",
        delay=1,
    )
    p.pprint(
        player,
        NAME,
        "然后， 你到旁边的建筑上， 通过脚手架爬到最高层下边， 再把建材放到§6允许方块§f上， 再点击旁边的§6音符盒§f， 就可以码放提交建材方块了。",
    )
    p.pprint(
        player,
        NAME,
        "然后， 你到旁边的建筑上， 通过脚手架爬到最高层下边， 再把建材放到§6允许方块§f上， 再点击旁边的§6音符盒§f， 就可以码放提交建材方块了。",
    )
    p.pprint(
        player, NAME, "让你提交多少建材你就提交多少， 别偷工减料啊。 现在去试试吧。"
    )
    sys.finish_quest(player, Q_carrier_recv)
    sys.add_quest(player, Q_carrier_work)


carrier_start.set_choice_insertion(
    "§e我来入职..",
    lambda player: sys.putils.player_is_in_quest(player, Q_carrier_recv.tag_name),
)

Q_goto_hr = sys.LegacyQuest(
    tag_name=plotpath / "前往人力资源部",  # 蔚蓝空域/职业入门:前往人力资源部
    disp_name=GLOBAL_NAME,
    priority=3,
    description="前往人力资源部寻找工作",
    cooldown=None,
    position=(220, 201, 322),
    add_quest_cb=None,
    detect_cb=None,
    finish_cb=None,
)
sys.regist_quest(Q_goto_hr)

Q_cleaner_recv = sys.LegacyQuest(
    tag_name=plotpath / "环卫工-接取工作",
    disp_name=GLOBAL_NAME,
    priority=3,
    description="接取环卫工工作",
    cooldown=None,
    position=(512, 198, 305),
    add_quest_cb=None,
    detect_cb=None,
    finish_cb=None,
)
sys.regist_quest(Q_cleaner_recv)

Q_cleaner_work = sys.LegacyQuest(
    tag_name=plotpath / "环卫工-工作",
    disp_name=GLOBAL_NAME,
    priority=3,
    description="找到一个垃圾桶..然后取走里面的垃鸡！",
    cooldown=None,
    position=None,
    add_quest_cb=None,
    detect_cb=None,
    finish_cb=None,
)
sys.regist_quest(Q_cleaner_work)

Q_carrier_recv = sys.LegacyQuest(
    tag_name=plotpath / "建材搬运工-接取工作",
    disp_name=GLOBAL_NAME,
    priority=3,
    description="接取建材搬运工工作",
    cooldown=None,
    position=(543, 198, 359),
    add_quest_cb=None,
    detect_cb=None,
    finish_cb=None,
)
sys.regist_quest(Q_carrier_recv)

Q_carrier_work = sys.LegacyQuest(
    tag_name=plotpath / "建材搬运工-工作",
    disp_name=GLOBAL_NAME,
    priority=3,
    description="接取建材， 运送并码放到指定地点",
    cooldown=None,
    position=(540, 278, 396),
    add_quest_cb=None,
    detect_cb=None,
    finish_cb=None,
)
sys.regist_quest(Q_carrier_work)

Q_mail_deliver_recv = sys.LegacyQuest(
    tag_name=plotpath / "邮递员-接取工作",
    disp_name=GLOBAL_NAME,
    priority=3,
    description="接取邮递员工作",
    cooldown=None,
    position=(446, 198, 273),
    add_quest_cb=None,
    detect_cb=None,
    finish_cb=None,
)
sys.regist_quest(Q_mail_deliver_recv)

Q_mail_deliver_work = sys.LegacyQuest(
    tag_name=plotpath / "邮递员-工作",
    disp_name=GLOBAL_NAME,
    priority=3,
    description="接取第一份邮件， 并投放到指定地点",
    cooldown=None,
    position=(450, 198, 276),
    add_quest_cb=None,
    detect_cb=None,
    finish_cb=None,
)
sys.regist_quest(Q_mail_deliver_work)

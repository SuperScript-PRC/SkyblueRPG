from tooldelta import Player
from dev_customrpg_plot import plot, get_system  # type: ignore

BOUND_ENTRANCE = "进入", "开始实验室-接入点"
BOUND_UNKNOWN_SPACE_0 = "未知空间", "未知空间-0"
BOUND_UNKNOWN_SPACE_1 = "未知空间1", "未知空间-1"
BOUND_UNKNOWN_SPACE_2 = "未知空间2", "未知空间-2"
BOUND_UNKNOWN_SPACE_RECALL = "未知空间-回忆", "未知空间-3"
BOUND_BIRCHSIDE_RESIDENT = "新手向导", "温带桦林-河心居民"
BOUND_BIRCHSIDE_RESIDENT_STARTSTAGE = "新手向导-开始剧情", "温带桦林-河心居民"
BOUND_AIRSHIP = "飞艇", "温带桦林-飞艇"
BOUND_AIRSHIP_FIRST = "飞艇首次", "温带桦林-飞艇"
BOUND_FIRST_DOWN = "首次落地", "蔚蓝空域-空艇总站"

Q_GETOUT = "未知空间/intro:找出口"
Q_GO_OUTDOOR = "未知空间/intro:出门"
Q_GOTO_AIRSHIP = "未知空间/intro:前往飞艇"
Q_MEMBER_REGISTRATION = "未知空间/intro:成员登记"

S_FIRSTTIME_ITEM_GETTED = "未知空间/intro:开始剧情物品领取"

sys = get_system()


@plot(*BOUND_ENTRANCE)
def entrance(player: Player):
    # 进入.tds
    p = sys.putils
    p.set_movement(player, False)
    ptext = p.plot_box_print(
        player,
        "调试员",
        "终于到最后的采样阶段了... 噢， "
        + player.name
        + "， 您现在确定要开始连接了吗？ 晴川小姐说她稍后会也会连接上来。",
        delay=0,
    )
    resp = p.plot_box_print_with_choice(
        player,
        ptext,
        ["今天的日程安排有什么？", "开始吧， 一鼓作气做完。", "我先休息一下。"],
    )
    if resp == 0:
        p.plot_box_print(
            player,
            "调试员",
            "您的日程表上今天只有对总线区域进行采样的说明， 除此以外直到星期一机房都没有任何安排了。",
        )
        p.set_movement(player, True)
        return
    elif resp == 1:
        p.plot_box_print(
            player,
            "调试员",
            "好的... 在连接之前， 其他几个人说是给您留一点东西， 以便这次采样的时候使用。",
        )
    elif resp == 2:
        p.plot_box_print(
            player,
            "调试员",
            "好的， 身体要紧， 您要是出了问题， 整个译解都会进行不下去。",
        )
        p.set_movement(player, True)
        return

    if not sys.get_state(player, S_FIRSTTIME_ITEM_GETTED):
        sys.rpg.backpack_holder.giveItem(player, sys.rpg.item_holder.createItem("SwordWuMing"))
    p.plot_box_print(
        player,
        "调试员",
        "这是枫先生说要留给您的， 说什么这把剑在身可以增加运气...",
    )
    if not sys.get_state(player, S_FIRSTTIME_ITEM_GETTED):
        sys.rpg.backpack_holder.giveItem(player, sys.rpg.item_holder.createItem("烤全鸡", 5))
    sys.set_state(player, S_FIRSTTIME_ITEM_GETTED, True)
    p.plot_box_print(
        player,
        "调试员",
        "这是莉莉小姐说要留给您的， 说您昨晚吃的很少， 特意顺路买下来的。 这还有段私人消息...",
    )
    p.plot_box_print(
        player,
        "<是莉莉莉莉吖>",
        player.name
        + "， 今晚一定要来门口那块地哦， 今晚开点心大会！ 记得留点肚子吃东西！",
    )
    p.trans(player, 1, 3, 1, 0x000000)
    p.plot_box_print(
        player,
        "调试员",
        "那么...开始连接吧。",
    )
    p.tp(player, (585, 262, -44))
    with p.snowball_ignorer(player):
        p.sleep(player, 0.5)
        fx = sys.spx.FXStage(player)
        fx.set_delay(0.3)
        fx.print("SKYBLUE EMULATOR BIOS BOOTSTRAPING..")
        for _ in range(3):
            fx.cprint(".")
        fx.cprint("OK")
        fx.beep()
        fx.set_delay(0.4)
        fx.print("Swaping memory..")
        fx.rprint("Swaping memory.. 0 Bytes")
        fx.rprint("Swaping memory.. 131,072 Bytes")
        fx.rprint("Swaping memory.. 262,144 Bytes")
        fx.rprint("Swaping memory.. 524,288 Bytes")
        fx.rprint("Swaping memory.. 1,048,576 Bytes")
        fx.rprint("Swaping memory.. 1,048,576 Bytes swaped")
        fx.beep()
        fx.set_delay(0.1)
        fx.print("Checking BRAM..")
        fx.set_delay(0.3)
        fx.rprint("Checking BRAM.. 0 Bytes")
        fx.rprint("Checking BRAM.. 1,152,921,504,606,846,976 Bytes")
        fx.print("Checking BRAM.. 1,152,921,504,606,846,976 Bytes avaliable")
        fx.set_delay(0.1)
        for lb in ("emulator", "chunkloader", "entity", "camrea", "ticking"):
            fx.print(f"Loading lib{lb}.so")
        for chrrom in ("BG1", "BG2", "SP1", "SP2", "BANKING"):
            fx.print(f"Loading {chrrom}.chr")
        for pcm in ("note.pling", "note.harp", "note.bit", "note.snare", "note.bass"):
            fx.print(f"Loading {pcm.replace('.', '_dot_')}.pcm")
        fx.print("")
        fx.beep()
        fx.set_delay(0.1)
        for _ in range(10):
            fx.rprint("Searching for avail pointer.. /")
            fx.rprint("Searching for avail pointer.. -")
            fx.rprint("Searching for avail pointer.. \\")
            fx.rprint("Searching for avail pointer.. |")
        fx.rprint("Searching for avail pointer.. OK")
        fx.rprint("Searching for avail pointer.. OK - entry *3")
        fx.set_delay(0.1)
        fx.print("Extend debugger waiting (42.186.200.42:19132)")
        for _ in range(5):
            fx.rprint("Extend debugger waiting (42.186.200.42:19132) _")
            fx.rprint("Extend debugger waiting (42.186.200.42:19132)")
        fx.rprint("Third-party debugger waiting (42.186.200.42:19132) connected")
        fx.set_delay(0.4)
        fx.print("debugger: LAN handshake complete")
        fx.beep()
        fx.print("language.zsh: set LANG=zh_CN.GBK")
        fx.print("debugger: §a交换机器内存完成")
        fx.beep()
        fx.set_delay(0.1)
        fx.print("debugger: §a交换生物内存完成")
        fx.beep()
        fx.set_delay(0.6)
        fx.print("debugger: §e同步信号已发出， 等待返回..")
        fx.print("debugger: §b现在正在使用同步指针连接至 #BUS-3.")
        fx.set_delay(1)
        fx.beep()
        fx.print("§6debugger: 无法完成用户要求的零知识证明")
        fx.print("debugger: 神经元指针已同步至 #BUS-3， 伺服器状态： §a良")
        fx.print("")
    p.trans(player, 2, 5, 2, 0x000000)
    p.plot_box_print(
        player,
        player.name,
        "（同步指针连接上了...）",
    )
    p.tp(player, (239, -53, 19))
    p.sleep(player, 5)
    p.plot_box_print(
        player,
        player.name,
        "（怎么一步都迈不出去？）",
    )
    p.sleep(player, 5)
    p.plot_box_print(
        player,
        player.name,
        "（这...为什么会传送到了这里？ 我现在不应该在命令块总线上吗？）",
    )
    p.set_movement(player, True)
    p.plot_box_print(
        player,
        player.name,
        "（总算能迈开腿了..看看怎么回事吧..）",
        delay=0
    )


entrance.set_as_main()


@plot(*BOUND_UNKNOWN_SPACE_0)
def unknown_space(player: Player):
    p = sys.putils
    p.disable_movement(player)
    if p.is_plot_completed(player, "未知空间"):
        return
    sys.game_ctrl.sendwocmd(
        f"/execute as {player.safe_name} at @s run playsound ambient.cave"
    )
    sys.game_ctrl.sendwocmd(
        f"/execute as {player.safe_name} at @s run playsound ambient.cave"
    )
    sys.game_ctrl.sendwocmd(
        f"/execute as {player.safe_name} at @s run playsound ambient.cave"
    )
    p.plot_box_print(player, player.name, "（这里...好冷...）", delay=3)
    p.simple_actionbar_print(player, "似乎有一阵冷风刮过， 你打了一个寒颤。", delay=3)
    p.plot_box_print(
        player,
        player.name,
        "（难道指针偏移量太大了...）",
    )
    p.enable_movement(player)
    p.start_quest(player, Q_GETOUT)


unknown_space.set_as_main()


@plot(*BOUND_UNKNOWN_SPACE_1)
def unknown_space1(player: Player):
    p = sys.putils
    if p.is_plot_completed(player, "未知空间1"):
        return
    p.set_movement(player, False)
    sys.game_ctrl.sendwocmd(
        f"/execute as {player.safe_name} at @s run playsound ambient.cave"
    )
    p.trans(player, 0, 0, 0, 0x0000ff)
    # p.sleep(player, 0.2)
    # p.trans_clear(player)
    # p.sleep(player, 0.15)
    # p.trans(player, 0, 1, 0, 0x0000ff)
    # p.sleep(player, 0.4)
    # p.trans_clear(player)
    sys.game_ctrl.sendwocmd(
        f"/execute as {player.safe_name} at @s run playsound ambient.cave"
    )
    p.plot_box_print(
        player, "？？？", "§4WARNING: §cCore bootstrap failed..", delay=2, spd=16
    )
    sys.game_ctrl.sendwocmd(
        "/execute as "
        + player.getSelector()
        + " at @s run playsound record.11 @s ~~~ 1 50"
    )
    p.plot_box_print(
        player, "？？？", "§4WARNING: §cCore bootstrap failed..", delay=2, spd=16
    )
    p.plot_box_print(player, player.name, "（这是..？）", delay=0)
    p.trans(player, 0, 0, 0, 0x000099)
    sys.game_ctrl.sendwocmd(
        "/execute as "
        + player.getSelector()
        + " at @s run playsound record.11 @s ~~~ 1 50"
    )
    p.plot_box_print(
        player, "？？？", "§4WARNING: §cCore bootstrap failed..", delay=2, spd=16
    )
    sys.game_ctrl.sendwocmd(
        "/execute as "
        + player.getSelector()
        + " at @s run playsound record.chirp @s ~~~ 1 50"
    )
    p.plot_box_print(
        player,
        "？？？",
        "§4WARNING: §cPlease eject this disk before core dumped!",
        delay=2,
        spd=32,
    )
    p.trans(player, 0, 0, 0, 0x0099aa)
    p.plot_box_print(
        player,
        "？？？",
        "§4WARNING: §cPlease eject this disk before core dumped!",
        delay=2,
        spd=60,
    )

    def explode(pitch: float, waitime: float):
        sys.game_ctrl.sendwocmd(
            "/execute as "
            + player.getSelector()
            + f" at @s run playsound random.explode @s ~~~ 1 {pitch}"
        )
        p.sleep(player, waitime)

    explode(0.2, 0.3)
    explode(0.1, 0.3)
    explode(0.4, 0.2)
    explode(0.3, 0.2)
    explode(0.5, 0.3)
    explode(0.2, 0.3)
    explode(0.1, 0.3)
    explode(0.3, 0.2)
    explode(0.2, 0.2)
    explode(0.2, 0.3)
    p.plot_box_print(
        player,
        player.name,
        "（立刻弹出数据盘？技术部今天没有把命令数据盘装好吗？）",
    )
    p.set_movement(player, True)


unknown_space1.set_as_main()


@plot(*BOUND_UNKNOWN_SPACE_2, disposable=True)
def unknown_space2(player: Player):
    p = sys.putils
    print("Started")

    def explode(pitch: float, waitime: float, volume: float = 1):
        sys.game_ctrl.sendwocmd(
            "/execute as "
            + player.getSelector()
            + f" at @s run playsound random.explode @s ~~~ {volume} {pitch}"
        )
        p.sleep(player, waitime)

    p.finish_quest(player, Q_GETOUT)
    p.set_movement(player, False)
    p.tp(player, (345, -53, 19))
    p.plot_box_print(
        player,
        "？？？",
        "§4WARNING: §cPlease eject this disk before core dumped!",
        delay=1,
        spd=60,
    )
    sys.game_ctrl.sendwocmd(f"/effect {player.safe_name} blindness 999 255 true")
    p.sleep(player, 0.3)
    explode(0.2, 0.3)
    p.plot_box_print(
        player,
        "？？？",
        "快， 去后面的变电室拉闸， 否则一旦采样指针偏移"
        + player.name
        + "就会被困在里面了！！",
        delay=1,
        spd=32,
    )
    p.plot_box_print(
        player,
        "？？？",
        "中控室已经断电了， 现在正在进VNC安全模式..坚持住..",
        delay=1,
        spd=32,
    )
    explode(0.15, 0)
    p.plot_box_print(
        player,
        "？？？",
        "§6WARNING: POWER OFF, Switching emergency battery [SoC Core=1.54V]",
        delay=0,
        spd=16,
    )
    explode(0.1, 0)
    p.plot_box_print(
        player,
        "？？？",
        "▓▓▓， 忘记了， 设置了备用电源， 快去把备用电源也关了！！",
        delay=1,
        spd=32,
    )
    p.plot_box_print(
        player,
        "？？？",
        "备用电源在负一层， 现在恐怕来不及了..",
        delay=1,
        spd=32,
    )
    explode(0.2, 0)
    p.plot_box_print(
        player,
        "？？？",
        "废什么话啊， 赶紧去啊！ 那可是一条人命， 况且还是" + player.name[:4] + "..",
        delay=1,
        spd=32,
    )
    explode(0.15, 0.3)
    sys.game_ctrl.sendwocmd(
        "/execute as "
        + player.getSelector()
        + " at @s run playsound mob.enderdragon.death @s ~~~ 1 0.4"
    )
    p.plot_box_print(
        player,
        "？？？",
        "§4ERROR: §cCore dumped!",
        delay=2,
        spd=16,
    )
    p.plot_box_print(
        player,
        "？？？",
        "糟了..和采样指针断开连接了.. "
        + player.name
        + "！！ 你听得见吗？ 你听得▓▓？ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓",
        delay=1,
        spd=16,
    )
    p.plot_box_print(
        player,
        player.name,
        "（实验室出现了什么意外吗？得赶紧想办法退出指针连接..）",
        delay=0.5,
        spd=16,
    )
    p.plot_box_print(
        player,
        "？？？",
        "§ePointer: §f§lREBO0T ..",
        delay=1,
        spd=8,
    )
    p.plot_box_print(
        player,
        player.name,
        "（不好， 命令链怎么重启了...）",
        delay=0,
        spd=16,
    )
    p.simple_actionbar_print(
        player,
        "来不及过多思考， " + player.name + " 就被突如其来的强震震得昏了过去。",
        speed=16,
        delay=0,
    )
    # HERE finish quest
    explode(1, 0.3)
    explode(0.8, 0.3, 0.8)
    explode(0.6, 0.3, 0.6)
    explode(0.4, 0.3, 0.4)
    p.tp(player, (305, -45, 19), (306, -45, 19))
    explode(0.2, 0.3, 0.2)
    explode(0.1, 0.3, 0.1)
    explode(0.1, 5, 0.1)
    p.plot_box_print(
        player,
        "？？？",
        "§d你不应该出现在这里。 离开。 请你们不要再干扰我们了。",
        delay=2,
        spd=16,
    )
    p.plot_box_print(
        player,
        player.name,
        "（这是？）",
        delay=1,
        spd=8,
    )
    p.plot_box_print(
        player,
        player.name,
        "（已经分辨不出来这声音是外界还是脑海里面的了...想办法断开连接吧。）",
        delay=0,
        spd=8,
    )
    sys.game_ctrl.sendwocmd(f"/effect {player.safe_name} blindness 0 0")
    p.set_movement(player, True)


unknown_space2.set_as_main()


@plot(*BOUND_UNKNOWN_SPACE_RECALL)
def unknown_space_recall(player: Player):
    p = sys.putils
    p.set_movement(player, False)
    sys.game_ctrl.sendwocmd(f"/effect {player.safe_name} blindness 999 255 true")
    p.plot_box_print(player, player.name, "（...）", delay=3)
    p.plot_box_print(
        player,
        "Karina？",
        "...机组的第一天测试， 你确定真的可以自己亲自试验吗？",
        delay=3,
    )
    p.plot_box_print(player, "枫？", "好， 你躺在这别动...", delay=3)
    p.plot_box_print(player, player.name, "（....）", delay=3)
    p.plot_box_print(
        player, "枫？", "看起来这次还算成功， 应该不会带来什么副作用吧...", delay=3
    )
    p.plot_box_print(
        player, "莉莉？", "没问题， 等我备份一下今天的测试数据， 明天继续...", delay=3
    )
    p.plot_box_print(player, player.name, "（.....）", delay=3)
    p.plot_box_print(
        player,
        "晴川？",
        "今天可是算第二次测试了喔， 这次需要我来和你进去进行采样...",
        delay=3,
    )
    p.plot_box_print(
        player,
        "枫？",
        "这次务必小心。 你进入后所在的命令链区域在总线和外围之间， 很容易发生突发情况。",
        delay=3,
    )
    p.plot_box_print(player, player.name, "（......）", delay=3)
    p.plot_box_print(
        player,
        "晴川？",
        "终于出来了， 呀， 困死了...",
        delay=3,
    )
    p.plot_box_print(
        player,
        "枫？",
        player.name + "， 看起来你的脸色不太好？ 你需要休息一两天了...",
        delay=3,
    )
    p.plot_box_print(
        player,
        "莉莉？",
        "那我备份数据去了...咦？ "
        + player.name
        + "， 你过来看看， 你到过这里吗？ 为什么日志显示你把这片区域的指令也采样了？",
        delay=3,
    )
    p.plot_box_print(player, player.name, "（......）", delay=1)
    p.plot_box_print(player, player.name, "（头好痛...）", delay=3)
    p.plot_box_print(
        player,
        "Karina？",
        "现在是最后一天测试， 补全这块区域， 现阶段就算是大功告成了。 加油！",
        delay=3,
    )
    p.plot_box_print(
        player,
        "枫？",
        "但是" + player.name + "的状态貌似不是很好...",
        delay=3,
    )
    p.plot_box_print(
        player,
        "晴川？",
        "就今天一天了， 我们做快点， 弄好了之后我们放个小长假怎么样？",
        delay=3,
    )
    p.plot_box_print(player, player.name, "（眩晕...）", delay=3)
    p.plot_box_print(player, player.name, "（......）", delay=1, spd=16)
    p.plot_box_print(player, player.name, "（......）", delay=1, spd=16)
    sys.game_ctrl.sendwocmd(
        "/execute as "
        + player.getSelector()
        + " at @s run playsound random.explode @s ~~~ 1 0.6"
    )
    p.plot_box_print(
        player,
        "莉莉？",
        "快， 去后面的变电室拉闸， 否则一旦写入完成"
        + player.name
        + "就会被困在里面了！！",
        delay=1,
        spd=32,
    )
    sys.game_ctrl.sendwocmd(
        "/execute as "
        + player.getSelector()
        + " at @s run playsound random.explode @s ~~~ 1 0.6"
    )
    p.plot_box_print(
        player,
        "枫？",
        "中控室已经断电了， 现在正在进安全模式.. 坚持住啊..",
        delay=1,
        spd=32,
    )
    p.plot_box_print(player, player.name, "（快撑不住了..）", delay=3)
    p.plot_box_print(
        player,
        "晴川？",
        "废什么话啊， 赶紧去啊！..",
        delay=1,
        spd=32,
    )
    p.trans(player, 5, 10, 5, 0x000000)
    sys.game_ctrl.sendwocmd(f"/effect {player.safe_name} blindness 0 0")
    p.tp(player, (333, -53, 19))
    p.plot_box_print(player, player.name, "（感觉..意识和记忆..在被剥离...）", delay=2)
    p.plot_box_print(player, player.name, "（..在..遗忘...）", delay=2)
    p.plot_box_print(player, player.name, "（...你们是谁？）", delay=3, spd=3)
    p.tp(player, (233, 63, -44))
    p.sleep(player, 5)
    p.plot_box_print(
        player,
        player.name,
        "（感觉大脑还是昏昏沉沉的...）",
        delay=3,
    )
    p.plot_box_print(
        player,
        player.name,
        "（唔...我又躺在哪里...我回▓▓了吗？）",
        delay=3,
    )
    p.simple_actionbar_print(player, "你发现了一张不起眼的小纸条被塞到了你的衣领上。")
    ptext = p.simple_actionbar_print(
        player,
        player.name
        + "， 不知道你能不能收到这张纸条... 这次的实验采样失败了， 命令指针发生了严重偏移， 采样到 /camera 命令的时候主内存溢出了， 我们两个进来采样恐怕很难出去了。 我离你的距离应该很远， 我用游戏刻空洞给你发来这张小纸条很吃力， 很快空洞要被自动销毁了， 可能再也没办法和你通信了。 在我写下这段话的时候你可能还在昏迷状态...之后我们还能再见到吗？ ...祝好， 我们若有机会， 还做同事。 ————晴川",
    )
    resp = p.plot_box_print_with_choice(
        player, ptext, ["晴川？", "她是谁？", "我好像想起来了..."]
    )
    if resp == 0 or resp == 2:
        p.simple_actionbar_print(
            player,
            "晴川？",
        )
        p.simple_actionbar_print(
            player,
            "你在努力回想着这个名字..",
        )
        p.simple_actionbar_print(
            player,
            "你越努力想， 思绪就越空虚。 好像有一股无名的力量阻挠着你的回忆。",
        )
    else:
        p.simple_actionbar_print(
            player,
            "似乎没有办法更深入回忆了。",
        )
    sys.rpg.backpack_holder.giveItem(player, sys.rpg.item_holder.createItem("小纸条-开始-1"))
    p.simple_actionbar_print(
        player,
        "什么实验？ 命令指针、 采样空洞都是什么？ 为什么一点也记不起来了？",
    )
    ptext = p.simple_actionbar_print(
        player,
        "你努力回想这之前都发生了什么， 却发现再也无法回忆过去， 除了名字几乎什么也记不起来了...",
    )
    p.plot_box_print_with_choice(player, ptext, ["这是..失忆了吗？", "老掉牙的剧本.."])
    p.plot_box_print(
        player, player.name, "（还是出去走走看吧， 说不定就能想起来点什么了呢。）"
    )
    p.start_quest(player, Q_GO_OUTDOOR)
    p.set_movement(player, True)


unknown_space_recall.set_as_main()


@plot(*BOUND_BIRCHSIDE_RESIDENT)
def guide(player: Player):
    p = sys.putils
    NAME = "悠闲的居民"
    text = p.plot_box_print(player, NAME, "...")
    section = p.plot_box_print_with_choice(
        player,
        text,
        ["..."],
        extra_insertion_sections=guide.get_available_choices_insertions(player),
    )
    if section == 0:
        p.simple_actionbar_print(player, "这位中年大叔把头偏到了另外一边。")


guide.set_as_main()


@plot(*BOUND_BIRCHSIDE_RESIDENT_STARTSTAGE)
def guide_startstage(player: Player):
    p = sys.putils
    NAME = "悠闲的居民"
    p.plot_box_print(
        player,
        NAME,
        "小伙子，你是第一次来这里玩吗？",
    )
    ptext = p.plot_box_print(
        player, player.name, "（看来我得找个地方好让我知道我这是在哪...）"
    )
    p.plot_box_print_with_choice(player, ptext, ["附近有什么城市吗？"])
    ptext = p.plot_box_print(
        player,
        NAME,
        "嗼...桦林附近确实没有什么城镇...除了§b蔚蓝空域§f， 你应该就是想来这里的吧？",
    )
    while 1:
        resp = p.plot_box_print_with_choice(
            player, ptext, ["蔚蓝空域？", "可以告诉我怎么去吗？"]
        )
        if resp == 0:
            p.plot_box_print(
                player,
                NAME,
                "蔚蓝空域主岛集群， 你居然还没了解过？ 附近最有名的大商圈... 哎， 真是花里胡哨的。 上面的生活节奏老快了， 我受不了才下来住的。",
            )
        else:
            p.plot_box_print(
                player,
                NAME,
                "这附近有飞艇待客点， 每十几分钟就会有一艘飞艇经过， 你可以搭飞艇上去。 最近节假日有补助， 不需要花钱就能坐。",
            )
            p.plot_box_print(
                player,
                NAME,
                "嗯， 现在正好是飞艇到站时间， 现在赶过去说不定还能立刻搭上。",
            )
            p.finish_quest(player, Q_GO_OUTDOOR)
            p.start_quest(player, Q_GOTO_AIRSHIP)
            break


guide_startstage.set_choice_insertion(
    "§e我刚来到这里...",
    lambda p: sys.putils.player_is_in_quest(p, Q_GO_OUTDOOR),
)


@plot(*BOUND_AIRSHIP)
def airship(player: Player):
    p = sys.putils
    p.set_movement(player, False)
    sys.game_ctrl.sendwocmd(f"effect {player.safe_name} blindness 4 0 true")
    p.sleep(player, 3)
    p.tp(player, (310, 206, 263))
    p.set_movement(player, True)


airship.set_as_main()


@plot(*BOUND_AIRSHIP_FIRST)
def airship_first(player: Player):
    p = sys.putils
    with p.MovementLimiter(player):
        p.plot_box_print(
            player,
            "（广播）",
            "飞艇即将起飞， 乘客们请坐好并放置好行李...",
            delay=1,
        )
        sys.game_ctrl.sendwocmd(f"effect {player.safe_name} blindness 7 0 true")
        p.sleep(player, 5)
        p.tp(player, (310, 206, 263))
        p.plot_box_print(
            player,
            "（广播）",
            "已到达蔚蓝空域， 请乘客们有序下艇。",
            delay=1,
        )
        p.finish_quest(player, Q_GOTO_AIRSHIP)


airship_first.set_insertion(lambda p: sys.putils.player_is_in_quest(p, Q_GOTO_AIRSHIP))


@plot(*BOUND_FIRST_DOWN, disposable=True)
def first_landing(player: Player):
    sys.putils.set_movement(player, False)
    sys.putils.plot_box_print(
        player,
        player.name,
        "（这就是他们说的蔚蓝空域吗...真大...）",
        delay=1,
    )
    sys.putils.set_movement(player, False)
    sys.putils.plot_box_print(
        player, "广播", "观光飞艇已经到站， 游客可在下方右侧的成员登记处登记身份信息。"
    )
    sys.putils.plot_box_print(player, player.name, "（..登记个人信息？ 去看看吧...）")
    sys.putils.start_quest(player, Q_MEMBER_REGISTRATION)
    sys.putils.set_movement(player, True)


first_landing.set_as_main()

# ...

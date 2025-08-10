if 0:
    from .. import CustomRPGTutorial
    from .. import Player

tag_name = "pve"
show_name = "战斗"

def entry(sys: "CustomRPGTutorial", player: "Player"):
    with sys.create_tutorial_env(player) as e:
        e.show_by_plot_async("找到一个怪物， 使用§e物品栏第一格的剑§r击败它。")
        e.wait_check_point("自定义RPG:击杀生物")
        e.show_by_plot_async("点击物品栏第二格的§e铁锭§r预备技能。")
        e.wait_check_point("自定义RPG:选中技能")
        e.show_by_plot_async("现在切换回物品栏第一格的剑， 然后§e攻击目标以§r释放技能。")
        e.wait_check_point("自定义RPG:使用技能")
        e.show_by_plot_async(
            "技能释放完毕后， 铁锭会变成有耐久条的头盔， 头盔耐久表示技能的冷却时间。"
        )
        e.show_by_plot_async(
            "继续战斗， 为终结技充能， 充能进度在物品栏第三格的金头盔以耐久条的形式展示。"
        )
        e.wait_check_point("自定义RPG:终结技充能完成")
        e.show_by_plot_async(
            "充能完成， 终结技可以释放了！点击物品栏第三格的§e金锭§r预备终结技。"
        )
        e.wait_check_point("自定义RPG:选中终结技")
        e.show_by_plot_async("现在切换回物品栏第一格的剑， 然后§e攻击目标以§r释放终结技。")
        e.wait_check_point("自定义RPG:使用终结技")
        e.show_by_plot_async("恭喜， 你现在已经掌握了战斗的主要技巧了！")

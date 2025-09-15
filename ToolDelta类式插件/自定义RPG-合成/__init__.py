import json
from dataclasses import dataclass
from tooldelta import Plugin, plugin_entry, Player, TYPE_CHECKING, cfg, utils


@dataclass
class Recipe:
    inputs: dict[str, int]
    outputs: dict[str, int]

    def can_craft(
        self,
        player: Player,
    ):
        hdr = entry.rpg.backpack_holder
        needs_and_have = {
            k: (v, hdr.getItemCount(player, k)) for k, v in self.inputs.items()
        }
        return all(have >= need for need, have in needs_and_have.values())

    def display(self, player: Player):
        bhdr = entry.rpg.backpack_holder
        ihdr = entry.rpg.item_holder
        needs_and_have = {
            ihdr.getOrigItem(k).force_disp(): (v, bhdr.getItemCount(player, k))
            for k, v in self.inputs.items()
        }
        can_craft = all(have >= need for need, have in needs_and_have.values())
        outputs = {ihdr.getOrigItem(k).force_disp(): v for k, v in self.outputs.items()}
        inputs_str = "+".join(
            f"§f{disp_name}§r§7x[{'§' + 'ac'[have < need]}{have}§7/{need}]"
            for disp_name, (need, have) in needs_and_have.items()
        )
        outputs_str = "+".join(
            f"§f{disp_name}§r§7x{amount}" for disp_name, amount in outputs.items()
        )
        return f"§7[{('§cx', '§a√')[can_craft]}§7] " + inputs_str + "§f➪" + outputs_str

    def craft(self, player: Player):
        for item_id, amount in self.inputs.items():
            entry.rpg.backpack_holder.clearItem(player, item_id, amount)
        for item_id, amount in self.outputs.items():
            entry.rpg.backpack_holder.giveItems(
                player, entry.rpg.item_holder.createItems(item_id, amount)
            )


class CustomRPGCrafting(Plugin):
    name = "自定义RPG-合成"
    author = "ToolDelta"
    version = (0, 0, 1)

    def __init__(self, frame):
        super().__init__(frame)
        self.ListenPreload(self.on_def)
        self.recipes: dict[str, dict[str, list[Recipe]]] = {}

    def on_def(self):
        self.rpg = self.GetPluginAPI("自定义RPG")
        self.backpack = self.GetPluginAPI("虚拟背包")
        self.snowmenu = self.GetPluginAPI("雪球菜单v3")
        self.sight = self.GetPluginAPI("视角菜单")
        self.cb2bot = self.GetPluginAPI("Cb2Bot通信")
        self.behavior = self.GetPluginAPI("行为监测")
        if TYPE_CHECKING:
            global SlotItem, Item
            from ..自定义RPG import CustomRPG
            from ..虚拟背包 import VirtuaBackpack, SlotItem, Item
            from ..雪球菜单v3 import SnowMenuV3
            from ..前置_视角菜单 import SightRotation
            from ..前置_行为监测 import ActionListener

            self.rpg: CustomRPG
            self.backpack: VirtuaBackpack
            self.snowmenu: SnowMenuV3
            self.sight: SightRotation
            self.behavior: ActionListener
        for file in self.data_path.iterdir():
            if file.is_file():
                content = file.read_text("utf-8")
                try:
                    thiscfg = json.loads(content)
                    cfg.check_auto(
                        cfg.AnyKeyValue(
                            cfg.AnyKeyValue(
                                cfg.JsonList(
                                    {
                                        "输入": cfg.AnyKeyValue(cfg.PInt),
                                        "输出": cfg.AnyKeyValue(cfg.PInt),
                                    }
                                )
                            )
                        ),
                        thiscfg,
                    )
                except Exception as e:
                    self.print(f"§c配置文件 {file.name} 出错: {e}")
                    raise SystemExit from e
                for category1, many_recipes in thiscfg.items():
                    for category2, recipes in many_recipes.items():
                        for recipe in recipes:
                            self.recipes.setdefault(category1, {}).setdefault(
                                category2, []
                            ).append(
                                Recipe(
                                    recipe["输入"],
                                    recipe["输出"],
                                )
                            )
        self.print(
            f"加载了 {len(self.recipes)} 个组类的 {sum(len(i) for i in self.recipes.values())} 个配方"
        )
        self.snowmenu.register_main_page(
            lambda p: self.on_craft(p) and False, "我的合成", priority=-100
        )

    @utils.thread_func("自定义RPG:合成")
    def on_craft(self, player: Player) -> bool:
        def auto_allocate_categories(categories: list[str], yrange=5, xrange=5):
            # 5x5
            categories = categories.copy()
            matrix: list[list[str | None]] = [[None] * xrange for _ in range(yrange)]
            for y in range(yrange):
                for x in range(xrange):
                    if categories:
                        matrix[y][x] = categories.pop(0)
                    else:
                        return matrix
            return matrix

        def simple_calc_len(string: str):
            return (
                sum((1 + (ord(i) > 0x4E00 and ord(i) < 0x9FA5)) for i in string)
                - string.count("§") * 2
            )

        m1 = auto_allocate_categories(["退出", *list(self.recipes.keys())])
        x1 = 0
        y1 = 0

        action = self.sight.HeadAction
        with self.sight.create_env(player) as menu:
            while True:
                first_ln = "§d选择一个分类 §7| §a扔雪球确认 §6上下左右划动屏幕切换选项§r §c扔雪球同时下蹲退出"
                outputs = []
                for _y, yline in enumerate(m1):
                    output_line = ""
                    for _x, elem in enumerate(yline):
                        if elem is None:
                            elem = "无"
                        output_line += (
                            ("§b" if x1 == _x and y1 == _y else "§8")
                            + elem
                            + " " * (12 - simple_calc_len(elem))
                            + " " * 2
                        )
                    outputs.append(output_line)
                match menu.wait_next_action(first_ln + "\n" + "\n\n".join(outputs)):
                    case action.UP:
                        y1 = (y1 - 1) % 5
                    case action.DOWN:
                        y1 = (y1 + 1) % 5
                    case action.LEFT:
                        x1 = (x1 - 1) % 5
                    case action.RIGHT:
                        x1 = (x1 + 1) % 5
                    case action.PLAYER_LEFT:
                        return True
                    case action.SNOWBALL_EXIT:
                        section1 = m1[y1][x1]
                        if section1 == "退出" or self.behavior.is_shifting(player):
                            break
                        elif section1 is None:
                            continue

                        c1 = self.recipes[section1]
                        m2 = auto_allocate_categories(["退出", *c1.keys()])
                        x2 = 0
                        y2 = 0
                        while True:
                            first_ln = "§d选择一个分类 §7| §a扔雪球确认 §6上下左右划动屏幕切换选项 §c下蹲同时扔雪球回退§r"
                            outputs = []
                            for _y, yline in enumerate(m2):
                                output_line = ""
                                for _x, elem in enumerate(yline):
                                    if elem is None:
                                        elem = "--"
                                    output_line += (
                                        ("§b" if x2 == _x and y2 == _y else "§8")
                                        + elem
                                        + " " * (12 - simple_calc_len(elem))
                                        + " " * 2
                                    )
                                outputs.append(output_line)
                            match menu.wait_next_action(
                                first_ln + "\n" + "\n\n".join(outputs)
                            ):
                                case action.UP:
                                    y2 = (y2 - 1) % 5
                                case action.DOWN:
                                    y2 = (y2 + 1) % 5
                                case action.LEFT:
                                    x2 = (x2 - 1) % 5
                                case action.RIGHT:
                                    x2 = (x2 + 1) % 5
                                case action.PLAYER_LEFT:
                                    return False
                                case action.SNOWBALL_EXIT:
                                    section2 = m2[y2][x2]
                                    if section2 == "退出" or self.behavior.is_shifting(
                                        player
                                    ):
                                        break
                                    elif section2 is None:
                                        break
                                    selected_recipes = c1[section2]

                                    y3 = 0
                                    max_section = len(selected_recipes)
                                    can_crafts = [
                                        i
                                        for i in selected_recipes
                                        if i.can_craft(player)
                                    ]
                                    cannot_crafts = [
                                        i
                                        for i in selected_recipes
                                        if not i.can_craft(player)
                                    ]
                                    selected_recipes = can_crafts + cannot_crafts
                                    while True:
                                        output = f"{section1} > {section2}"
                                        for i, recipe in enumerate(selected_recipes):
                                            output += (
                                                f"§r\n{recipe.display(player)}"
                                                + (
                                                    " §r§a< [扔雪球合成]"
                                                    if y3 == i
                                                    else ""
                                                )
                                            )
                                        output += "§r§8"
                                        for _ in range(10 - len(selected_recipes)):
                                            output += "\n--"
                                        output += "§c左划退出 §a扔雪球确定 §6上下划动屏幕进行选择"
                                        match menu.wait_next_action(output):
                                            case action.UP:
                                                y3 = (y3 - 1) % max_section
                                            case action.DOWN:
                                                y3 = (y3 + 1) % max_section
                                            case action.LEFT:
                                                break
                                            case action.RIGHT:
                                                pass
                                            case action.PLAYER_LEFT:
                                                return False
                                            case action.SNOWBALL_EXIT:
                                                recipe = selected_recipes[y3]
                                                if not recipe.can_craft(player):
                                                    self.rpg.show_fail(
                                                        player,
                                                        "无法进行合成， 材料不足",
                                                    )
                                                    continue
                                                recipe.craft(player)
        player.setActionbar("§7[§cx§7] §c合成站已关闭")
        return True


entry = plugin_entry(CustomRPGCrafting, "自定义RPG-合成")

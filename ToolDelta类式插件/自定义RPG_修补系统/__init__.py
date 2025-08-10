from tooldelta import Plugin, fmts, cfg, TYPE_CHECKING, utils, plugin_entry


class CustomRPGRepair(Plugin):
    name = "自定义RPG-修补系统"
    author = "SuperScript"
    version = (0, 0, 1)

    def __init__(self, frame):
        super().__init__(frame)
        CFG_STD = {
            "修补材料等级": cfg.AnyKeyValue(float),
            "消耗货币": str,
            "消耗货币计算公式": str,
        }
        CFG_DEFAULT = {
            "修补材料等级": {"精炼铁锭": 1.0},
            "消耗货币": "蔚蓝点",
            "消耗货币计算公式": "修补耐久/30*材料等级",
        }
        self.cfg, _ = cfg.get_plugin_config_and_version(
            self.name, CFG_STD, CFG_DEFAULT, self.version
        )
        self.ListenPreload(self.on_def)
        self.ListenActive(self.on_inject)

    def on_def(self):
        self.rpg = self.GetPluginAPI("自定义RPG")
        self.jobs = self.GetPluginAPI("自定义RPG-职业")
        self.backpack = self.GetPluginAPI("虚拟背包")
        self.snowmenu = self.GetPluginAPI("雪球菜单v3")
        self.sight = self.GetPluginAPI("视角菜单")
        cb2bot = self.GetPluginAPI("Cb2Bot通信")
        if TYPE_CHECKING:
            global SlotItem
            from 自定义RPG import CustomRPG
            from 自定义RPG_职业 import CustomRPGJobs
            from 虚拟背包 import VirtuaBackpack, SlotItem
            from 雪球菜单v3 import SnowMenuV3
            from 前置_视角菜单 import SightRotation
            from 前置_Cb2Bot通信 import TellrawCb2Bot

            self.rpg: CustomRPG
            self.jobs: CustomRPGJobs
            self.backpack: VirtuaBackpack
            self.snowmenu: SnowMenuV3
            self.sight: SightRotation
            cb2bot: TellrawCb2Bot
        try:
            self.repair_cost_syntax = compile(
                self.cfg["消耗货币计算公式"], filename=self.name, mode="eval"
            )
        except SyntaxError:
            fmts.print_err("消耗货币计算公式 不合法")
            raise SystemExit
        cb2bot.regist_message_cb(
            "sr.anvil.use", lambda x: self.player_repair_item(x[0])
        )
        # tellraw @a[tag=sr.rpg_bot] {"rawtext":[{"text":"sr.anvil.use"},{"selector":"@p"}]}

    def on_inject(self):
        # self.snowmenu.register_main_page(self.player_repair_item, "物品修补")
        for item_tag_name in self.cfg["修补材料等级"].keys():
            if not self.rpg.item_holder.item_exists(item_tag_name):
                fmts.print_err(f"修补系统: 物品不存在: {item_tag_name}")
                raise SystemExit
        if not self.rpg.item_holder.item_exists(self.cfg["消耗货币"]):
            fmts.print_err(f"修补系统: 货币不存在: {self.cfg['消耗货币']}")
            raise SystemExit
        pass

    @utils.thread_func("自定义RPG-修补")
    def player_repair_item(self, playername: str):
        player = self.rpg.getPlayer(playername)
        with utils.ChatbarLock(playername):
            # is_repairist = self.jobs.has_job(player, "修补匠")
            self.snowmenu.set_player_page(player, None)
            syntax = self.repair_cost_syntax
            actions = self.sight.HeadAction
            maybe_can_repair_items = self.backpack.load_backpack(
                player
            ).find_item_by_metadata_key("DBL")
            can_repair_items: list["SlotItem"] = []
            item_max_durability: dict[str, int] = {}
            avali_repair_materials: dict[str, dict[str, int]] = {}
            for slotitem in maybe_can_repair_items:
                if (
                    self.rpg.item_holder.getItemType(tag_name := slotitem.item.id)
                    == "Weapon"
                ):
                    wpcls = self.rpg.find_weapon_class(tag_name)
                    if not hasattr(wpcls, "repair_materials"):
                        continue
                    if slotitem.metadata["DBL"] == wpcls.default_durability:
                        continue
                    avali_repair_materials[tag_name] = wpcls.repair_materials
                    item_max_durability[tag_name] = wpcls.default_durability
                    can_repair_items.append(slotitem)
            tlen = len(can_repair_items)
            if tlen == 0:
                self.rpg.show_inf(player, "暂无需要修补的物品..")
                return False
            now_index = 0
            with self.sight.create_env(player) as e:
                while 1:
                    format_txt = "§b选择待修补的道具§7>"
                    for i in range(now_index - 3, now_index + 4):
                        if i >= 0 and i < tlen:
                            slotitem = can_repair_items[i]
                            if i == now_index:
                                format_txt += "\n§r§e> "
                            else:
                                format_txt += "\n§r§7| "
                            curr_dur = slotitem.metadata["DBL"]
                            max_dur = item_max_durability[slotitem.item.id]
                            format_txt += (
                                f"§f{slotitem.item.show_name} "
                                f"§r§7[§fLv.§e{slotitem.metadata['Lv']}§7] "
                                + self.format_durability_bar(curr_dur, max_dur)
                            )
                        else:
                            format_txt += "\n§r§7| "
                    format_txt += "\n§r§b上下划动屏幕切换， 扔雪球选择"
                    match e.wait_next_action(format_txt):
                        case actions.UP:
                            if now_index > 0:
                                now_index -= 1
                        case actions.DOWN:
                            if now_index < tlen - 1:
                                now_index += 1
                        case actions.SNOWBALL_EXIT:
                            section = can_repair_items[now_index]
                            break
                        case actions.PLAYER_LEFT:
                            return
            item_need_repaired = section
            this_repair_materials: dict[str, int] = avali_repair_materials[
                section.item.id
            ]
            playerhave_materials = {
                m: c
                for m in this_repair_materials.keys()
                if (c := self.rpg.backpack_holder.getItemCount(player, m)) > 0
            }
            if playerhave_materials == {}:
                self.rpg.show_fail(player, "没有任何材料可用于修复该物品")
                self.rpg.show_inf(player, "推荐的材料：")
                for material in this_repair_materials.keys():
                    self.rpg.show_inf(
                        player,
                        "  " + self.rpg.item_holder.getOrigItem(material).show_name,
                    )
                return
            materials = list(playerhave_materials.keys())
            now_index = 0
            material_count = 1
            if materials == []:
                self.rpg.show_fail(player, "你没有任何修补材料")
                return
            # fix: not unbound
            money_cost = 0
            playerhave_vault_count = 0
            # not unbound end
            with self.sight.create_env(player) as e:
                while 1:
                    this_material = materials[now_index]
                    this_material_count = playerhave_materials[this_material]
                    this_material_rep_dur = this_repair_materials[this_material]
                    repair_max_use_mat = 0
                    while 1:
                        if (
                            self.after_repaired(
                                curr_dur,
                                max_dur,
                                this_material_rep_dur,
                                repair_max_use_mat,
                            )
                            >= max_dur
                        ):
                            break
                        repair_max_use_mat += 1
                    if material_count > this_material_count:
                        material_count = this_material_count
                    if material_count > repair_max_use_mat:
                        material_count = repair_max_use_mat
                    curr_dur = section.metadata["DBL"]
                    max_dur = item_max_durability[section.item.id]
                    dur_after_repair = self.after_repaired(
                        curr_dur,
                        max_dur,
                        this_material_rep_dur,
                        material_count,
                    )
                    vault_name = self.rpg.item_holder.getOrigItem(
                        vault := self.cfg["消耗货币"]
                    )
                    playerhave_vault_count = self.rpg.backpack_holder.getItemCount(
                        player, vault
                    )
                    money_cost = int(
                        eval(
                            syntax,
                            {
                                "修补耐久": dur_after_repair - curr_dur,
                                "材料等级": self.cfg["修补材料等级"].get(
                                    this_material, 1
                                ),
                            },
                        )
                    )
                    format_txt = f"§b选择修补材料 §6当前§e{material_count}§6份§7>"
                    for i in range(now_index - 3, now_index + 4):
                        if i >= 0 and i < len(materials):
                            material = materials[i]
                            if i == now_index:
                                format_txt += "\n§r§e> "
                            else:
                                format_txt += "\n§r§7| "
                            format_txt += f"§f{self.rpg.item_holder.getOrigItem(material).show_name} {self.rpg.item_holder.make_item_starlevel(material)}"
                        else:
                            format_txt += "\n§r§7| "
                    fmt_a = self.format_durability_bar(
                        curr_dur,
                        max_dur,
                        new_dur := self.after_repaired(
                            curr_dur,
                            max_dur,
                            this_material_rep_dur,
                            material_count,
                        ),
                    )
                    format_txt += (
                        f"\n§r§7修补结果 §r{fmt_a} §7花费： §"
                        + ("f" if money_cost <= playerhave_vault_count else "c")
                        + f"{money_cost}§7x§f{vault_name.show_name}\n"
                        "§f上下滑动§7切换材料 §f左右滑动§7增减份数， §f扔雪球§7选择"
                    )
                    match e.wait_next_action(format_txt):
                        case actions.UP:
                            if now_index > 0:
                                now_index -= 1
                        case actions.DOWN:
                            if now_index < tlen - 1:
                                now_index += 1
                        case actions.LEFT:
                            if material_count > 1:
                                material_count -= 1
                        case actions.RIGHT:
                            if material_count < min(
                                repair_max_use_mat, this_material_count
                            ):
                                material_count += 1
                        case actions.SNOWBALL_EXIT:
                            section = can_repair_items[now_index]
                            break
                        case actions.PLAYER_LEFT:
                            return False
            if money_cost > playerhave_vault_count:
                self.rpg.show_fail(
                    player, f"§c修复所需辅料不足 §7(§c{money_cost}§f/{money_cost}§7)"
                )
                return
            material_to_repair = this_material
            new_duration = new_dur
            fmt_txt = (
                f"§6目前将使用 §f{material_count} §r§6份 "
                f"§f{self.rpg.item_holder.getOrigItem(material_to_repair).show_name} "
                f"§r§6来修补 §f{item_need_repaired.item.show_name}\n"
            )
            section = self.snowmenu.simple_select_dict(
                player,
                {0: fmt_txt + "§a> 确认   §7取消", 1: fmt_txt + "§7  确认 §c> 取消"},
            )
            if section is None or section == 1:
                return
            # check #2
            if (
                ncount := self.rpg.backpack_holder.getItemCount(
                    player, material_to_repair
                )
            ) < material_count:
                self.rpg.show_fail(
                    player,
                    f"§c修复所需材料不足 (Item count changed: {ncount}/{material_count})",
                )
                return
            if money_cost > playerhave_vault_count:
                self.rpg.show_fail(
                    player, "§c修复所需额外物品不足 (Item count changed)"
                )
                return
            # DANGEROUS: 直接修改物品 metadata
            item_need_repaired.metadata["DBL"] = new_duration
            self.rpg.backpack_holder.clearItem(
                player, material_to_repair, material_count
            )
            self.rpg.backpack_holder.clearItem(player, vault, money_cost)
            self.game_ctrl.sendwocmd(
                f"execute as {player.getSelector()} at @s run playsound random.anvil_use"
            )
            item_name = item_need_repaired.item.show_name
            self.rpg.show_succ(player, f"{item_name} §r§a修复完成")
            player.setActionbar(
                f"{item_name} §r§7耐久: {self.format_durability_bar(new_duration, max_dur)}",
            )

    @staticmethod
    def format_durability_bar(currd: int, maxd: int, extrad: int = 0, T=30):
        _dbar_n = int(currd / maxd * T)
        _dbar_c = "c" if _dbar_n <= 3 else "6" if _dbar_n <= 6 else "a"
        if extrad > 0:
            _dbar_a = int(extrad / maxd * T)
            return (
                f"§{_dbar_c}"
                + "|" * _dbar_n
                + "§d"
                + "|" * (_dbar_a - _dbar_n)
                + "§8"
                + "|" * (T - _dbar_a)
            )
        else:
            return f"§{_dbar_c}" + "|" * _dbar_n + "§8" + "|" * (T - _dbar_n)

    @staticmethod
    def after_repaired(old_dur: int, max_dur: int, mat_rep: int, count: int):
        return min(old_dur + mat_rep * count, max_dur)


entry = plugin_entry(CustomRPGRepair)

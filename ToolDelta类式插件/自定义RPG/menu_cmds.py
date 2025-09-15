from typing import TYPE_CHECKING
from tooldelta import Player, utils
from .rpg_lib.constants import AttackType
from .rpg_lib.rpg_entities import make_entity_panel
from .rpg_lib.utils import list_sub

if TYPE_CHECKING:
    from . import CustomRPG


class MenuCommands:
    def __init__(self, sys: "CustomRPG"):
        self.sys = sys
        self.menu = sys.menu

    def prepare_chatbarmenu(self):
        self.menu.add_new_trigger(
            ["reset-world-spawn"],
            [],
            "查询角色当前的攻击力等信息",
            lambda player, _: self.on_reset_world_spawn(player),
            op_only=True,
        )
        self.menu.add_new_trigger(
            ["个人信息", "prof"],
            [],
            "查询角色当前的攻击力等信息",
            lambda player, _: self.player_check_panel(player),
        )
        self.menu.add_new_trigger(
            ["buf", "buff", "效果列表"],
            [],
            "查看角色自身的效果",
            lambda player, _: self.player_check_effects(player),
        )
        self.menu.add_new_trigger(
            ["rgive"],
            [("物品ID", str, None), ("数量", int, 1), ("玩家", str, "")],
            "给予数据化虚拟物品",
            self.on_menu_give,
            op_only=True,
        )
        self.menu.add_new_trigger(
            ["rclear"],
            [("物品ID", str, None)],
            "清除数据化虚拟物品",
            self.on_menu_clear,
            op_only=True,
        )
        self.menu.add_new_trigger(
            ["rlv"],
            [("等级", int, None), ("经验值", int, None)],
            "更改当前等级和经验值",
            self.on_menu_setlv,
            op_only=True,
        )
        self.menu.add_new_trigger(
            ["rhp"],
            [("生命值", int, None), ("生命值上限", int, None)],
            "更改当前等级和经验值",
            self.on_menu_sethp,
            op_only=True,
        )
        self.menu.add_new_trigger(
            ["rkill"],
            [("范围", int, None)],
            "清除范围内的玩家和生物",
            self.on_menu_killmob,
            op_only=True,
        )
        self.menu.add_new_trigger(
            ["raddexp"],
            [("玩家名", str, None), ("经验值", int, None)],
            "向玩家添加经验",
            self.on_menu_addexp,
            op_only=True,
        )

    def on_reset_world_spawn(self, player: Player):
        self.sys.game_ctrl.sendwocmd("setworldspawn 586 262 -170")
        player.show("§a成功重置世界生成点")

    def on_menu_give(self, player: Player, args: tuple):
        item_id, count, target = args
        if target == "":
            target = player.name
        count = utils.try_int(count)
        target = self.sys.game_ctrl.players.getPlayerByName(target)
        if count is None or count <= 0:
            self.sys.show_fail(player, "指令出错: 数量不正确")
            return
        if target is None:
            self.sys.show_fail(player, "§c指令出错: 玩家不存在")
            return
        try:
            self.sys.backpack_holder.giveItems(
                target, self.sys.item_holder.createItems(item_id, count)
            )
        except Exception as err:
            self.sys.show_fail(player, f"指令出错: {err}")

    def on_menu_clear(self, player: Player, args: tuple):
        if len(args) == 1:
            count = -1
        elif len(args) == 2:
            count = utils.try_int(args[1])
            if count is None or count <= 0:
                self.sys.show_fail(player, "指令出错: 数量不正确")
                return
        else:
            self.sys.show_fail(player, "指令出错: 需要 1~2 个参数")
            return
        item_id = args[0]
        try:
            r = self.sys.backpack_holder.clearItem(player, item_id, count)
            self.sys.show_inf(player, f"已清除自己{r}个物品")
        except ValueError as err:
            self.sys.show_fail(player, f"指令出错: {err}")

    def on_menu_setlv(self, player: Player, args: tuple):
        playerbas = self.sys.player_holder.get_player_basic(player)
        if len(args) == 1:
            exp = playerbas.Exp
        else:
            exp = utils.try_int(args[1])
        lv = utils.try_int(args[0])
        if lv is None or exp is None or lv < 0 or exp < 0:
            self.sys.show_fail(player, "§c无效的等级和经验")
            return
        playerbas.Level = lv
        playerbas.Exp = exp
        self.sys.rpg_upgrade.add_player_exp(player, 0)
        self.sys.player_holder.save_game_player_data(player)
        self.sys.show_inf(
            player,
            f"更改当前等级: Level[{lv}] Exp[{exp}§7/{self.sys.rpg_upgrade.get_levelup_exp(playerbas)}§f]",
        )

    def on_menu_sethp(self, player: Player, args: tuple):
        playerbas = self.sys.player_holder.get_player_basic(player)
        playerinf = self.sys.player_holder.get_playerinfo(player)
        if len(args) == 1:
            hpmax = playerbas.HP_max
        else:
            hpmax = utils.try_int(args[1])
        hp = utils.try_int(args[0])
        if hp is None or hpmax is None or hp < 0 or hpmax < 0:
            self.sys.show_fail(player, "§c无效的HP和HP上限")
            return
        playerbas.HP = hp
        playerbas.HP_max = hpmax
        self.sys.player_holder.update_property_from_basic(playerbas, playerinf)
        self.sys.player_holder.save_game_player_data(player)
        self.sys.show_inf(
            player,
            f"更改当前生命值: HP[{hp}] HPMax[{hpmax}]",
        )
        player.setActionbar(make_entity_panel(playerinf, None))

    def on_menu_killmob(self, player: Player, args: tuple):
        playerinf = self.sys.player_holder.get_playerinfo(player)
        if args == []:
            selector = "r=10"
        else:
            r = utils.try_int(args[0])
            if r is None or r not in range(1, 10000):
                player.show("请输入一个1~10000内的数值")
                return
            selector = f"r={r}"
        players, mobs = self.sys.entity_holder.get_surrounding_entities(
            player.name, selector
        )
        for playerf in players:
            playerf.hp = 0
            playerf.died(playerinf, death_type=AttackType.NORMAL)
        for mob in mobs:
            mob.hp = 0
            mob.died(playerinf, death_type=AttackType.NORMAL)
        self.sys.show_succ(
            player, f"成功清除了 {', '.join(e.name for e in players + mobs)}"
        )

    def player_check_panel(self, player: Player):
        playerinf = self.sys.player_holder.get_playerinfo(player)
        playerinf._update()
        p_orig_hpmax = playerinf.original_hpmax
        p_bas_hpmax = playerinf.basic_hp_max
        bas_hpmax = playerinf.basic_hp_max - p_bas_hpmax
        eff_hpmax = playerinf.tmp_hp_max - p_bas_hpmax - bas_hpmax
        bas_atks = playerinf.basic_atks
        bas_defs = playerinf.basic_defs
        eff_atks = list_sub(playerinf.tmp_atks, playerinf.basic_atks)
        eff_defs = list_sub(playerinf.tmp_defs, playerinf.basic_defs)
        p_bas_crit_pc = playerinf.original_crit_pc
        p_bas_crit_add = playerinf.original_crit_add
        bas_crit_pc = playerinf.basic_crit_pc - p_bas_crit_pc
        bas_crit_add = playerinf.basic_crit_add - p_bas_crit_add
        eff_crit_pc = playerinf.tmp_crit_pc - p_bas_crit_pc - bas_crit_pc
        eff_crit_add = playerinf.tmp_crit_add - p_bas_crit_add - bas_crit_add
        basic_chg_add = playerinf.basic_chg_add
        eff_chg_add = playerinf.tmp_chg_add - basic_chg_add
        bas_eff_hit = playerinf.basic_effect_hit
        bas_eff_anti = playerinf.basic_effect_anti
        eff_eff_hit = playerinf.tmp_effect_hit - bas_eff_hit
        eff_eff_anti = playerinf.tmp_effect_anti - bas_eff_anti
        # ...
        elems = self.sys.cfg["基本属性名称"]
        txts = []
        n_elems = [elems[f"属性{i}"] for i in range(1, len(elems) + 1)]
        append = txts.append
        if eff_hpmax == 0:
            append(f"§7 - §f生命值上限 §7{p_orig_hpmax}->§f{p_bas_hpmax}§a+{bas_hpmax}")
        else:
            append(f"§7 - §f生命值上限 §f{p_bas_hpmax}§a+{bas_hpmax}§6+{eff_hpmax}")
        for i, elem in enumerate(n_elems):
            t = ""
            bas_atk = bas_atks[i]
            eff_atk = eff_atks[i]
            bas_def = bas_defs[i]
            eff_def = eff_defs[i]
            if eff_atk > 0:
                t += f"§f{bas_atk}§6+{eff_atk}"
            else:
                t += f"§f{bas_atk}"
            t += "§f / "
            if eff_def > 0:
                t += f"§f{bas_def}§6+{eff_def}"
            else:
                t += f"§f{bas_def}"
            append(f"§7 - {elem} (攻击/防御): " + t)
        if eff_crit_pc > 0:
            append(
                f"§7 - §4暴击率 §f{round(p_bas_crit_pc * 100)}%%§a+{round(bas_crit_pc * 100)}%%§6+{round(eff_crit_pc * 100)}%%"
            )
        else:
            append(
                f"§7 - §4暴击率 §f{round(p_bas_crit_pc * 100)}%%§a+{round(bas_crit_pc * 100)}%%"
            )
        if eff_crit_add > 0:
            append(
                f"§7 - §4暴击伤害加成 §f{round(p_bas_crit_add * 100)}%%§a+{round(bas_crit_pc * 100)}%%§6+{round(eff_crit_pc * 100)}%%"
            )
        else:
            append(
                f"§7 - §4暴击伤害加成 §f{round(p_bas_crit_add * 100)}%%§a+{round(bas_crit_add * 100)}%%"
            )
        if eff_eff_hit > 0:
            append(
                f"§7 - §3效果命中 §f{round(bas_eff_hit * 100)}%%§6+{round(eff_eff_hit * 100)}%%"
            )
        else:
            append(f"§7 - §3效果命中 §f{round(bas_eff_hit * 100)}%%")
        if eff_eff_anti > 0:
            append(
                f"§7 - §3效果抵抗 §f{round(bas_eff_anti * 100)}%%§6+{round(eff_eff_anti * 100)}%%"
            )
        else:
            append(f"§7 - §3效果抵抗 §f{round(bas_eff_anti * 100)}%%")

        player.show("§7=========§f｛§l§e属性详情§r§f｝§7=========")
        player.show("\n".join(txts))
        player.show("§7===========================")

    def player_check_effects(self, player: Player):
        playerinf = self.sys.player_holder.get_playerinfo(player)
        playerinf._update()
        player.show("§7========§f｛§l§e效果详情§r§f｝§7========")
        if not playerinf.effects:
            player.show("§7 空空如也..")
        for effect in playerinf.effects:
            player.show(
                f"§7 {effect.icon}§f {effect.name}{effect.self_level()}  §7{effect.timeleft_str()}",
            )
        player.show("§7========================")

    def on_menu_addexp(self, player: Player, args: tuple):
        target, exp = args
        try:
            playerbas = self.sys.player_holder.get_player_basic(
                self.sys.getPlayer(target)
            )
        except Exception:
            self.sys.show_fail(player, "玩家不存在")
            return
        if exp not in range(-100000, 100000):
            self.sys.show_fail(player, "§c无效的等级和经验")
            return
        playerbas.Exp += exp
        self.sys.rpg_upgrade.add_player_exp(player, 0)
        self.sys.player_holder.save_game_player_data(player)
        self.sys.show_inf(
            player,
            "更改成功",
        )

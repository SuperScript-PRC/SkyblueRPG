from tooldelta import tooldelta, Print


def init_scoreboards():
    for scb_name, scb_id in (
        ("怪物UUID", "sr:ms_uuid"),
        ("玩家主手物品显示", "sr:mh_weapon"),
        ("技能检测", "sr:skillmode"),
        ("怪物血量", "sr:ms_hp"),
        ("怪物种类", "sr:ms_type"),
    ):
        resp = tooldelta.get_game_control().sendwscmd_with_resp(
            f"/scoreboard objectives add {scb_id} dummy {scb_name}"
        )
        if resp.SuccessCount:
            Print.print_suc(f"成功创建计分板 {scb_name} (id={scb_id})")
        elif (
            resp.OutputMessages[0].Message
            == "commands.scoreboard.objectives.add.alreadyExists"
        ):
            Print.print_suc(f"计分板 {scb_name} (id={scb_id}) 已存在, 不需再次创建")
        else:
            Print.print_err(f"计分板 {scb_name} (id={scb_id}) 创建失败")


def on_reset_spawnpoint(self, sys):
    if getattr(sys.frame.launcher, "serverNumber") != 59141823:
        sys.print("此功能无法在此租赁服启用")
    sys.game_ctrl.sendwocmd("/setworldspawn")

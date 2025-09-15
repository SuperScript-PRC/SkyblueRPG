import json
import numpy as np
import time
from tooldelta import Player, utils
from threading import Lock
from .frame import MiniGame, MiniGameStage
from .sign_waiter import wait_put_sign
from .util_funcs import select_levels

EVENT_STARTGAME = r"srgame.block_and_go.start"
EVENT_QUITGAME = r"srgame.block_and_go.quit"
EVENT_BTN_LEFT = r"srgame.block_and_go.button.left"
EVENT_BTN_RIGHT = r"srgame.block_and_go.button.right"
EVENT_BTN_UP = r"srgame.block_and_go.button.up"
EVENT_BTN_DOWN = r"srgame.block_and_go.button.down"

BLOCK_TYPE_AIR = 0
BLOCK_TYPE_BARRIER = 1
BLOCK_TYPE_GOLD = 2


class BlockAndGo(MiniGame["BlockAndGoStage"]):
    data_name = "block_and_go"
    name = "挖金矿"
    min_player_num = max_player_num = 1
    winning_gets = 20
    final_win_give_items = ("吉米克的谜题馈赠",)

    def init(self):
        super().init()
        self.sys.chatbar.add_new_trigger(
            ["srgame-b2g-addstage"],
            [("场地编号", str, None)],
            "添加一个挖金矿舞台",
            self.on_create_stage,
        )
        self.sys.chatbar.add_new_trigger(
            ["srgame-b2g-getxz"],
            [],
            "为挖金矿选定舞台范围",
            self.on_get_xz,
        )
        self.sys.chatbar.add_new_trigger(
            ["srgame-b2g-scan"],
            [("关卡名", str, None)],
            "扫描并保存一个挖金矿关卡",
            self.on_scan_level,
        )
        self.x1, self.y1, self.z1 = None, None, None
        self.x2, self.y2, self.z2 = None, None, None
        self.sys.cb2bot.regist_message_cb(EVENT_STARTGAME, self.on_start_game)
        self.sys.cb2bot.regist_message_cb(EVENT_QUITGAME, self.on_quit_game)
        self.sys.cb2bot.regist_message_cb(EVENT_BTN_LEFT, self.on_button_left)
        self.sys.cb2bot.regist_message_cb(EVENT_BTN_RIGHT, self.on_button_right)
        self.sys.cb2bot.regist_message_cb(EVENT_BTN_UP, self.on_button_up)
        self.sys.cb2bot.regist_message_cb(EVENT_BTN_DOWN, self.on_button_down)

    def on_button_left(self, args: list[str]):
        (stage_id,) = args
        stage = self.get_stage_by_id(stage_id)
        if stage:
            stage.on_button_left()

    def on_button_right(self, args: list[str]):
        (stage_id,) = args
        stage = self.get_stage_by_id(stage_id)
        if stage:
            stage.on_button_right()

    def on_button_up(self, args: list[str]):
        (stage_id,) = args
        stage = self.get_stage_by_id(stage_id)
        if stage:
            stage.on_button_up()

    def on_button_down(self, args: list[str]):
        (stage_id,) = args
        stage = self.get_stage_by_id(stage_id)
        if stage:
            stage.on_button_down()

    def on_create_stage(self, player: Player, args):
        stage_id = args[0]
        player.show("请走到舞台区一角放置告示牌")
        if (res := wait_put_sign(player)) is None:
            return
        # 假设都在主世界
        (x1, y1, z1), _ = res
        player.show(f"第一点：{x1, y1, z1}")
        player.show("请走到舞台区另外一角放置告示牌")
        if (res := wait_put_sign(player)) is None:
            return
        (x2, y2, z2), _ = res
        player.show(f"第二点：{x2, y2, z2}")
        start_x, end_x = min(x1, x2), max(x1, x2)
        start_y, end_y = min(y1, y2), max(y1, y2)
        start_z, end_z = min(z1, z2), max(z1, z2)
        player.show("请走到舞台控制区中心放置告示牌")
        if (res := wait_put_sign(player)) is None:
            return
        (ctrlx, ctrly, ctrlz), _ = res
        player.show("请走到开始游戏命令方块放置处放置告示牌")
        if (res := wait_put_sign(player)) is None:
            return
        (startx, starty, startz), _ = res
        player.show("请走到退出游戏命令方块放置处放置告示牌")
        if (res := wait_put_sign(player)) is None:
            return
        (quitx, quity, quitz), _ = res
        levels_res = select_levels(player, self.level_data_path)
        if levels_res is None:
            return
        startgame_tellraw = {
            "rawtext": [
                {"text": EVENT_STARTGAME},
                {"selector": "@p"},
                {"text": stage_id},
                {"text": f"{start_x}, {start_y}, {start_z}, {end_x}, {end_y}, {end_z}"},
                {"text": f"{startx}, {starty}, {startz}, {ctrlx}, {ctrly}, {ctrlz}"},
                {"text": ", ".join(levels_res)},
            ]
        }
        self.sys.intr.place_command_block(
            self.sys.intr.make_packet_command_block_update(
                (startx, starty - 2, startz),
                f"tellraw @a[tag=sr.rpg_bot] {json.dumps(startgame_tellraw, ensure_ascii=False)}",
                need_redstone=True,
            )
        )
        quitgame_tellraw = {
            "rawtext": [
                {"text": EVENT_QUITGAME},
                {"text": stage_id},
            ]
        }
        self.sys.intr.place_command_block(
            self.sys.intr.make_packet_command_block_update(
                (quitx, quity - 2, quitz),
                f"tellraw @a[tag=sr.rpg_bot] {json.dumps(quitgame_tellraw, ensure_ascii=False)}",
                need_redstone=True,
            )
        )
        for evt_name, x_offset, z_offset in (
            (EVENT_BTN_LEFT, -1, 0),
            (EVENT_BTN_RIGHT, 1, 0),
            (EVENT_BTN_UP, 0, -1),
            (EVENT_BTN_DOWN, 0, 1),
        ):
            cmd = "tellraw @a[tag=sr.rpg_bot] " + json.dumps(
                {
                    "rawtext": [
                        {"text": evt_name},
                        {"text": stage_id},
                    ]
                },
                ensure_ascii=False,
            )
            self.sys.intr.place_command_block(
                self.sys.intr.make_packet_command_block_update(
                    (ctrlx + x_offset, ctrly - 2, ctrlz + z_offset),
                    cmd,
                    need_redstone=True,
                )
            )
            self.sys.game_ctrl.sendcmd("tp ~~10~")
        player.show("§a设置完成")

    def on_get_xz(self, player: Player, _):
        player.show("请走到舞台区一角放置告示牌")
        if (res := wait_put_sign(player)) is None:
            return
        # 假设都在主世界
        (x1, y1, z1), _ = res
        player.show(f"第一点：{x1, y1, z1}")
        player.show("请走到舞台区另外一角放置告示牌")
        if (res := wait_put_sign(player)) is None:
            return
        (x2, y2, z2), _ = res
        player.show(f"第二点：{x2, y2, z2}")
        self.x1, self.x2 = min(x1, x2), max(x1, x2)
        self.y1, self.y2 = min(y1, y2), max(y1, y2)
        self.z1, self.z2 = min(z1, z2), max(z1, z2)
        player.show(f"§aOK： {self.x1, self.y1, self.z1} ~ {self.x2, self.y2, self.z2}")

    def on_scan_level(self, player: Player, args):
        level_name: str = args[0]
        if (
            self.x1 is None
            or self.x2 is None
            or self.y1 is None
            or self.y2 is None
            or self.z1 is None
            or self.z2 is None
        ):
            player.show("§c请先设置舞台区域")
            return
        size_x = self.x2 - self.x1 + 1
        size_z = self.z2 - self.z1 + 1
        area = self.sys.intr.get_structure(
            (self.x1, self.y1, self.z1),
            (size_x, 1, size_z),
        )
        res: dict[str, str] = {}
        for x in range(size_x):
            for z in range(size_z):
                block = area.get_block((x, 0, z))
                if block.foreground is None or block.foreground.name.endswith("air"):
                    continue
                res[f"{x},{z}"] = block.foreground.name.removeprefix("minecraft:")
        path = self.get_leveldata_path(level_name)
        if path.is_file():
            if player.input("§6关卡已存在， 覆盖吗（覆盖输入y）：") != "y":
                return
        self.write_leveldata_raw(
            level_name, {"size_x": size_x, "size_z": size_z, "blocks": res}
        )
        player.show("§a扫描完成")

    def on_start_game(self, args: list[str]):
        (
            playername,
            stage_id,
            stage_start_pos_and_end_pos,
            start_and_ctrl_pos,
            levels,
        ) = args
        player = self.get_player_by_name(playername)
        if player is None:
            return
        elif self.check_running(stage_id, player):
            return
        sx, sy, sz, ex, ey, ez = tuple(map(int, stage_start_pos_and_end_pos.split(",")))
        ssx, ssy, ssz, cx, cy, cz = tuple(map(int, start_and_ctrl_pos.split(",")))
        levels = levels.split(", ")
        available_levels = self.get_player_unfinished_levelnames(
            player, levels
        )
        if not available_levels:
            return
        if not self.display_and_wait(player, stage_id, levels, available_levels):
            return
        stage = BlockAndGoStage(
            self,
            stage_id,
            available_levels,
            [player],
            (sx, sy, sz),
            (ex, ey, ez),
            (ssx, ssy, ssz),
            (cx, cy, cz),
        )
        self.set_stage(stage_id, stage)
        stage.activate()

    def on_quit_game(self, args: list[str]):
        stage_id = args[0]
        stage = self.get_stage_by_id(stage_id)
        if stage is not None:
            stage.quit()

    def read_level(self, level_name: str):
        content = self.read_leveldata_raw(level_name)
        assert content is not None, f"关卡不存在: {level_name}"
        res: list[tuple[int, int, str]] = []
        for block_pos, block_id in content["blocks"].items():
            x, z = map(int, block_pos.split(","))
            res.append((x, z, block_id))
        return res


class BlockAndGoStage(MiniGameStage["BlockAndGo"]):
    def __init__(
        self,
        game: BlockAndGo,
        stage_id: str,
        level_names: list[str],
        players: list[Player],
        start_pos: tuple[int, int, int],
        end_pos: tuple[int, int, int],
        startgame_pos: tuple[int, int, int],
        ctrl_pos: tuple[int, int, int],
    ):
        super().__init__(game, stage_id, level_names, players, startgame_pos, ctrl_pos)
        self.player = self.players[0]
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.stage_size_x = end_pos[0] - start_pos[0]
        self.stage_size_z = end_pos[2] - start_pos[2]
        self.op_lock = Lock()

    def activate(self, from_prev_stage: bool = False):
        super().activate(from_prev_stage)
        test_level = self.main.read_level(self.current_level)
        assert test_level
        self.load_from_level(test_level)
        self.player.setTitle("§a开始游戏", "§6帮骷髅先生挖到金矿！")



    def load_from_level(self, level_data: list[tuple[int, int, str]]):
        self.skull_x = -1
        self.skull_z = -1
        self.stage = np.full(
            (self.stage_size_x, self.stage_size_z), BLOCK_TYPE_AIR, dtype=np.int8
        )
        for x, z, block_id in level_data:
            if block_id == "skull":
                self.skull_x = x
                self.skull_z = z
            elif block_id == "gold_ore":
                self.stage[x, z] = BLOCK_TYPE_GOLD
            else:
                self.stage[x, z] = BLOCK_TYPE_BARRIER
            abs_x, abs_y, abs_z = self.to_absolute_pos(x, z)
            self.sys.game_ctrl.sendwocmd(f"setblock {abs_x} {abs_y} {abs_z} {block_id}")
        if self.skull_x == -1 or self.skull_z == -1:
            raise ValueError("Skull not found")

    def on_button_up(self):
        if self.op_lock.locked():
            return
        self.go(0, -1)

    def on_button_down(self):
        if self.op_lock.locked():
            return
        self.go(0, 1)

    def on_button_left(self):
        if self.op_lock.locked():
            return
        self.go(-1, 0)

    def on_button_right(self):
        if self.op_lock.locked():
            return
        self.go(1, 0)

    def on_next_level(self):
        self.player.setTitle("§bLevel Up")
        time.sleep(1)

    @utils.thread_func("自定义RPG-小游戏:BlockAndGo:骷髅运动")
    def go(self, dx: int, dz: int):
        self.update()
        with self.op_lock:
            while not self.exited:
                next_x = self.skull_x + dx
                next_z = self.skull_z + dz
                if (
                    next_x >= self.stage_size_x
                    or next_x < 0
                    or next_z >= self.stage_size_z
                    or next_z < 0
                ):
                    skx, sky, skz = self.get_skull_absolute_pos()
                    self.sys.game_ctrl.sendwocmd(f"setblock {skx} {sky} {skz} air")
                    self.lose()
                    return
                if (block_type := (self.stage[next_x, next_z])) != BLOCK_TYPE_AIR:
                    if block_type == BLOCK_TYPE_GOLD:
                        self.win()
                    break
                skx, sky, skz = self.get_skull_absolute_pos()
                self.sys.game_ctrl.sendwocmd(f"setblock {skx} {sky} {skz} air")
                self.skull_x = next_x
                self.skull_z = next_z
                skx, sky, skz = self.get_skull_absolute_pos()
                self.sys.game_ctrl.sendwocmd(f"setblock {skx} {sky} {skz} skull")
                self.sys.game_ctrl.sendwocmd(
                    f"execute as {self.player.safe_name} at @s run playsound dig.stone"
                )
                time.sleep(0.3)

    def finish(self, win=False):
        time.sleep(1)
        self.clear_stage()
        super().finish(win)

    def clear_stage(self):
        sx, sy, sz = self.start_pos
        ex, ey, ez = self.end_pos
        self.sys.game_ctrl.sendwocmd(f"fill {sx} {sy} {sz} {ex} {ey} {ez} air")

    def win(self):
        self.player.setTitle("§a游戏胜利", "§e骷髅先生挖到了金矿！")
        self.sys.game_ctrl.sendwocmd(
            f"execute as {self.player.safe_name} at @s run playsound random.levelup"
        )
        skx, sky, skz = self.get_skull_absolute_pos()
        self.sys.game_ctrl.sendwocmd(
            f"particle minecraft:totem_particle {skx} {sky + 1} {skz}"
        )
        for _ in range(6):
            self.sys.game_ctrl.sendwocmd(
                f"particle minecraft:heart_particle {skx} {sky + 1} {skz}"
            )
            time.sleep(0.5)
        self.finish(win=True)

    def lose(self):
        self.player.setTitle("§7游戏结束", "§6骷髅先生掉出了这个世界..")
        self.sys.game_ctrl.sendwocmd(
            f"execute as {self.player.safe_name} at @s run playsound mob.skeleton.death"
        )
        skx, sky, skz = self.get_skull_absolute_pos()
        self.sys.game_ctrl.sendwocmd(
            f"particle minecraft:knockback_roar_particle {skx} {sky} {skz}"
        )
        self.finish()

    def quit(self):
        self.player.setTitle("§7游戏结束", "§6骷髅先生还是没能挖到金矿..")
        self.finish()

    def get_skull_absolute_pos(self):
        return self.to_absolute_pos(self.skull_x, self.skull_z)

    def to_absolute_pos(self, _x: int, _z: int):
        x, y, z = self.start_pos
        return x + _x, y, z + _z

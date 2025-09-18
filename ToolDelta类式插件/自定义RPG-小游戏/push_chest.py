import json
import os
import numpy as np
import time
import base64
from tooldelta import Player
from threading import Lock
from .frame import MiniGame, MiniGameStage
from .sign_waiter import wait_put_sign
from .util_funcs import select_levels

EVENT_STARTGAME = r"srgame.push_chest.start"
EVENT_QUITGAME = r"srgame.push_chest.quit"
EVENT_BTN_LEFT = r"srgame.push_chest.button.left"
EVENT_BTN_RIGHT = r"srgame.push_chest.button.right"
EVENT_BTN_UP = r"srgame.push_chest.button.up"
EVENT_BTN_DOWN = r"srgame.push_chest.button.down"

BLOCK_TYPE_AIR = 0
BLOCK_TYPE_BARRIER = 1
BLOCK_TYPE_CHEST = 2
GROUND_TYPE_OTHER = 0
GROUND_TYPE_ENDPOINT = 1

GROUND_TEXTURE = "dried_kelp_block"
WALL_TEXTURE = "stone"

LEVEL_DATA = tuple[
    tuple[int, int],
    tuple[int, int],
    list[tuple[int, int]],
    list[tuple[int, int]],
    list[bool],
]


def bool_list_to_bytes(bool_list: list[bool]):
    # 使用numpy进行更高效的转换
    arr = np.array(bool_list, dtype=np.uint8)
    # 补齐到8的倍数
    padding = (8 - len(arr) % 8) % 8
    if padding > 0:
        arr = np.pad(arr, (0, padding), "constant")

    # 重塑为8位组并转换为字节
    arr = arr.reshape(-1, 8)
    bytes_arr = np.packbits(arr, axis=1)
    return bytes(bytes_arr.flatten())


def bytes_to_bool_list(
    byte_data: bytes, expected_length: int | None = None
) -> list[bool]:
    """
    将bytes转换为bool列表

    Args:
        byte_data: 要转换的字节数据
        expected_length: 期望的布尔列表长度（可选）

    Returns:
        bool列表
    """
    # 使用numpy进行更高效的转换
    arr = np.frombuffer(byte_data, dtype=np.uint8)
    bits = np.unpackbits(arr)

    # 如果指定了期望长度，则截取到指定长度
    if expected_length is not None:
        bits = bits[:expected_length]

    # 转换为布尔值列表
    return [bool(bit) for bit in bits]


class PushChest(
    MiniGame["PushChestStage"],
    data_name="push_chest",
    name="推箱子",
    disp_name="推箱子",
    description="帮助骷髅先生将所有箱子归位！ 你可以通过场地上的 §f↑↓←→§7 按键让骷髅头移动， 当骷髅先生面前有一个箱子时， 向前移动可以向前推动该箱子， 把所有箱子推到§a绿宝石块§7上即可通关。 注意： 骷髅先生没办法一次性推动多个箱子！",
    min_player_num=1,
    max_player_num=1,
    winning_gets=20,
    final_win_give_items=("吉米克的谜题馈赠",),
):
    def init(self):
        self.data_path = self.sys.data_path / "push_chest"
        os.makedirs(self.data_path, exist_ok=True)
        self.sys.chatbar.add_new_trigger(
            ["srgame-pch-addstage"],
            [("场地编号", str, None)],
            "添加一个推箱子舞台",
            self.on_create_stage,
        )
        self.sys.chatbar.add_new_trigger(
            ["srgame-pch-getxz"],
            [],
            "为推箱子选定舞台范围",
            self.on_get_xz,
        )
        self.sys.chatbar.add_new_trigger(
            ["srgame-pch-scan"],
            [("关卡名", str, None)],
            "扫描并保存一个推箱子关卡",
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
            self.sys.intr.place_command_block(
                self.sys.intr.make_packet_command_block_update(
                    (ctrlx + x_offset, ctrly - 3, ctrlz + z_offset),
                    "clone ~~-1~ ~~-1~ ~~3~",
                    mode=2,
                )
            )
            self.sys.game_ctrl.sendwocmd(
                f"setblock {ctrlx + x_offset} {ctrly - 4} {ctrlz + z_offset} stone_button 1"
            )
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
            (self.x1, self.y1 - 1, self.z1),
            (size_x, 2, size_z),
        )
        chests: list[list[int]] = []
        skull_posx = -1
        skull_posz = -1
        endpoints: list[list[int]] = []
        barriers = [False] * size_x * size_z
        for x in range(size_x):
            for z in range(size_z):
                block = area.get_block((x, 0, z))
                if block.foreground is not None and block.foreground.name.endswith(
                    "emerald_block"
                ):
                    endpoints.append([x, z])
                block = area.get_block((x, 1, z))
                if block.foreground is None or block.foreground.name.endswith("air"):
                    continue
                if block.foreground.name.endswith("chest"):
                    chests.append([x, z])
                elif block.foreground.name.endswith("skull"):
                    skull_posx = x
                    skull_posz = z
                else:
                    barriers[x * size_z + z] = True
        if skull_posx == -1 or skull_posz == -1:
            raise ValueError("Skull not found")
        barrier_asbytes = base64.b64encode(bool_list_to_bytes(barriers)).decode()
        path = self.get_leveldata_path(level_name)
        if path.is_file():
            if player.input("§6关卡已存在， 覆盖吗（覆盖输入y）：") != "y":
                return
        self.write_leveldata_raw(
            level_name,
            {
                "size_xz": [size_x, size_z],
                "skull_pos": [skull_posx, skull_posz],
                "chests": chests,
                "endpoints": endpoints,
                "barriers": barrier_asbytes,
            },
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
        available_levels = self.get_player_unfinished_levelnames(player, levels)
        if not available_levels:
            return
        if not self.display_and_wait(player, stage_id, levels, available_levels):
            return
        stage = PushChestStage(
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

    def read_level(self, level_name: str) -> LEVEL_DATA | None:
        content = self.read_leveldata_raw(level_name)
        if content is None:
            return None
        size_x, size_z = content["size_xz"]
        skull_posx, skull_posz = content["skull_pos"]
        chests: list[tuple[int, int]] = [(x, z) for x, z in content["chests"]]
        endpoints: list[tuple[int, int]] = []
        for x, z in content["endpoints"]:
            endpoints.append((x, z))
        barriers = bytes_to_bool_list(
            base64.b64decode(content["barriers"]), size_x * size_z
        )
        return ((size_x, size_z), (skull_posx, skull_posz), endpoints, chests, barriers)


class PushChestStage(MiniGameStage["PushChest"]):
    def __init__(
        self,
        game: PushChest,
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

    def activate(self, from_prev_level: bool = False):
        super().activate(from_prev_level)
        self.skull_x = 0
        self.skull_z = 0
        self.ok_chests = 0
        self.total_chests = 0
        self.stage = np.full(
            (self.stage_size_x, self.stage_size_z), BLOCK_TYPE_AIR, dtype=np.int8
        )
        self.ground = np.full(
            (self.stage_size_x, self.stage_size_z), GROUND_TYPE_OTHER, dtype=np.int8
        )
        test_level = self.main.read_level(self.current_level)
        assert test_level, f"No level named {self.current_level}"
        self.load_from_level(test_level)
        self.player.setTitle("§a开始游戏", "§6帮骷髅先生把箱子推到绿宝石块上！")

    def load_from_level(self, level_data: LEVEL_DATA):
        (size_x, size_z), (self.skull_x, self.skull_z), endpoints, chests, barriers = (
            level_data
        )
        self.total_chests = len(chests)
        for x in range(size_x):
            for z in range(size_z):
                if barriers[x * size_z + z]:
                    self.stage[x, z] = BLOCK_TYPE_BARRIER
                    abs_x, abs_y, abs_z = self.to_absolute_pos(x, z)
                    self.sys.game_ctrl.sendwocmd(
                        f"setblock {abs_x} {abs_y} {abs_z} {WALL_TEXTURE}"
                    )
                    time.sleep(0.01)
        for x, z in endpoints:
            self.ground[x, z] = GROUND_TYPE_ENDPOINT
            abs_x, abs_y, abs_z = self.to_absolute_pos(x, z)
            self.sys.game_ctrl.sendwocmd(
                f"setblock {abs_x} {abs_y - 1} {abs_z} emerald_block"
            )
        for x, z in chests:
            self.stage[x, z] = BLOCK_TYPE_CHEST
            if self.ground[x, z] == GROUND_TYPE_ENDPOINT:
                self.ok_chests += 1
            abs_x, abs_y, abs_z = self.to_absolute_pos(x, z)
            self.sys.game_ctrl.sendwocmd(f"setblock {abs_x} {abs_y} {abs_z} chest")
        skx, sky, skz = self.get_skull_absolute_pos()
        self.sys.game_ctrl.sendwocmd(f"setblock {skx} {sky} {skz} skull")

    def finish(self, win=False):
        sx, sy, sz = self.start_pos
        ex, ey, ez = self.end_pos
        self.sys.game_ctrl.sendwocmd(f"fill {sx} {sy} {sz} {ex} {ey} {ez} air")
        self.sys.game_ctrl.sendwocmd(
            f"fill {sx} {sy - 1} {sz} {ex} {ey - 1} {ez} {GROUND_TEXTURE}"
        )
        super().finish(win)

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

    def go(self, dx: int, dz: int):
        self.update()
        with self.op_lock:
            next_x = self.skull_x + dx
            next_z = self.skull_z + dz
            nextnext_x = self.skull_x + dx * 2
            nextnext_z = self.skull_z + dz * 2
            if (
                next_x >= self.stage_size_x
                or next_x < 0
                or next_z >= self.stage_size_z
                or next_z < 0
            ):
                # self.player.show("无法推动:边界")
                return
            elif self.stage[next_x, next_z] == BLOCK_TYPE_AIR:
                skx, sky, skz = self.get_skull_absolute_pos()
                self.sys.game_ctrl.sendwocmd(f"setblock {skx} {sky} {skz} air")
                self.skull_x = next_x
                self.skull_z = next_z
                skx, sky, skz = self.get_skull_absolute_pos()
                self.sys.game_ctrl.sendwocmd(f"setblock {skx} {sky} {skz} skull")
                self.sys.game_ctrl.sendwocmd(
                    f"execute as {self.player.safe_name} at @s run playsound step.wood"
                )
            elif self.stage[next_x, next_z] == BLOCK_TYPE_CHEST:
                if (
                    nextnext_x >= self.stage_size_x
                    or nextnext_x < 0
                    or nextnext_z >= self.stage_size_z
                    or nextnext_z < 0
                ) or self.stage[nextnext_x, nextnext_z] != BLOCK_TYPE_AIR:
                    # self.player.show("无法推动:箱子->石头或边界")
                    return
                if self.ground[next_x, next_z] == GROUND_TYPE_ENDPOINT:
                    self.ok_chests -= 1
                self.stage[next_x, next_z] = BLOCK_TYPE_AIR
                self.stage[nextnext_x, nextnext_z] = BLOCK_TYPE_CHEST
                if self.ground[nextnext_x, nextnext_z] == GROUND_TYPE_ENDPOINT:
                    self.ok_chests += 1
                    self.player.setTitle(
                        "§a",
                        f"§a箱子已归位， 还剩 {self.total_chests - self.ok_chests} 个箱子",
                    )
                    self.sys.game_ctrl.sendwocmd(
                        f"execute as {self.player.safe_name} at @s run playsound random.chestclosed"
                    )
                else:
                    self.sys.game_ctrl.sendwocmd(
                        f"execute as {self.player.safe_name} at @s run playsound step.wood"
                    )
                skx, sky, skz = self.get_skull_absolute_pos()
                self.sys.game_ctrl.sendwocmd(f"setblock {skx} {sky} {skz} air")
                self.skull_x = next_x
                self.skull_z = next_z
                skx, sky, skz = self.get_skull_absolute_pos()
                self.sys.game_ctrl.sendwocmd(f"setblock {skx} {sky} {skz} skull")
                cx, cy, cz = self.to_absolute_pos(nextnext_x, nextnext_z)
                self.sys.game_ctrl.sendwocmd(f"setblock {cx} {cy} {cz} chest")
                if self.ok_chests == self.total_chests:
                    self.add_score(self.player, 100 * self.ok_chests)
                    self.win()
            else:
                pass
                # self.player.show(f"无法推动:石头 {self.stage[next_x, next_z]} {self.skull_x, self.skull_z} {next_x, next_z}")

    def win(self):
        self.player.setTitle("§a游戏胜利", "§e骷髅先生摆放好了所有的箱子！")
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

    def quit(self):
        self.player.setTitle("§7游戏结束", "§6骷髅先生还是没能整理好箱子..")
        self.finish()

    def get_skull_absolute_pos(self):
        return self.to_absolute_pos(self.skull_x, self.skull_z)

    def to_absolute_pos(self, _x: int, _z: int):
        x, y, z = self.start_pos
        return x + _x, y, z + _z

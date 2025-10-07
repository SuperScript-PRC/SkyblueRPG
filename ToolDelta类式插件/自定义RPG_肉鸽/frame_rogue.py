import time
import random
from threading import Event
from tooldelta import Player, utils
from .define import LEVELTYPE_TO_NPCNAME as LTN, AREA_NAME, NewRecordEnum
from .storage import RogueStatusStorage
from .frame_areas import AreaType
from .frame_levels import Level, LevelType, EntranceLevel, BossLevel
from .rogue_utils import (
    allocate_area,
    clear_rogue_virtual_items,
    recover_from_rogue_status,
)

if 0:
    from . import CustomRPGRogue, entry

    RPGEffect = entry.rpg.frame_effects.RPGEffect


class Rogue:
    def __init__(
        self,
        levels: list[type[Level]],
        typed_level_amount_max: dict[LevelType, int],
        *,
        shake_value_threshold: int = 200,
        initial_effects: list["RPGEffect"] = [],
    ):
        self.levels = levels
        self.typed_level_amount_max = typed_level_amount_max
        self.active_players: set[Player] = set()
        self.shake_value_threshold = shake_value_threshold
        self.initial_effects = initial_effects

    def enter_rogue(self, storage: RogueStatusStorage):
        self.add_player(storage.sys, storage.player)
        self.start_level(
            storage, EntranceLevel(storage, allocate_area(AreaType.Entrance))
        )

    def start_level(self, storage: RogueStatusStorage, level: Level):
        "开始关卡"
        storage.current_level = level
        storage.current_level_passed = False
        self._teleport_to_current_level(storage)
        time.sleep(1)
        level.activate()

    def level_finished(self, storage: RogueStatusStorage, level: Level):
        "记录关卡, 并展示接下来的关卡"
        storage.passed_levels.append(level.type)
        if not level.final:
            new_levels = self._random_choice_nextlevels(storage, 3)
            storage.next_levels = new_levels
            self._display_levels(storage.sys, level, new_levels)
        storage.current_level_passed = True

    def select_and_goto_next_level(self, storage: RogueStatusStorage, n: int):
        "选择并前往和开始下一关"
        section = self._select_next_level(storage, n)
        if section is None:
            return
        if storage.current_level is not None:
            self._clear_display_levels(storage.sys, storage.current_level)
        assert storage.current_level
        storage.current_level.destroy()
        storage.add_shake_value(section.shake_value)
        self.start_level(storage, section)
        self._display_rogue_values(storage)

    def add_player(self, sys: "CustomRPGRogue", player: Player):
        self.active_players.add(player)
        sys.pdstore.set_property(player, "srpg:in_rogue", True)

    def remove_player(self, sys: "CustomRPGRogue", player: Player):
        if player in self.active_players:
            self.active_players.remove(player)
            sys.pdstore.set_property(player, "srpg:in_rogue", False)

    def player_complete_rogue(
        self, sys: "CustomRPGRogue", storage: RogueStatusStorage, cur_level: BossLevel
    ):
        cur_level.on_open_chest()
        self.player_leave_rogue(sys, storage, True)

    def player_leave_rogue(self, sys: "CustomRPGRogue", storage: RogueStatusStorage, win=False, display_scb=True):
        if display_scb:
            self._display_scoreboard(sys, storage)
        sys.game_ctrl.sendwocmd(
            f"camera {storage.player.safe_name} fade time 0.5 0.5 0.5"
        )
        time.sleep(1)
        sys.game_ctrl.sendwocmd(
            f"tp {storage.player.safe_name} 368 206 397 facing 367 207 397"
        )
        recover_from_rogue_status(storage.player)
        clear_rogue_virtual_items(storage.player)

    def _display_rogue_values(self, storage: RogueStatusStorage):
        player = storage.player
        if storage.current_level:
            lname = AREA_NAME.get(storage.current_level.area.type, "？？？")
        else:
            lname = "--"
        text = f"§6§l映像 §f{storage.passed_levels_num}  §6>§e> §f{lname} §e<§6<"
        player.setTitle("§a", f"{text}" + "\n§a" * 7)

    def _select_next_level(self, storage: RogueStatusStorage, n: int):
        if not storage.current_level_passed:
            storage.sys.rpg.show_fail(storage.player, "请先完成当前关卡")
            return None
        next_levels = storage.next_levels
        if n >= len(next_levels):
            storage.sys.rpg.show_fail(storage.player, "选择的关卡有误")
            return None
        return next_levels[n]

    def _teleport_to_current_level(self, storage: RogueStatusStorage):
        game = storage.sys.game_ctrl
        player = storage.player
        game.sendwocmd(f"camera {player.safe_name} fade time 0.5 0.5 0.5")
        time.sleep(0.5)
        assert storage.current_level
        x, y, z = storage.current_level.area.safe_pos
        game.sendwocmd(
            f"tp {player.safe_name} "
            + " ".join(map(str, storage.current_level.area.safe_pos))
            + f" facing {x + 2} {y + 0.8} {z}"
        )

    def _display_levels(
        self, sys: "CustomRPGRogue", current_level: Level, levels: list[Level]
    ):
        poses: list[tuple[tuple[int, int, int], str]] = []
        a = current_level.area
        if len(levels) >= 1:
            poses.append((a.npc_1_pos, LTN[levels[0].type]))
        if len(levels) >= 2:
            poses.append((a.npc_2_pos, LTN[levels[1].type]))
        if len(levels) >= 3:
            poses.append((a.npc_3_pos, LTN[levels[2].type]))
        for pos, name in poses:
            sys.game_ctrl.sendwocmd(f"structure load {name} {' '.join(map(str, pos))}")

    def _random_choice_level_classes(self, storage: RogueStatusStorage, max_k=3):
        lws = [
            (level, level.weight)
            for level in self.levels
            if self.typed_level_amount_max[level.type]
            - storage.passed_levels.count(level.type)
            > 0
            and level.shake_value
            <= max(0, self.shake_value_threshold - storage.shake_value)
        ]
        level_classes = [i[0] for i in lws]
        level_weights = [i[1] for i in lws]
        nlevel_classes: list[type[Level]] = []
        for _ in range(max_k):
            if not level_classes:
                break
            level_cls = random.choices(level_classes, weights=level_weights)[0]
            level_weights.pop(level_classes.index(level_cls))
            level_classes.remove(level_cls)
            nlevel_classes.append(level_cls)
        return nlevel_classes

    def _random_choice_nextlevels(self, storage: RogueStatusStorage, k=3):
        classes = self._random_choice_level_classes(storage, k)
        return [cls(storage, allocate_area(cls.area_type)) for cls in classes]

    def _clear_display_levels(self, sys: "CustomRPGRogue", current_level: Level):
        a = current_level.area
        x0, y0, z0 = a.npc_1_pos
        x1, y1, z1 = a.npc_3_pos
        sys.game_ctrl.sendwocmd(
            f"kill @e[type=npc,x={x0},y={y0},z={z0},dx={x1 - x0 + 1},dy={y1 - y0 + 1},dz={z1 - z0 + 1}]"
        )

    def _display_scoreboard(self, sys: "CustomRPGRogue", storage: RogueStatusStorage):
        align = sys.bigchar.mctext.align
        nrs = sys.update_rank(storage)
        rec = storage.to_record()
        outputs = ["§a"] * 8
        t = 0
        e = Event()
        br = sys.bigchar
        clstime = br(f"{rec.clear_time // 60:02d}m{rec.clear_time % 60:02d}s")

        @utils.thread_func("肉鸽:最终日志显示")
        def disp():
            nonlocal outputs, t
            L = 20
            R = 20
            while not e.is_set():
                if t == 0:
                    outputs[0] = (
                        f"§9❈ §b{sys.bigchar('Reflect World Emulator')} §f| 映像世界运行日志"
                    )
                elif t == 1:
                    outputs[1] = align.align_simple(
                        ("  镜像用户： ", L), (R, rec.playername)
                    )
                elif t == 2:
                    outputs[2] = align.align_simple(
                        ("  记录映像数： ", L),
                        (
                            R,
                            br(rec.images_amount)
                            + (
                                "§6[新纪录！]"
                                if nrs & NewRecordEnum.ImagesAmount
                                else ""
                            ),
                        ),
                    )
                elif t == 3:
                    outputs[3] = align.align_simple(
                        ("  获得金粒： ", L),
                        (
                            R,
                            br(rec.final_money)
                            + ("§6[新纪录！]" if nrs & NewRecordEnum.Money else ""),
                        ),
                    )
                elif t == 4:
                    outputs[4] = align.align_simple(
                        ("  反馈数量： ", L),
                        (
                            R,
                            br(rec.effects_amount)
                            + (
                                "§6[新纪录！]"
                                if nrs & NewRecordEnum.EffectsAmount
                                else ""
                            ),
                        ),
                    )
                elif t == 5:
                    outputs[1] += align.align_simple(
                        ("  累计得分：", L),
                        (
                            R,
                            br(rec.final_score)
                            + ("§6[新纪录！]" if nrs & NewRecordEnum.Score else ""),
                        ),
                    )
                elif t == 6:
                    outputs[2] += align.align_simple(
                        ("  运行时长： ", L),
                        (
                            R,
                            clstime
                            + ("§6[新纪录！]" if nrs & NewRecordEnum.ClearTime else ""),
                        ),
                    )
                elif t > 8:
                    outputs[7] = "§" + "8f"[t % 2] + "抬头或低头退出界面~"
                time.sleep(1)
                t += 1

        def _disp_cb(_, page: int):
            if page > 2:
                return None
            nonlocal outputs
            return "\n".join(outputs)

        disp()
        sys.snowmenu.simple_select(storage.player, _disp_cb)
        e.set()

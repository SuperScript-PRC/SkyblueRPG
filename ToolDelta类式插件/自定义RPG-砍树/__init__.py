import time
import random
import importlib
from tooldelta import Plugin, Player, TYPE_CHECKING, utils, plugin_entry

from . import anti_areas

importlib.reload(anti_areas)
tmpjs = utils.tempjson
OAK_PROCESS = 2
SIZEX = 15
SIZEY = 15
SIZEZ = 15
PX = SIZEX // 2 + 1
PY = SIZEY // 2 + 1
PZ = SIZEZ // 2 + 1


class CustomRPGTree(Plugin):
    name = "自定义RPG-伐木系统"
    author = "SuperScript"
    version = (0, 0, 1)

    def __init__(self, frame):
        super().__init__(frame)
        self.ListenPreload(self.on_def)
        self.ListenActive(self.on_inject)

    def on_def(self):
        global PlayerEntity, Structure
        self.rpg = self.GetPluginAPI("自定义RPG")
        self.intr = self.GetPluginAPI("前置-世界交互")
        self.career = self.GetPluginAPI("自定义RPG-职业")
        self.cached_process: dict[Player, tuple[int, int]] = {}
        if TYPE_CHECKING:
            from 自定义RPG import CustomRPG
            from 前置_世界交互 import GameInteractive, Structure
            from 自定义RPG_职业 import CustomRPGJobs

            PlayerEntity = CustomRPG.PlayerEntity
            self.rpg: CustomRPG
            self.intr: GameInteractive
            self.career: CustomRPGJobs
        self.rpg.add_weapon_use_listener("AxeRefinedIron", self.on_player_use_axe)

    def on_inject(self):
        self.clear_cache()

    def find_block_in_area(
        self,
        startx: int,
        starty: int,
        startz: int,
        dx: int,
        dy: int,
        dz: int,
        block_id: str,
    ):
        area = self.intr.get_structure((startx, starty, startz), (dx, dy, dz))
        for x in range(dx):
            for y in range(dy):
                for z in range(dz):
                    if block := area.get_block((x, y, z)).foreground:
                        block_name = block.name
                    else:
                        block_name = ""
                    if block_name == block_id:
                        return area, (x, y, z)
        return None

    def match_block_in_area(
        self,
        startx: int,
        starty: int,
        startz: int,
        dx: int,
        dy: int,
        dz: int,
        prefix: str,
        suffix: str,
    ):
        area = self.intr.get_structure((startx, starty, startz), (dx, dy, dz))
        for x in range(dx):
            for y in range(dy):
                for z in range(dz):
                    if block := area.get_block((x, y, z)).foreground:
                        block_name = block.name
                    else:
                        block_name = ""
                    simplify_name = block_name.removeprefix(
                        "minecraft:"
                    )
                    if simplify_name.startswith(prefix) and simplify_name.endswith(
                        suffix
                    ):
                        return area, (x, y, z), simplify_name
        return None

    def on_player_use_axe(self, playerinf: "PlayerEntity"):
        player = playerinf.player
        x, y, z = (int(i) for i in player.getPos()[1:])
        res = self.simple_cut_wood(player, x, y, z)
        if res is None:
            return
        area, (bx, by, bz), matched_block = res
        self.add_process(player)
        if self.cached_process[player][0] >= OAK_PROCESS:
            del self.cached_process[player]
            self.finish_process(player, area, x, y, z, bx, by, bz, matched_block)

    def add_process(self, player: Player):
        prgs, _ = self.cached_process.get(player, (0, 0))
        self.cached_process[player] = (prgs + 1, int(time.time()))
        self.show_progress_to_player(player)

    @utils.timer_event(10, "砍树进度缓存清除")
    def clear_cache(self):
        for k, (_, tim) in self.cached_process.copy().items():
            if time.time() - tim >= 30:
                del self.cached_process[k]

    def simple_cut_wood(self, player: Player, x: int, y: int, z: int):
        res = self.match_block_in_area(
            x - PX, y - PY, z - PZ, SIZEX, SIZEY, SIZEZ, "stripped", "log"
        )
        if res is None:
            # 也许是没有用斧头
            return None
        _, (block_x, block_y, block_z), simpify_blockid = res
        origin_wood_id = simpify_blockid.removeprefix("stripped_")
        self.game_ctrl.sendwocmd(
            f"execute as {player.getSelector()} at @s run "
            f"fill ~-{PX}~-{PY}~-{PZ}~{SIZEX - PX}~{SIZEY - PY}~{SIZEZ - PZ} "
            f"{origin_wood_id} 0 replace {simpify_blockid}"
        )
        if self.can_break_wood(
            x - PX + block_x, y + PY + block_y, z - PZ + block_z, origin_wood_id
        ):
            self.add_process(player)
            return res
        else:
            player.setActionbar("§c无法在此砍伐§6这种种类§c的树")
            return None

    def can_break_wood(self, x: int, y: int, z: int, woodname: str):
        for antiarea in anti_areas.anti_areas:
            if antiarea.can_cut(x, y, z, woodname):
                return True
        return False

    def finish_process(
        self,
        player: Player,
        cached_area: "Structure",
        x: int,
        y: int,
        z: int,
        bx: int,
        by: int,
        bz: int,
        block_id_without_prefix: str,
    ):
        lower_y = None
        upper_y = None
        found_x = x - PX + bx
        _ = y - PY + by
        found_z = z - PZ + bz
        origin_wood_id = block_id_without_prefix.removeprefix("stripped_")
        for cy in range(SIZEY - 1):
            actual_y = y - PY + cy
            if cached_area.get_block((bx, cy, bz)).foreground.name in ( # type: ignore[attr-defined]
                "minecraft:dirt",
                "minecraft:grass",
            ) and cached_area.get_block((bx, cy + 1, bz)).foreground.name.removeprefix(  # type: ignore[attr-defined]
                "minecraft:"
            ) in (block_id_without_prefix, origin_wood_id):
                lower_y = actual_y + 1
            elif (
                cached_area.get_block((bx, cy, bz)).foreground.name.removeprefix("minecraft:")  # type: ignore[attr-defined]
                in (block_id_without_prefix, origin_wood_id)
                and "leaves" in cached_area.get_block((bx, cy + 1, bz)).foreground.name  # type: ignore[attr-defined]
            ):
                upper_y = actual_y
        if lower_y is None:
            self.rpg.show_fail(player, "你站的太高了， 无法砍伐")
            return
        if upper_y is None:
            self.rpg.show_fail(player, "你站的太低了， 无法砍伐")
            return
        self.game_ctrl.sendwocmd(
            f"execute as {player.getSelector()} at @s run "
            f"fill {found_x} {lower_y} {found_z} {found_x} "
            f"{upper_y} {found_z} air 0 destroy"
        )
        self.game_ctrl.sendwocmd(
            f"execute as {player.getSelector()} at @s run "
            f"setblock {found_x} {lower_y} {found_z} sapling"
        )
        self.game_ctrl.sendwocmd(
            f"execute as {player.getSelector()} at @s run "
            f"setblock {found_x} {upper_y + 3} {found_z} barrier"
        )
        self.game_ctrl.sendwocmd(
            f"execute as {player.getSelector()} at @s run "
            f"kill @e[type=item,x={found_x},y={lower_y},z={found_z},dx=1,dy=12,dz=1]"
        )
        give_woods = int((upper_y - lower_y + 1) * random.randint(15, 25) / 10)
        gen_exps = (upper_y - lower_y + 1) // 2
        self.rpg.show_any(player, "n", "§2砍伐了一棵§a橡树§2， 获得了：")
        self.rpg.backpack_holder.giveItems(player, self.rpg.item_holder.createItems("木料", give_woods))
        # self.career.add_career_exp(player, "伐木", gen_exps)

    def show_progress_to_player(self, player: Player):
        PRGBAR_LEN = 30
        now_progress = self.cached_process[player][0]
        prgs_now = int(now_progress / OAK_PROCESS * PRGBAR_LEN)
        player.setActionbar(
            "§7正在砍伐 §l§f[§6"
            + "|" * prgs_now
            + "§7"
            + "|" * (PRGBAR_LEN - prgs_now)
            + "§7]",
        )


entry = plugin_entry(CustomRPGTree)

import time
from math import sin, cos, pi
from dataclasses import dataclass
from tooldelta import Plugin, Player, utils, TYPE_CHECKING, plugin_entry

MODE_GACHA_MAIN = 1
MODE_GACHA_FOLLOWING = 2
MODE_GACHA_BLANK = 3


@dataclass
class GachaPool:
    main_items_weight: float
    main_items_and_weights: tuple[str, float]
    following_items_weight: float
    following_items_and_weights: tuple[str, float]
    blank_items_weight: float
    blank_items_and_probabilities: tuple[str, float]
    floor_main_gacha_count: int
    floor_main_gacha_add: float
    floor_follow_gacha_count: int


# CURRENT_GACHA = GachaPool(
# )
class CustomRPGGacha(Plugin):
    name = "自定义RPG-抽奖"
    author = "SuperScript"
    version = (0, 0, 1)

    def __init__(self, frame):
        super().__init__(frame)
        self.ListenPreload(self.on_def)

    def on_def(self):
        intr = self.GetPluginAPI("前置-世界交互")
        cb2bot = self.GetPluginAPI("Cb2Bot通信")
        chatbar = self.GetPluginAPI("聊天栏菜单")
        rpg = self.GetPluginAPI("自定义RPG")
        if TYPE_CHECKING:
            from 前置_世界交互 import GameInteractive
            from 前置_Cb2Bot通信 import TellrawCb2Bot
            from 前置_聊天栏菜单 import ChatbarMenu
            from 自定义RPG import CustomRPG

            intr: GameInteractive
            cb2bot: TellrawCb2Bot
            chatbar: ChatbarMenu
            self.rpg: CustomRPG

        self.intr = intr
        self.rpg = rpg
        chatbar.add_new_trigger(
            ["sfxput"], [], "放置特效播放命令方块", self.on_place_cb, op_only=True
        )
        cb2bot.regist_message_cb("gacha.sfx", self.handle_sfx_cmd)

    @utils.thread_func("抽奖特效1")
    def play_sfx1_at(self, player: Player, x: int, y: int, z: int):
        RT = 50
        R = 20
        for t0 in range(RT):
            self.horizon_round(
                x, y + sin(t0 / 5) * 5, z, "endrod", R - (t0 / RT) * R, t0 / RT / 3
            )
            time.sleep(0.1)
        # for _ in range(8):
        #    self.game_ctrl.sendwocmd(f"particle minecraft:knockback_roar_particle {x} {y+5} {z}")
        for y1 in range(y, 195, -1):
            self.game_ctrl.sendwocmd(f"particle minecraft:sonic_explosion {x} {y1} {z}")
            time.sleep(0.03)

    def horizon_round(
        self, x: float, y: float, z: float, par_id: str, r: float, rotation: float
    ):
        PS = 10
        for t0 in range(PS):
            t = t0 / PS / 2 * pi + rotation
            px = r * sin(t * pi)
            pz = r * cos(t * pi)
            px1 = r * sin(t * pi + pi)
            pz1 = r * cos(t * pi + pi)
            self.game_ctrl.sendwocmd(
                f"particle minecraft:{par_id} {x + px + 0.5} {y} {z + pz + 0.5}"
            )
            self.game_ctrl.sendwocmd(
                f"particle minecraft:{par_id} {x + px1 + 0.5} {y} {z + pz1 + 0.5}"
            )

    def on_place_cb(self, player: Player, _):
        x, y, z = (int(i) for i in player.getPos()[1:])
        traw = f'{{"rawtext":[{{"text":"gacha.sfx"}},{{"text":"{x} {y} {z}"}},{{"selector":"{player.name}"}}]}}'
        self.intr.place_command_block(
            self.intr.make_packet_command_block_update(
                (x, y, z), f"tellraw @a[tag=sr.rpg_bot] {traw}", need_redstone=True
            )
        )
        self.game_ctrl.sendcmd("tp ~~10~")
        player.show("命令方块放置完成")

    def handle_sfx_cmd(self, args: list[str]):
        xyz, target = args
        x, y, z = (int(i) for i in xyz.split())
        self.play_sfx1_at(self.rpg.getPlayer(target), x, y, z)

    def play_gacha_sfx(self): ...
    def gacha(self, player: Player, gacha_mode: GachaPool, count: int):
        self.play_gacha_sfx()
        record = self.get_gacha_record(player)

    def get_gacha_record(self, player: Player):
        return utils.tempjson.load_and_read(
            self.format_data_path(
                player.xuid
            ),
            default=[0, 0, 0],
        )

    def add_gacha_record(self, player: Player, item: str, mode: int):
        ctx: list = utils.tempjson.load_and_read(
            self.format_data_path(
                player.xuid
            ),
            default=[0, 0, 0],
        )
        if mode == MODE_GACHA_MAIN:
            ctx[0] += 1
        elif mode == MODE_GACHA_FOLLOWING:
            ctx[1] += 1
        ctx[2] += 1
        ctx.append(item)


entry = plugin_entry(CustomRPGGacha)

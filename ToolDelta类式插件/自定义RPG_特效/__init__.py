import time
from dataclasses import dataclass
from tooldelta import Plugin, Player, utils, plugin_entry

MAX_CONTENT = 10
SPACE_NUM = 60


@dataclass
class FXStage:
    target: Player
    delay: float = 0.1

    def __init__(self, target: Player):
        self.contents: list[str] = []
        self.target = target

    def set_delay(self, delay: float):
        self.delay = delay

    def show(self):
        self.contents = self.contents[-MAX_CONTENT:]
        new_content = self.contents + ["§a"] * (MAX_CONTENT - len(self.contents))
        self.target.setActionbar(
            "\n§r".join(new_content) + "\n§a" + " " * SPACE_NUM + "§a"
        )
        time.sleep(self.delay)

    def sfx(self, id: str, pitch: float = 1):
        entry.game_ctrl.sendwocmd(
            f'execute as "{self.target.name}" at @s run playsound {id} @s ~~~ 1 {pitch}'
        )

    def beep(self):
        self.sfx("note.bit", 1.4)

    def print(self, msg: str):
        self.contents.append(msg)
        self.show()

    def rprint(self, msg: str):
        self.contents[-1] = msg
        self.show()

    def cprint(self, msg: str):
        self.contents[-1] += msg
        self.show()

    def cls(self):
        self.contents = ["§a"] * MAX_CONTENT


def load_sfx_1(player: Player):
    sfx = FXStage(player)
    sfx.set_delay(0.3)
    sfx.print("§aBIOS Loading")
    sfx.cprint(".")
    sfx.cprint(".")
    sfx.cprint(".")
    sfx.cprint("OK")
    sfx.beep()
    sfx.set_delay(0.4)
    sfx.print("Checking memory..")
    sfx.rprint("Checking memory.. 0 Bytes")
    sfx.rprint("Checking memory.. 131072 Bytes")
    sfx.rprint("Checking memory.. 262144 Bytes")
    sfx.rprint("Checking memory.. 524288 Bytes")
    sfx.rprint("Checking memory.. 1048576 Bytes")
    sfx.rprint("Checking memory.. 1048576 Bytes avaliable")
    sfx.beep()
    sfx.set_delay(0.1)
    sfx.print("Checking VRAM..")
    sfx.set_delay(0.3)
    sfx.rprint("Checking VRAM.. 65536 Bytes")
    sfx.rprint("Checking VRAM.. 65536 Bytes avaliable")
    sfx.beep()
    sfx.set_delay(0.1)
    sfx.print("UEFI Bootstraping../")
    for _ in range(10):
        sfx.rprint("AZ3 BIOS Bootstraping../")
        sfx.rprint("AZ3 BIOS Bootstraping..-")
        sfx.rprint("AZ3 BIOS Bootstraping..\\")
        sfx.rprint("AZ3 BIOS Bootstraping..|")
    sfx.rprint("UEFI Bootstraping..OK")
    sfx.beep()
    sfx.set_delay(0.4)
    sfx.print("Connecting to Azure LAN (42.186.200.42:19132)")
    for _ in range(5):
        sfx.rprint("Connecting to Azure LAN (42.186.200.42:19132) _")
        sfx.rprint("Connecting to Azure LAN (42.186.200.42:19132)")
    sfx.rprint("Connecting to Azure LAN (42.186.200.42:19132) Auth Passed")
    sfx.beep()
    sfx.set_delay(0.1)
    sfx.print("§bUse device id: SilverWolf [admin=SuperScript]")
    sfx.print("fetching data from server..")
    sfx.set_delay(0.5)
    sfx.print("fetching 12 files, unpacking..")
    sfx.set_delay(0.1)
    sfx.print("Unpacking azure-dos to main dir")
    sfx.print("Unpacking azure-terminal to main dir")
    sfx.print("Unpacking azure-user-cli to main dir")
    sfx.print("Unpacking libazure-turbo to main dir")
    sfx.print("Unpacking libzure-gui to main dir")
    sfx.print("Reload system components..")
    sfx.set_delay(0.8)
    sfx.print("Reload system components finished.")
    sfx.set_delay(0.4)
    sfx.print("Azure systemctl commands ready: ")
    sfx.print("docker@azure-terminal.service")
    sfx.print("redis@azure-terminal.service")
    sfx.set_delay(0.8)
    sfx.print("azure-net@azure-terminal.service")
    sfx.cls()
    sfx.set_delay(0)
    sfx.print("§fWelcome use Azure Terminal.")
    sfx.print("§f")
    sfx.print('§f Type §l".help"§r§f to lern more')
    sfx.print('§f Type §l".prof"§r§f to open your profile')
    sfx.print("§f Join our qgroup to get newest update")
    sfx.print("§f Open the snowmenu and have a look!")
    sfx.print("§f")
    sfx.set_delay(1)
    sfx.print("§fSkyblueSuper@terminal: ~#")
    sfx.cprint(" azure-l98.EXE")
    sfx.cls()


class FXStageShow(Plugin):
    name = "特效展示台"

    FXStage = FXStage
    SFXStage = FXStage # deprecated

    def __init__(self, frame):
        super().__init__(frame)
        self.ListenPreload(self.on_def)

    def on_def(self):
        cb2bot = self.GetPluginAPI("Cb2Bot通信")
        if 0:
            from 前置_Cb2Bot通信 import TellrawCb2Bot

            cb2bot = self.get_typecheck_plugin_api(TellrawCb2Bot)
        cb2bot.regist_message_cb("sfx-1", self.show_sfx)

    @utils.thread_func("特效展示")
    def show_sfx(self, args):
        load_sfx_1(args[0])


entry = plugin_entry(FXStageShow, "自定义RPG-特效")

from collections.abc import Callable
from tooldelta import Player, utils
from tooldelta.constants import PacketIDS

if 0:
    from . import CustomRPGGames

system: "CustomRPGGames | None"


def set_system(sys: "CustomRPGGames"):
    global system
    system = sys
    sys.ListenPacket(PacketIDS.BlockActorData, on_sign, priority=1000)


def get_system() -> "CustomRPGGames":
    if system is None:
        raise RuntimeError("SYSTEM is not initialized")
    return system



cbs: dict[Player, list[Callable[[tuple[tuple[int, int, int], str]], None]]] = {}

def wait_put_sign(player: Player, remove_sign=True, timeout=60):
    getter, setter = utils.create_result_cb(tuple[tuple[int, int, int], str])
    cbs.setdefault(player, []).append(setter)
    res = getter(timeout)
    if res is None:
        return None
    else:
        x, y, z = res[0]
        get_system().game_ctrl.sendwocmd(f"setblock {x} {y} {z} air")
        return res

def on_sign(pk: dict):
    if "NBTData" in pk and "id" in pk["NBTData"]:
        if not (pk["NBTData"]["id"] == "Sign"):
            return False
        owner = pk["NBTData"]["FrontText"]["TextOwner"]
        player = get_system().game_ctrl.players.getPlayerByXUID(owner)
        if player is None:
            return False
        if player in cbs:
            signText = pk["NBTData"]["FrontText"]["Text"]
            placeX, placeY, placeZ = (
                pk["NBTData"]["x"],
                pk["NBTData"]["y"],
                pk["NBTData"]["z"],
            )
            cbs[player].pop(0)(((placeX, placeY, placeZ), signText))
            if not cbs[player]:
                del cbs[player]
    return False

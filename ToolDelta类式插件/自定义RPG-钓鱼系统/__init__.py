import random
from dataclasses import dataclass
from tooldelta import (
    Plugin,
    utils,
    TYPE_CHECKING,
    Config,
    fmts,
    game_utils,
    Player,
    plugin_entry,
)

FISH_PERCENT = 0.95


def _cmp(x, y):
    return (x, y) if x < y else (y, x)


class Cube:
    def __init__(
        self, sx: float, sy: float, sz: float, ex: float, ey: float, ez: float
    ):
        self.sx, self.ex = _cmp(sx, ex)
        self.sy, self.ey = _cmp(sy, ey)
        self.sz, self.ez = _cmp(sz, ez)

    def __contains__(self, inc: tuple[float, float, float]):
        x, y, z = inc
        return (
            self.sx <= x <= self.ex
            and self.sy <= y <= self.ey
            and self.sz <= z <= self.ez
        )


@dataclass
class FishingArea:
    hook: float
    time_range: tuple[int, int]
    area: Cube
    fish_and_weight: dict[str, float]
    treasure_and_weight: dict[str, float]


@dataclass
class Bait:
    name: str
    not_empty: float = 0.5
    speed_up: float = 0
    treasure: float = 0.1
    fish: float = 0.1
    reduce: float = 0.9


class CRPGFishing(Plugin):
    name = "自定义RPG-钓鱼系统"
    author = "SuperScript"
    version = (0, 0, 1)

    def __init__(self, frame):
        super().__init__(frame)
        CFG_STD = {
            "最小出鱼秒数": Config.PInt,
            "最大出鱼秒数": Config.PInt,
            "鱼饵效果": Config.AnyKeyValue(
                {
                    Config.KeyGroup(
                        "不钓空概率", "速度提升率", "上宝概率", "上鱼概率", "消耗概率"
                    ): float
                }
            ),
            "鱼池分配": Config.AnyKeyValue(
                {
                    Config.KeyGroup("上钩概率"): float,
                    "最小上钩秒数": int,
                    "最大上钩秒数": int,
                    "物品和权重": {
                        "鱼类": Config.AnyKeyValue((Config.PFloat, Config.PInt)),
                        "宝藏": Config.AnyKeyValue((Config.PFloat, Config.PInt)),
                    },
                }
            ),
        }
        CFG_DEFAULT = {
            "最小出鱼秒数": 10,
            "最大出鱼秒数": 20,
            "鱼饵效果": {},
            "鱼池分配": {
                "100000,10,100000~100064,64,100064": {
                    "上钩概率": 0.6,
                    "最小上钩秒数": 10,
                    "最大上钩秒数": 15,
                    "物品和权重": {},
                }
            },
        }
        self.cfg, _ = Config.get_plugin_config_and_version(
            self.name, CFG_STD, CFG_DEFAULT, self.version
        )
        self.fishings = self.load_cfg(self.cfg)
        self.baits = self.load_baits()
        self.ListenPreload(self.on_def)
        self.ListenPlayerLeave(self.on_player_leave)

    def load_baits(self):
        baits: dict[str, Bait] = {}
        for name, bait in self.cfg["鱼饵效果"].items():
            baits[name] = Bait(
                name,
                bait.get("不钓空概率", 0),
                bait.get("速度提升率", 0),
                bait.get("上宝概率", 0),
                bait.get("上鱼概率", 0),
                bait.get("消耗概率", 1),
            )
        return baits

    def load_cfg(self, cfg):
        fishings: list[FishingArea] = []
        for k, v in cfg["鱼池分配"].items():
            try:
                pos1, pos2 = k.split("~")
                sx, sy, sz = (float(i) for i in pos1.split(","))
                ex, ey, ez = (float(i) for i in pos2.split(","))
            except Exception:
                fmts.print_err(f"鱼池坐标名有误: {k}")
                raise SystemExit
            fishings.append(
                FishingArea(
                    v.get("上钩概率", 0.7),
                    (v["最小上钩秒数"], v["最大上钩秒数"]),
                    Cube(sx, sy, sz, ex, ey, ez),
                    v["物品和权重"]["鱼类"],
                    v["物品和权重"]["宝藏"],
                )
            )
        return fishings

    def on_def(self):
        self.rpg = self.GetPluginAPI("自定义RPG")
        self.cb2bot = self.GetPluginAPI("Cb2Bot通信")
        if TYPE_CHECKING:
            from 自定义RPG import CustomRPG
            from 前置_Cb2Bot通信 import TellrawCb2Bot

            self.rpg: CustomRPG
            self.cb2bot: TellrawCb2Bot
        self.check_cfg()
        self.cb2bot.regist_message_cb(r"sr.fishing.hook", self.hook_ok)
        self.cb2bot.regist_message_cb(r"sr.fishing.hook_init", self.hook_init)
        self.baits_player_loaded: dict[str, Bait | None] = {}

    def on_player_leave(self, playerf: Player):
        player = playerf.name
        if self.baits_player_loaded.get(player):
            del self.baits_player_loaded[player]

    def get_player_bait(self, player: Player):
        if player not in self.baits_player_loaded.keys():
            playerbas = self.rpg.player_holder.get_player_basic(player)
            use_bait = playerbas.metadatas.get("fish_bait")
            if use_bait:
                bait_item = self.rpg.backpack_holder.getItem(player, use_bait)
                if bait_item is not None:
                    tag_name = bait_item.item.id
                    if tag_name not in self.baits.keys():
                        raise ValueError(f"未加载鱼饵 {tag_name}")
                    bait = self.baits[tag_name]
                else:
                    bait = None
            else:
                bait = None
            self.baits_player_loaded[player.name] = bait
        else:
            bait = self.baits_player_loaded[player.name]
        return bait

    def check_cfg(self):
        for k, v in self.cfg["鱼池分配"].items():
            for item_tags in v["物品和权重"].values():
                for item_tag in item_tags.keys():
                    if not self.rpg.item_holder.item_exists(item_tag):
                        fmts.print_err(f"自定义RPG-钓鱼系统: 物品不存在: {item_tag}")
                        raise SystemExit

    @utils.thread_func("自定义RPG-钓鱼上钩")
    def hook_ok(self, args):
        (hook_uuid,) = args
        x, y, z = game_utils.getPosXYZ(f"@e[scores={{fish:uuid={hook_uuid}}}]")
        nearestPlayer = game_utils.getTarget(f"@a[x={x},y={y},z={z},c=1]")[0]
        in_pool = self.find_pool(x, y, z)
        if in_pool:
            self.game_ctrl.player_title(nearestPlayer, "§a")
            self.game_ctrl.player_subtitle(nearestPlayer, "§3≋≋§b≋≋ §f上钩！ §b≋≋§3≋≋")
            self.game_ctrl.sendwocmd(
                f"execute as {utils.to_player_selector(nearestPlayer)} at @s run playsound random.splash"
            )
            self.hook_ok_give(self.rpg.getPlayer(nearestPlayer), in_pool)
            self.game_ctrl.sendwocmd(f"kill @e[scores={{fish:uuid={hook_uuid}}}]")

    def hook_ok_give(self, player: Player, area: FishingArea):
        bait = self.get_player_bait(player)
        hook_percent = area.hook
        fish_percent = FISH_PERCENT
        if bait:
            hook_percent += bait.not_empty
            fish_percent += bait.fish - bait.treasure
        if random.random() >= hook_percent:
            player.show(
                "§6┃ ☬ 鱼儿脱钩啦... 这是一杆空竿。",
            )
            return
        is_fish = random.random() < fish_percent
        items: list[str] = []
        weights: list[float] = []
        for item, weight in (
            area.fish_and_weight if is_fish else area.treasure_and_weight
        ).items():
            items.append(item)
            weights.append(weight)
        final_section = random.choices(items, weights)[0]
        self.rpg.backpack_holder.giveItems(player, item := self.rpg.item_holder.createItems(final_section), False)
        item = item[0].item
        player.show(
            f"§b┃ ☬ §3你钓到了 §7<{self.rpg.item_holder.make_item_starlevel(item.id)}§7> §f{item.show_name}",
        )
        if self.rpg.item_holder.get_item_starlevel(final_section) >= 3:
            self.game_ctrl.say_to(
                f'@a[name=!"{player.name}"]',
                f"§b┃ ☬ §b{player.name} §3钓到了 §7<{self.rpg.item_holder.make_item_starlevel(item.id)}§7> §f{item.show_name}",
            )
        if bait:
            if random.random() > bait.reduce:
                self.rpg.backpack_holder.clearItem(player, bait.name, 1)
            if self.rpg.backpack_holder.getItemCount(player, bait.name) == 0:
                self.rpg.show_warn(player, "你当前的鱼饵用完了..")
                self.baits_player_loaded[player.name] = None

    def find_pool(self, x: float, y: float, z: float):
        for fishing_area in self.fishings:
            if (x, y, z) in fishing_area.area:
                return fishing_area
        return None

    def hook_init(self, args: list[str]):
        hook_uuid, player = args
        try:
            x, y, z = game_utils.getPosXYZ(f"@e[scores={{fish:uuid={hook_uuid}}}]")
        except ValueError:
            return
        pool = self.find_pool(x, y, z)
        if pool:
            smin, smax = pool.time_range
            r = random.randint(smin, smax)
            self.game_ctrl.sendwocmd(
                f"scoreboard players set @e[scores={{fish:uuid={hook_uuid}}}] fish:timer_ok {r}"
            )
            self.game_ctrl.player_title(player, "§a")
            self.game_ctrl.player_subtitle(player, "§3≋≋§b≋≋ §f抛竿... §b≋≋§3≋≋")
        else:
            self.game_ctrl.player_title(player, "§a")
            self.game_ctrl.player_subtitle(
                player, "§c✗ §6哎哎？ 在这里什么都钓不到的啊.."
            )


entry = plugin_entry(CRPGFishing)

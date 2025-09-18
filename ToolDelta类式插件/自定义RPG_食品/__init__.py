from importlib import reload
from tooldelta import Plugin, Player, utils, TYPE_CHECKING, plugin_entry

from . import food_frame, food_loader, event_apis

reload(food_loader)


class CustomRPGFood(Plugin):
    name = "自定义RPG-食品系统"
    author = "SuperScript"
    version = (0, 0, 1)

    event_apis = event_apis

    def __init__(self, frame):
        super().__init__(frame)
        self.food_loaded: dict[Player, food_frame.RPGFood] = {}
        food_frame.set_system(self)
        self.ListenPreload(self.on_def)
        self.ListenActive(self.on_inject)
        self.food_cds: dict[Player, float] = {}

    def on_def(self):
        self.cb2bot = self.GetPluginAPI("Cb2Bot通信")
        self.rpg = self.GetPluginAPI("自定义RPG")
        self.backpack = self.GetPluginAPI("虚拟背包")
        self.tutor = self.GetPluginAPI("自定义RPG-教程")
        if TYPE_CHECKING:
            global SlotItem
            from 前置_Cb2Bot通信 import TellrawCb2Bot
            from 自定义RPG import CustomRPG
            from 虚拟背包 import VirtuaBackpack
            from 自定义RPG_教程 import CustomRPGTutorial

            self.cb2bot: TellrawCb2Bot
            self.rpg: CustomRPG
            self.backpack: VirtuaBackpack
            self.tutor: CustomRPGTutorial
            SlotItem = VirtuaBackpack.SlotItem
        self.cb2bot.regist_message_cb("sr.food_eat", self.on_eat)
        food_loader.load_scripts(self)

    def on_inject(self):
        self.inject_use_func()

    def on_eat(self, args: list[str]):
        player = self.rpg.getPlayer(args[0])
        if player not in self.food_loaded.keys():
            food_uuid = self.rpg.player_holder.get_player_basic(player).metadatas.get(
                "onhand_food"
            )
            if food_uuid is None:
                self.rpg.show_warn(player, "你暂时没有这个食物..")
                self.set_food_to_hotbar(player, None)
                return
            else:
                food = self.load_food_from_basic(player, food_uuid)
                if food is None:
                    return
                self.food_loaded[player] = food
        food = self.food_loaded[player]
        food_run_out = self.player_eat(player, food)
        if food_run_out:
            self.rpg.show_warn(player, "你手上的食物被吃完了..")
            self.set_food_to_hotbar(player, None)
        else:
            self.set_food_to_hotbar(player, food)
        self.BroadcastEvent(event_apis.PlayerEatEvent(player, food).to_broadcast())

    def player_eat(self, player: Player, food: food_frame.RPGFood):
        need_reduced = not food.eat()
        if need_reduced:
            self.rpg.backpack_holder.clearItem(
                player,
                food.tag_name,
                1,  # , show_to_player=False
            )
            # self.rpg.rpg_upgrade.add_player_exp(player, 1)
            player.show("§a┃ §e吃到了美味的食物。")
        else:
            player.show(
                f"§a┃ {self.rpg.item_holder.getOrigItem(food.tag_name).disp_name} §r§e味道不错。"
            )
        food_run_out = self.rpg.backpack_holder.getItemCount(player, food.tag_name) <= 0
        if food_run_out:
            self.rpg.show_warn(player, "你手上的食物被吃完了..")
        self.BroadcastEvent(event_apis.PlayerEatEvent(player, food).to_broadcast())
        return food_run_out

    def load_food_from_basic(self, player: Player, food_uuid: str):
        food_slot = self.rpg.backpack_holder.getItem(player, food_uuid)
        if food_slot is None:
            self.set_food_to_hotbar(player, None)
            return None
        else:
            food = self.food_loaded[player] = food_frame.get_food_cls_by_tagname(
                food_slot.item.id
            )(self.rpg.player_holder.get_playerinfo(player))
            return food

    def switch_food(self, slotitem: "SlotItem", player: Player):
        food_id = slotitem.item.id
        playerinf = self.rpg.player_holder.get_playerinfo(player)
        if self.food_loaded.get(player) is None:
            food = self.load_food_from_basic(player, slotitem.uuid)
            self.rpg.show_succ(player, f"现在可在物品栏食用 §f{slotitem.disp_name}")
            self.rpg.show_inf(player, "再次使用可以将食物放回背包")
            self.rpg.player_holder.get_player_basic(player).metadatas["onhand_food"] = (
                slotitem.uuid
            )
            self.set_food_to_hotbar(player, food)
        elif self.food_loaded[player].tag_name != food_id:
            food = self.food_loaded[player] = food_frame.get_food_cls_by_tagname(
                food_id
            )(playerinf)
            self.rpg.show_inf(player, f"物品栏的食物换成了 §f{slotitem.disp_name}")
            self.rpg.player_holder.get_player_basic(player).metadatas["onhand_food"] = (
                slotitem.uuid
            )
            self.set_food_to_hotbar(player, food)
        else:
            del self.food_loaded[player]
            self.set_food_to_hotbar(player, None)
            self.rpg.show_inf(player, f"你把 §f{slotitem.disp_name} §r§f放回了背包中")
            self.rpg.player_holder.get_player_basic(player).metadatas["onhand_food"] = (
                None
            )

    def direct_eat(self, slotitem: "SlotItem", player: Player):
        entity = self.rpg.player_holder.get_playerinfo(player)
        food = food_frame.registered_foods_tagname[slotitem.id](entity)
        self.player_eat(player, food)

    def inject_use_func(self):
        foods = food_frame.registered_foods_tagname
        for k, v in self.backpack.get_registed_items().items():
            if food := foods.get(k):
                self.rpg.item_holder.LoadExtraItem(v, food.star_level)
                v.on_use["拿出/放回"] = self.switch_food
                v.on_use["食用"] = self.direct_eat

    def set_food_to_hotbar(self, player: Player, food: "food_frame.RPGFood | None"):
        player_s = player.safe_name
        if food:
            self.game_ctrl.sendwocmd(f"tag {player_s} add sr.have_food")
            self.game_ctrl.sendwocmd(
                f"replaceitem entity {player_s} slot.hotbar 3 {food.model_id} 1 {food.model_data} "
                r'{"item_lock":{"mode": "lock_in_slot"}}'
            )
        else:
            self.game_ctrl.sendwocmd(
                f"replaceitem entity {player_s} slot.hotbar 3 air 1 0"
            )
            self.game_ctrl.sendwocmd(f"tag {player_s} remove sr.have_food")

    @utils.timer_event(1, "CRPG:食品冷却")
    def on_timer(self):
        for player, cd in self.food_cds.copy().items():
            if cd <= 0:
                del self.food_cds[player]
                if (food := self.food_loaded.get(player)) is not None:
                    self.game_ctrl.sendwocmd(
                        f"replaceitem entity {player.safe_name} slot.hotbar 3 {food.model_id} 1 {food.model_data}"
                    )
            else:
                self.food_cds[player] = cd - 1


entry = plugin_entry(CustomRPGFood, "自定义RPG-食品")

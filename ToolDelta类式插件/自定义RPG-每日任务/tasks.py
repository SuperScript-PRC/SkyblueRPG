from .task_frame import DailyTask


# 击败 40 只怪物
class Kill20Monsters(DailyTask):
    disp_name = "击败 20 只怪物"
    points = 16

    @staticmethod
    def load_to_system(system):
        system.require_listen(system.rpg.event_apis.PlayerKillMobEvent)

    def __init__(self, parent, player, global_data):
        super().__init__(parent, player, global_data)
        self.e = self.sys.rpg.event_apis

    def OnEvent(self, event, player):
        if isinstance(event, self.e.PlayerKillMobEvent):
            mob = event.mob.cls
            if mob.is_harmful():
                o = self.data.get("kill", 0) + 1
                if o >= 1:
                    self.finish()
                else:
                    self.data["kill"] = o

    def Display(self) -> str:
        return f"§6{self.data.get('kill', 0)}§7/1 次击杀"


class RepairObject1Time(DailyTask):
    disp_name = "修补 1 次物品"
    points = 12

    @staticmethod
    def load_to_system(system):
        system.require_listen(system.rpg_repair.event_apis.PlayerRepairObjectEvent)

    def __init__(self, parent, player, global_data):
        super().__init__(parent, player, global_data)
        self.e = self.sys.rpg_repair.event_apis

    def OnEvent(self, event, player):
        if isinstance(event, self.e.PlayerRepairObjectEvent):
            self.finish()

    def Display(self) -> str:
        return "§6进行中"


class UpgradeObject1Time(DailyTask):
    disp_name = "升级 1 次武器或饰品"
    points = 12

    @staticmethod
    def load_to_system(system):
        system.require_listen(system.rpg_upgrade.event_apis.PlayerUpgradeObjectEvent)

    def __init__(self, parent, player, global_data):
        super().__init__(parent, player, global_data)
        self.e = self.sys.rpg_upgrade.event_apis

    def OnEvent(self, event, player):
        if isinstance(event, self.e.PlayerUpgradeObjectEvent):
            self.finish()

    def Display(self) -> str:
        return "§6进行中"


class Fish10Times(DailyTask):
    disp_name = "进行 10 次不空杆钓鱼"
    points = 16

    @staticmethod
    def load_to_system(system) -> None:
        system.require_listen(system.rpg_fishing.event_apis.PlayerFishHookedEvent)

    def __init__(self, parent, player, global_data):
        super().__init__(parent, player, global_data)
        self.e = self.sys.rpg_fishing.event_apis

    def OnEvent(self, event, player):
        if isinstance(event, self.e.PlayerFishHookedEvent) and event.not_empty:
            o = self.data.get("hooked", 0) +1
            if o >= 10:
                self.finish()
            self.data["hooked"] = o

    def Display(self) -> str:
        return f"§6{self.data.get('hooked', 0)}§7/10 次上钩"


class Eat4Times(DailyTask):
    disp_name = "享用 4 份食物"
    points = 20

    @staticmethod
    def load_to_system(system) -> None:
        system.require_listen(system.rpg_food.event_apis.PlayerEatEvent)

    def __init__(self, parent, player, global_data):
        super().__init__(parent, player, global_data)
        self.e = self.sys.rpg_food.event_apis

    def OnEvent(self, event, player):
        if isinstance(event, self.e.PlayerEatEvent):
            o = self.data.get("eat", 0) + 1
            if o >= 4:
                self.finish()
            self.data["eat"] = o

    def Display(self) -> str:
        return f"§6{self.data.get('eat', 0)}§7/4 次进食"


class Collect10Times(DailyTask):
    disp_name = "采集 10 份资源"
    points = 16

    @staticmethod
    def load_to_system(system) -> None:
        system.require_listen(system.rpg_source.event_apis.PlayerDigSourceEvent)

    def __init__(self, parent, player, global_data):
        super().__init__(parent, player, global_data)
        self.e = self.sys.rpg_source.event_apis

    def OnEvent(self, event, player):
        if isinstance(event, self.e.PlayerDigSourceEvent):
            o = self.data.get("dig", 0) + 1
            if o >= 4:
                self.finish()
            self.data["dig"] = o

    def Display(self) -> str:
        return f"§6{self.data.get('dig', 0)}§7/10 次采集"


class Trade10Times(DailyTask):
    disp_name = "进行 10 次交易"
    points = 12

    @staticmethod
    def load_to_system(system) -> None:
        system.require_listen(system.rpg_plot.event_apis.PlayerTradingWithNPCEvent)

    def __init__(self, parent, player, global_data):
        super().__init__(parent, player, global_data)
        self.e = self.sys.rpg_plot.event_apis

    def OnEvent(self, event, player):
        if isinstance(event, self.e.PlayerTradingWithNPCEvent):
            o = self.data.get("trade", 0) + 1
            if o >= 4:
                self.finish()
            self.data["trade"] = o + 1

    def Display(self) -> str:
        return f"§6{self.data.get('trade', 0)}§7/10 次交易"

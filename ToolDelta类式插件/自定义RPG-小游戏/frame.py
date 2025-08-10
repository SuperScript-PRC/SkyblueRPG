from tooldelta import Player

class Room:
    def __init__(self, room_id: str, player: Player):
        self.room_id = room_id
        self.player = player

    def start(self): ...

    def reset(self): ...

    def exit(self): ...

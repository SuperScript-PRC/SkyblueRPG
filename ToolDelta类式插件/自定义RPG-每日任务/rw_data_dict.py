from typing import Any, TYPE_CHECKING
from tooldelta import utils, Player

if TYPE_CHECKING:
    from . import CustomRPGDailyTask


class RWDataDict:
    def __init__(
        self, sys: "CustomRPGDailyTask", player: Player, with_name: str | None = None
    ):
        self.path = sys.format_player_data_path(player)
        self._with_name = with_name
        self.changed = False

    def get(self, key: str, default=None) -> Any:
        return self._datas.get(key, default)

    def reset(self):
        if self._with_name is not None:
            self._shown_datas.clear()
        else:
            raise ValueError("with_name is None when calling reset()")

    def __enter__(self):
        self._datas = utils.tempjson.load_and_read(
            self.path, need_file_exists=False, default={}
        )
        if self._with_name is not None:
            self._shown_datas = self._datas.get(self._with_name, {})
        else:
            self._shown_datas = self._datas
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._with_name is not None:
            self._datas[self._with_name] = self._shown_datas
        if self.changed:
            utils.tempjson.load_and_write(self.path, self._datas, need_file_exists=False)

    def __getitem__(self, item: str):
        return self._datas[item]

    def __setitem__(self, key: str, value):
        self._datas[key] = value
        self.changed = True

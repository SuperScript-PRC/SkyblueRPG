from ..插件文件.ToolDelta类式插件.自定义RPG_剧情与任务 import CustomRPGPlotAndTask
from ..插件文件.ToolDelta类式插件.自定义RPG_剧情与任务.quest_loader import (
    RegisteredPlot,
    plot,
)

CPT = CustomRPGPlotAndTask

__all__ = [
    "CPT",
    "RegisteredPlot",
    "plot",
]

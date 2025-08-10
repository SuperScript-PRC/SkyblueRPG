from tooldelta.utils import cfg


def get_material_cfg_standard():
    return cfg.AnyKeyValue(
        {"显示名": str, "星级": int, cfg.KeyGroup("所属组类"): str, "描述": str}
    )


def get_basic_cfg_standard():
    return {
        "玩家初始设置": {"血量": cfg.PInt},
        "星级显示": {"亮": str, "暗": str},
        "基本属性名称": {
            "属性1": str,
            "属性2": str,
            "属性3": str,
            "属性4": str,
            "属性5": str,
            "属性6": str,
            "属性7": str,
        },
        "玩家默认设置": {"默认重生点": cfg.JsonList(int, 3)},
    }


def get_basic_cfg_default():
    return {
        "玩家初始设置": {"血量": 100},
        "星级显示": {"亮": "§e♦", "暗": "§7♦"},
        "基本属性名称": {
            "属性1": "§c火属性",
            "属性2": "§b冰属性",
            "属性3": "§a草属性",
            "属性4": "§d雷属性",
            "属性5": "§e金属性",
            "属性6": "§9虚空属性",
            "属性7": "§5末影属性",
        },
        "玩家默认设置": {"默认重生点": [0, 0, 0]},
    }

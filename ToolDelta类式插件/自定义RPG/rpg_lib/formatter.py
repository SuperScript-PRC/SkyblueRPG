if 0:
    from .. import CustomRPG

PROPS_PROC: dict[str, str] = {}

# ROME = {
#     "I": "Ｉ",
#     "V": "Ｖ",
#     "X": "Ｘ",
#     "C": "Ｃ",
#     "L": "Ｌ",
#     "M": "Ｍ",
#     "D": "Ｄ",
# }


def init_proc_mapping(system: "CustomRPG") -> dict[str, str]:
    props_atk = system.constants.Properties.atks()
    props_def = system.constants.Properties.defs()
    props_atkadd = system.constants.Properties.atk_adds()
    props_defadd = system.constants.Properties.def_adds()
    properties = system.constants.Properties
    return dict(
        (
            (properties.ATKBoost, "§4攻击加成"),
            (properties.DEFBoost, "§9防御加成"),
            (
                properties.HPBoost,
                "§c生命提升",
            ),
            (
                properties.HPBoostAdd,
                "§c生命提升加成",
            ),
            (
                properties.ChargeAdd,
                "§b充能效率加成",
            ),
            (
                properties.CritChance,
                "§d暴击率",
            ),
            (
                properties.CritDamage,
                "§d暴击伤害",
            ),
            (
                properties.EffectHit,
                "§s效果命中",
            ),
            (
                properties.EffectRes,
                "§u效果抵抗",
            ),
            *(
                (
                    i,
                    f"{j}攻击力",
                )
                for i, j in zip(props_atk, system.elements.values())
            ),
            *(
                (
                    i,
                    f"{j}防御力",
                )
                for i, j in zip(props_def, system.elements.values())
            ),
            *(
                (
                    i,
                    f"{j}攻击加成",
                )
                for i, j in zip(props_atkadd, system.elements.values())
            ),
            *(
                (
                    i,
                    f"{j}防御加成",
                )
                for i, j in zip(props_defadd, system.elements.values())
            ),
        )
    )

def to_rome(num: int):
    output = ""
    while num >= 50:
        output += "L"
        num -= 50
    while num >= 10:
        output += "X"
        num -= 10
    if num == 9:
        return output + "IX"
    elif num >= 5:
        return output + "V" + "I" * (num - 5)
    elif num == 4:
        return output + "IV"
    else:
        return output + "I" * num

def to_big_rome(num: int):
    output = ""
    while num >= 50:
        output += "Ｌ"
        num -= 50
    while num >= 10:
        output += "Ｘ"
        num -= 10
    if num == 9:
        return output + "ＩＸ"
    elif num >= 5:
        return output + "Ｖ" + "Ｉ" * (num - 5)
    elif num == 4:
        return output + "ＩＶ"
    elif num > 0:
        return output + "Ｉ" * num
    else:
        return "0"


def format_prop(system: "CustomRPG", prop_name: str, level: int):
    if PROPS_PROC == {}:
        m: dict[str, str] = init_proc_mapping(system)
        PROPS_PROC.update(m)
    return PROPS_PROC[prop_name], to_rome(level)

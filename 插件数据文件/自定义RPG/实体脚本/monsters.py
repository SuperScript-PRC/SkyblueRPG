from dev_rpg_lib import frame_mobs, rpg_entities, constants # type: ignore[reportMissingModuleSource]

SrcType = constants.SrcType
Mob = frame_mobs.Mob
PlayerEntity = rpg_entities.PlayerEntity

class Doll(Mob):
    model_id = "villager"
    show_name = "测试人偶"
    tag_name = "测试人偶"
    type_id = 32767
    max_hp = 999999999999
    atks = (0, 0, 0, 0, 0, 0, 0)
    defs = (0, 0, 0, 0, 0, 0, 0)
    drop_exp_range = (0, 1)
    loots: tuple[tuple[str, float], ...] = ()

    @classmethod
    def injured(
        cls,
        entity,
        fromwho,
        damages: list[int],
        is_crit: bool
    ) -> bool:
        if isinstance(fromwho, PlayerEntity):
            weapon = fromwho.weapon
            if weapon is not None:
                if weapon.default_durability - weapon.durability < 10:
                    weapon.durability = weapon.default_durability
                if fromwho.player.is_op():
                    weapon.durability = weapon.default_durability
                    fromwho.add_charge(10)
        return False

    @classmethod
    def ready_died(
        cls,
        entity,
        killer,
    ) -> bool:
        entity.cured(entity, SrcType.NORMAL, cls.max_hp)
        return True

class FuHuaJiangShi(Mob):
    model_id = "zombie"
    show_name = "辐化僵尸"
    tag_name = "辐化僵尸"
    type_id = 1
    max_hp = 200
    atks = (0, 0, 8, 0, 8, 4, 0)
    defs = (0, 0, 0, 0, 0, 0, 0)
    drop_exp_range = (4, 6)
    loots = (
        ("铜币", 1, 0.2),
        ("精炼铁锭", 1, 0.05),
    )


class YanCengZhiZhu(Mob):
    model_id = "spider"
    show_name = "岩层蜘蛛"
    tag_name = "岩层蜘蛛"
    type_id = 2
    max_hp = 140
    atks = (0, 0, 7, 0, 12, 0, 0)
    defs = (0, 0, 0, 0, 0, 0, 0)
    effect_hit = 0.1
    effect_anti = 0.1
    drop_exp_range = (2, 3)
    loots = (
        ("蛛丝", 1, 1),
        ("蛛丝", 1, 0.2),
        ("地岩粉", 1, 0.04),
    )

class ConglinZhiZhu(Mob):
    model_id = "spider"
    show_name = "丛林蜘蛛"
    tag_name = "丛林蜘蛛"
    type_id = 3
    max_hp = 140
    atks = (0, 0, 7, 0, 11, 0, 0)
    defs = (0, 0, 0, 0, 0, 0, 0)
    effect_hit = 0.1
    effect_anti = 0.1
    drop_exp_range = (2, 3)
    loots = (
        ("蛛丝", 1, 1),
        ("蛛丝", 1, 0.2),
        ("蛛丝", 1, 0.1),
    )

class FuGuJianShi(Mob):
    model_id = "skeleton"
    show_name = "腐骨剑士"
    tag_name = "腐骨剑士"
    type_id = 4
    max_hp = 180
    atks = (0, 16, 0, 0, 8, 0, 0)
    defs = (0, 0, 0, 0, 10, 0, 0)
    drop_exp_range = (5, 7)
    loots = (
        ("腐骨", 1, 1),
        ("腐骨", 1, 0.3),
        ("骨片", 1, 0.1),
    )

    @classmethod
    def init(cls, entity):
        entity.run_cmd("replaceitem entity %t slot.weapon.mainhand 0 iron_sword")



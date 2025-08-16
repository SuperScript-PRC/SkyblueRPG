from dev_rpg_lib import frame_mobs # type: ignore[reportMissingModuleSource]

Mob = frame_mobs.Mob


class FuGuJianShi(Mob):
    model_id = "chicken"
    show_name = "丛林鸡"
    tag_name = "丛林鸡"
    type_id = 5
    max_hp = 80
    drop_exp_range = (1, 2)
    loots = (
        ("生鸡肉", 1, 1),
        ("生鸡肉", 1, 0.3),
    )


class QianShuiYu(Mob):
    model_id = "tropicalfish"
    show_name = "浅水鱼"
    tag_name = "浅水鱼"
    type_id = 6
    max_hp = 10
    drop_exp_range = (1, 2)
    loots = (
        ("浅水鱼肉块", 2, 1),
        ("浅水鱼肉块", 1, 0.3),
    )


class YeNiu(Mob):
    model_id = "cow"
    show_name = "野牛"
    tag_name = "野牛"
    type_id = 7
    max_hp = 220
    effect_hit = 0.1
    effect_anti = 0.1
    drop_exp_range = (3, 5)
    loots = (
        ("生牛肉", 1, 1),
        ("生牛肉", 1, 0.6),
        ("生牛肉", 1, 0.3),
        ("牛皮", 1, 0.6),
    )

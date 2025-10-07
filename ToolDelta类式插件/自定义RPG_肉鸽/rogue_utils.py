from threading import Event
from tooldelta import Player
from .define import AreaType, MobWave
from .frame_areas import allocate_area as _allocate_area
from .frame_levels import PVELevel

if 0:
    from . import entry

    RPGEffect = entry.rpg.frame_effects.RPGEffect

MAX_EFFECT_TIME = 0xFFFFFFFF
MONEY_TAGNAME = "r:金粒"


def get_system():
    from . import entry

    return entry


def calculate_mc_text_length(text: str):
    return sum((2 if ord(char) in range(0x4E00, 0xA000) else 1) for char in text)


def cut_content_by_length(text: str, max_length: int = 40):
    lines: list[str] = []
    cache_content = ""
    line_len = 0
    for char in text:
        if char == "\n":
            lines.append(cache_content)
            cache_content = ""
            line_len = 0
            continue
        cache_content += char
        line_len += 2 if ord(char) in range(0x4E00, 0xA000) else 1
        if line_len >= max_length:
            lines.append(cache_content)
            cache_content = ""
            line_len = 0
    if cache_content:
        lines.append(cache_content)
    return lines


def select_effect(player: Player, _effects: list["tuple[str, int, int] | RPGEffect"]):
    sys = get_system()
    align = sys.bigchar.mctext.align
    RPGEffect = sys.rpg.frame_effects.RPGEffect
    entity = sys.rpg.api_holder.get_player_entity(player)
    snowmenu = sys.snowmenu
    curr_page = -1
    output = ""
    effects = [
        i
        if isinstance(i, RPGEffect)
        else sys.rpg.find_effect_class(i[0])(entity, entity, i[1], i[2])
        for i in _effects
    ]

    def update_disp(page: int):
        nonlocal output
        output = "请选择一项效果：\n"
        effect_names = [f"➜【{e.name}】  " for e in effects]
        prefix_length = align.get_lines_width(effect_names) // 12
        prefix_spaces = align.get_specific_length_spaces(prefix_length * 12)
        for i, effect in enumerate(effects):
            docs = align.cut_by_length(effect.doc(), 40)
            prefix = f"【{effect.name}】 "
            body = (
                align.align_left(("§a➜" if i == page else "§2") + prefix, prefix_length)
                + "§7"
                + docs[0]
            )
            if len(docs) > 1:
                body += ("\n§a" + prefix_spaces).join("§7" + i for i in docs[1:])
            output += "\n" + body

    def disp(_, page: int):
        if page >= len(effects):
            return None
        nonlocal curr_page, output
        if curr_page != page:
            update_disp(page)
        curr_page = page
        return output

    while True:
        section = snowmenu.simple_select(player, disp)
        if section is None:
            if player not in get_system().game_ctrl.players:
                return None
            get_system().rpg.show_warn(player, "请选择一个选项")
            continue
        break
    entity.add_effect(eff := effects[section])
    return eff


def select_effect_simple(player: Player, _effects: list[tuple[str, int] | str]):
    effects: list["tuple[str, int, int] | RPGEffect"] = []
    for e in _effects:
        if isinstance(e, str):
            effects.append((e, MAX_EFFECT_TIME, 1))
        else:
            effects.append((e[0], MAX_EFFECT_TIME, e[1]))
    if s := select_effect(player, effects):
        return s
    raise SystemExit("未选择效果")


def allocate_area(area_type: AreaType):
    return _allocate_area(area_type)


def clear_rogue_virtual_items(player: Player):
    rpg = get_system().rpg
    items = set(
        rpg.backpack.load_backpack(player).find_item_by_metadata_key("srpg:rogue_item")
        + rpg.backpack.load_backpack(player).find_item_by_category("映像世界")
    )
    for item in items:
        rpg.backpack_holder.removePlayerStore(player, item, count=item.count)


def recover_from_rogue_status(player: Player):
    rpg = get_system().rpg
    player_basic = rpg.api_holder.get_player_basic(player)
    orig_weapon_uuids = rpg.pdstore.get_property(player, "srpg:orig_weapon_uuids")
    if orig_weapon_uuids is not None:
        player_basic.mainhand_weapons_uuid = orig_weapon_uuids
    else:
        get_system().print_war("恢复玩家的主手物品 失败")
        # player_basic.mainhand_weapons_uuid = [None] * 4
    orig_relic_uuids = rpg.pdstore.get_property(player, "srpg:orig_relic_uuids")
    if orig_relic_uuids is not None:
        player_basic.relics_uuid = orig_relic_uuids
    else:
        get_system().print_war("恢复玩家的饰品 失败")
        # player_basic.mainhand_weapons_uuid = [None] * 8
    rpg.player_holder.update_playerentity_from_basic_easy(player)


def copy_weapons_and_relics_to_virtual(player: Player):
    rpg = get_system().rpg
    player_basic = rpg.api_holder.get_player_basic(player)
    # weapons
    orig_weapon_uuids = player_basic.mainhand_weapons_uuid.copy()
    weapon_items_copy = [
        (it.copy() if (it := rpg.backpack_holder.getItem(player, i)) else None)
        if i is not None
        else None
        for i in orig_weapon_uuids
    ]
    player_basic.mainhand_weapons_uuid = [
        i.uuid if i else None for i in weapon_items_copy
    ]
    for weapon_item in weapon_items_copy:
        if weapon_item is not None:
            weapon_item.metadata["srpg:rogue_item"] = True
            # TODO: 武器耐久给满
            rpg.backpack_holder.giveItem(player, weapon_item)
    # relics
    orig_relic_uuids = player_basic.relics_uuid.copy()
    relic_items_copy = [
        (it.copy() if (it := rpg.backpack_holder.getItem(player, i)) else None)
        if i is not None
        else None
        for i in orig_relic_uuids
    ]
    player_basic.relics_uuid = [i.uuid if i else None for i in relic_items_copy]
    for relic_item in relic_items_copy:
        if relic_item is not None:
            relic_item.metadata["srpg:rogue_item"] = True
            rpg.backpack_holder.giveItem(player, relic_item)
    # update
    rpg.pdstore.set_property(player, "srpg:orig_weapon_uuids", orig_weapon_uuids)
    rpg.pdstore.set_property(player, "srpg:orig_relic_uuids", orig_relic_uuids)
    rpg.player_holder.update_playerentity_from_basic_easy(player)


def pve(player: Player, mob_waves: list[MobWave]):
    finished_event = Event()
    storage = get_system().get_storage(player)

    def on_finished(_):
        finished_event.set()

    main_level = storage.current_level
    temp_level = PVELevel(storage, allocate_area(AreaType.PVE), on_finished=on_finished)
    temp_level.mob_waves = mob_waves.copy()
    # temp change current level
    storage.executor.rogue.start_level(storage, temp_level)
    storage.current_level = main_level
    while not finished_event.is_set():
        finished_event.wait(10)
    storage.executor.rogue._teleport_to_current_level(storage)
    return temp_level.win


def add_effect(player: Player, effect_name: str, sec: int, lv: int = 1):
    player_entity = get_system().rpg.api_holder.get_player_entity(player)
    player_entity.add_effect(effect_name, None, sec, lv)


def give_money(player: Player, amount: int):
    api = get_system().rpg.api_holder
    api.giveItem(player, api.createItem(MONEY_TAGNAME, amount))


def get_money_amount(player: Player):
    api = get_system().rpg.api_holder
    return api.getItemCount(player, MONEY_TAGNAME)


def reduce_money(player: Player, amount: int):
    api = get_system().rpg.api_holder
    api.clearItem(player, MONEY_TAGNAME, amount)

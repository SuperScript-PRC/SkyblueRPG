## Broadcasts
- "CRPG:WeaponEquip"
    - 玩家装备/切换武器
    - args:
        - Player: 触发装备动作的玩家
        - int: 槽位号
        - SlotItem: 被装备的道具
    - returns:
        - None: 允许装备武器
        - str: 拦截装备武器(原因)

- "CRPG:WeaponUnequip"
    - 玩家卸下武器
    - args:
        - Player: 触发卸下动作的玩家
        - int: 槽位号
    - returns:
        - None: 允许卸下武器
        - str: 拦截卸下武器(原因)

- "CRPG:ArmorEquip"
    - 玩家装备护甲
    - args:
        - Player: 触发装备动作的玩家
        - int: 槽位号
        - SlotItem: 被装备的道具
    - returns:
        - None: 允许装备护甲
        - str: 拦截装备护甲(原因)
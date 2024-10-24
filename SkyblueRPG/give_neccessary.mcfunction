# {"初始方向1": "z+", "初始方向2": "x+", "最大延伸": "100"}
# #(循环)#{80}
execute as @a unless entity @s[hasitem={item=minecraft:snowball}] run give @s minecraft:snowball 16 0 {"item_lock":{ "mode":"lock_in_inventory"}}
# #(连锁)
execute as @a unless entity @s[hasitem={item=minecraft:splash_potion}] run give @s minecraft:splash_potion 1 0 {"item_lock":{ "mode":"lock_in_inventory"}}
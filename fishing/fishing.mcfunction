# {"初始方向1": "z+", "初始方向2": "x+", "最大延伸": "100"}
# #(循环)#{20}
scoreboard players add @e[type=minecraft:fishing_hook] fish:uuid 0
# #(连锁)
scoreboard players add @e[type=minecraft:fishing_hook] fish:timer 1
execute as @e[type=minecraft:fishing_hook] at @s if block ~~~ water [] if score @s fish:timer > @s fish:timer_ok run tellraw @a[tag=sr.rpg_bot] {"rawtext":[{"text":"sr.fishing.hook"},{"score":{"name":"@s","objective":"fish:uuid"}}]}
# #(循环)#{5}
execute as @e[type=minecraft:fishing_hook,scores={fish:uuid=0},c=1] run scoreboard players add uuid fish:uuid 1
# #(连锁)
execute as @e[type=minecraft:fishing_hook,scores={fish:uuid=0},c=1] at @s if block ~~~ water [] at @s run tellraw @a[tag=sr.rpg_bot] {"rawtext":[{"text":"sr.fishing.hook_init"},{"score":{"name":"uuid","objective":"fish:uuid"}},{"selector":"@p"}]}
execute as @e[type=minecraft:fishing_hook,scores={fish:uuid=0},c=1] run scoreboard players operation @s fish:uuid = uuid fish:uuid
# #(脉冲)
scoreboard objectives add fish:timer dummy
# #(连锁)
scoreboard objectives add fish:timer_ok dummy
scoreboard objectives add fish:uuid dummy
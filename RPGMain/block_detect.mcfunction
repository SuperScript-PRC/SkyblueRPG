# {"初始方向1": "z+", "初始方向2": "x+", "最大延伸": "100"}
# #(循环)#{5}
# ================ 水
execute as @e[scores={sr:ms_rtid=1..},tag=!bd.in_water] at @s if block ~~~ minecraft:water run tellraw @a[tag=sr.rpg_bot] {"rawtext":[{"text":"act.in_water"},{"score":{"name":"@s","objective":"sr:ms_rtid"}},{"score":{"name":"@s","objective":"sr:ms_uuid"}}]}
# #(连锁)#[1]
execute as @e[scores={sr:ms_rtid=1..},tag=!bd.in_water] at @s if block ~~~ minecraft:water run tag @s add bd.in_water
execute as @e[scores={sr:ms_rtid=1..},tag=bd.in_water] at @s unless block ~~~ minecraft:water run tellraw @a[tag=sr.rpg_bot] {"rawtext":[{"text":"act.out_water"},{"score":{"name":"@s","objective":"sr:ms_rtid"}},{"score":{"name":"@s","objective":"sr:ms_uuid"}}]}
# #[1]
execute as @e[scores={sr:ms_rtid=1..},tag=bd.in_water] at @s unless block ~~~ minecraft:water run tag @s remove bd.in_water
# ================ 火
execute as @e[scores={sr:ms_rtid=1..},tag=!bd.in_fire] at @s if block ~~~ minecraft:fire run tellraw @a[tag=sr.rpg_bot] {"rawtext":[{"text":"act.in_fire"},{"score":{"name":"@s","objective":"sr:ms_rtid"}},{"score":{"name":"@s","objective":"sr:ms_uuid"}}]}
# #(连锁)#[1]
execute as @e[scores={sr:ms_rtid=1..},tag=!bd.in_fire] at @s if block ~~~ minecraft:fire run tag @s add bd.in_fire
execute as @e[scores={sr:ms_rtid=1..},tag=bd.in_fire] at @s unless block ~~~ minecraft:fire run tellraw @a[tag=sr.rpg_bot] {"rawtext":[{"text":"act.out_fire"},{"score":{"name":"@s","objective":"sr:ms_rtid"}},{"score":{"name":"@s","objective":"sr:ms_uuid"}}]}
# #[1]
execute as @e[scores={sr:ms_rtid=1..},tag=bd.in_fire] at @s unless block ~~~ minecraft:fire run tag @s remove bd.in_fire
# ================ 熔岩
execute as @e[scores={sr:ms_rtid=1..},tag=!bd.in_lava] at @s if block ~~~ minecraft:lava run tellraw @a[tag=sr.rpg_bot] {"rawtext":[{"text":"act.in_lava"},{"score":{"name":"@s","objective":"sr:ms_rtid"}},{"score":{"name":"@s","objective":"sr:ms_uuid"}}]}
# #(连锁)#[1]
execute as @e[scores={sr:ms_rtid=1..},tag=!bd.in_lava] at @s if block ~~~ minecraft:lava run tag @s add bd.in_lava
execute as @e[scores={sr:ms_rtid=1..},tag=bd.in_lava] at @s unless block ~~~ minecraft:lava run tellraw @a[tag=sr.rpg_bot] {"rawtext":[{"text":"act.out_lava"},{"score":{"name":"@s","objective":"sr:ms_rtid"}},{"score":{"name":"@s","objective":"sr:ms_uuid"}}]}
# #[1]
execute as @e[scores={sr:ms_rtid=1..},tag=bd.in_lava] at @s unless block ~~~ minecraft:lava run tag @s remove bd.in_lava
# ================ 水中
execute as @e[family=!fish,scores={sr:ms_rtid=1..},tag=!bd.in_water2] at @s if block ~~1.2~ minecraft:water run tellraw @a[tag=sr.rpg_bot] {"rawtext":[{"text":"act.in_water2"},{"score":{"name":"@s","objective":"sr:ms_rtid"}},{"score":{"name":"@s","objective":"sr:ms_uuid"}}]}
# #(连锁)#[1]
execute as @e[family=!fish,scores={sr:ms_rtid=1..},tag=!bd.in_water2] at @s if block ~~1.2~ minecraft:water run tag @s add bd.in_water2
execute as @e[family=!fish,scores={sr:ms_rtid=1..},tag=bd.in_water2] at @s unless block ~~1.2~ minecraft:water run tellraw @a[tag=sr.rpg_bot] {"rawtext":[{"text":"act.out_water2"},{"score":{"name":"@s","objective":"sr:ms_rtid"}},{"score":{"name":"@s","objective":"sr:ms_uuid"}}]}
# #[1]
execute as @e[family=!fish,scores={sr:ms_rtid=1..},tag=bd.in_water2] at @s unless block ~~1.2~ minecraft:water run tag @s remove bd.in_water2
# ================ 雪中
execute as @e[scores={sr:ms_rtid=1..},tag=!bd.in_snow] at @s if block ~~~ minecraft:powder_snow run tellraw @a[tag=sr.rpg_bot] {"rawtext":[{"text":"act.in_snow"},{"score":{"name":"@s","objective":"sr:ms_rtid"}},{"score":{"name":"@s","objective":"sr:ms_uuid"}}]}
# #(连锁)#[1]
execute as @e[scores={sr:ms_rtid=1..},tag=!bd.in_snow] at @s if block ~~~ minecraft:powder_snow run tag @s add bd.in_snow
execute as @e[scores={sr:ms_rtid=1..},tag=bd.in_snow] at @s unless block ~~~ minecraft:powder_snow run tellraw @a[tag=sr.rpg_bot] {"rawtext":[{"text":"act.out_snow"},{"score":{"name":"@s","objective":"sr:ms_rtid"}},{"score":{"name":"@s","objective":"sr:ms_uuid"}}]}
# #[1]
execute as @e[scores={sr:ms_rtid=1..},tag=bd.in_snow] at @s unless block ~~~ minecraft:powder_snow run tag @s remove bd.in_snow
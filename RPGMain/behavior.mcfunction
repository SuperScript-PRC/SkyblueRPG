# {"初始方向1": "z+", "初始方向2": "x+", "最大延伸": "100"}
# #(循环)#{10}
# 奔跑检测
execute as @a[tag=!sr.running] at @s anchored eyes positioned ~~-1.2~ unless entity @s[r=0.4] run tellraw @a[tag=sr.rpg_bot] {"rawtext":[{"text":"sr.switch.running"},{"selector":"@s"}]}
# #(连锁)#[1]
execute as @a[tag=!sr.running] at @s anchored eyes positioned ~~-1.2~ unless entity @s[r=0.4] run tag @s add sr.running
execute as @a[tag=sr.running] at @s anchored eyes positioned ~~-1.2~ if entity @s[r=0.4] run tellraw @a[tag=sr.rpg_bot] {"rawtext":[{"text":"sr.switch.no.running"},{"selector":"@s"}]}
# #[1]
execute as @a[tag=sr.running] at @s anchored eyes positioned ~~-1.2~ if entity @s[r=0.4] run tag @s remove sr.running
# 潜行检测
execute as @a[tag=sr.shifted,tag=!sr.shifting] run tellraw @a[tag=sr.rpg_bot] {"rawtext":[{"text":"sr.switch.no.shifting"},{"selector":"@s"}]}
# #[1]
execute as @a[tag=sr.shifted,tag=!sr.shifting] at @s run tag @s remove sr.shifted
tag @a remove sr.shifting
execute as @a[tag=!sr.shifted] at @s unless entity @s[y=~1.51,dy=1] run tag @s add sr.shifting
execute as @a[tag=sr.shifting,tag=!sr.shifted] run tellraw @a[tag=sr.rpg_bot] {"rawtext":[{"text":"sr.switch.shifting"},{"selector":"@s"}]}
# #[1]
tag @a[tag=sr.shifting,tag=!sr.shifted] add sr.shifted
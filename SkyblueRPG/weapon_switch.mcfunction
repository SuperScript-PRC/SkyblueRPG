# {"初始方向1": "z+", "初始方向2": "x+", "最大延伸": "100"}
# #(循环)#{5}
tag @a[tag=sr.shifting] add sr.shifted
execute as @a[tag=sr.shifted] at @s if entity @s[y=~1.51,dy=1] run tag @s add sr.shifted
tag @a remove sr.shifted
execute as @a[tag=!sr.shifted] at @s unless entity @s[y=~1.51,dy=1] run tag @s add sr.shifting
execute as @a[tag=sr.shifted] at @s if entity @s[hasitem={item=minecraft:snowball,location=slot.slot.weapon.mainhand}] run tellraw @a[tag=sr.rpg_bot] {"rawtext":[{"text":"sr.player.switch.weapon"},{"selector":"@s"}]}
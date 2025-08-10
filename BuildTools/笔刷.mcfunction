# {"初始方向1": "z+", "初始方向2": "x+", "最大延伸": "100"}
# #(循环)
execute as @a[tag=build.paint] at @s positioned ^^^8 run structure load 笔刷 ~~~
# #(连锁)
execute as @a[tag=!build.paint] at @s if entity @s[hasitem={item=minecraft:iron_ingot,data=700,location=slot.weapon.mainhand}] run tag @s add build.paint
execute as @a[tag=build.paint] unless entity @s[hasitem={item=minecraft:iron_ingot,data=700,location=slot.weapon.mainhand}] run tag @s remove build.paint


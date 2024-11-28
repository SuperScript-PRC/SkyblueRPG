# {"初始方向1": "z+", "初始方向2": "x+", "最大延伸": "100"}
# #(循环)#{5}
replaceitem entity @a[tag=sr.have_food] slot.hotbar 3 keep minecraft:snowball 1 667
# #(连锁)#[4]
tag @a[hasitem={location=slot.hotbar,item=minecraft:snowball,slot=3,data=667},tag=sr.have_food] add sr.food_eat
execute as @a[tag=sr.food_eat] run tellraw @a[tag=sr.rpg_bot] {"rawtext":[{"text":"sr.food_eat"},{"selector":"@s"}]}
clear @a[tag=sr.food_eat] snowball 667 1
execute as @a[tag=sr.food_eat] at @s run particle minecraft:heart_particle ~~1~
tag @a[tag=sr.food_eat] remove sr.have_food
tag @a remove sr.food_eat
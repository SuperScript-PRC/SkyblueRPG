# {"初始方向1": "z+", "初始方向2": "x+", "最大延伸": "100"}
# #(循环)#{5}
replaceitem entity @a[scores={sr:food_model=1..,sr:food_count=1..}] slot.hotbar 3 keep minecraft:snowball 1 667
# #(连锁)
tag @a[hasitem={location=slot.hotbar,item=minecraft:snowball,slot=3,data=667},scores={sr:food_count=1..}] add sr.food_eat
setblock ~~~1 minecraft:chain_command_block 3
say inited!
# 1=面包
# 2=苹果
# 5=烤鸡
# 6=烤牛排
# 7=干海带
# 8=烤兔肉
# 9=烤鱼
replaceitem entity @a[tag=sr.food_eat,scores={sr:food_model=1}] slot.hotbar 3 minecraft:bread 1 0 {"item_lock":{"mode": "lock_in_slot"}}
replaceitem entity @a[tag=sr.food_eat,scores={sr:food_model=1}] slot.hotbar 3 minecraft:apple 1 0 {"item_lock":{"mode": "lock_in_slot"}}
replaceitem entity @a[tag=sr.food_eat,scores={sr:food_model=5}] slot.hotbar 3 minecraft:cooked_chicken 1 0 {"item_lock":{"mode": "lock_in_slot"}}
replaceitem entity @a[tag=sr.food_eat,scores={sr:food_model=6}] slot.hotbar 3 minecraft:cooked_beef 1 0 {"item_lock":{"mode": "lock_in_slot"}}
replaceitem entity @a[tag=sr.food_eat,scores={sr:food_model=7}] slot.hotbar 3 dried_kelp 1 0 {"item_lock":{"mode": "lock_in_slot"}}
replaceitem entity @a[tag=sr.food_eat,scores={sr:food_model=8}] slot.hotbar 3 minecraft:cooked_rabbit 1 0 {"item_lock":{"mode": "lock_in_slot"}}
replaceitem entity @a[tag=sr.food_eat,scores={sr:food_model=9}] slot.hotbar 3 minecraft:cooked_fish 1 0 {"item_lock":{"mode": "lock_in_slot"}}
execute as @a[tag=sr.food_eat,scores={sr:food_model=1..}] run tellraw @a[tag=sr.rpg_bot] {"rawtext":[{"text":"sr.food_eat"},{"selector":"@s"}]}
scoreboard players remove @a[tag=sr.food_eat,scores={sr:food_model=1..}] sr:food_count 1
execute as @a[tag=sr.food_eat,scores={sr:food_model=1..}] run particle minecraft:heart_particle ~~~
tag @a remove sr.food_eat
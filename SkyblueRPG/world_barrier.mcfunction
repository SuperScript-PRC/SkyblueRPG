# {"初始方向1": "z+", "初始方向2": "x+", "最大延伸": "100"}
# #(循环)#{40}
execute as @a[tag=!op,m=!1] at @s unless block ~ -63 ~ minecraft:emerald_block run kill
# #(连锁)
execute as @a[tag=!op,m=!1] at @s unless block ~ -63 ~ minecraft:emerald_block run title @s title §c前方区域未解锁
execute as @a[tag=!op,m=!1] at @s unless block ~ -63 ~ minecraft:emerald_block run title @s subtitle §c以后再来探索吧
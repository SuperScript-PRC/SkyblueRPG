# {"初始方向1": "y-", "初始方向2": "x+", "最大延伸": "100"}
# #(脉冲)$1
clear @p minecraft:hay_block 0 1
# #(连锁)#[5]
clone ~1~~ ~1~~ ~1~-1~
setblock ~1~~ air 0 destroy
kill @e[name=箱子,type=item,r=3]
tp @r[type=item,r=3] ~~5~
kill @e[type=item,r=4]
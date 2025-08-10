scoreboard players set @a itemtri 0
execute @a[hasitem={location=slot.weapon.mainhand,item=minecraft:emerald,data=667}] ~~~ scoreboard players set @s itemtri 1
execute @a[score={itemtri=1,itemtri2!=1}] ~~~ tellraw @a[tag=robot] {"rawtext":[{"text":"itemtri.evt"},{"selector":"@s"},{"score":{"name":"@s","objective":"itemtri"}}]}
execute @a[score={itemtri=1,itemtri2!=1}] ~~~ scoreboard players set @s itemtri2 1
execute @a[hasitem={location=slot.weapon.mainhand,item=minecraft:emerald,data=667}] ~~~ scoreboard players set @s itemtri 1
execute @a[score={itemtri=1,itemtri2!=1}] ~~~ tellraw @a[tag=robot] {"rawtext":[{"text":"itemtri.evt"},{"selector":"@s"},{"score":{"name":"@s","objective":"itemtri"}}]}
execute @a[score={itemtri=1,itemtri2!=1}] ~~~ scoreboard players set @s itemtri2 1
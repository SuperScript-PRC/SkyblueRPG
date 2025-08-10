execute @a[ry=-5] ~~~ tellraw @a[tag=robot] {"rawtext":[{"text":"headmove.left"},{"selector":"@s"}]}
execute @a[ry=-5] ~~~ tp ~~~ 0 0
execute @a[rym=5] ~~~ tellraw @a[tag=robot] {"rawtext":[{"text":"headmove.right"},{"selector":"@s"}]}
execute @a[rym=5] ~~~ tp ~~~ 0 0

playsound portal.trigger @s
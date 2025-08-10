# if False:
#     DETECT_HEAD = [
#         (
#             'execute as @a[tag=bagdetect,ry=-5] at @s run tellraw @a[tag=robot] {"rawtext":[{"text":"headmove.left"},{"selector":"@s"}]}',
#             1,
#             0,
#         ),
#         ("execute as @a[tag=bagdetect,ry=-5] at @s run tp ~~~ ~+4 0", 2, 1),
#         (
#             'execute as @a[tag=bagdetect,rym=5] at @s run tellraw @a[tag=robot] {"rawtext":[{"text":"headmove.right"},{"selector":"@s"}]}',
#             2,
#             0,
#         ),
#         ("execute as @a[tag=bagdetect,rym=5] at @s run tp ~~~ ~-4 0", 2, 1),
#         (
#             'execute as @a[tag=bagdetect,rxm=5] at @s run tellraw @a[tag=robot] {"rawtext":[{"text":"headmove.down"},{"selector":"@s"}]}',
#             2,
#             0,
#         ),
#         ("execute as @a[tag=bagdetect,rxm=5] at @s run tp ~~~ 0 ~-4", 2, 1),
#         (
#             'execute as @a[tag=bagdetect,rx=-5] at @s run tellraw @a[tag=robot] {"rawtext":[{"text":"headmove.up"},{"selector":"@s"}]}',
#             2,
#             0,
#         ),
#         ("execute as @a[tag=bagdetect,rx=-5] at @s run tp ~~~ 0 ~+4", 2, 1),
#     ]
DETECT_HEAD = [
    r'execute as @a[tag=bagdetect,ry=-40] at @s run tellraw @a[tag=robot] {"rawtext":[{"text":"headmove.left"},{"selector":"@s"},{"text":"1"}]}',
    r'execute as @a[tag=bagdetect,ry=-30] at @s run tellraw @a[tag=robot] {"rawtext":[{"text":"headmove.left"},{"selector":"@s"},{"text":"1"}]}',
    r'execute as @a[tag=bagdetect,ry=-20] at @s run tellraw @a[tag=robot] {"rawtext":[{"text":"headmove.left"},{"selector":"@s"},{"text":"1"}]}',
    #
    r'execute as @a[tag=bagdetect,rym=40] at @s run tellraw @a[tag=robot] {"rawtext":[{"text":"headmove.right"},{"selector":"@s"},{"text":"1"}]}',
    r'execute as @a[tag=bagdetect,rym=30] at @s run tellraw @a[tag=robot] {"rawtext":[{"text":"headmove.right"},{"selector":"@s"},{"text":"1"}]}',
    r'execute as @a[tag=bagdetect,rym=20] at @s run tellraw @a[tag=robot] {"rawtext":[{"text":"headmove.right"},{"selector":"@s"},{"text":"1"}]}',
    #
    r"execute as @a[tag=bagdetect,ry=-20] at @s run tp ~~~ 0 0",
    r"execute as @a[tag=bagdetect,rym=20] at @s run tp ~~~ 0 0",
    #
    r'execute as @a[tag=bagdetect,rxm=40] at @s run tellraw @a[tag=robot] {"rawtext":[{"text":"headmove.down"},{"selector":"@s"},{"text":"3"}]}',
    r'execute as @a[tag=bagdetect,rxm=30] at @s run tellraw @a[tag=robot] {"rawtext":[{"text":"headmove.down"},{"selector":"@s"},{"text":"2"}]}',
    r'execute as @a[tag=bagdetect,rxm=20] at @s run tellraw @a[tag=robot] {"rawtext":[{"text":"headmove.down"},{"selector":"@s"},{"text":"1"}]}',
    #
    r'execute as @a[tag=bagdetect,rx=-40] at @s run tellraw @a[tag=robot] {"rawtext":[{"text":"headmove.up"},{"selector":"@s"},{"text":"3"}]}',
    r'execute as @a[tag=bagdetect,rx=-30] at @s run tellraw @a[tag=robot] {"rawtext":[{"text":"headmove.up"},{"selector":"@s"},{"text":"2"}]}',
    r'execute as @a[tag=bagdetect,rx=-20] at @s run tellraw @a[tag=robot] {"rawtext":[{"text":"headmove.up"},{"selector":"@s"},{"text":"1"}]}',
    #
    r"execute as @a[tag=bagdetect,rx=-20] at @s run tp ~~~ 0 0",
    r"execute as @a[tag=bagdetect,rxm=20] at @s run tp ~~~ 0 0",
]

from enum import Enum     # for enum34, or the stdlib version
# from aenum import Enum  # for the aenum version
Direction = Enum('Direction', 'down rightDown right rightUp up')

def get_head_indexes(direction: Direction) -> list[int]:
    if direction == Direction.down:
        return [0]
    elif direction == Direction.rightDown:
        return [1]
    elif direction == Direction.right:
        return [2]
    elif direction == Direction.rightUp:
        return [3]
    elif direction == Direction.up:
        return [4]

def get_leg_indexes(direction: Direction, animation: str) -> list[int]:
    if animation == 'idle':
        if direction == Direction.down:
            return [0]
        elif direction == Direction.rightDown:
            return [1]
        elif direction == Direction.right:
            return [2]
        elif direction == Direction.up:
            return [3]
    elif animation == 'walk':
        if direction == Direction.down:
            return [5, 6, 7, 8]
        elif direction == Direction.rightDown:
            return [9, 10, 11, 12]
        elif direction == Direction.right:
            return [13, 14, 15, 16]
        elif direction == Direction.rightUp:
            return [17, 18, 19, 20]
        elif direction == Direction.up:
            return [21, 22, 23, 24]
    elif animation == 'crouch':
        if direction == Direction.down or direction == Direction.rightDown or direction == Direction.right:
            return [67]
        else:
            return [68]
    elif animation == 'crawl':
        if direction == Direction.down:
            return [27, 28, 29, 30]
        elif direction == Direction.rightDown:
            return [31, 32, 33, 34]
        elif direction == Direction.right:
            return [35, 36, 37, 38]
        elif direction == Direction.rightUp:
            return [39, 40, 41, 42]
        elif direction == Direction.up:
            return [43, 44, 45, 46]
    elif animation == 'run':
        if direction == Direction.down:
            return [47, 48, 49, 50]
        elif direction == Direction.rightDown:
            return [51, 52, 53, 54]
        elif direction == Direction.right:
            return [55, 56, 57, 58]
        elif direction == Direction.rightUp:
            return [59, 60, 61, 62]
        elif direction == Direction.up:
            return [63, 64, 65, 66]
    elif animation == 'climb':
        return [69, 70, 71, 72]
    elif animation == 'jump':
        if direction == Direction.down:
            return [73]
        elif direction == Direction.rightDown:
            return [74]
        elif direction == Direction.right:
            return [75]
        elif direction == Direction.rightUp:
            return [76]
        elif direction == Direction.up:
            return [77]
    elif animation == 'dead':
        if direction == Direction.down:
            return [88]
        elif direction == Direction.rightDown:
            return [89]
        elif direction == Direction.right:
            return [90]
        elif direction == Direction.rightUp:
            return [91]
        elif direction == Direction.up:
            return [92]
    elif animation == 'keelOver':
        return [93]
    
def get_unarmed_indexes(direction: Direction, animation: str) -> list[int]:
    if animation == 'idle':
        if direction == Direction.down:
            return [0]
        elif direction == Direction.rightDown:
            return [1]
        elif direction == Direction.right:
            return [2]
        elif direction == Direction.rightUp:
            return [3]
        elif direction == Direction.up:
            return [4]
    elif animation == 'walk':
        if direction == Direction.down:
            return [5, 6, 7, 8]
        elif direction == Direction.rightDown:
            return [9, 10, 11, 12]
        elif direction == Direction.right:
            return [13, 14, 15, 16]
        elif direction == Direction.rightUp:
            return [17, 18, 19, 20]
        elif direction == Direction.up:
            return [21, 22, 23, 24]
    elif animation == 'crouch':
        if direction == Direction.down or direction == Direction.rightDown or direction == Direction.right:
            return [67]
        else:
            return [68]
    elif animation == 'crawl':
        if direction == Direction.down:
            return [27, 28, 29, 30]
        elif direction == Direction.rightDown:
            return [31, 32, 33, 34]
        elif direction == Direction.right:
            return [35, 36, 37, 38]
        elif direction == Direction.rightUp:
            return [39, 40, 41, 42]
        elif direction == Direction.up:
            return [43, 44, 45, 46]
    elif animation == 'run':
        if direction == Direction.down:
            return [47, 48, 49, 50]
        elif direction == Direction.rightDown:
            return [51, 52, 53, 54]
        elif direction == Direction.right:
            return [55, 56, 57, 58]
        elif direction == Direction.rightUp:
            return [59, 60, 61, 62]
        elif direction == Direction.up:
            return [63, 64, 65, 66]
    elif animation == 'climb':
        return [69, 70, 71, 72]
    elif animation == 'jump':
        if direction == Direction.down:
            return [73]
        elif direction == Direction.rightDown:
            return [74]
        elif direction == Direction.right:
            return [75]
        elif direction == Direction.rightUp:
            return [76]
        elif direction == Direction.up:
            return [77]
    elif animation == 'dead':
        if direction == Direction.down:
            return [88]
        elif direction == Direction.rightDown:
            return [89]
        elif direction == Direction.right:
            return [90]
        elif direction == Direction.rightUp:
            return [91]
        elif direction == Direction.up:
            return [92]
    elif animation == 'keelOver':
        return [93]
    elif animation == 'use':
        if direction == Direction.down:
            return [78]
        elif direction == Direction.rightDown:
            return [79]
        elif direction == Direction.right:
            return [80]
        elif direction == Direction.rightUp:
            return [81]
        elif direction == Direction.up:
            return [82]
    elif animation == 'handsUp':
        if direction == Direction.down:
            return [83]
        elif direction == Direction.rightDown:
            return [84]
        elif direction == Direction.right:
            return [85]
        elif direction == Direction.rightUp:
            return [86]
        elif direction == Direction.up:
            return [87]
    elif animation == 'keelOver':
        return [93]

def get_pistol_indexes(direction: Direction, animation: str) -> list[int]:
    if animation == 'idle':
        if direction == Direction.down:
            return [0]
        elif direction == Direction.rightDown:
            return [3]
        elif direction == Direction.right:
            return [6]
        elif direction == Direction.rightUp:
            return [9]
        elif direction == Direction.up:
            return [12]
    elif animation == 'shoot':
        if direction == Direction.down:
            return [1, 2]
        elif direction == Direction.rightDown:
            return [4, 5]
        elif direction == Direction.right:
            return [7, 8]
        elif direction == Direction.rightUp:
            return [10, 11]
        elif direction == Direction.up:
            return [13, 14]
    elif animation == 'reload':
        if direction == Direction.down:
            return [15, 16, 17, 18, 19, 20]
        elif direction == Direction.rightDown:
            return [24, 25, 26, 27, 28, 29]
        elif direction == Direction.right:
            return [33, 34, 35, 36, 37, 38]
        elif direction == Direction.rightUp:
            return [42, 43, 44, 45, 46, 47]
        elif direction == Direction.up:
            return [51, 52, 53]
    elif animation == 'rack':
        if direction == Direction.down:
            return [21, 22, 23, 22]
        elif direction == Direction.rightDown:
            return [30, 31, 32, 31]
        elif direction == Direction.right:
            return [39, 40, 41, 40]
        elif direction == Direction.rightUp:
            return [48, 49, 50, 49]
        elif direction == Direction.up:
            return [53]
    elif animation == 'run':
        if direction == Direction.down:
            return [54, 55, 56, 57]
        elif direction == Direction.rightDown:
            return [58, 59, 60, 61]
        elif direction == Direction.right:
            return [62, 63, 64, 65]
        elif direction == Direction.rightUp:
            return [66, 67, 68, 69]
        elif direction == Direction.up:
            return [70, 71, 72, 73]

def get_smg_indexes(direction: Direction, animation: str) -> list[int]:
    if animation == 'idle':
        if direction == Direction.down:
            return [0]
        elif direction == Direction.rightDown:
            return [3]
        elif direction == Direction.right:
            return [6]
        elif direction == Direction.rightUp:
            return [9]
        elif direction == Direction.up:
            return [12]
    elif animation == 'shoot':
        if direction == Direction.down:
            return [1, 2]
        elif direction == Direction.rightDown:
            return [4, 5]
        elif direction == Direction.right:
            return [7, 8]
        elif direction == Direction.rightUp:
            return [10, 11]
        elif direction == Direction.up:
            return [13]
    elif animation == 'reload':
        if direction == Direction.down:
            return [14, 15, 16, 17, 18, 19]
        elif direction == Direction.rightDown:
            return [22, 23, 24, 25, 26, 27]
        elif direction == Direction.right:
            return [30, 31, 32, 33, 34, 35]
        elif direction == Direction.rightUp:
            return [38, 39, 40, 41, 42, 43]
        elif direction == Direction.up:
            return [46, 47, 48, 49, 49, 49]
    elif animation == 'rack':
        if direction == Direction.down:
            return [19, 20, 21, 20]
        elif direction == Direction.rightDown:
            return [27, 28, 29, 28]
        elif direction == Direction.right:
            return [35, 36, 37, 36]
        elif direction == Direction.rightUp:
            return [43, 44, 45, 44]
        elif direction == Direction.up:
            return [49]
    elif animation == 'run':
        if direction == Direction.down:
            return [50, 51, 52, 53]
        elif direction == Direction.rightDown:
            return [54, 55, 56, 57]
        elif direction == Direction.right:
            return [58, 59, 60, 61]
        elif direction == Direction.rightUp:
            return [62, 63, 64, 65]
        elif direction == Direction.up:
            return [66, 67, 68, 69]
        
def get_shotgun_indexes(direction: Direction, animation: str) -> list[int]:
    if animation == 'idle':
        if direction == Direction.down:
            return [0]
        elif direction == Direction.rightDown:
            return [5]
        elif direction == Direction.right:
            return [10]
        elif direction == Direction.rightUp:
            return [14]
        elif direction == Direction.up:
            return [18]
    elif animation == 'shoot':
        if direction == Direction.down:
            return [1, 2]
        elif direction == Direction.rightDown:
            return [6, 7]
        elif direction == Direction.right:
            return [11, 12]
        elif direction == Direction.rightUp:
            return [15, 16]
        elif direction == Direction.up:
            return [19]
    elif animation == 'rack':
        if direction == Direction.down:
            return [3, 4, 3]
        elif direction == Direction.rightDown:
            return [8, 9, 8]
        elif direction == Direction.right:
            return [11, 13, 11]
        elif direction == Direction.rightUp:
            return [15, 17, 15]
        elif direction == Direction.up:
            return [19]
    elif animation == 'reload':
        if direction == Direction.down:
            return [20, 21, 22, 23, 24, 25]
        elif direction == Direction.rightDown:
            return [26, 27, 28, 29, 30, 31]
        elif direction == Direction.right:
            return [32, 33, 34, 35, 36, 37]
        elif direction == Direction.rightUp:
            return [38, 39, 40, 41, 42, 43]
        elif direction == Direction.up:
            return [44, 45, 46, 47, 48, 49]
    elif animation == 'run': 
        return get_smg_indexes(direction, 'run')

def get_rifle_indexes(direction: Direction, animation: str) -> list[int]:
    if animation == 'idle':
        if direction == Direction.down:
            return [0]
        elif direction == Direction.rightDown:
            return [3]
        elif direction == Direction.right:
            return [6]
        elif direction == Direction.rightUp:
            return [9]
        elif direction == Direction.up:
            return [12]
    elif animation == 'shoot':
        if direction == Direction.down:
            return [1, 2]
        elif direction == Direction.rightDown:
            return [4, 5]
        elif direction == Direction.right:
            return [7, 8]
        elif direction == Direction.rightUp:
            return [10, 11]
        elif direction == Direction.up:
            return [13, 13]
    elif animation == 'reload':
        if direction == Direction.down:
            return [14, 15, 16, 17, 18, 19]
        elif direction == Direction.rightDown:
            return [22, 23, 24, 25, 26, 27]
        elif direction == Direction.right:
            return [30, 31, 32, 33, 34, 35]
        elif direction == Direction.rightUp:
            return [38, 39, 40, 41, 42, 43]
        elif direction == Direction.up:
            return [46, 47, 48, 49, 49, 49]
    elif animation == 'rack':
        if direction == Direction.down:
            return [19, 20, 21, 20]
        elif direction == Direction.rightDown:
            return [27, 28, 29, 28]
        elif direction == Direction.right:
            return [35, 36, 37, 36]
        elif direction == Direction.rightUp:
            return [43, 44, 45, 44]
        elif direction == Direction.up:
            return [49]
    elif animation == 'run':
        return get_smg_indexes(direction, 'run')

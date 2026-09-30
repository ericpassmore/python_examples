

def isPalendrom(x: int) -> bool:
    stringify_num = str(x)
    if stringify_num[0] != stringify_num[-1]:
        return False
    if stringify_num == stringify_num[::-1]:
        return True
    return False

assert(isPalendrom(121)), f'expected True returned {isPalendrom(121)}'
assert(not isPalendrom(-121)), f'expected False returned {isPalendrom(-121)}'



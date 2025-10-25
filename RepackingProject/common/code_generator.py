import itertools
import random

sequence = list(itertools.product("1234567890", repeat=5))


def generate_code():
    i = random.randint(0, 99999)
    return "".join(sequence[i])

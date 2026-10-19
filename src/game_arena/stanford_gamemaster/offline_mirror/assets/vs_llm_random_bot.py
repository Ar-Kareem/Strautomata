import random


def policy(state, role, legal_moves):
    if not legal_moves:
        raise RuntimeError("random bot requires at least one legal move")
    return random.choice(list(legal_moves))


import functools

@functools.lru_cache(maxsize=None)
def is_losing(state: tuple[int, int, int, int]) -> bool:
    if state == (0, 0, 0, 0):
        return True
    has_win_move = False
    for i in range(4):
        for take in range(1, state[i] + 1):
            new_state_list = list(state)
            new_state_list[i] -= take
            if sum(new_state_list) > 0:
                new_state = tuple(new_state_list)
                if is_losing(new_state):
                    has_win_move = True
                    break
        if has_win_move:
            break
    return not has_win_move

def policy(piles: list[int]) -> str:
    best_move = None
    for i in range(4):
        for take in range(1, piles[i] + 1):
            new_state_list = list(piles)
            new_state_list[i] -= take
            new_state = tuple(new_state_list)
            if sum(new_state_list) > 0 and is_losing(new_state):
                best_move = f"{i},{take}"
                break
        if best_move:
            break
    if best_move:
        return best_move
    # If no best move, choose any legal move
    for i in range(4):
        for take in range(1, piles[i] + 1):
            new_state_list = list(piles)
            new_state_list[i] -= take
            if sum(new_state_list) > 0:
                return f"{i},{take}"

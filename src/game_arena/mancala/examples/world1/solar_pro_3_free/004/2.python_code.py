
from functools import lru_cache
import math

BOARD_SIZE = 14          # 6 your pits + 1 your store + 6 opponent pits + 1 opponent store
MAX_DEPTH = 5            # depth‑limited minimax (5 plies)

def apply_move(board: tuple[int, ...], side: int, move: int) -> tuple[list[int], bool]:
    """
    Perform a single sowing move from `move` (legal house index) for `side`.
    side == 0 → you are moving (you store = index 6)
    side == 1 → opponent is moving (opponent store = index 13)

    Returns the resulting board (list) and a flag indicating if the mover
    gets an extra move (last seed landed in his own store).
    """
    board_list = list(board)           # mutable copy
    original = board_list.copy()       # keep pre‑sowing configuration for capture
    seeds = original[move]              # number of seeds to sow
    board_list[move] = 0                # empty the source house

    new_board = board_list.copy()
    store_idx = 6 if side == 0 else 13  # store position for the player who sows

    # Sow seeds step by step
    last_pos = -1
    for step in range(seeds):
        pos = (move + step + 1) % BOARD_SIZE
        last_pos = pos
        if pos == store_idx:          # land in own store
            new_board[store_idx] += 1
        elif (side == 0 and pos == 13) or (side == 1 and pos == 6):
            # Skip opponent store when it is reached
            continue
        else:
            # Put a seed in a house
            if pos <= 5:
                new_board[pos] += 1
            else:                     # opponent's houses 7‑12
                new_board[pos] += 1

    extra_move = last_pos == store_idx

    # Capture handling (only possible if the last seed lands in a house)
    if side == 0 and 0 <= last_pos <= 5:
        opp_house_global = 7 + (5 - last_pos)        # opponent opposite pit
        if original[last_pos] == 0 and original[opp_house_global] > 0:
            captured = original[opp_house_global] + 1
            new_board[6] += captured
            new_board[last_pos] = 0
            new_board[opp_house_global] = 0
    elif side == 1 and 7 <= last_pos <= 12:
        opp_idx_local = last_pos - 7                  # 0‑5 on opponent side
        you_opposite_global = 5 - opp_idx_local        # your opposite pit
        if original[last_pos] == 0 and original[you_opposite_global] > 0:
            captured = original[you_opposite_global] + 1
            new_board[13] += captured
            new_board[last_pos] = 0
            new_board[you_opposite_global] = 0

    return new_board, extra_move


def evaluate(state: tuple[int, ...]) -> int:
    """
    Static evaluation: heavily favour seeds in your own store,
    then favour more seeds in your houses vs opponent’s.
    """
    you = state[:7]               # indices 0‑5 = your houses, 6 = your store
    opponent = state[7:]           # 7‑12 = opponent houses, 13 = opponent store
    store_diff = you[6] - opponent[13]
    house_diff = sum(you[:6]) - sum(opponent[:6])
    # weight store advantage ten times more than house advantage
    return store_diff * 10 + house_diff


@lru_cache(maxsize=None)
def search(state: tuple[int, ...], depth: int, side: int) -> tuple[int, int]:
    """
    α‑β minimax search with depth limit.
    Returns (score, best_move) for the given state.
    """
    # Base case – no plies left → return heuristic score
    if depth == 0 or depth < 0:
        return evaluate(state), None

    # Determine legal moves for the current player
    if side == 0:  # you to move
        moves = [i for i, v in enumerate(state[:6]) if v > 0]
    else:          # opponent to move
        moves = [i for i, v in enumerate(state[7:13]) if v > 0]

    alpha = -math.inf
    beta  =  math.inf
    best_score = -math.inf
    best_move = None

    for move in moves:
        new_board, extra = apply_move(state, side, move)
        new_state = tuple(new_board)

        # Determine who moves next
        if side == 0 and extra:
            next_side = 0          # you get another turn
        elif side == 1 and extra:
            next_side = 1          # opponent gets another turn
        else:
            next_side = 1 - side   # turn switches

        child_score, _ = search(new_state, depth - 1, next_side)

        if side == 0:  # maximizing (you)
            if child_score > best_score:
                best_score = child_score
                best_move = move
            if child_score > alpha:
                alpha = child_score
            if alpha >= beta:
                break
        else:          # minimizing (opponent)
            if child_score < best_score:
                best_score = child_score
                best_move = move
            if child_score < beta:
                beta = child_score
            if beta <= alpha:
                break

    return best_score, best_move


def policy(you: list[int], opponent: list[int]) -> int:
    """
    Required API – chooses the next legal move for the current player.
    Always returns an integer i (0‑5) with you[i] > 0.
    """
    board = tuple(you + opponent)
    score, move = search(board, MAX_DEPTH, side=0)
    # `move` is guaranteed to be legal because `search` only iterates over
    # non‑empty houses.
    return move


import time
from typing import List

# ----------------------------------------------------------------------
# Helper: custom exception for timeout
# ----------------------------------------------------------------------
class TimeOut(Exception):
    pass

# ----------------------------------------------------------------------
# Apply a move for the current player.
# `you` : current player's pits (len 7: houses 0-5, store 6)
# `opp` : opponent's pits
# returns (new_you, new_opp, extra_turn)
# ----------------------------------------------------------------------
def apply_move(you: List[int], opp: List[int], move: int):
    # build the 13-pit cycle: your houses (0-5), your store (6), opp houses (7-12)
    board = you[:6] + [you[6]] + opp[:6]
    seeds = board[move]
    board[move] = 0
    idx = move
    for _ in range(seeds):
        idx = (idx + 1) % 13
        board[idx] += 1

    extra = (idx == 6)
    # capture?
    if 0 <= idx <= 5 and board[idx] == 1:
        opp_idx = 12 - idx
        if board[opp_idx] > 0:
            board[6] += board[idx] + board[opp_idx]
            board[idx] = 0
            board[opp_idx] = 0

    new_you = board[0:7]
    new_opp = opp[:]               # keep opponent's store
    new_opp[:6] = board[7:13]

    # game over? then no extra turn
    if sum(new_you[:6]) == 0 or sum(new_opp[:6]) == 0:
        extra = False

    return new_you, new_opp, extra

# ----------------------------------------------------------------------
# Terminal evaluation – final store counts after adding remaining seeds.
# ----------------------------------------------------------------------
def evaluate_terminal(ai_you: List[int], ai_opp: List[int]) -> float:
    ai_houses = sum(ai_you[:6])
    opp_houses = sum(ai_opp[:6])
    if ai_houses == 0:
        ai_score = ai_you[6]
        opp_score = ai_opp[6] + opp_houses
    else:  # opp_houses == 0
        ai_score = ai_you[6] + ai_houses
        opp_score = ai_opp[6]

    diff = ai_score - opp_score
    if diff > 0: return 10000
    if diff < 0: return -10000
    return 0

# ----------------------------------------------------------------------
# Heuristic for non-terminal states.
# ----------------------------------------------------------------------
def heuristic(ai_you: List[int], ai_opp: List[int]) -> float:
    my_store = ai_you[6]
    opp_store = ai_opp[6]
    my_houses = sum(ai_you[:6])
    opp_houses = sum(ai_opp[:6])
    my_moves = sum(1 for x in ai_you[:6] if x > 0)
    opp_moves = sum(1 for x in ai_opp[:6] if x > 0)

    # store diff is most important, then total seeds, then mobility
    return (my_store - opp_store) * 2.0 + (my_houses - opp_houses) + 0.5 * (my_moves - opp_moves)

# ----------------------------------------------------------------------
# Check if state is terminal (current player has no moves or opponent has none)
# ----------------------------------------------------------------------
def is_terminal(you: List[int], opp: List[int]) -> bool:
    return sum(you[:6]) == 0 or sum(opp[:6]) == 0

# ----------------------------------------------------------------------
# Order moves: extra turn first, then capture, then others.
# ----------------------------------------------------------------------
def order_moves(you: List[int], opp: List[int], moves: List[int]):
    scored = []
    for m in moves:
        seeds = you[m]
        last = (m + seeds) % 13
        extra = (last == 6)
        capture = False
        if not extra and 0 <= last <= 5:
            if you[last] == 0 and opp[5 - last] > 0:
                capture = True
        score = 2 if extra else (1 if capture else 0)
        scored.append((m, score))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored

# ----------------------------------------------------------------------
# Alpha‑beta search.
# `you` is the current player's state, `opp` is the opponent's.
# `maximizing` = True  -> current player is AI
# `maximizing` = False -> current player is opponent
# ----------------------------------------------------------------------
def alphabeta(you: List[int], opp: List[int], depth: int,
              alpha: float, beta: float, maximizing: bool,
              start_time: float, time_limit: float) -> float:

    if time.time() - start_time > time_limit:
        raise TimeOut()

    # Terminal?
    if is_terminal(you, opp):
        if maximizing:
            return evaluate_terminal(you, opp)
        else:
            return evaluate_terminal(opp, you)

    if depth == 0:
        if maximizing:
            return heuristic(you, opp)
        else:
            return heuristic(opp, you)

    legal = [i for i in range(6) if you[i] > 0]
    ordered = order_moves(you, opp, legal)

    if maximizing:
        value = -float('inf')
        for move, _ in ordered:
            new_you, new_opp, extra = apply_move(you, opp, move)
            if extra:
                val = alphabeta(new_you, new_opp, depth - 1,
                                alpha, beta, True, start_time, time_limit)
            else:
                if is_terminal(new_you, new_opp):
                    val = evaluate_terminal(new_you, new_opp)
                else:
                    val = alphabeta(new_opp, new_you, depth - 1,
                                    alpha, beta, False, start_time, time_limit)
            if val > value:
                value = val
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value
    else:
        value = float('inf')
        for move, _ in ordered:
            new_you, new_opp, extra = apply_move(you, opp, move)
            if extra:
                val = alphabeta(new_you, new_opp, depth - 1,
                                alpha, beta, False, start_time, time_limit)
            else:
                if is_terminal(new_you, new_opp):
                    val = evaluate_terminal(new_opp, new_you)
                else:
                    val = alphabeta(new_opp, new_you, depth - 1,
                                    alpha, beta, True, start_time, time_limit)
            if val < value:
                value = val
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value

# ----------------------------------------------------------------------
# Root search: iterative deepening over the AI's root moves.
# ----------------------------------------------------------------------
def root_alphabeta(you: List[int], opp: List[int], depth: int,
                   start_time: float, time_limit: float):
    legal = [i for i in range(6) if you[i] > 0]
    ordered = order_moves(you, opp, legal)
    best_move = ordered[0][0]
    alpha = -float('inf')
    beta = float('inf')

    for move, _ in ordered:
        if time.time() - start_time > time_limit:
            raise TimeOut()
        new_you, new_opp, extra = apply_move(you, opp, move)
        if extra:
            val = alphabeta(new_you, new_opp, depth - 1,
                            alpha, beta, True, start_time, time_limit)
        else:
            if is_terminal(new_you, new_opp):
                val = evaluate_terminal(new_you, new_opp)
            else:
                val = alphabeta(new_opp, new_you, depth - 1,
                                alpha, beta, False, start_time, time_limit)
        if val > alpha:
            alpha = val
            best_move = move

    return alpha, best_move

# ----------------------------------------------------------------------
# Main policy function – called by the arena.
# ----------------------------------------------------------------------
def policy(you: List[int], opponent: List[int]) -> int:
    start = time.time()
    limit = 0.95  # seconds, leaves a small margin

    legal = [i for i in range(6) if you[i] > 0]
    if not legal:
        return -1   # should never be called without a move

    best_move = legal[0]
    depth = 1

    while True:
        try:
            _, move = root_alphabeta(you, opponent, depth, start, limit)
            best_move = move
            depth += 1
        except TimeOut:
            break

    return best_move

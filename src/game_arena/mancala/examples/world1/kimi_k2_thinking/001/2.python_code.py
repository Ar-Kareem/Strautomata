
import random
from typing import List, Tuple

# ----------------------------------------------------------------------
# Helpers for board manipulation
# ----------------------------------------------------------------------
def sow(you: List[int], opponent: List[int], move: int) -> Tuple[List[int], List[int], bool]:
    """
    Perform a move (0‑5) on a Kalah board.
    Returns (new_you, new_opponent, extra_move).
    """
    assert 0 <= move <= 5 and you[move] > 0
    # Copy board
    y = you[:]
    o = opponent[:]
    seeds = y[move]
    y[move] = 0
    pos = move
    extra = False

    # Distribute seeds
    while seeds:
        pos += 1
        if pos == 13:  # skip opponent's store
            pos = 0
        if pos == 6:  # your store
            y[pos] += 1
            seeds -= 1
            if seeds == 0:
                extra = True  # last seed in your store → extra move
        elif pos < 6:  # your houses
            y[pos] += 1
            seeds -= 1
            if seeds == 0 and y[pos] == 1:  # capture
                opposite = 5 - pos
                if o[opposite] > 0:
                    y[6] += 1 + o[opposite]
                    y[pos] = 0
                    o[opposite] = 0
        else:  # opponent's houses (pos 7‑12 map to o[0‑5])
            o[pos - 7] += 1
            seeds -= 1

    # Check for end-of-game sweep
    if all(h == 0 for h in y[:6]):
        # opponent sweeps their side
        o[6] += sum(o[:6])
        o[:6] = [0] * 6
    elif all(h == 0 for h in o[:6]):
        # you sweep your side
        y[6] += sum(y[:6])
        y[:6] = [0] * 6

    return y, o, extra


def legal_moves(you: List[int]) -> List[int]:
    """Return list of legal move indices (0‑5) for the current player."""
    return [i for i in range(6) if you[i] > 0]


def evaluate(you: List[int], opponent: List[int]) -> float:
    """
    Simple evaluation: store difference + small bonus for seeds in houses.
    """
    store_diff = you[6] - opponent[6]
    seed_diff = (sum(you[:6]) - sum(opponent[:6])) * 0.1
    return store_diff + seed_diff


def is_terminal(you: List[int], opponent: List[int]) -> bool:
    """Return True if the game has ended (one side has no seeds in houses)."""
    return all(h == 0 for h in you[:6]) or all(h == 0 for h in opponent[:6])


def order_moves(you: List[int], opponent: List[int], moves: List[int]) -> List[int]:
    """
    Heuristic ordering: moves that give an extra move first,
    then captures, then higher seed counts.
    """
    scored = []
    for m in moves:
        y, o, extra = sow(you, opponent, m)
        score = 0
        if extra:
            score += 1000
        # capture detection: if last seed lands in an empty house on your side
        # and opposite side has seeds, it's a capture.
        # We approximate by checking if the move results in a gain in your store
        # beyond the normal sow.
        if y[6] > you[6] + 1:  # heuristic: more than just the last seed
            score += 500
        score += you[m]  # prefer moving more seeds
        scored.append((-score, m))
    scored.sort()
    return [m for _, m in scored]


def minimax(you: List[int],
            opponent: List[int],
            depth: int,
            maximizing: bool,
            alpha: float,
            beta: float) -> float:
    """
    Depth‑limited minimax with alpha‑beta pruning.
    Returns the evaluated score of the position.
    """
    if depth == 0 or is_terminal(you, opponent):
        return evaluate(you, opponent)

    moves = legal_moves(you if maximizing else opponent)
    if not moves:  # no legal moves → pass turn (should not happen per rules)
        return minimax(you, opponent, depth - 1, not maximizing, alpha, beta)

    if maximizing:
        max_eval = -float('inf')
        for m in order_moves(you, opponent, moves):
            y, o, extra = sow(you, opponent, m)
            if extra:
                # same player moves again
                eval_ = minimax(y, o, depth, True, alpha, beta)
            else:
                eval_ = minimax(o, y, depth - 1, False, alpha, beta)
            max_eval = max(max_eval, eval_)
            alpha = max(alpha, eval_)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for m in order_moves(opponent, you, moves):
            o, y, extra = sow(opponent, you, m)
            if extra:
                eval_ = minimax(y, o, depth, False, alpha, beta)
            else:
                eval_ = minimax(y, o, depth - 1, True, alpha, beta)
            min_eval = min(min_eval, eval_)
            beta = min(beta, eval_)
            if beta <= alpha:
                break
        return min_eval


def policy(you: List[int], opponent: List[int]) -> int:
    """
    Return a legal move (0‑5) for the current player.
    Performs iterative deepening up to a fixed depth (6‑8) within time constraints.
    """
    # Quick exit if only one move exists
    moves = legal_moves(you)
    if len(moves) == 1:
        return moves[0]

    # Iterative deepening
    best_move = moves[0]
    # Use a fixed depth that stays safe for 1 s on a 3 GHz CPU
    MAX_DEPTH = 7

    for depth in range(1, MAX_DEPTH + 1):
        best_val = -float('inf')
        current_best = best_move
        for m in order_moves(you, opponent, moves):
            y, o, extra = sow(you, opponent, m)
            if extra:
                val = minimax(y, o, depth, True, -float('inf'), float('inf'))
            else:
                val = minimax(o, y, depth - 1, False, -float('inf'), float('inf'))
            if val > best_val:
                best_val = val
                current_best = m
        best_move = current_best

    return best_move


#!/usr/bin/env python3
"""
Othello (Reversi) policy implementation.

API:
    def policy(you: np.ndarray, opponent: np.ndarray) -> str

Returns a legal move string like "d3" or "pass".
"""
import time
import numpy as np
from typing import List, Tuple, Optional

# Directions: 8 neighbors (dr, dc)
DIRS = [(-1, -1), (-1, 0), (-1, 1),
        (0, -1),          (0, 1),
        (1, -1),  (1, 0), (1, 1)]

# Positional weights emphasizing corners and penalizing "X" squares
WEIGHTS = np.array([
    [120, -20,  20,   5,   5,  20, -20, 120],
    [-20, -40,  -5,  -5,  -5,  -5, -40, -20],
    [20,   -5,  15,   3,   3,  15,  -5,  20],
    [5,    -5,   3,   3,   3,   3,  -5,   5],
    [5,    -5,   3,   3,   3,   3,  -5,   5],
    [20,   -5,  15,   3,   3,  15,  -5,  20],
    [-20, -40,  -5,  -5,  -5,  -5, -40, -20],
    [120, -20,  20,   5,   5,  20, -20, 120]
], dtype=float)

# Time budget per move (seconds)
TIME_LIMIT = 0.95  # leave small margin for safety

def in_bounds(r: int, c: int) -> bool:
    return 0 <= r < 8 and 0 <= c < 8

def find_legal_moves(you: np.ndarray, opp: np.ndarray) -> List[Tuple[int,int]]:
    empties = np.where((you == 0) & (opp == 0))
    moves = []
    for r, c in zip(empties[0], empties[1]):
        if is_legal(you, opp, r, c):
            moves.append((r, c))
    return moves

def is_legal(you: np.ndarray, opp: np.ndarray, r: int, c: int) -> bool:
    if you[r, c] or opp[r, c]:
        return False
    for dr, dc in DIRS:
        rr, cc = r + dr, c + dc
        found_opp = False
        while in_bounds(rr, cc) and opp[rr, cc]:
            found_opp = True
            rr += dr; cc += dc
        if found_opp and in_bounds(rr, cc) and you[rr, cc]:
            return True
    return False

def apply_move(you: np.ndarray, opp: np.ndarray, move: Tuple[int,int]) -> Tuple[np.ndarray, np.ndarray]:
    r, c = move
    new_you = you.copy()
    new_opp = opp.copy()
    new_you[r, c] = 1
    for dr, dc in DIRS:
        rr, cc = r + dr, c + dc
        path = []
        while in_bounds(rr, cc) and new_opp[rr, cc]:
            path.append((rr, cc))
            rr += dr; cc += dc
        if path and in_bounds(rr, cc) and new_you[rr, cc]:
            # flip path
            for fr, fc in path:
                new_opp[fr, fc] = 0
                new_you[fr, fc] = 1
    return new_you, new_opp

def evaluate(you: np.ndarray, opp: np.ndarray) -> float:
    # Positional weights
    pos_score = float((WEIGHTS * (you - opp)).sum())

    # Disc difference
    you_discs = you.sum()
    opp_discs = opp.sum()
    disc_diff = you_discs - opp_discs
    if you_discs + opp_discs != 0:
        disk_parity = 100.0 * disc_diff / (you_discs + opp_discs)
    else:
        disk_parity = 0.0

    # Mobility
    my_moves = len(find_legal_moves(you, opp))
    opp_moves = len(find_legal_moves(opp, you))
    if my_moves + opp_moves > 0:
        mobility = 100.0 * (my_moves - opp_moves) / (my_moves + opp_moves)
    else:
        mobility = 0.0

    # Combine heuristics with tuned weights
    score = pos_score * 1.0 + disk_parity * 2.0 + mobility * 8.0
    return score

# Globals for timing control
_start_time = 0.0

def time_left() -> float:
    return TIME_LIMIT - (time.time() - _start_time)

def minimax(you: np.ndarray, opp: np.ndarray, depth: int, alpha: float, beta: float, maximizing: bool) -> Tuple[float, Optional[Tuple[int,int]]]:
    # Time cutoff
    if time_left() <= 0:
        return evaluate(you, opp), None

    my_moves = find_legal_moves(you, opp)
    opp_moves = find_legal_moves(opp, you)

    # Terminal: no moves for both or board full
    if (not my_moves) and (not opp_moves):
        # final score: difference in discs
        final_score = float((you.sum() - opp.sum()) * 1000)
        return final_score, None
    if depth == 0:
        return evaluate(you, opp), None

    if maximizing:
        if not my_moves:
            # pass move: opponent moves next
            val, mv = minimax(opp, you, depth - 1, -beta, -alpha, False)
            # returned val is from opponent perspective, flip sign
            return -val, None
        best_val = -1e9
        best_move = None
        # Move ordering: try moves with better immediate evaluation first
        scored_moves = []
        for m in my_moves:
            ny, no = apply_move(you, opp, m)
            scored_moves.append((evaluate(ny, no), m))
        scored_moves.sort(reverse=True, key=lambda x: x[0])
        for _, m in scored_moves:
            ny, no = apply_move(you, opp, m)
            val, _ = minimax(no, ny, depth - 1, -beta, -alpha, False)
            val = -val
            if val > best_val:
                best_val = val
                best_move = m
            alpha = max(alpha, val)
            if alpha >= beta or time_left() <= 0:
                break
        return best_val, best_move
    else:
        # minimizing: opponent to move; we treat symmetrical by swapping roles
        if not my_moves:
            val, mv = minimax(opp, you, depth - 1, -beta, -alpha, True)
            return -val, None
        best_val = -1e9
        best_move = None
        scored_moves = []
        for m in my_moves:
            ny, no = apply_move(you, opp, m)
            scored_moves.append((evaluate(ny, no), m))
        scored_moves.sort(reverse=True, key=lambda x: x[0])
        for _, m in scored_moves:
            ny, no = apply_move(you, opp, m)
            val, _ = minimax(no, ny, depth - 1, -beta, -alpha, True)
            val = -val
            if val > best_val:
                best_val = val
                best_move = m
            alpha = max(alpha, val)
            if alpha >= beta or time_left() <= 0:
                break
        return best_val, best_move

def choose_depth(you: np.ndarray, opp: np.ndarray) -> int:
    empties = int(((you == 0) & (opp == 0)).sum())
    # More search depth in late game, less in early game
    if empties > 40:
        return 3
    elif empties > 24:
        return 4
    elif empties > 12:
        return 5
    else:
        return 8  # very late game, deeper search (branching small)

def coord_to_str(move: Tuple[int,int]) -> str:
    r, c = move
    file = chr(ord('a') + c)
    rank = str(r + 1)
    return f"{file}{rank}"

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    Decide and return a legal move for the current player.
    you and opponent are 8x8 numpy arrays of 0/1 ints.
    """
    global _start_time
    _start_time = time.time()

    you = you.astype(np.int8)
    opponent = opponent.astype(np.int8)

    legal = find_legal_moves(you, opponent)
    if not legal:
        return "pass"

    # Quick heuristic fallback if extremely low time
    # Determine search depth
    depth = choose_depth(you, opponent)

    # Iterative deepening while time allows — attempt increasing depths up to chosen depth
    best_move = None
    best_score = -1e9
    try_depths = list(range(1, depth + 1))
    for d in try_depths:
        if time_left() <= 0:
            break
        score, mv = minimax(you, opponent, d, -1e9, 1e9, True)
        if mv is not None:
            best_move = mv
            best_score = score
        # If decisive endgame found (large magnitude), we can stop
        if abs(score) > 90000:
            break

    # If minimax didn't find a move (time cutoff), pick best immediate heuristic move
    if best_move is None:
        best_val = -1e9
        best_move = legal[0]
        for m in legal:
            ny, no = apply_move(you, opponent, m)
            val = evaluate(ny, no)
            if val > best_val:
                best_val = val
                best_move = m

    return coord_to_str(best_move)

# If used as a script, provide a tiny test (not executed in arena)
if __name__ == "__main__":
    # Starting position test
    you = np.zeros((8,8), dtype=int)
    opp = np.zeros((8,8), dtype=int)
    you[3,4] = 1
    you[4,3] = 1
    opp[3,3] = 1
    opp[4,4] = 1
    print(policy(you, opp))


import numpy as np
import random
from typing import List, Tuple

# directions: N, NE, E, SE, S, SW, W, NW
DIRS = [(-1, 0), (-1, 1), (0, 1), (1, 1),
        (1, 0), (1, -1), (0, -1), (-1, -1)]

# classic Othello weight matrix
WEIGHT = np.array([
    [120, -20,  20,  5,  5, 20, -20, 120],
    [-20, -40,  -5, -5, -5, -5, -40, -20],
    [ 20,  -5,  15,  3,  3, 15,  -5,  20],
    [  5,  -5,   3,  3,  3,  3,  -5,   5],
    [  5,  -5,   3,  3,  3,  3,  -5,   5],
    [ 20,  -5,  15,  3,  3, 15,  -5,  20],
    [-20, -40,  -5, -5, -5, -5, -40, -20],
    [120, -20,  20,  5,  5, 20, -20, 120],
], dtype=np.int32)

def inside(r: int, c: int) -> bool:
    return 0 <= r < 8 and 0 <= c < 8

def legal_moves(you: np.ndarray, opp: np.ndarray) -> List[Tuple[int, int]]:
    """Return list of (r,c) where a move is legal for 'you'."""
    empty = (you == 0) & (opp == 0)
    moves = []
    for r in range(8):
        for c in range(8):
            if not empty[r, c]:
                continue
            for dr, dc in DIRS:
                nr, nc = r + dr, c + dc
                found_opponent = False
                while inside(nr, nc) and opp[nr, nc]:
                    found_opponent = True
                    nr += dr
                    nc += dc
                if found_opponent and inside(nr, nc) and you[nr, nc]:
                    moves.append((r, c))
                    break
    return moves

def flip_discs(you: np.ndarray, opp: np.ndarray,
               r: int, c: int) -> Tuple[np.ndarray, np.ndarray]:
    """Place a disc for 'you' at (r,c) and flip opponent discs."""
    new_you = you.copy()
    new_opp = opp.copy()
    new_you[r, c] = 1
    for dr, dc in DIRS:
        flips = []
        nr, nc = r + dr, c + dc
        while inside(nr, nc) and new_opp[nr, nc]:
            flips.append((nr, nc))
            nr += dr
            nc += dc
        if flips and inside(nr, nc) and new_you[nr, nc]:
            for fr, fc in flips:
                new_you[fr, fc] = 1
                new_opp[fr, fc] = 0
    return new_you, new_opp

def evaluate(you: np.ndarray, opp: np.ndarray) -> int:
    """Static evaluation using the weight matrix."""
    return int((WEIGHT * you).sum() - (WEIGHT * opp).sum())

def minimax(you: np.ndarray, opp: np.ndarray,
            depth: int, maximizing: bool,
            alpha: int, beta: int) -> int:
    """Depth‑limited minimax with alpha‑beta pruning."""
    moves = legal_moves(you, opp)
    if depth == 0 or not moves:
        # If no moves for current player, they must pass.
        # The evaluation is the same; the opponent will move next.
        return evaluate(you, opp)

    if maximizing:
        best = -10**9
        for r, c in moves:
            n_you, n_opp = flip_discs(you, opp, r, c)
            # opponent's turn after our move
            score = minimax(n_opp, n_you, depth - 1, False, alpha, beta)
            best = max(best, score)
            alpha = max(alpha, best)
            if beta <= alpha:
                break
        return best
    else:
        best = 10**9
        for r, c in moves:
            n_opp, n_you = flip_discs(opp, you, r, c)  # opponent plays
            score = minimax(n_you, n_opp, depth - 1, True, alpha, beta)
            best = min(best, score)
            beta = min(beta, best)
            if beta <= alpha:
                break
        return best

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """Return the best legal move in algebraic notation or 'pass'."""
    moves = legal_moves(you, opponent)
    if not moves:
        return "pass"

    best_score = -10**9
    best_moves = []
    for r, c in moves:
        n_you, n_opp = flip_discs(you, opponent, r, c)
        # opponent's response (depth 1)
        score = minimax(n_opp, n_you, depth=1, maximizing=False,
                        alpha=-10**9, beta=10**9)
        if score > best_score:
            best_score = score
            best_moves = [(r, c)]
        elif score == best_score:
            best_moves.append((r, c))

    # deterministic but varied tie‑breaker
    r, c = random.choice(best_moves)

    file = chr(ord('a') + c)
    rank = str(r + 1)
    return f"{file}{rank}"

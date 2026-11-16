
import numpy as np
from itertools import product

def rotate_quadrant(board: np.ndarray, quad: int, direction: str) -> np.ndarray:
    """Return a new board with the specified 3×3 quadrant rotated."""
    b = board.copy()
    # map quadrant to slice indices
    rows = slice(0, 3) if quad < 2 else slice(3, 6)
    cols = slice(0, 3) if quad % 2 == 0 else slice(3, 6)
    sub = b[rows, cols]
    if direction == 'L':          # 90° anticlockwise
        sub = np.rot90(sub, k=1)
    else:                         # 'R' – 90° clockwise
        sub = np.rot90(sub, k=-1)
    b[rows, cols] = sub
    return b

def apply_move(you: np.ndarray, opp: np.ndarray,
               row: int, col: int, quad: int, direction: str):
    """Place a marble for 'you' at (row,col) then rotate the chosen quadrant."""
    y = you.copy()
    o = opp.copy()
    y[row, col] = 1
    y = rotate_quadrant(y, quad, direction)
    o = rotate_quadrant(o, quad, direction)
    return y, o

def max_consecutive(arr: np.ndarray) -> int:
    """Longest run of 1's in a 1‑D array."""
    best = cur = 0
    for v in arr:
        if v:
            cur += 1
            if cur > best:
                best = cur
        else:
            cur = 0
    return best

def any_five(board: np.ndarray) -> bool:
    """Return True if board contains ≥5 consecutive stones in any line."""
    # rows & columns
    for i in range(6):
        if max_consecutive(board[i, :]) >= 5:
            return True
        if max_consecutive(board[:, i]) >= 5:
            return True
    # diagonals (down‑right)
    for d in range(-1, 6):          # offsets for np.diagonal
        diag = board.diagonal(offset=d)
        if max_consecutive(diag) >= 5:
            return True
    # diagonals (up‑right)
    flipped = np.fliplr(board)
    for d in range(-1, 6):
        diag = flipped.diagonal(offset=d)
        if max_consecutive(diag) >= 5:
            return True
    return False

def policy(you, opponent) -> str:
    """
    Return a legal Pentago move as "row,col,quad,dir".
    you, opponent are 6×6 array‑likes with 0/1 entries.
    """
    you = np.array(you, dtype=int)
    opp = np.array(opponent, dtype=int)

    empty = [(r, c) for r in range(6) for c in range(6) if you[r, c] == 0 and opp[r, c] == 0]
    quads = range(4)
    dirs = ('L', 'R')

    # 1️⃣  Try to win immediately
    for r, c in empty:
        for q, d in product(quads, dirs):
            y2, o2 = apply_move(you, opp, r, c, q, d)
            win_you = any_five(y2)
            win_opp = any_five(o2)
            if win_you and not win_opp:
                return f"{r+1},{c+1},{q},{d}"

    # 2️⃣  Detect opponent immediate threats
    threat_cells = set()
    for r, c in empty:
        for q, d in product(quads, dirs):
            # opponent places at (r,c)
            o2, y2 = apply_move(opp, you, r, c, q, d)   # note swapped roles
            if any_five(o2) and not any_five(y2):
                threat_cells.add((r, c))

    # If we can block, do it (any rotation works)
    for r, c in threat_cells:
        if you[r, c] == 0 and opp[r, c] == 0:
            # simple block: place on the threatened cell, rotate quadrant 0 left
            return f"{r+1},{c+1},0,L"

    # 3️⃣  Choose best continuation move (longest run we create)
    best_score = -1
    best_move = None
    for r, c in empty:
        for q, d in product(quads, dirs):
            y2, _ = apply_move(you, opp, r, c, q, d)
            # evaluate longest consecutive run for us
            score = 0
            for i in range(6):
                score = max(score, max_consecutive(y2[i, :]))
                score = max(score, max_consecutive(y2[:, i]))
            # diagonals
            for off in range(-1, 6):
                score = max(score, max_consecutive(y2.diagonal(offset=off)))
            flipped = np.fliplr(y2)
            for off in range(-1, 6):
                score = max(score, max_consecutive(flipped.diagonal(offset=off)))
            if score > best_score:
                best_score = score
                best_move = (r, c, q, d)
    # fallback – should always find something
    r, c, q, d = best_move
    return f"{r+1},{c+1},{q},{d}"

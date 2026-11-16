
import numpy as np
import random
from typing import List, Tuple

def _neighbor_boxes(row: int, col: int, direction: str) -> List[Tuple[int, int]]:
    """Return the list of box coordinates (i,j) that touch the given edge."""
    boxes = []
    if direction == 'H':
        # horizontal edge at (row, col) connects dots (row, col) – (row, col+1)
        # It is the top of box (row, col) and bottom of box (row-1, col)
        if row < 4:          # box below
            boxes.append((row, col))
        if row > 0:          # box above
            boxes.append((row - 1, col))
    else:  # 'V'
        # vertical edge at (row, col) connects dots (row, col) – (row+1, col)
        # It is the left of box (row, col) and right of box (row, col-1)
        if col < 4:          # box to the right
            boxes.append((row, col))
        if col > 0:          # box to the left
            boxes.append((row, col - 1))
    return boxes

def _box_side_count(i: int, j: int, h: np.ndarray, v: np.ndarray) -> int:
    """Count how many of the four edges of box (i,j) are already drawn."""
    count = 0
    count += 1 if h[i, j] != 0 else 0          # top
    count += 1 if h[i + 1, j] != 0 else 0      # bottom
    count += 1 if v[i, j] != 0 else 0          # left
    count += 1 if v[i, j + 1] != 0 else 0      # right
    return count

def policy(horizontal: np.ndarray, vertical: np.ndarray,
           capture: np.ndarray) -> str:
    """Return a legal move string 'row,col,dir' for a 4x4 Dots‑and‑Boxes board."""
    moves = []  # each entry: (row, col, dir, captures, danger, border)

    # ---------- collect horizontal moves ----------
    for r in range(5):
        for c in range(5):
            if horizontal[r, c] != 0:
                continue
            # keep only edges that belong to at least one box
            neigh = _neighbor_boxes(r, c, 'H')
            if not neigh:
                continue
            captures = 0
            danger = 0
            # simulate drawing this edge
            for (i, j) in neigh:
                before = _box_side_count(i, j, horizontal, vertical)
                after = before + 1  # this edge will be added
                if after == 4:
                    captures += 1
                elif after == 3:
                    danger += 1
            border = len(neigh) == 1
            moves.append((r, c, 'H', captures, danger, border))

    # ---------- collect vertical moves ----------
    for r in range(5):
        for c in range(5):
            if vertical[r, c] != 0:
                continue
            neigh = _neighbor_boxes(r, c, 'V')
            if not neigh:
                continue
            captures = 0
            danger = 0
            for (i, j) in neigh:
                before = _box_side_count(i, j, horizontal, vertical)
                after = before + 1
                if after == 4:
                    captures += 1
                elif after == 3:
                    danger += 1
            border = len(neigh) == 1
            moves.append((r, c, 'V', captures, danger, border))

    # ---------- 1️⃣ Prefer captures ----------
    max_capt = max(m[3] for m in moves)
    if max_capt > 0:
        best = [m for m in moves if m[3] == max_capt]
        # among them pick minimal danger (usually 0) then border preference
        min_danger = min(m[4] for m in best)
        best = [m for m in best if m[4] == min_danger]
        border_moves = [m for m in best if m[5]]
        choice = random.choice(border_moves) if border_moves else random.choice(best)
        return f"{choice[0]},{choice[1]},{choice[2]}"

    # ---------- 2️⃣ Safe moves (danger == 0) ----------
    safe_moves = [m for m in moves if m[4] == 0]
    if safe_moves:
        # prefer border edges (they are less likely to start a chain)
        border_moves = [m for m in safe_moves if m[5]]
        choice = random.choice(border_moves) if border_moves else random.choice(safe_moves)
        return f"{choice[0]},{choice[1]},{choice[2]}"

    # ---------- 3️⃣ Forced sacrifice ----------
    # minimise danger, then prefer border
    min_danger = min(m[4] for m in moves)
    cand = [m for m in moves if m[4] == min_danger]
    border_moves = [m for m in cand if m[5]]
    choice = random.choice(border_moves) if border_moves else random.choice(cand)
    return f"{choice[0]},{choice[1]},{choice[2]}"

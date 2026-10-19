
from typing import List, Tuple

def _all_lines() -> List[List[Tuple[int, int, int]]]:
    """Generate all unique lines of length 3 in a 3x3x3 grid.
    Each line is a list of three (i,j,k) coordinates where i,j,k in 0..2.
    """
    lines = []
    dirs = [(dx, dy, dz)
            for dx in (-1, 0, 1)
            for dy in (-1, 0, 1)
            for dz in (-1, 0, 1)
            if not (dx == dy == dz == 0)]
    # keep only one orientation of each direction (lexicographically > 0)
    dirs = [d for d in dirs if (d[0] > 0) or (d[0] == 0 and d[1] > 0) or (d[0] == 0 and d[1] == 0 and d[2] > 0)]
    for i in range(3):
        for j in range(3):
            for k in range(3):
                for dx, dy, dz in dirs:
                    coords = []
                    for t in range(3):
                        ni = i + dx * t
                        nj = j + dy * t
                        nk = k + dz * t
                        if not (0 <= ni < 3 and 0 <= nj < 3 and 0 <= nk < 3):
                            break
                        coords.append((ni, nj, nk))
                    if len(coords) == 3:
                        # sort to canonical order to avoid duplicates
                        # but keep the same order for consistent scoring / picking the empty cell
                        # we'll store as a tuple of coords, and use a set to ensure uniqueness
                        lines.append(coords)
    # remove duplicates by converting to a canonical representation (sorted tuple)
    uniq = {}
    for line in lines:
        key = tuple(sorted(line))
        if key not in uniq:
            uniq[key] = line  # keep original order (start->end)
    return list(uniq.values())

# Precompute lines once
_LINES = _all_lines()

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    """
    Choose a move for a 3x3x3 Tic Tac Toe board.
    board is a 3x3x3 list of lists with values: 0 (empty), 1 (me), -1 (opponent).
    Returns a tuple (i, j, k) with coordinates 0..2 corresponding to the input board indexing.
    """
    # helper to get value
    def val(coord):
        i, j, k = coord
        return board[i][j][k]

    # 1) Immediate win: if any line has sum == 2 (two of mine and one empty), take the empty
    for line in _LINES:
        s = sum(val(c) for c in line)
        if s == 2:
            for c in line:
                if val(c) == 0:
                    return c

    # 2) Block opponent immediate win: if any line has sum == -2 (two opponent and one empty)
    for line in _LINES:
        s = sum(val(c) for c in line)
        if s == -2:
            for c in line:
                if val(c) == 0:
                    return c

    # 3) Take center if available
    center = (1, 1, 1)
    if val(center) == 0:
        return center

    # 4) Heuristic: choose empty cell that participates in the most promising lines.
    #    For each empty cell, look at lines containing it:
    #      - ignore any line that already has an opponent mark (-1)
    #      - weight lines with 2 of my marks highest, then 1, then 0
    best_score = None
    best_move = None
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] != 0:
                    continue
                score = 0
                coord = (i, j, k)
                for line in _LINES:
                    if coord not in line:
                        continue
                    line_vals = [val(c) for c in line]
                    if -1 in line_vals:
                        continue  # blocked line, ignore
                    my_count = line_vals.count(1)
                    # weight: two-in-line -> very strong, one-in-line -> moderate, empty -> small
                    if my_count == 2:
                        score += 100
                    elif my_count == 1:
                        score += 10
                    else:
                        score += 1
                # tie-break deterministically by lexicographic coordinate (prefer smaller tuple)
                if best_score is None or score > best_score or (score == best_score and coord < best_move):
                    best_score = score
                    best_move = coord

    if best_move is not None:
        return best_move

    # 5) Fallback: pick first empty cell (should not usually happen)
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    return (i, j, k)

    # No moves left; return an arbitrary coordinate (game over)
    return (0, 0, 0)


# If this file is used as a module, policy(...) is available.
# No top-level execution or I/O per requirements.

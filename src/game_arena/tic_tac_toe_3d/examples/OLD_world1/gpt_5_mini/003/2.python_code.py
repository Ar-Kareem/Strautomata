
from typing import List, Tuple

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    """
    Choose a move for an n x n x n Tic-Tac-Toe board.
    board[z][y][x] (or board[layer][row][col]) contains:
      0 for empty, 1 for our marks, -1 for opponent.
    Returns a tuple (x, y, z) with coordinates in 0..n-1 for an empty cell.
    Strategy:
      1. If we can win in one move, play that move.
      2. If opponent can win in one move, block it.
      3. Otherwise evaluate all empty cells and pick the one maximizing a heuristic:
         - Counts lines through the cell that are still open (no opponent marks).
         - Lines with more of our marks get higher weight.
         - Slight bonus for center and corners.
      Deterministic tie-breaking: choose the smallest coordinate tuple.
    """
    n = len(board)
    # Convert board indexing convention: board[z][y][x].
    # We'll treat coords as (x, y, z) matching return order.
    # Helper to check in-bounds
    def in_bounds(x, y, z):
        return 0 <= x < n and 0 <= y < n and 0 <= z < n

    # Build all straight lines of length n in the grid.
    dirs = [(dx, dy, dz)
            for dx in (-1, 0, 1)
            for dy in (-1, 0, 1)
            for dz in (-1, 0, 1)
            if not (dx == dy == dz == 0)]
    lines = []
    seen = set()
    for x in range(n):
        for y in range(n):
            for z in range(n):
                for dx, dy, dz in dirs:
                    # Only start lines where the previous cell in this direction would be out of bounds;
                    # this avoids duplicates.
                    px, py, pz = x - dx, y - dy, z - dz
                    if in_bounds(px, py, pz):
                        continue
                    # Build the line of length n
                    coords = []
                    ok = True
                    for k in range(n):
                        nx, ny, nz = x + k*dx, y + k*dy, z + k*dz
                        if not in_bounds(nx, ny, nz):
                            ok = False
                            break
                        coords.append((nx, ny, nz))
                    if not ok:
                        continue
                    key = tuple(coords)
                    if key not in seen:
                        seen.add(key)
                        lines.append(coords)

    # Precompute line sums and empty positions
    line_info = []
    for coords in lines:
        s = 0
        empties = []
        for (x, y, z) in coords:
            v = board[z][y][x]
            s += v
            if v == 0:
                empties.append((x, y, z))
        line_info.append((coords, s, empties))

    # 1) Immediate win: find a line with sum == n-1 and one empty -> play it
    for coords, s, empties in line_info:
        if s == (n - 1) and len(empties) == 1:
            return empties[0]

    # 2) Block opponent immediate win: opponent sum == -(n-1)
    for coords, s, empties in line_info:
        if s == -(n - 1) and len(empties) == 1:
            return empties[0]

    # 3) Heuristic evaluation of all empty cells
    # For each empty cell, evaluate score based on lines containing it.
    best_score = None
    best_moves = []

    # Precompute mapping from cell to lines that include it
    from collections import defaultdict
    cell_to_lines = defaultdict(list)
    for idx, (coords, s, empties) in enumerate(line_info):
        for c in coords:
            cell_to_lines[c].append(idx)

    for x in range(n):
        for y in range(n):
            for z in range(n):
                if board[z][y][x] != 0:
                    continue
                score = 0.0
                cell = (x, y, z)
                for idx in cell_to_lines[cell]:
                    coords, s, empties = line_info[idx]
                    # If opponent already in this line, it's not a winnable line for us
                    # except blocking possibilities handled above. So skip lines containing -1.
                    contains_opponent = any(board[cz][cy][cx] == -1 for (cx, cy, cz) in coords)
                    if contains_opponent:
                        continue
                    # Count how many of our marks are already in this line
                    our_count = sum(1 for (cx, cy, cz) in coords if board[cz][cy][cx] == 1)
                    # Lines with more of our marks are more valuable
                    score += 1 + (our_count * 8)  # base 1, plus 8 per our mark
                # Slight bonuses for center (best for 3x3x3) and corners
                center_bonus = 0.0
                if n % 2 == 1:
                    mid = n // 2
                    if (x, y, z) == (mid, mid, mid):
                        center_bonus = 50.0
                # corner bonus if each coordinate is at boundary
                corner_bonus = 0.0
                if (x in (0, n-1)) and (y in (0, n-1)) and (z in (0, n-1)):
                    corner_bonus = 3.0
                score += center_bonus + corner_bonus

                if best_score is None or score > best_score:
                    best_score = score
                    best_moves = [cell]
                elif score == best_score:
                    best_moves.append(cell)

    # If no empty cells (shouldn't happen in proper play), pick first found
    if not best_moves:
        # find any empty
        for x in range(n):
            for y in range(n):
                for z in range(n):
                    if board[z][y][x] == 0:
                        return (x, y, z)
        # No empty: return (0,0,0) as fallback
        return (0, 0, 0)

    # Deterministic tie-break: smallest lexicographic tuple
    best_moves.sort()
    return best_moves[0]

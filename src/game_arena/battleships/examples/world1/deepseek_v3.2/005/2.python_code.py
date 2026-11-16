
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Helper to get adjacent cells (orthogonal)
    def neighbors(r, c):
        for dr, dc in [(1,0), (-1,0), (0,1), (0,-1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 10 and 0 <= nc < 10:
                yield nr, nc

    # 1. Find all hit cells
    hits = [(r, c) for r in range(10) for c in range(10) if board[r][c] == 1]

    # 2. Try to find a target based on existing hits
    # We'll examine each hit to see if it's part of an unsunk ship
    # Prefer hits that are part of a line (have a hit neighbor)
    target_hits = []
    for r, c in hits:
        # Check if any adjacent unknown
        unknown_adj = any(board[nr][nc] == 0 for nr, nc in neighbors(r, c))
        if not unknown_adj:
            continue  # this hit is surrounded by misses/hits, likely sunk
        # Check for hit neighbors to determine orientation
        hit_up = r > 0 and board[r-1][c] == 1
        hit_down = r < 9 and board[r+1][c] == 1
        hit_left = c > 0 and board[r][c-1] == 1
        hit_right = c < 9 and board[r][c+1] == 1
        target_hits.append((r, c, unknown_adj, hit_up, hit_down, hit_left, hit_right))

    if target_hits:
        # First, try to extend a known line
        for r, c, _, hu, hd, hl, hr in target_hits:
            # vertical line?
            if hu or hd:
                # find topmost and bottommost hits in this column
                top = r
                while top >= 0 and board[top][c] == 1:
                    top -= 1
                bottom = r
                while bottom < 10 and board[bottom][c] == 1:
                    bottom += 1
                # Check top-1 and bottom (just outside the line)
                if top >= 0 and board[top][c] == 0:
                    return (top, c)
                if bottom < 10 and board[bottom][c] == 0:
                    return (bottom, c)
            # horizontal line?
            if hl or hr:
                # find leftmost and rightmost hits in this row
                left = c
                while left >= 0 and board[r][left] == 1:
                    left -= 1
                right = c
                while right < 10 and board[r][right] == 1:
                    right += 1
                if left >= 0 and board[r][left] == 0:
                    return (r, left)
                if right < 10 and board[r][right] == 0:
                    return (r, right)

        # If no line extension possible, pick a hit with unknown adjacent and shoot at first unknown neighbor
        for r, c, _, _, _, _, _ in target_hits:
            for nr, nc in neighbors(r, c):
                if board[nr][nc] == 0:
                    return (nr, nc)

    # 3. Hunt mode: probability density
    heat = [[0] * 10 for _ in range(10)]
    ship_lengths = [5, 4, 3, 3, 2]
    for length in ship_lengths:
        # horizontal placements
        for r in range(10):
            for c in range(10 - length + 1):
                valid = True
                for k in range(length):
                    if board[r][c + k] == -1:
                        valid = False
                        break
                if valid:
                    for k in range(length):
                        heat[r][c + k] += 1
        # vertical placements
        for r in range(10 - length + 1):
            for c in range(10):
                valid = True
                for k in range(length):
                    if board[r + k][c] == -1:
                        valid = False
                        break
                if valid:
                    for k in range(length):
                        heat[r + k][c] += 1

    # Find cell with maximum heat among unknowns
    max_heat = -1
    candidates = []
    for r in range(10):
        for c in range(10):
            if board[r][c] == 0:
                if heat[r][c] > max_heat:
                    max_heat = heat[r][c]
                    candidates = [(r, c)]
                elif heat[r][c] == max_heat:
                    candidates.append((r, c))

    # Tie-breaking: prefer cells that are more central (min distance from center (4.5,4.5))
    def dist_from_center(cell):
        r, c = cell
        return abs(r - 4.5) + abs(c - 4.5)
    candidates.sort(key=lambda cell: (dist_from_center(cell), cell[0], cell[1]))
    return candidates[0]

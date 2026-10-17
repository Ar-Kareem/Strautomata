
from typing import List, Tuple

# Standard Battleship fleet
SHIP_LENGTHS = [5, 4, 3, 3, 2]

def policy(board: List[List[int]]) -> Tuple[int, int]:
    n = 10

    hits = [(r, c) for r in range(n) for c in range(n) if board[r][c] == 1]

    # Group connected hits
    groups = []
    visited = set()
    for hr, hc in hits:
        if (hr, hc) in visited:
            continue
        stack = [(hr, hc)]
        group = []
        visited.add((hr, hc))
        while stack:
            r, c = stack.pop()
            group.append((r, c))
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < n and 0 <= nc < n and board[nr][nc] == 1 and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    stack.append((nr, nc))
        groups.append(group)

    # Target mode if any hits
    if hits:
        best_move = None
        best_score = -1
        best_group_size = -1

        all_hits_set = set(hits)

        for group in groups:
            group_set = set(group)
            other_hits = all_hits_set - group_set
            size = len(group)

            # Determine orientation
            rows = {r for r, _ in group}
            cols = {c for _, c in group}
            orientation = None
            if len(rows) == 1 and len(group) > 1:
                orientation = 'H'
            elif len(cols) == 1 and len(group) > 1:
                orientation = 'V'

            # Generate candidates
            candidates = set()
            if orientation == 'H':
                row = next(iter(rows))
                minc = min(cols)
                maxc = max(cols)
                for nc in [minc-1, maxc+1]:
                    if 0 <= nc < n and board[row][nc] == 0:
                        candidates.add((row, nc))
            elif orientation == 'V':
                col = next(iter(cols))
                minr = min(rows)
                maxr = max(rows)
                for nr in [minr-1, maxr+1]:
                    if 0 <= nr < n and board[nr][col] == 0:
                        candidates.add((nr, col))
            else:
                # Unknown orientation: try all neighbors
                for r, c in group:
                    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                        nr, nc = r+dr, c+dc
                        if 0 <= nr < n and 0 <= nc < n and board[nr][nc] == 0:
                            candidates.add((nr, nc))

            # Score each candidate based on compatible ship placements
            for cand in candidates:
                score = count_placements_for_group(board, group, other_hits, cand)
                if size > best_group_size or (size == best_group_size and score > best_score) or \
                   (size == best_group_size and score == best_score and best_move and cand < best_move):
                    best_group_size = size
                    best_score = score
                    best_move = cand

        if best_move is not None:
            return best_move

    # If no target or no valid candidates, hunt mode
    return hunt_mode(board, allow_hits=bool(hits))

def count_placements_for_group(board, group, other_hits, cand):
    n = 10
    group_set = set(group)
    rlist = [r for r, _ in group]
    clist = [c for _, c in group]

    rows = set(rlist)
    cols = set(clist)
    orientation = None
    if len(rows) == 1 and len(group) > 1:
        orientation = 'H'
    elif len(cols) == 1 and len(group) > 1:
        orientation = 'V'

    total = 0
    for L in SHIP_LENGTHS:
        if L < len(group):
            continue
        for ori in ['H', 'V']:
            if orientation and ori != orientation:
                continue
            if ori == 'H':
                row = next(iter(rows)) if len(rows) == 1 else group[0][0]
                if cand[0] != row:
                    continue
                minc = min(clist)
                maxc = max(clist)
                start_min = maxc - L + 1
                start_max = minc
                for start in range(start_min, start_max + 1):
                    end = start + L - 1
                    if not (start <= cand[1] <= end):
                        continue
                    valid = True
                    for cc in range(start, end + 1):
                        if not (0 <= cc < n):
                            valid = False
                            break
                        cell = board[row][cc]
                        if cell == -1:
                            valid = False
                            break
                        if cell == 1 and (row, cc) in other_hits:
                            valid = False
                            break
                    if valid:
                        total += 1
            else:
                col = next(iter(cols)) if len(cols) == 1 else group[0][1]
                if cand[1] != col:
                    continue
                minr = min(rlist)
                maxr = max(rlist)
                start_min = maxr - L + 1
                start_max = minr
                for start in range(start_min, start_max + 1):
                    end = start + L - 1
                    if not (start <= cand[0] <= end):
                        continue
                    valid = True
                    for rr in range(start, end + 1):
                        if not (0 <= rr < n):
                            valid = False
                            break
                        cell = board[rr][col]
                        if cell == -1:
                            valid = False
                            break
                        if cell == 1 and (rr, col) in other_hits:
                            valid = False
                            break
                    if valid:
                        total += 1
    return total

def hunt_mode(board, allow_hits=False):
    n = 10
    density = [[0 for _ in range(n)] for _ in range(n)]

    for L in SHIP_LENGTHS:
        # Horizontal
        for r in range(n):
            for c in range(n - L + 1):
                cells = [(r, c+i) for i in range(L)]
                if any(board[rr][cc] == -1 for rr, cc in cells):
                    continue
                if not allow_hits and any(board[rr][cc] == 1 for rr, cc in cells):
                    continue
                for rr, cc in cells:
                    if board[rr][cc] == 0:
                        density[rr][cc] += 1
        # Vertical
        for c in range(n):
            for r in range(n - L + 1):
                cells = [(r+i, c) for i in range(L)]
                if any(board[rr][cc] == -1 for rr, cc in cells):
                    continue
                if not allow_hits and any(board[rr][cc] == 1 for rr, cc in cells):
                    continue
                for rr, cc in cells:
                    if board[rr][cc] == 0:
                        density[rr][cc] += 1

    best = None
    best_score = -1
    for r in range(n):
        for c in range(n):
            if board[r][c] == 0:
                score = density[r][c]
                if score > best_score or (score == best_score and best and (r, c) < best):
                    best_score = score
                    best = (r, c)

    if best is not None:
        return best

    # Fallback: return first unknown
    for r in range(n):
        for c in range(n):
            if board[r][c] == 0:
                return (r, c)

    # Should never happen
    return (0, 0)

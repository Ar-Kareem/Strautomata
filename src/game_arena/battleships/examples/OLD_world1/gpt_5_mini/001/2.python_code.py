import random
from collections import deque
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Battleship targeting policy for an n x n board (assumes n == 10 typically).
    board values:
      0 -> unknown
     -1 -> miss
      1 -> hit
    Returns (row, col) of a cell not previously fired at (board[row][col] == 0).
    Strategy:
      - If there are one or more hits, enter "target" mode: focus around contiguous hit groups,
        extending along inferred orientation to finish that ship.
      - Otherwise, use a probability-style hunt: for each remaining ship length (5,4,3,3,2),
        enumerate all placements consistent with known misses and accumulate a heat map of how
        many placements cover each unknown cell. Fire at the unknown cell with highest score.
      - Tie-breaking is random. Fallbacks use a parity hunt pattern to spread shots.
    """
    n = len(board)
    # Basic bounds safety
    if n == 0:
        return (0, 0)

    # Ship lengths (standard fleet)
    ship_lengths = [5, 4, 3, 3, 2]

    # Helpers
    def in_bounds(r, c):
        return 0 <= r < n and 0 <= c < n

    # Collect hits and misses
    hits = [(r, c) for r in range(n) for c in range(n) if board[r][c] == 1]
    misses = {(r, c) for r in range(n) for c in range(n) if board[r][c] == -1}

    # Build heatmap from possible ship placements
    def build_heatmap():
        heat = [[0] * n for _ in range(n)]
        for length in ship_lengths:
            # horizontal placements
            for r in range(n):
                for c in range(n - length + 1):
                    segment = [(r, c + i) for i in range(length)]
                    # can't overlap a known miss
                    if any(board[rr][cc] == -1 for rr, cc in segment):
                        continue
                    # it's allowed even if it doesn't cover hits; placements that cover hits contribute more
                    for rr, cc in segment:
                        if board[rr][cc] == 0:
                            heat[rr][cc] += 1
            # vertical placements
            for c in range(n):
                for r in range(n - length + 1):
                    segment = [(r + i, c) for i in range(length)]
                    if any(board[rr][cc] == -1 for rr, cc in segment):
                        continue
                    for rr, cc in segment:
                        if board[rr][cc] == 0:
                            heat[rr][cc] += 1
        return heat

    heatmap = build_heatmap()

    # Find connected components of hits (4-neighbor)
    def hit_components():
        comps = []
        visited = [[False] * n for _ in range(n)]
        dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        for (r, c) in hits:
            if visited[r][c]:
                continue
            # BFS
            q = deque()
            q.append((r, c))
            comp = []
            visited[r][c] = True
            while q:
                rr, cc = q.popleft()
                comp.append((rr, cc))
                for dr, dc in dirs:
                    nr, nc = rr + dr, cc + dc
                    if in_bounds(nr, nc) and not visited[nr][nc] and board[nr][nc] == 1:
                        visited[nr][nc] = True
                        q.append((nr, nc))
            comps.append(comp)
        return comps

    # Target mode: try to finish off ships near hits
    if hits:
        comps = hit_components()
        # Prefer the largest component (most likely active ship)
        comps.sort(key=lambda x: -len(x))
        target_candidates = []
        for comp in comps:
            if not comp:
                continue
            if len(comp) == 1:
                r, c = comp[0]
                # consider all 4 neighbors
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if in_bounds(nr, nc) and board[nr][nc] == 0:
                        target_candidates.append((nr, nc))
            else:
                # infer orientation
                rows = {r for r, _ in comp}
                cols = {c for _, c in comp}
                if len(rows) == 1:
                    # horizontal
                    row = next(iter(rows))
                    sorted_cols = sorted(c for _, c in comp)
                    left = sorted_cols[0] - 1
                    right = sorted_cols[-1] + 1
                    if in_bounds(row, left) and board[row][left] == 0:
                        target_candidates.append((row, left))
                    if in_bounds(row, right) and board[row][right] == 0:
                        target_candidates.append((row, right))
                    # also consider adjacent cells above/below each hit if ends blocked
                    if not target_candidates:
                        for rr, cc in comp:
                            for dr in (-1, 1):
                                nr = rr + dr
                                nc = cc
                                if in_bounds(nr, nc) and board[nr][nc] == 0:
                                    target_candidates.append((nr, nc))
                elif len(cols) == 1:
                    # vertical
                    col = next(iter(cols))
                    sorted_rows = sorted(r for r, _ in comp)
                    top = sorted_rows[0] - 1
                    bottom = sorted_rows[-1] + 1
                    if in_bounds(top, col) and board[top][col] == 0:
                        target_candidates.append((top, col))
                    if in_bounds(bottom, col) and board[bottom][col] == 0:
                        target_candidates.append((bottom, col))
                    if not target_candidates:
                        for rr, cc in comp:
                            for dc in (-1, 1):
                                nr = rr
                                nc = cc + dc
                                if in_bounds(nr, nc) and board[nr][nc] == 0:
                                    target_candidates.append((nr, nc))
                else:
                    # weird shape (shouldn't happen in valid game), fallback to neighbors of hits
                    for rr, cc in comp:
                        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                            nr, nc = rr + dr, cc + dc
                            if in_bounds(nr, nc) and board[nr][nc] == 0:
                                target_candidates.append((nr, nc))
            # If we found candidates around the current (largest-first) component, use them
            if target_candidates:
                break

        if target_candidates:
            # pick candidate with highest heatmap value (break ties randomly)
            best_score = -1
            best_cells = []
            for (r, c) in target_candidates:
                score = heatmap[r][c]
                if score > best_score:
                    best_score = score
                    best_cells = [(r, c)]
                elif score == best_score:
                    best_cells.append((r, c))
            return random.choice(best_cells)

    # Hunting mode: use heatmap to pick highest-probability cell
    best_score = -1
    best_cells = []
    for r in range(n):
        for c in range(n):
            if board[r][c] != 0:
                continue
            score = heatmap[r][c]
            if score > best_score:
                best_score = score
                best_cells = [(r, c)]
            elif score == best_score:
                best_cells.append((r, c))

    if best_cells and best_score > 0:
        return random.choice(best_cells)

    # If heatmap yields nothing (rare), use parity hunt (checkerboard) to maximize coverage.
    parity_cells = [(r, c) for r in range(n) for c in range(n) if board[r][c] == 0 and ((r + c) % 2 == 0)]
    if parity_cells:
        return random.choice(parity_cells)

    # Final fallback: pick any unknown cell
    unknowns = [(r, c) for r in range(n) for c in range(n) if board[r][c] == 0]
    if unknowns:
        return random.choice(unknowns)

    # If no unknowns left (shouldn't happen), return (0,0)
    return (0, 0)
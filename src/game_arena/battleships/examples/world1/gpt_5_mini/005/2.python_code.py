
import random
from collections import deque
from typing import List, Tuple

SHIP_LENGTHS = [5, 4, 3, 3, 2]
GRID_SIZE = 10


def _find_hit_clusters(board: List[List[int]]) -> List[List[Tuple[int, int]]]:
    visited = [[False] * GRID_SIZE for _ in range(GRID_SIZE)]
    clusters = []
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if board[r][c] == 1 and not visited[r][c]:
                # BFS for 4-connected cluster
                q = deque()
                q.append((r, c))
                visited[r][c] = True
                comp = []
                while q:
                    cr, cc = q.popleft()
                    comp.append((cr, cc))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE:
                            if board[nr][nc] == 1 and not visited[nr][nc]:
                                visited[nr][nc] = True
                                q.append((nr, nc))
                clusters.append(comp)
    return clusters


def _in_bounds(r: int, c: int) -> bool:
    return 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE


def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Choose a cell (row, col) to fire at next, given the current board knowledge.
    board: 10x10 list of lists with values: 0 unknown, -1 miss, 1 hit.
    Returns a tuple (row, col) for an unknown cell.
    """
    # Validate and prepare
    assert len(board) == GRID_SIZE and all(len(row) == GRID_SIZE for row in board)
    # Unknown cells mask
    unknown = [[board[r][c] == 0 for c in range(GRID_SIZE)] for r in range(GRID_SIZE)]
    unknown_cells = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE) if unknown[r][c]]
    if not unknown_cells:
        # No unknowns (shouldn't happen in normal play). Return arbitrary.
        return (0, 0)

    # Step 1: detect hit clusters and generate target-mode candidate extension cells
    clusters = _find_hit_clusters(board)
    candidate_set = set()
    # For each cluster, try to extend in inferred direction; if single hit, add its neighbors
    for comp in clusters:
        if len(comp) >= 2:
            rows = [r for r, _ in comp]
            cols = [c for _, c in comp]
            if all(r == rows[0] for r in rows):
                # horizontal
                r = rows[0]
                minc = min(cols)
                maxc = max(cols)
                for nc in (minc - 1, maxc + 1):
                    if _in_bounds(r, nc) and board[r][nc] == 0:
                        candidate_set.add((r, nc))
            elif all(c == cols[0] for c in cols):
                # vertical
                c = cols[0]
                minr = min(rows)
                maxr = max(rows)
                for nr in (minr - 1, maxr + 1):
                    if _in_bounds(nr, c) and board[nr][c] == 0:
                        candidate_set.add((nr, c))
            else:
                # Non-linear cluster (could be adjacent ships). Add neighbors of every hit.
                for (r, c) in comp:
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nr, nc = r + dr, c + dc
                        if _in_bounds(nr, nc) and board[nr][nc] == 0:
                            candidate_set.add((nr, nc))
        else:
            # single hit: consider all 4 neighbors
            r, c = comp[0]
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if _in_bounds(nr, nc) and board[nr][nc] == 0:
                    candidate_set.add((nr, nc))

    # Step 2: build heatmap from possible single-ship placements (avoid misses)
    heat = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
    for L in SHIP_LENGTHS:
        # horizontal placements
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE - L + 1):
                placement_cells = [(r, cc) for cc in range(c, c + L)]
                conflict = any(board[pr][pc] == -1 for pr, pc in placement_cells)
                if conflict:
                    continue
                # Valid placement; increment heat
                for pr, pc in placement_cells:
                    heat[pr][pc] += 1
        # vertical placements
        for c in range(GRID_SIZE):
            for r in range(GRID_SIZE - L + 1):
                placement_cells = [(rr, c) for rr in range(r, r + L)]
                conflict = any(board[pr][pc] == -1 for pr, pc in placement_cells)
                if conflict:
                    continue
                for pr, pc in placement_cells:
                    heat[pr][pc] += 1

    # Helper to choose best from a set of candidates according to heat (break ties randomly)
    def choose_best(cands):
        best_score = None
        best_list = []
        for (r, c) in cands:
            score = heat[r][c]
            if best_score is None or score > best_score:
                best_score = score
                best_list = [(r, c)]
            elif score == best_score:
                best_list.append((r, c))
        return random.choice(best_list) if best_list else None

    # If we have target candidates, choose among them (prioritize cluster extension)
    if candidate_set:
        # Filter to unknown just in case
        candidate_list = [pos for pos in candidate_set if board[pos[0]][pos[1]] == 0]
        if candidate_list:
            pick = choose_best(candidate_list)
            if pick:
                return pick

    # Otherwise, choose the unknown cell with maximum heat
    max_heat = -1
    best_cells = []
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if board[r][c] == 0:
                if heat[r][c] > max_heat:
                    max_heat = heat[r][c]
                    best_cells = [(r, c)]
                elif heat[r][c] == max_heat:
                    best_cells.append((r, c))
    if best_cells:
        return random.choice(best_cells)

    # As a last resort (should not occur), return a random unknown cell
    return random.choice(unknown_cells)

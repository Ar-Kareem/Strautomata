
import numpy as np
from collections import deque

# Battleship policy for 10x10 grid
# board values: 0 unknown, -1 miss, 1 hit
# returns (row, col) to fire at (must be currently unknown)

GRID_SIZE = 10
SHIP_LENGTHS = [5, 4, 3, 3, 2]


def _neighbors(r, c):
    if r > 0:
        yield (r - 1, c)
    if r < GRID_SIZE - 1:
        yield (r + 1, c)
    if c > 0:
        yield (r, c - 1)
    if c < GRID_SIZE - 1:
        yield (r, c + 1)


def _connected_components_of_hits(board_arr):
    visited = np.zeros_like(board_arr, dtype=bool)
    comps = []
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if board_arr[r, c] == 1 and not visited[r, c]:
                # BFS
                q = deque()
                q.append((r, c))
                visited[r, c] = True
                comp = []
                while q:
                    x, y = q.popleft()
                    comp.append((x, y))
                    for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                        if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                            if board_arr[nx, ny] == 1 and not visited[nx, ny]:
                                visited[nx, ny] = True
                                q.append((nx, ny))
                comps.append(comp)
    return comps


def _compute_heatmap(board_arr):
    heat = np.zeros_like(board_arr, dtype=int)
    # For each ship length, enumerate placements that do not cross misses (-1)
    for L in SHIP_LENGTHS:
        # horizontal
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE - L + 1):
                span = board_arr[r, c : c + L]
                if np.any(span == -1):
                    continue
                # placement allowed; add 1 to unknown cells (we only want to choose unknowns)
                for idx in range(L):
                    if board_arr[r, c + idx] == 0:
                        heat[r, c + idx] += 1
        # vertical
        for c in range(GRID_SIZE):
            for r in range(GRID_SIZE - L + 1):
                span = board_arr[r : r + L, c]
                if np.any(span == -1):
                    continue
                for idx in range(L):
                    if board_arr[r + idx, c] == 0:
                        heat[r + idx, c] += 1
    return heat


def _target_mode_choice(board_arr, heat):
    # Find connected hit components and try to finish them
    comps = _connected_components_of_hits(board_arr)
    if not comps:
        return None

    # Build a list of candidate target cells with priority
    candidates = []
    for comp in comps:
        comp = sorted(comp)  # deterministic
        if len(comp) >= 2:
            # determine orientation
            rows = [p[0] for p in comp]
            cols = [p[1] for p in comp]
            if len(set(rows)) == 1:
                # horizontal
                r = rows[0]
                minc = min(cols)
                maxc = max(cols)
                # left
                if minc - 1 >= 0 and board_arr[r, minc - 1] == 0:
                    candidates.append((r, minc - 1))
                # right
                if maxc + 1 < GRID_SIZE and board_arr[r, maxc + 1] == 0:
                    candidates.append((r, maxc + 1))
            elif len(set(cols)) == 1:
                # vertical
                c = cols[0]
                minr = min(rows)
                maxr = max(rows)
                if minr - 1 >= 0 and board_arr[minr - 1, c] == 0:
                    candidates.append((minr - 1, c))
                if maxr + 1 < GRID_SIZE and board_arr[maxr + 1, c] == 0:
                    candidates.append((maxr + 1, c))
            else:
                # L-shaped hits (shouldn't happen), treat all neighbouring unknowns
                for (x, y) in comp:
                    for nx, ny in _neighbors(x, y):
                        if board_arr[nx, ny] == 0:
                            candidates.append((nx, ny))
        else:
            # single hit: try neighbours
            r, c = comp[0]
            for nx, ny in _neighbors(r, c):
                if board_arr[nx, ny] == 0:
                    candidates.append((nx, ny))

    # Filter unique candidates preserving order
    seen = set()
    uniq_cands = []
    for cell in candidates:
        if cell not in seen:
            seen.add(cell)
            uniq_cands.append(cell)

    if not uniq_cands:
        return None

    # Choose candidate with highest heat value; tie-breaker smallest (row, col)
    best = None
    best_score = -1
    for (r, c) in uniq_cands:
        score = int(heat[r, c])
        if score > best_score or (score == best_score and (best is None or (r, c) < best)):
            best_score = score
            best = (r, c)
    return best


def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Given current knowledge of opponent board, return a coordinate (row, col)
    to fire at next. Board is 10x10 with values 0 (unknown), -1 (miss), 1 (hit).
    """
    # convert to numpy array for convenience
    arr = np.array(board, dtype=int)
    # Safety: ensure shape is 10x10
    if arr.shape != (GRID_SIZE, GRID_SIZE):
        # if not, try to handle flexible sizes but default to 10x10
        arr = arr.reshape((GRID_SIZE, GRID_SIZE))

    # If no unknowns left, just return something valid (shouldn't happen in normal play)
    unknowns = list(zip(*np.where(arr == 0)))
    if not unknowns:
        # choose any cell (fallback)
        return (0, 0)

    # Compute heatmap of likely ship positions
    heat = _compute_heatmap(arr)

    # If there are hits, enter target mode to try to finish ships
    if np.any(arr == 1):
        target_choice = _target_mode_choice(arr, heat)
        if target_choice is not None:
            return target_choice

    # If no target or none valid, choose the unknown cell with highest heat
    # If heat is all zeros (rare if many misses), fall back to parity or first unknown.
    max_heat = np.max(heat)
    if max_heat > 0:
        # pick smallest (row,col) among those with max heat
        candidates = list(zip(*np.where(heat == max_heat)))
        candidates.sort()
        return candidates[0]
    else:
        # fallback parity strategy: prefer checkerboard by (r+c) % 2 == 0
        # but choose among unknowns
        parity_candidates = [cell for cell in unknowns if (cell[0] + cell[1]) % 2 == 0]
        if parity_candidates:
            parity_candidates.sort()
            return parity_candidates[0]
        # else return first unknown
        unknowns.sort()
        return unknowns[0]

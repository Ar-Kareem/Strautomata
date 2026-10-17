
from typing import List, Tuple
from collections import deque, defaultdict

# Standard Battleship ship lengths for a 10x10 game
SHIP_LENGTHS = [5, 4, 3, 3, 2]
N = 10

def neighbors(r: int, c: int):
    for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)):
        rr, cc = r+dr, c+dc
        if 0 <= rr < N and 0 <= cc < N:
            yield rr, cc

def connected_components_of_hits(board: List[List[int]]):
    visited = [[False]*N for _ in range(N)]
    components = []
    for r in range(N):
        for c in range(N):
            if board[r][c] == 1 and not visited[r][c]:
                comp = []
                dq = deque()
                dq.append((r,c))
                visited[r][c] = True
                while dq:
                    x,y = dq.popleft()
                    comp.append((x,y))
                    for nx, ny in neighbors(x,y):
                        if board[nx][ny] == 1 and not visited[nx][ny]:
                            visited[nx][ny] = True
                            dq.append((nx,ny))
                components.append(comp)
    return components

def build_probability_map(board: List[List[int]]) -> List[List[int]]:
    # For each ship length and orientation, count all placements that do not overlap misses (-1)
    # and increment coverage counts for all cells in that placement.
    prob = [[0]*N for _ in range(N)]
    # For each ship length attempt placements
    for L in SHIP_LENGTHS:
        # horizontal placements
        for r in range(N):
            for c in range(N - L + 1):
                ok = True
                for k in range(L):
                    val = board[r][c+k]
                    if val == -1:  # can't place through a miss
                        ok = False
                        break
                if not ok:
                    continue
                # This placement is valid: increment cells
                for k in range(L):
                    prob[r][c+k] += 1
        # vertical placements
        for c in range(N):
            for r in range(N - L + 1):
                ok = True
                for k in range(L):
                    val = board[r+k][c]
                    if val == -1:
                        ok = False
                        break
                if not ok:
                    continue
                for k in range(L):
                    prob[r+k][c] += 1
    return prob

def first_zero_cell(board: List[List[int]]) -> Tuple[int,int]:
    for r in range(N):
        for c in range(N):
            if board[r][c] == 0:
                return (r,c)
    # fallback (shouldn't happen)
    return (0,0)

def policy(board: List[List[int]]) -> Tuple[int,int]:
    """
    Returns a target (row, col) on a 10x10 Battleship board given current knowledge.
    board values:
      0 -> unknown
     -1 -> miss
      1 -> hit
    Strategy:
      - Build a placement-based probability map for ship locations (avoid misses).
      - If there are any hits, enter target mode: find connected hit components and pick
        the most promising adjacent unknown cell (prefer extensions along known orientation).
      - Otherwise use the highest-probability unknown cell from the map.
    """
    # Basic checks
    # Ensure board is N x N
    if len(board) != N or any(len(row) != N for row in board):
        # Invalid board shape; just return first available cell
        return first_zero_cell(board)

    prob = build_probability_map(board)

    # Find all hits and their connected components
    components = connected_components_of_hits(board)

    # If there are hits, attempt to target around them (target mode)
    if components:
        best_candidate = None
        best_score = -1
        # For each hit component, generate candidate unknown cells to try to finish the ship.
        for comp in components:
            # Sort comp for deterministic behavior
            comp_sorted = sorted(comp)
            size = len(comp_sorted)
            rows = {r for r,c in comp_sorted}
            cols = {c for r,c in comp_sorted}

            candidates = []

            if size > 1:
                # Determine orientation if possible
                if len(rows) == 1:
                    # Horizontal
                    r = next(iter(rows))
                    minc = min(c for _,c in comp_sorted)
                    maxc = max(c for _,c in comp_sorted)
                    # extend left
                    if minc-1 >= 0 and board[r][minc-1] == 0:
                        candidates.append((r, minc-1))
                    # extend right
                    if maxc+1 < N and board[r][maxc+1] == 0:
                        candidates.append((r, maxc+1))
                elif len(cols) == 1:
                    # Vertical
                    c = next(iter(cols))
                    minr = min(r for r,_ in comp_sorted)
                    maxr = max(r for r,_ in comp_sorted)
                    if minr-1 >= 0 and board[minr-1][c] == 0:
                        candidates.append((minr-1, c))
                    if maxr+1 < N and board[maxr+1][c] == 0:
                        candidates.append((maxr+1, c))
                else:
                    # Unexpected shape (L-shape) - fallback to checking neighbors of each hit
                    for (r,c) in comp_sorted:
                        for nr, nc in neighbors(r,c):
                            if board[nr][nc] == 0:
                                candidates.append((nr,nc))
            else:
                # Single hit: try four neighbors
                (r,c) = comp_sorted[0]
                for nr, nc in neighbors(r,c):
                    if board[nr][nc] == 0:
                        candidates.append((nr,nc))

                # If no immediate neighbors unknown (rare), also allow cells adjacent to hits diagonally? skip.

            # If no candidates by orientation, try any adjacent zeros to the component
            if not candidates:
                for (r,c) in comp_sorted:
                    for nr, nc in neighbors(r,c):
                        if board[nr][nc] == 0:
                            candidates.append((nr,nc))

            # Evaluate candidates using probability map
            for cand in candidates:
                (cr,cc) = cand
                # only consider unknown cells
                if board[cr][cc] != 0:
                    continue
                score = prob[cr][cc]
                # tie-break deterministically by row,col (smaller is preferred)
                if score > best_score or (score == best_score and (best_candidate is None or cand < best_candidate)):
                    best_score = score
                    best_candidate = cand

        if best_candidate is not None:
            return best_candidate

    # Hunt mode: pick the unknown cell with the highest probability
    best = None
    best_score = -1
    for r in range(N):
        for c in range(N):
            if board[r][c] == 0:
                sc = prob[r][c]
                if sc > best_score or (sc == best_score and (best is None or (r,c) < best)):
                    best_score = sc
                    best = (r,c)

    if best is not None:
        return best

    # If probability map yields nothing (all zeros used?), return first unknown
    return first_zero_cell(board)

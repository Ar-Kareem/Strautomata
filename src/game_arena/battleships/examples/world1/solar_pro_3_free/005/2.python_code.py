
from typing import List, Tuple
from collections import deque

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """Return the next legal shot on a 10×10 Battleship board.

    The board contains:
        0 – un‑shot cell
        1 – hit
       -1 – miss
    The returned tuple (row, col) must point to an un‑shot cell.

    Heuristic:
        score = row_hits[row] + col_hits[col] + 3*adj_hits - 2*adj_water
               - dist_to_nearest_hit   (ignore if no hits yet)
    Tie‑break: smallest row, then smallest column.
    """
    ROWS, COLS = 10, 10

    # sanity check (optional, can be removed)
    if len(board) != ROWS or any(len(row) != COLS for row in board):
        raise ValueError("board must be a 10×10 matrix")

    # 1. Count hits per row and per column
    row_hits = [sum(cell == 1 for cell in row) for row in board]
    col_hits = [sum(board[i][j] == 1 for i in range(ROWS)) for j in range(COLS)]

    # 2. Distance map from nearest known hit (BFS)
    dist = [[float('inf')] * COLS for _ in range(ROWS)]
    if any(board[i][j] == 1 for i in range(ROWS) for j in range(COLS)):
        dq = deque()
        for i in range(ROWS):
            for j in range(COLS):
                if board[i][j] == 1:
                    dist[i][j] = 0
                    dq.append((i, j))
        # BFS propagation
        while dq:
            i, j = dq.popleft()
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ni, nj = i + di, j + dj
                if 0 <= ni < ROWS and 0 <= nj < COLS and dist[ni][nj] == float('inf'):
                    dist[ni][nj] = dist[i][j] + 1
                    dq.append((ni, nj))

    # 3. Evaluate all legal cells (board[r][c] == 0)
    best_score = -1
    best_cells: List[Tuple[int, int]] = []

    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c] != 0:          # already shot
                continue

            # Adjacent hits / water
            adj_hits = sum(board[nr][nc] == 1 for nr, nc in
                           [(r-1, c), (r+1, c), (r, c-1), (r, c+1)]
                           if 0 <= nr < ROWS and 0 <= nc < COLS)

            adj_water = sum(board[nr][nc] == -1 for nr, nc in
                           [(r-1, c), (r+1, c), (r, c-1), (r, c+1)]
                           if 0 <= nr < ROWS and 0 <= nc < COLS)

            base_score = row_hits[r] + col_hits[c] + 3 * adj_hits - 2 * adj_water

            # distance penalty only when hits exist
            if dist[r][c] != float('inf'):
                base_score -= dist[r][c]          # discourage far cells

            score = max(base_score, 0)           # ignore negative scores

            if score > best_score:
                best_score = score
                best_cells = [(r, c)]
            elif score == best_score:
                best_cells.append((r, c))

    # deterministic tie‑breaker: smallest row then smallest column
    best_cells.sort(key=lambda cell: (cell[0], cell[1]))
    return best_cells[0]

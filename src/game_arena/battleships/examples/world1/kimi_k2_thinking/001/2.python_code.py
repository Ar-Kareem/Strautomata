
def policy(board):
    """Return the next shot for a Battleship-like game on a 10×10 grid.

    board – 10×10 list of ints: 0 = unknown, -1 = miss, 1 = hit.
    Returns a tuple (row, col) with 0 ≤ row, col ≤ 9.
    """
    SIZE = 10

    # ------------------------------------------------------------------
    # 1.  Collect all hits and group them into orthogonal clusters
    # ------------------------------------------------------------------
    hits = [(r, c) for r in range(SIZE) for c in range(SIZE) if board[r][c] == 1]

    visited = set()
    clusters = []
    for (r, c) in hits:
        if (r, c) in visited:
            continue
        # simple BFS/DFS to collect one cluster
        stack = [(r, c)]
        cluster = []
        while stack:
            cr, cc = stack.pop()
            if (cr, cc) in visited:
                continue
            visited.add((cr, cc))
            cluster.append((cr, cc))
            for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                nr, nc = cr + dr, cc + dc
                if 0 <= nr < SIZE and 0 <= nc < SIZE and board[nr][nc] == 1 and (nr, nc) not in visited:
                    stack.append((nr, nc))
        clusters.append(cluster)

    # ------------------------------------------------------------------
    # 2.  For each cluster build the set of still‑unknown cells that could
    #     belong to that ship (internal gaps + extensions at both ends).
    # ------------------------------------------------------------------
    from collections import defaultdict
    candidate_counts = defaultdict(int)          # cell -> how many clusters suggest it

    for cluster in clusters:
        # ---- determine orientation -------------------------------------------------
        if len(cluster) == 1:
            orientation = None                     # single cell – orientation unknown
        else:
            rows = {pos[0] for pos in cluster}
            cols = {pos[1] for pos in cluster}
            if len(rows) == 1:
                orientation = 'horizontal'
            elif len(cols) == 1:
                orientation = 'vertical'
            else:
                orientation = None                 # should never happen

        # ---- collect candidate cells for this cluster -------------------------------
        candidates = set()

        if orientation == 'horizontal':
            row = cluster[0][0]
            cols = [pos[1] for pos in cluster]
            min_c = min(cols)
            max_c = max(cols)

            # internal unknown cells
            for col in range(min_c, max_c + 1):
                if board[row][col] == 0:
                    candidates.add((row, col))

            # possible extensions beyond the two ends
            left = min_c - 1
            if left >= 0 and board[row][left] == 0:
                candidates.add((row, left))
            right = max_c + 1
            if right < SIZE and board[row][right] == 0:
                candidates.add((row, right))

        elif orientation == 'vertical':
            col = cluster[0][1]
            rows = [pos[0] for pos in cluster]
            min_r = min(rows)
            max_r = max(rows)

            # internal unknown cells
            for r in range(min_r, max_r + 1):
                if board[r][col] == 0:
                    candidates.add((r, col))

            # extensions beyond the two ends
            top = min_r - 1
            if top >= 0 and board[top][col] == 0:
                candidates.add((top, col))
            bottom = max_r + 1
            if bottom < SIZE and board[bottom][col] == 0:
                candidates.add((bottom, col))

        else:   # single cell cluster – try the four orthogonal neighbours
            r, c = cluster[0]
            for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < SIZE and 0 <= nc < SIZE and board[nr][nc] == 0:
                    candidates.add((nr, nc))

        # increase the global score of every candidate cell
        for cell in candidates:
            candidate_counts[cell] += 1

    # ------------------------------------------------------------------
    # 3.  If we have candidates, pick the one with the highest score
    #     (tie‑break by smallest row, then column).
    # ------------------------------------------------------------------
    if candidate_counts:
        # list of (score, row, col)
        scored = [(count, r, c) for (r, c), count in candidate_counts.items()]
        scored.sort(key=lambda x: (-x[0], x[1], x[2]))
        for _, r, c in scored:
            if board[r][c] == 0:          # safety, should always be true
                return (r, c)

    # ------------------------------------------------------------------
    # 4.  No active cluster → hunt mode (checkerboard)
    # ------------------------------------------------------------------
    total_hits = len(hits)
    parity = total_hits % 2                # 0 → even squares, 1 → odd squares

    for r in range(SIZE):
        for c in range(SIZE):
            if board[r][c] == 0 and (r + c) % 2 == parity:
                return (r, c)

    # ------------------------------------------------------------------
    # 5.  Last resort – any still‑unknown cell (should never happen)
    # ------------------------------------------------------------------
    for r in range(SIZE):
        for c in range(SIZE):
            if board[r][c] == 0:
                return (r, c)

    # The board is completely known – this line is never reached in a legal game.
    return (0, 0)

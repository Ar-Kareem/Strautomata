
import random

# ----------------------------------------------------------------------
# Pre‑compute all possible ship placements (horizontal & vertical)
# ----------------------------------------------------------------------
SHIP_LENGTHS = [5, 4, 3, 3, 2]
PLACEMENTS = []

for L in SHIP_LENGTHS:
    # horizontal
    for r in range(10):
        for c in range(10 - L + 1):
            cells = [(r, c + i) for i in range(L)]
            PLACEMENTS.append(cells)
    # vertical
    for c in range(10):
        for r in range(10 - L + 1):
            cells = [(r + i, c) for i in range(L)]
            PLACEMENTS.append(cells)


# ----------------------------------------------------------------------
# Main policy
# ----------------------------------------------------------------------
def policy(board):
    """
    Returns a (row, col) tuple with a legal move.
    board[r][c] == 0 : unknown
    board[r][c] == -1: miss
    board[r][c] == 1 : hit
    """
    # ------------------------------------------------------------------
    # Gather basic information
    # ------------------------------------------------------------------
    unknowns = []
    hits = []
    for r in range(10):
        for c in range(10):
            val = board[r][c]
            if val == 0:
                unknowns.append((r, c))
            elif val == 1:
                hits.append((r, c))

    # ------------------------------------------------------------------
    # Compute a simple probability score for every unknown cell:
    # number of valid ship placements that contain the cell.
    # ------------------------------------------------------------------
    score = {}
    for placement in PLACEMENTS:
        # a placement is invalid if it contains a known miss
        valid = True
        for (r, c) in placement:
            if board[r][c] == -1:
                valid = False
                break
        if valid:
            for (r, c) in placement:
                if board[r][c] == 0:          # only unknown cells matter for shooting
                    score[(r, c)] = score.get((r, c), 0) + 1

    # ------------------------------------------------------------------
    # TARGET MODE – try to sink a ship that we have already hit
    # ------------------------------------------------------------------
    if hits:
        # ---- find clusters of adjacent hits --------------------------------
        clusters = []
        visited = set()
        for start in hits:
            if start in visited:
                continue
            stack = [start]
            cluster = []
            while stack:
                r, c = stack.pop()
                if (r, c) in visited:
                    continue
                visited.add((r, c))
                cluster.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 1 and (nr, nc) not in visited:
                        stack.append((nr, nc))
            clusters.append(cluster)

        # ---- generate candidate moves around each cluster -------------------
        candidate_moves = []
        for cluster in clusters:
            if len(cluster) == 1:
                r, c = cluster[0]
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                        candidate_moves.append((nr, nc))
            else:
                rows = {rc for rc, _ in cluster}
                cols = {c for _, c in cluster}
                if len(rows) == 1:                     # horizontal line
                    r = rows.pop()
                    cols_sorted = sorted([c for _, c in cluster])
                    min_c, max_c = cols_sorted[0], cols_sorted[-1]
                    if min_c > 0 and board[r][min_c - 1] == 0:
                        candidate_moves.append((r, min_c - 1))
                    if max_c < 9 and board[r][max_c + 1] == 0:
                        candidate_moves.append((r, max_c + 1))
                elif len(cols) == 1:                    # vertical line
                    c = cols.pop()
                    rows_sorted = sorted([r for r, _ in cluster])
                    min_r, max_r = rows_sorted[0], rows_sorted[-1]
                    if min_r > 0 and board[min_r - 1][c] == 0:
                        candidate_moves.append((min_r - 1, c))
                    if max_r < 9 and board[max_r + 1][c] == 0:
                        candidate_moves.append((max_r + 1, c))
                else:
                    # should not happen for a single ship, treat as isolated hits
                    for r, c in cluster:
                        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                                candidate_moves.append((nr, nc))

        # remove duplicates
        candidate_moves = list(set(candidate_moves))

        if candidate_moves:
            # choose the candidate with the highest probability score
            max_score = -1
            best = None
            best_candidates = []
            for cell in candidate_moves:
                s = score.get(cell, 0)
                if s > max_score:
                    max_score = s
                    best = cell
                    best_candidates = [cell]
                elif s == max_score:
                    best_candidates.append(cell)
            return random.choice(best_candidates)

    # ------------------------------------------------------------------
    # HUNT MODE – no hits (or no valid targets), search the board
    # ------------------------------------------------------------------
    if not unknowns:
        # No unknown cells left – this should not happen in a legal game.
        raise RuntimeError("No unknown cells to shoot at.")

    max_score = -1
    best = None
    best_candidates = []
    for cell in unknowns:
        s = score.get(cell, 0)
        if s > max_score:
            max_score = s
            best = cell
            best_candidates = [cell]
        elif s == max_score:
            best_candidates.append(cell)

    return random.choice(best_candidates)

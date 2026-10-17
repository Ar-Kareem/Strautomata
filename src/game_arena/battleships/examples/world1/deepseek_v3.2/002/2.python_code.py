
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Helper to compute probability map for unknown cells
    def compute_probability_map(board):
        prob = [[0]*10 for _ in range(10)]
        ship_lengths = [5, 4, 3, 3, 2]
        for r in range(10):
            for c in range(10):
                if board[r][c] != 0:
                    continue
                total = 0
                for L in ship_lengths:
                    # Horizontal placements that include (r,c)
                    # c0 is the start column, must satisfy c0 <= c <= c0+L-1
                    for c0 in range(max(0, c - L + 1), min(c, 10 - L) + 1):
                        valid = True
                        for k in range(L):
                            if board[r][c0 + k] == -1:
                                valid = False
                                break
                        if valid:
                            total += 1
                    # Vertical placements
                    for r0 in range(max(0, r - L + 1), min(r, 10 - L) + 1):
                        valid = True
                        for k in range(L):
                            if board[r0 + k][c] == -1:
                                valid = False
                                break
                        if valid:
                            total += 1
                prob[r][c] = total
        return prob

    # Collect all hits
    hits = [(r, c) for r in range(10) for c in range(10) if board[r][c] == 1]

    # Group hits into connected components (adjacent horizontally/vertically)
    visited = set()
    components = []
    for hit in hits:
        if hit in visited:
            continue
        stack = [hit]
        comp = []
        while stack:
            r, c = stack.pop()
            if (r, c) in visited:
                continue
            visited.add((r, c))
            comp.append((r, c))
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 1 and (nr, nc) not in visited:
                    stack.append((nr, nc))
        components.append(comp)

    # Filter out components that are already sunk (no possible extensions)
    unsunk = []
    for comp in components:
        if len(comp) == 1:
            r, c = comp[0]
            # Check if any adjacent cell is unknown
            has_unknown = False
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                    has_unknown = True
                    break
            if not has_unknown:
                continue  # sunk
        else:
            # Determine orientation
            rows = {r for r, _ in comp}
            cols = {c for _, c in comp}
            if len(rows) == 1:
                # horizontal
                row = next(iter(rows))
                cols_sorted = sorted(c for _, c in comp)
                left = cols_sorted[0]
                right = cols_sorted[-1]
                # Check left extension
                left_unknown = left - 1 >= 0 and board[row][left - 1] == 0
                # Check right extension
                right_unknown = right + 1 < 10 and board[row][right + 1] == 0
                if not left_unknown and not right_unknown:
                    continue  # sunk
            elif len(cols) == 1:
                # vertical
                col = next(iter(cols))
                rows_sorted = sorted(r for r, _ in comp)
                top = rows_sorted[0]
                bottom = rows_sorted[-1]
                top_unknown = top - 1 >= 0 and board[top - 1][col] == 0
                bottom_unknown = bottom + 1 < 10 and board[bottom + 1][col] == 0
                if not top_unknown and not bottom_unknown:
                    continue  # sunk
            else:
                # Should not happen for a single ship; treat as not sunk
                pass
        unsunk.append(comp)

    # If there are unsunk ships, generate target candidates
    if unsunk:
        # Sort by size (largest first)
        unsunk.sort(key=lambda c: len(c), reverse=True)
        candidates = []
        for comp in unsunk:
            if len(comp) == 1:
                r, c = comp[0]
                for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                        candidates.append((nr, nc))
            else:
                rows = {r for r, _ in comp}
                cols = {c for _, c in comp}
                if len(rows) == 1:
                    row = next(iter(rows))
                    cols_sorted = sorted(c for _, c in comp)
                    left = cols_sorted[0]
                    right = cols_sorted[-1]
                    if left - 1 >= 0 and board[row][left - 1] == 0:
                        candidates.append((row, left - 1))
                    if right + 1 < 10 and board[row][right + 1] == 0:
                        candidates.append((row, right + 1))
                elif len(cols) == 1:
                    col = next(iter(cols))
                    rows_sorted = sorted(r for r, _ in comp)
                    top = rows_sorted[0]
                    bottom = rows_sorted[-1]
                    if top - 1 >= 0 and board[top - 1][col] == 0:
                        candidates.append((top - 1, col))
                    if bottom + 1 < 10 and board[bottom + 1][col] == 0:
                        candidates.append((bottom + 1, col))
        if candidates:
            # Compute probability map for all unknown cells
            prob_map = compute_probability_map(board)
            # Pick the candidate with highest probability
            best = max(candidates, key=lambda cell: prob_map[cell[0]][cell[1]])
            return best

    # Hunt mode: no unsunk ships or no candidates
    prob_map = compute_probability_map(board)
    unknown_cells = [(r, c) for r in range(10) for c in range(10) if board[r][c] == 0]
    # Pick the cell with highest probability; break ties by row then column
    best = max(unknown_cells, key=lambda cell: (prob_map[cell[0]][cell[1]], -cell[0], -cell[1]))
    return best

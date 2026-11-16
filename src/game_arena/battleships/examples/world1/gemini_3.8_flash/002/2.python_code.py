
def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Computes the next optimal Battleship move on a 10x10 board.
    board: 10x10 grid with 0 = unknown, -1 = miss, 1 = hit.
    Returns: (row, col) tuple of integers in range 0-9.
    """
    # 1. Identify all hits on the board
    hits = {(r, c) for r in range(10) for c in range(10) if board[r][c] == 1}

    # 2. Group hits into 4-connected components
    visited = set()
    components = []
    for r, c in hits:
        if (r, c) not in visited:
            comp = []
            queue = [(r, c)]
            visited.add((r, c))
            for curr_r, curr_c in queue:
                comp.append((curr_r, curr_c))
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = curr_r + dr, curr_c + dc
                    if (nr, nc) in hits and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        queue.append((nr, nc))
            components.append(comp)

    # 3. Detect fully resolved (sunk) ships
    resolved_hits = set()
    resolved_lengths = []

    for comp in components:
        if len(comp) < 2:
            continue
        rows = {r for r, c in comp}
        cols = {c for r, c in comp}

        # Horizontal straight line
        if len(rows) == 1:
            r = next(iter(rows))
            min_c = min(cols)
            max_c = max(cols)
            if len(comp) == max_c - min_c + 1:
                left_blocked = (min_c == 0 or board[r][min_c - 1] == -1)
                right_blocked = (max_c == 9 or board[r][max_c + 1] == -1)
                if left_blocked and right_blocked:
                    for cell in comp:
                        resolved_hits.add(cell)
                    resolved_lengths.append(len(comp))

        # Vertical straight line
        elif len(cols) == 1:
            c = next(iter(cols))
            min_r = min(rows)
            max_r = max(rows)
            if len(comp) == max_r - min_r + 1:
                top_blocked = (min_r == 0 or board[min_r - 1][c] == -1)
                bottom_blocked = (max_r == 9 or board[max_r + 1][c] == -1)
                if top_blocked and bottom_blocked:
                    for cell in comp:
                        resolved_hits.add(cell)
                    resolved_lengths.append(len(comp))

    # 4. Deduce remaining fleet
    remaining_fleet = [5, 4, 3, 3, 2]
    for k in resolved_lengths:
        if k in remaining_fleet:
            remaining_fleet.remove(k)
        elif k == 6:
            for sub in [3, 3]:
                if sub in remaining_fleet:
                    remaining_fleet.remove(sub)
        elif k == 7:
            for sub in [4, 3]:
                if sub in remaining_fleet:
                    remaining_fleet.remove(sub)

    # 5. Determine active hits with open adjacent cells
    active_hits = hits - resolved_hits
    target_hits = set()
    for r, c in active_hits:
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                target_hits.add((r, c))
                break

    # 6. TARGET MODE
    if target_hits:
        candidate_cells = set()
        for r, c in target_hits:
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                    candidate_cells.add((nr, nc))

        target_scores = {cell: 0.0 for cell in candidate_cells}

        for length in remaining_fleet:
            # Horizontal placements
            for r in range(10):
                for c in range(11 - length):
                    cells = [(r, c + i) for i in range(length)]
                    if any(board[cr][cc] == -1 or (cr, cc) in resolved_hits for cr, cc in cells):
                        continue
                    h_count = sum(1 for cell in cells if cell in active_hits)
                    z_count = sum(1 for cr, cc in cells if board[cr][cc] == 0)
                    if h_count > 0 and z_count > 0:
                        weight = 10 ** (2 * h_count)
                        for cell in cells:
                            if cell in target_scores:
                                target_scores[cell] += weight

            # Vertical placements
            for c in range(10):
                for r in range(11 - length):
                    cells = [(r + i, c) for i in range(length)]
                    if any(board[cr][cc] == -1 or (cr, cc) in resolved_hits for cr, cc in cells):
                        continue
                    h_count = sum(1 for cell in cells if cell in active_hits)
                    z_count = sum(1 for cr, cc in cells if board[cr][cc] == 0)
                    if h_count > 0 and z_count > 0:
                        weight = 10 ** (2 * h_count)
                        for cell in cells:
                            if cell in target_scores:
                                target_scores[cell] += weight

        if candidate_cells:
            best_cell = max(
                candidate_cells,
                key=lambda cell: (
                    target_scores[cell],
                    -((cell[0] - 4.5) ** 2 + (cell[1] - 4.5) ** 2)
                )
            )
            return int(best_cell[0]), int(best_cell[1])

    # 7. HUNT MODE
    s_min = min(remaining_fleet) if remaining_fleet else 2
    hunt_scores = [[0 for _ in range(10)] for _ in range(10)]

    for length in remaining_fleet:
        # Horizontal placements
        for r in range(10):
            for c in range(11 - length):
                if all(board[r][c + i] == 0 for i in range(length)):
                    for i in range(length):
                        hunt_scores[r][c + i] += 1
        # Vertical placements
        for c in range(10):
            for r in range(11 - length):
                if all(board[r + i][c] == 0 for i in range(length)):
                    for i in range(length):
                        hunt_scores[r + i][c] += 1

    open_cells = [(r, c) for r in range(10) for c in range(10) if board[r][c] == 0]
    if not open_cells:
        return 0, 0

    # Maintain parity continuity
    misses = [(r, c) for r in range(10) for c in range(10) if board[r][c] == -1]
    miss_counts = [sum(1 for r, c in misses if (r + c) % s_min == p) for p in range(s_min)]
    preferred_parity = max(range(s_min), key=lambda p: (miss_counts[p], -p))

    parity_cells = [
        cell for cell in open_cells
        if (cell[0] + cell[1]) % s_min == preferred_parity and hunt_scores[cell[0]][cell[1]] > 0
    ]

    if not parity_cells:
        parity_cells = [cell for cell in open_cells if hunt_scores[cell[0]][cell[1]] > 0]

    if not parity_cells:
        parity_cells = open_cells

    best_cell = max(
        parity_cells,
        key=lambda cell: (
            hunt_scores[cell[0]][cell[1]],
            -((cell[0] - 4.5) ** 2 + (cell[1] - 4.5) ** 2)
        )
    )

    return int(best_cell[0]), int(best_cell[1])

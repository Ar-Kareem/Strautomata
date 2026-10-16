
def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Determines the next move for a Battleship game on a 10x10 grid.
    
    board: 10x10 grid where:
      0 = unknown
     -1 = miss
      1 = hit
      
    Returns (row, col) with board[row][col] == 0.
    """
    GRID_SIZE = 10
    ALL_SHIPS = [5, 4, 3, 3, 2]

    # 1. Identify Sunk Ships and Active Hits
    remaining_fleet = list(ALL_SHIPS)
    sunk_cells = set()

    # Detect horizontal sunk segments
    for r in range(GRID_SIZE):
        c = 0
        while c < GRID_SIZE:
            if board[r][c] == 1:
                start_c = c
                while c < GRID_SIZE and board[r][c] == 1:
                    c += 1
                end_c = c - 1
                length = end_c - start_c + 1

                left_blocked = (start_c == 0 or board[r][start_c - 1] == -1)
                right_blocked = (end_c == GRID_SIZE - 1 or board[r][end_c + 1] == -1)

                if (left_blocked and right_blocked and length >= 2) or length == 5:
                    if length in remaining_fleet:
                        remaining_fleet.remove(length)
                    for col in range(start_c, end_c + 1):
                        sunk_cells.add((r, col))
            else:
                c += 1

    # Detect vertical sunk segments
    for c in range(GRID_SIZE):
        r = 0
        while r < GRID_SIZE:
            if board[r][c] == 1:
                start_r = r
                while r < GRID_SIZE and board[r][c] == 1:
                    r += 1
                end_r = r - 1
                length = end_r - start_r + 1

                top_blocked = (start_r == 0 or board[start_r - 1][c] == -1)
                bottom_blocked = (end_r == GRID_SIZE - 1 or board[end_r + 1][c] == -1)

                if (top_blocked and bottom_blocked and length >= 2) or length == 5:
                    if length in remaining_fleet:
                        remaining_fleet.remove(length)
                    for row in range(start_r, end_r + 1):
                        sunk_cells.add((row, c))
            else:
                r += 1

    # Active hits are hits not accounted for by sunk ships
    active_hits = {
        (r, c)
        for r in range(GRID_SIZE)
        for c in range(GRID_SIZE)
        if board[r][c] == 1 and (r, c) not in sunk_cells
    }

    # 2. Target Mode: If active hits exist, target adjacent unknown cells
    target_candidates = set()
    for r, c in active_hits:
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE and board[nr][nc] == 0:
                target_candidates.add((nr, nc))

    if target_candidates:
        candidate_scores = {cand: 0.0 for cand in target_candidates}

        for ship_len in remaining_fleet:
            # Horizontal placements
            for r in range(GRID_SIZE):
                for c in range(GRID_SIZE - ship_len + 1):
                    placement = [(r, c + i) for i in range(ship_len)]
                    # Cannot cross misses or known sunk cells
                    if any(board[pr][pc] == -1 or (pr, pc) in sunk_cells for pr, pc in placement):
                        continue
                    active_count = sum(1 for p in placement if p in active_hits)
                    if active_count > 0:
                        weight = 100.0 ** active_count
                        for p in placement:
                            if p in candidate_scores:
                                candidate_scores[p] += weight

            # Vertical placements
            for c in range(GRID_SIZE):
                for r in range(GRID_SIZE - ship_len + 1):
                    placement = [(r + i, c) for i in range(ship_len)]
                    if any(board[pr][pc] == -1 or (pr, pc) in sunk_cells for pr, pc in placement):
                        continue
                    active_count = sum(1 for p in placement if p in active_hits)
                    if active_count > 0:
                        weight = 100.0 ** active_count
                        for p in placement:
                            if p in candidate_scores:
                                candidate_scores[p] += weight

        # Pick candidate with highest score, tie-breaking towards center
        best_target = max(
            target_candidates,
            key=lambda cell: (
                candidate_scores[cell],
                - (abs(cell[0] - 4.5) + abs(cell[1] - 4.5))
            )
        )
        return best_target

    # 3. Hunt Mode: Probability Density Function with Checkerboard Parity
    hunt_scores = [[0.0] * GRID_SIZE for _ in range(GRID_SIZE)]

    for ship_len in remaining_fleet:
        # Horizontal
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE - ship_len + 1):
                placement = [(r, c + i) for i in range(ship_len)]
                if all(board[pr][pc] == 0 for pr, pc in placement):
                    for pr, pc in placement:
                        hunt_scores[pr][pc] += 1.0

        # Vertical
        for c in range(GRID_SIZE):
            for r in range(GRID_SIZE - ship_len + 1):
                placement = [(r + i, c) for i in range(ship_len)]
                if all(board[pr][pc] == 0 for pr, pc in placement):
                    for pr, pc in placement:
                        hunt_scores[pr][pc] += 1.0

    # Prefer checkerboard parity cells ((r + c) % 2 == 0)
    parity_cells = [
        (r, c)
        for r in range(GRID_SIZE)
        for c in range(GRID_SIZE)
        if board[r][c] == 0 and (r + c) % 2 == 0
    ]

    candidates_to_eval = parity_cells if parity_cells else [
        (r, c)
        for r in range(GRID_SIZE)
        for c in range(GRID_SIZE)
        if board[r][c] == 0
    ]

    if candidates_to_eval:
        best_hunt = max(
            candidates_to_eval,
            key=lambda cell: (
                hunt_scores[cell[0]][cell[1]],
                - (abs(cell[0] - 4.5) + abs(cell[1] - 4.5))
            )
        )
        return best_hunt

    # Fallback to any remaining legal cell
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if board[r][c] == 0:
                return (r, c)

    return (0, 0)

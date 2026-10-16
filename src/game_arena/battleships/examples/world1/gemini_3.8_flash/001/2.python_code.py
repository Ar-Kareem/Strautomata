
def policy(board: list[list[int]]) -> tuple[int, int]:
    fleet_lengths = [5, 4, 3, 3, 2]
    
    # Identify known sunk ships to avoid targeting already-destroyed vessels
    sunk_cells = set()
    remaining_fleet = list(fleet_lengths)
    
    # 1. Detect fully identified ships
    # Length 5 ships: any contiguous segment of 5 hits is guaranteed sunk
    for r in range(10):
        for c in range(6):
            if all(board[r][c + i] == 1 for i in range(5)):
                if 5 in remaining_fleet:
                    sunk_cells.update((r, c + i) for i in range(5))
                    remaining_fleet.remove(5)
    for c in range(10):
        for r in range(6):
            if all(board[r + i][c] == 1 for i in range(5)):
                if 5 in remaining_fleet:
                    sunk_cells.update((r + i, c) for i in range(5))
                    remaining_fleet.remove(5)

    # Length 4, 3, 2 ships: check for maximal segments bounded by misses/edges/sunk cells
    def is_blocked(r: int, c: int) -> bool:
        return r < 0 or r >= 10 or c < 0 or c >= 10 or board[r][c] == -1 or (r, c) in sunk_cells

    for length in [4, 3, 2]:
        while length in remaining_fleet:
            found = False
            # Horizontal check
            for r in range(10):
                for c in range(11 - length):
                    segment = [(r, c + i) for i in range(length)]
                    if all(board[cr][cc] == 1 and (cr, cc) not in sunk_cells for cr, cc in segment):
                        if is_blocked(r, c - 1) and is_blocked(r, c + length):
                            sunk_cells.update(segment)
                            remaining_fleet.remove(length)
                            found = True
                            break
                if found:
                    break
            if found:
                continue
                
            # Vertical check
            for c in range(10):
                for r in range(11 - length):
                    segment = [(r + i, c) for i in range(length)]
                    if all(board[cr][cc] == 1 and (cr, cc) not in sunk_cells for cr, cc in segment):
                        if is_blocked(r - 1, c) and is_blocked(r + length, c):
                            sunk_cells.update(segment)
                            remaining_fleet.remove(length)
                            found = True
                            break
                if found:
                    break
            if not found:
                break

    # Unresolved hits are hits not attributed to a fully destroyed ship
    unresolved_hits = {
        (r, c) for r in range(10) for c in range(10)
        if board[r][c] == 1 and (r, c) not in sunk_cells
    }
    
    scores = [[0.0] * 10 for _ in range(10)]
    
    # --- TARGET MODE ---
    if unresolved_hits:
        for length in set(remaining_fleet):
            # Horizontal placements
            for r in range(10):
                for c in range(11 - length):
                    coords = [(r, c + i) for i in range(length)]
                    if any(board[cr][cc] == -1 or (cr, cc) in sunk_cells for cr, cc in coords):
                        continue
                    num_hits = sum(1 for pos in coords if pos in unresolved_hits)
                    num_zeros = sum(1 for cr, cc in coords if board[cr][cc] == 0)
                    if num_hits > 0 and num_zeros > 0:
                        weight = 100.0 ** num_hits
                        for cr, cc in coords:
                            if board[cr][cc] == 0:
                                scores[cr][cc] += weight
                                
            # Vertical placements
            for c in range(10):
                for r in range(11 - length):
                    coords = [(r + i, c) for i in range(length)]
                    if any(board[cr][cc] == -1 or (cr, cc) in sunk_cells for cr, cc in coords):
                        continue
                    num_hits = sum(1 for pos in coords if pos in unresolved_hits)
                    num_zeros = sum(1 for cr, cc in coords if board[cr][cc] == 0)
                    if num_hits > 0 and num_zeros > 0:
                        weight = 100.0 ** num_hits
                        for cr, cc in coords:
                            if board[cr][cc] == 0:
                                scores[cr][cc] += weight

        # If surrounding placements scored candidates, select the top candidate
        valid_targets = [(r, c) for r in range(10) for c in range(10) if board[r][c] == 0 and scores[r][c] > 0]
        if valid_targets:
            return max(
                valid_targets,
                key=lambda pos: (scores[pos[0]][pos[1]], -abs(pos[0] - 4.5) - abs(pos[1] - 4.5))
            )

        # Fallback for target mode: orthogonal neighbors of any unresolved hit
        neighbors = []
        for r, c in unresolved_hits:
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                    neighbors.append((nr, nc))
        if neighbors:
            return max(neighbors, key=lambda pos: -abs(pos[0] - 4.5) - abs(pos[1] - 4.5))

    # --- HUNT MODE ---
    # Global heatmap over unknown waters
    for length in remaining_fleet:
        # Horizontal
        for r in range(10):
            for c in range(11 - length):
                coords = [(r, c + i) for i in range(length)]
                if all(board[cr][cc] == 0 for cr, cc in coords):
                    for cr, cc in coords:
                        scores[cr][cc] += 1.0
        # Vertical
        for c in range(10):
            for r in range(11 - length):
                coords = [(r + i, c) for i in range(length)]
                if all(board[cr][cc] == 0 for cr, cc in coords):
                    for cr, cc in coords:
                        scores[cr][cc] += 1.0

    # Apply parity constraint according to the minimum surviving ship length
    l_min = min(remaining_fleet) if remaining_fleet else 2
    
    # Select the parity offset that has the most history or highest score density
    best_offset = 0
    max_offset_score = -1.0
    for offset in range(l_min):
        shot_count = sum(
            1 for r in range(10) for c in range(10)
            if board[r][c] != 0 and (r + c) % l_min == offset
        )
        total_score = sum(
            scores[r][c] for r in range(10) for c in range(10)
            if board[r][c] == 0 and (r + c) % l_min == offset
        )
        metric = shot_count * 1000.0 + total_score
        if metric > max_offset_score:
            max_offset_score = metric
            best_offset = offset

    candidates = [
        (r, c) for r in range(10) for c in range(10)
        if board[r][c] == 0 and (r + c) % l_min == best_offset and scores[r][c] > 0
    ]
    
    # If no candidates match parity with positive score, expand to all valid zeroes
    if not candidates:
        candidates = [(r, c) for r in range(10) for c in range(10) if board[r][c] == 0]

    return max(
        candidates,
        key=lambda pos: (scores[pos[0]][pos[1]], -abs(pos[0] - 4.5) - abs(pos[1] - 4.5))
    )

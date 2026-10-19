
def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Optimal Battleship policy using a 3-tier target/hunt hierarchy:
    1. Active line extensions
    2. Isolated hit exploration
    3. Checkerboard parity probability density map
    """
    GRID_SIZE = 10
    ALL_SHIPS = [5, 4, 3, 3, 2]

    # --- Step 1: Detect completed (sunk) hit segments ---
    # A contiguous line of hits with both ends blocked (by misses or edges) is completed.
    sunk_cells = set()
    sunk_lengths = []

    # Check horizontal segments of hits
    for r in range(GRID_SIZE):
        c = 0
        while c < GRID_SIZE:
            if board[r][c] == 1:
                start_c = c
                while c < GRID_SIZE and board[r][c] == 1:
                    c += 1
                end_c = c - 1
                length = end_c - start_c + 1
                if length >= 2:
                    left_blocked = (start_c == 0 or board[r][start_c - 1] == -1)
                    right_blocked = (end_c == GRID_SIZE - 1 or board[r][end_c + 1] == -1)
                    if left_blocked and right_blocked:
                        for col in range(start_c, end_c + 1):
                            sunk_cells.add((r, col))
                        sunk_lengths.append(length)
            else:
                c += 1

    # Check vertical segments of hits
    for c in range(GRID_SIZE):
        r = 0
        while r < GRID_SIZE:
            if board[r][c] == 1:
                start_r = r
                while r < GRID_SIZE and board[r][c] == 1:
                    r += 1
                end_r = r - 1
                length = end_r - start_r + 1
                if length >= 2:
                    top_blocked = (start_r == 0 or board[start_r - 1][c] == -1)
                    bottom_blocked = (end_r == GRID_SIZE - 1 or board[end_r + 1][c] == -1)
                    if top_blocked and bottom_blocked:
                        for row in range(start_r, end_r + 1):
                            sunk_cells.add((row, c))
                        sunk_lengths.append(length)
            else:
                r += 1

    # Determine remaining ships
    remaining_ships = list(ALL_SHIPS)
    for sl in sunk_lengths:
        if sl in remaining_ships:
            remaining_ships.remove(sl)
        else:
            # Match larger combinations if ships were placed end-to-end
            for s in sorted(remaining_ships, reverse=True):
                if s <= sl:
                    remaining_ships.remove(s)
                    break
    if not remaining_ships:
        remaining_ships = [2]

    # --- Step 2: Find active (unsunk) hits and lines ---
    active_hits = set()
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if board[r][c] == 1 and (r, c) not in sunk_cells:
                active_hits.add((r, c))

    # --- Tier 1: Active Lines (Length >= 2) with open ends ---
    active_lines = []

    # Horizontal active lines
    for r in range(GRID_SIZE):
        c = 0
        while c < GRID_SIZE:
            if (r, c) in active_hits:
                start_c = c
                while c < GRID_SIZE and (r, c) in active_hits:
                    c += 1
                end_c = c - 1
                length = end_c - start_c + 1
                if length >= 2:
                    open_ends = []
                    if start_c > 0 and board[r][start_c - 1] == 0:
                        open_ends.append(('left', (r, start_c - 1)))
                    if end_c < GRID_SIZE - 1 and board[r][end_c + 1] == 0:
                        open_ends.append(('right', (r, end_c + 1)))
                    if open_ends:
                        active_lines.append(('H', r, start_c, end_c, length, open_ends))
            else:
                c += 1

    # Vertical active lines
    for c in range(GRID_SIZE):
        r = 0
        while r < GRID_SIZE:
            if (r, c) in active_hits:
                start_r = r
                while r < GRID_SIZE and (r, c) in active_hits:
                    r += 1
                end_r = r - 1
                length = end_r - start_r + 1
                if length >= 2:
                    open_ends = []
                    if start_r > 0 and board[start_r - 1][c] == 0:
                        open_ends.append(('top', (start_r - 1, c)))
                    if end_r < GRID_SIZE - 1 and board[end_r + 1][c] == 0:
                        open_ends.append(('bottom', (end_r + 1, c)))
                    if open_ends:
                        active_lines.append(('V', c, start_r, end_r, length, open_ends))
            else:
                r += 1

    if active_lines:
        # Prioritize the longest active line
        active_lines.sort(key=lambda item: item[4], reverse=True)
        orientation, fixed, start_idx, end_idx, length, open_ends = active_lines[0]

        if len(open_ends) == 1:
            return open_ends[0][1]

        # Both ends are open: evaluate available room in each direction
        if orientation == 'H':
            r = fixed
            room_left = 0
            for col in range(start_idx - 1, -1, -1):
                if board[r][col] == 0:
                    room_left += 1
                else:
                    break
            room_right = 0
            for col in range(end_idx + 1, GRID_SIZE):
                if board[r][col] == 0:
                    room_right += 1
                else:
                    break

            left_pos = (r, start_idx - 1)
            right_pos = (r, end_idx + 1)
            return left_pos if room_left >= room_right else right_pos
        else:
            c = fixed
            room_top = 0
            for row in range(start_idx - 1, -1, -1):
                if board[row][c] == 0:
                    room_top += 1
                else:
                    break
            room_bottom = 0
            for row in range(end_idx + 1, GRID_SIZE):
                if board[row][c] == 0:
                    room_bottom += 1
                else:
                    break

            top_pos = (start_idx - 1, c)
            bottom_pos = (end_idx + 1, c)
            return top_pos if room_top >= room_bottom else bottom_pos

    # --- Tier 2: Isolated Active Hits (Length == 1) ---
    line_hit_cells = set()
    for _, _, start, end, _, _ in active_lines:
        pass  # active_lines is empty if we reach here

    isolated_hits = []
    for (r, c) in active_hits:
        has_adj_hit = False
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE and (nr, nc) in active_hits:
                has_adj_hit = True
                break
        if not has_adj_hit:
            isolated_hits.append((r, c))

    if isolated_hits:
        candidate_scores: dict[tuple[int, int], int] = {}
        for (hr, hc) in isolated_hits:
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = hr + dr, hc + dc
                if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE and board[nr][nc] == 0:
                    score = 0
                    is_horizontal = (dr == 0)
                    for ship_len in remaining_ships:
                        if is_horizontal:
                            min_c = min(hc, nc)
                            max_c = max(hc, nc)
                            for sc in range(max(0, max_c - ship_len + 1), min(GRID_SIZE - ship_len + 1, min_c + 1)):
                                valid = True
                                for col in range(sc, sc + ship_len):
                                    if board[hr][col] == -1 or (hr, col) in sunk_cells:
                                        valid = False
                                        break
                                if valid:
                                    score += 1
                        else:
                            min_r = min(hr, nr)
                            max_r = max(hr, nr)
                            for sr in range(max(0, max_r - ship_len + 1), min(GRID_SIZE - ship_len + 1, min_r + 1)):
                                valid = True
                                for row in range(sr, sr + ship_len):
                                    if board[row][hc] == -1 or (row, hc) in sunk_cells:
                                        valid = False
                                        break
                                if valid:
                                    score += 1
                    candidate_scores[(nr, nc)] = candidate_scores.get((nr, nc), 0) + score

        if candidate_scores:
            best_candidate = max(candidate_scores.keys(), key=lambda pos: candidate_scores[pos])
            return best_candidate

    # --- Tier 3: Hunt Mode (Probability Density Map with Checkerboard Parity) ---
    density = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]

    for ship_len in remaining_ships:
        # Horizontal placements
        for r in range(GRID_SIZE):
            for sc in range(GRID_SIZE - ship_len + 1):
                valid = True
                for c in range(sc, sc + ship_len):
                    if board[r][c] != 0:
                        valid = False
                        break
                if valid:
                    for c in range(sc, sc + ship_len):
                        density[r][c] += 1

        # Vertical placements
        for c in range(GRID_SIZE):
            for sr in range(GRID_SIZE - ship_len + 1):
                valid = True
                for r in range(sr, sr + ship_len):
                    if board[r][c] != 0:
                        valid = False
                        break
                if valid:
                    for r in range(sr, sr + ship_len):
                        density[r][c] += 1

    # Choose checkerboard parity that contains the most available open cells
    parity_counts = {0: 0, 1: 0}
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if board[r][c] == 0:
                parity_counts[(r + c) % 2] += 1

    pref_parity = 0 if parity_counts[0] >= parity_counts[1] else 1

    # Filter to highest density parity cells
    best_score = -1.0
    best_move = None

    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if board[r][c] == 0:
                is_pref = ((r + c) % 2 == pref_parity)
                center_dist = abs(r - 4.5) + abs(c - 4.5)
                # Heavily prioritize preferred parity, then density, then center proximity
                score = (density[r][c] * 10.0 - center_dist)
                if is_pref:
                    score += 10000.0

                if score > best_score:
                    best_score = score
                    best_move = (r, c)

    if best_move is not None:
        return best_move

    # Absolute safety fallback: return first available unknown cell
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if board[r][c] == 0:
                return (r, c)

    return (0, 0)

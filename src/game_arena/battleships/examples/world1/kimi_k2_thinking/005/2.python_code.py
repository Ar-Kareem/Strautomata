
def policy(board):
    """
    Return the next shot for the Battleship‑like game on a 10×10 grid.

    :param board: list of 10 lists, each element is
                  0 = unknown, -1 = miss, 1 = hit.
    :return: (row, col) with 0 ≤ row, col ≤ 9 and board[row][col] == 0.
    """
    # ----------------------------------------------------------------------
    # 1. Configuration
    # ----------------------------------------------------------------------
    SHIP_LENGTHS = [5, 4, 3, 3, 2]
    BOARD_SIZE = 10

    # ----------------------------------------------------------------------
    # 2. Probability map – count how many still‑possible placements cover each cell
    # ----------------------------------------------------------------------
    prob = [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)]

    for length in SHIP_LENGTHS:
        # ---- horizontal placements ------------------------------------------------
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE - length + 1):
                valid = True
                unknown_cells = []
                for dc in range(length):
                    val = board[r][c + dc]
                    if val == -1:                 # crosses a known miss → illegal
                        valid = False
                        break
                    if val == 0:
                        unknown_cells.append((r, c + dc))
                if not valid:
                    continue
                for ur, uc in unknown_cells:
                    prob[ur][uc] += 1

        # ---- vertical placements --------------------------------------------------
        for r in range(BOARD_SIZE - length + 1):
            for c in range(BOARD_SIZE):
                valid = True
                unknown_cells = []
                for dr in range(length):
                    val = board[r + dr][c]
                    if val == -1:
                        valid = False
                        break
                    if val == 0:
                        unknown_cells.append((r + dr, c))
                if not valid:
                    continue
                for ur, uc in unknown_cells:
                    prob[ur][uc] += 1

    # ----------------------------------------------------------------------
    # 3. Bonuses for cells that help finish a ship
    # ----------------------------------------------------------------------
    # 3a) Adjacent to any hit (large bonus)
    adj_bonus = [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    # 3b) Extension of a known line (even larger bonus)
    orient_bonus = [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)]

    # hit positions
    hits = [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) if board[r][c] == 1]

    # directions: up, down, left, right
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    # adjacency bonus
    for r, c in hits:
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board[nr][nc] == 0:
                adj_bonus[nr][nc] += 500   # 500 per adjacent hit

    # orientation bonus – only when at least two consecutive hits are aligned
    for r, c in hits:
        # count consecutive hits in each direction
        left = 0
        i = c - 1
        while i >= 0 and board[r][i] == 1:
            left += 1
            i -= 1
        right = 0
        i = c + 1
        while i < BOARD_SIZE and board[r][i] == 1:
            right += 1
            i += 1
        up = 0
        i = r - 1
        while i >= 0 and board[i][c] == 1:
            up += 1
            i -= 1
        down = 0
        i = r + 1
        while i < BOARD_SIZE and board[i][c] == 1:
            down += 1
            i += 1

        horizontal_len = 1 + left + right
        vertical_len = 1 + up + down

        if horizontal_len >= 2 and vertical_len >= 2:
            # ambiguous – several ships touching, ignore orientation bonus
            continue
        if horizontal_len >= 2:
            # ship lies horizontally, cells beyond the ends are promising
            leftmost = c - left
            rightmost = c + right
            if leftmost - 1 >= 0 and board[r][leftmost - 1] == 0:
                orient_bonus[r][leftmost - 1] += 2000
            if rightmost + 1 < BOARD_SIZE and board[r][rightmost + 1] == 0:
                orient_bonus[r][rightmost + 1] += 2000
        elif vertical_len >= 2:
            # ship lies vertically
            topmost = r - up
            bottommost = r + down
            if topmost - 1 >= 0 and board[topmost - 1][c] == 0:
                orient_bonus[topmost - 1][c] += 2000
            if bottommost + 1 < BOARD_SIZE and board[bottommost + 1][c] == 0:
                orient_bonus[bottommost + 1][c] += 2000
        # single hit → no orientation bonus (adjacency bonus already covers it)

    # ----------------------------------------------------------------------
    # 4. Decide which cell to shoot
    # ----------------------------------------------------------------------
    # Is there any unfished neighbourhood (i.e. are we in targeting mode)?
    have_active = any(
        adj_bonus[r][c] > 0 or orient_bonus[r][c] > 0
        for r in range(BOARD_SIZE) for c in range(BOARD_SIZE)
    )

    best_score = -1
    best_cell = None

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != 0:               # already fired here
                continue
            # In targeting mode we only consider cells with a bonus,
            # otherwise we stick to the parity pattern.
            if have_active:
                if adj_bonus[r][c] == 0 and orient_bonus[r][c] == 0:
                    continue
            else:
                if (r + c) % 2 != 0:           # checkerboard while scanning
                    continue

            score = prob[r][c] + adj_bonus[r][c] + orient_bonus[r][c]
            # Deterministic tie‑breaker (smallest row, then col)
            if score > best_score or (score == best_score and
                (best_cell is None or r < best_cell[0] or (r == best_cell[0] and c < best_cell[1]))):
                best_score = score
                best_cell = (r, c)

    # Fallback – should never happen, but guarantees a legal move.
    if best_cell is None:
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board[r][c] == 0:
                    return (r, c)

    return best_cell

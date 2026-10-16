
def policy(you, opponent) -> str:
    import itertools
    import copy

    # Build a 6x6 grid: +1 for us, -1 for opponent
    def build_grid():
        grid = [[0] * 6 for _ in range(6)]
        for r in range(6):
            for c in range(6):
                if you[r][c] == 1:
                    grid[r][c] = 1
                elif opponent[r][c] == 1:
                    grid[r][c] = -1
        return grid

    # Rotate a 3x3 quadrant in-place: L = anticlockwise, R = clockwise
    def rotate_quadrant(grid, quad, dir_char):
        # Determine 3x3 block boundaries
        row_start = 0 if quad < 2 else 3
        col_start = 0 if (quad % 2) * 3 else 3
        # Extract 3x3
        sub = [grid[row_start + i][col_start:col_start + 3] for i in range(3)]
        if dir_char == 'L':  # anticlockwise
            # (r, c) <- (2 - c, r)
            new_sub = [[0] * 3 for _ in range(3)]
            for r in range(3):
                for c in range(3):
                    new_sub[2 - c][r] = sub[r][c]
        else:  # dir_char == 'R', clockwise
            # (r, c) <- (c, 2 - r)
            new_sub = [[0] * 3 for _ in range(3)]
            for r in range(3):
                for c in range(3):
                    new_sub[c][2 - r] = sub[r][c]
        # Write back
        for i in range(3):
            grid[row_start + i][col_start:col_start + 3] = new_sub[i]

    # Evaluate a board with +1/-1 pieces.
    # Scores are based on line lengths without blocking.
    def score_board(grid):
        # Helper to count lines for a given player (+1 or -1)
        def line_lengths_for(player):
            lengths = []
            # Rows
            for r in range(6):
                c = 0
                while c < 6:
                    if grid[r][c] == player:
                        start = c
                        while c < 6 and grid[r][c] == player:
                            c += 1
                        lengths.append(c - start)
                    else:
                        c += 1
            # Columns
            for c in range(6):
                r = 0
                while r < 6:
                    if grid[r][c] == player:
                        start = r
                        while r < 6 and grid[r][c] == player:
                            r += 1
                        lengths.append(r - start)
                    else:
                        r += 1
            # Diagonal top-left to bottom-right
            for s in range(-5, 6):
                r = max(0, s)
                c = s - r
                cur_len = 0
                while r < 6 and c < 6:
                    if grid[r][c] == player:
                        cur_len += 1
                    else:
                        if cur_len > 0:
                            lengths.append(cur_len)
                        cur_len = 0
                    r += 1
                    c += 1
                if cur_len > 0:
                    lengths.append(cur_len)
            # Diagonal top-right to bottom-left
            for s in range(0, 11):
                r = min(5, s)
                c = s - r
                cur_len = 0
                while r >= 0 and c < 6:
                    if grid[r][c] == player:
                        cur_len += 1
                    else:
                        if cur_len > 0:
                            lengths.append(cur_len)
                        cur_len = 0
                    r -= 1
                    c += 1
                if cur_len > 0:
                    lengths.append(cur_len)
            return lengths

        my_lengths = line_lengths_for(1)
        op_lengths = line_lengths_for(-1)

        # Weights: quadratic reward for longer lines, strong penalty for opponent's lines
        def weights(ln):
            if ln >= 5:
                return 1000000
            if ln == 4:
                return 8000
            if ln == 3:
                return 600
            if ln == 2:
                return 80
            if ln == 1:
                return 10
            return 0

        my_score = sum(weights(l) for l in my_lengths)
        opp_score = sum(weights(l) for l in op_lengths)
        return my_score - opp_score

    # Compute longest line length for player on a board
    def longest_line_length(grid, player):
        best = 0
        # Rows
        for r in range(6):
            c = 0
            while c < 6:
                if grid[r][c] == player:
                    start = c
                    while c < 6 and grid[r][c] == player:
                        c += 1
                    best = max(best, c - start)
                else:
                    c += 1
        # Columns
        for c in range(6):
            r = 0
            while r < 6:
                if grid[r][c] == player:
                    start = r
                    while r < 6 and grid[r][c] == player:
                        r += 1
                    best = max(best, r - start)
                else:
                    r += 1
        # Diagonal top-left to bottom-right
        for s in range(-5, 6):
            r = max(0, s)
            c = s - r
            cur = 0
            while r < 6 and c < 6:
                if grid[r][c] == player:
                    cur += 1
                    best = max(best, cur)
                else:
                    cur = 0
                r += 1
                c += 1
        # Diagonal top-right to bottom-left
        for s in range(0, 11):
            r = min(5, s)
            c = s - r
            cur = 0
            while r >= 0 and c < 6:
                if grid[r][c] == player:
                    cur += 1
                    best = max(best, cur)
                else:
                    cur = 0
                r -= 1
                c += 1
        return best

    # Precompute list of empty cells
    empty_cells = []
    for r in range(6):
        for c in range(6):
            if you[r][c] == 0 and opponent[r][c] == 0:
                empty_cells.append((r, c))

    base_grid = build_grid()
    best_score = -10**18
    best_move = None

    # Try every legal move (place then rotate)
    for (r, c) in empty_cells:
        for quad in range(4):
            for dir_char in ('L', 'R'):
                # Build candidate grid
                cand = copy.deepcopy(base_grid)
                cand[r][c] = 1  # place our marble
                rotate_quadrant(cand, quad, dir_char)

                # If this move wins for us, return immediately
                if longest_line_length(cand, 1) >= 5:
                    return f"{r+1},{c+1},{quad},{dir_char}"

                # Evaluate position quality
                sc = score_board(cand)

                # Tweak score to break ties toward center placements and prefer R
                center_r, center_c = abs(r - 2.5), abs(c - 2.5)
                sc += (6 - center_r - center_c) * 0.01
                if dir_char == 'R':
                    sc += 0.005

                if sc > best_score:
                    best_score = sc
                    best_move = (r, c, quad, dir_char)

    # Fallback: choose a move that minimizes opponent's best line if all else equal
    if best_move is None:
        min_opp_len = 6
        for (r, c) in empty_cells:
            for quad in range(4):
                for dir_char in ('L', 'R'):
                    cand = copy.deepcopy(base_grid)
                    cand[r][c] = 1
                    rotate_quadrant(cand, quad, dir_char)
                    opp_len = longest_line_length(cand, -1)
                    my_len = longest_line_length(cand, 1)
                    if opp_len < min_opp_len or (opp_len == min_opp_len and my_len > longest_line_length(copy.deepcopy(base_grid), 1)):
                        min_opp_len = opp_len
                        best_move = (r, c, quad, dir_char)

    r, c, quad, dir_char = best_move
    return f"{r+1},{c+1},{quad},{dir_char}"

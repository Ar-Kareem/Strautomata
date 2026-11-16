
def policy(board: list[list[int]]) -> int:
    ROWS, COLS = 6, 7

    def get_valid_moves(b):
        return [c for c in range(COLS) if b[0][c] == 0]

    def drop(b, col, player):
        new_b = [row[:] for row in b]
        for r in range(ROWS - 1, -1, -1):
            if new_b[r][col] == 0:
                new_b[r][col] = player
                return new_b
        return None

    def is_win(b, player):
        # horizontal
        for r in range(ROWS):
            for c in range(COLS - 3):
                if all(b[r][c + i] == player for i in range(4)):
                    return True
        # vertical
        for c in range(COLS):
            for r in range(ROWS - 3):
                if all(b[r + i][c] == player for i in range(4)):
                    return True
        # diagonal /
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                if all(b[r + i][c + i] == player for i in range(4)):
                    return True
        # diagonal \
        for r in range(ROWS - 3):
            for c in range(3, COLS):
                if all(b[r + i][c - i] == player for i in range(4)):
                    return True
        return False

    def heuristic(b):
        score = 0
        col_w = [1, 2, 3, 5, 3, 2, 1]
        for c in range(COLS):
            for r in range(ROWS):
                cell = b[r][c]
                w = col_w[c]
                if cell == 1:
                    score += w
                elif cell == -1:
                    score -= w
        return score

    def get_ordered_moves(b, player):
        valid = get_valid_moves(b)
        win_moves = [c for c in valid if (nb := drop(b, c, player)) is not None and is_win(nb, player)]
        non_wins = [c for c in valid if c not in win_moves]
        ordered_non = sorted(non_wins, key=lambda c: (abs(c - 3), c))
        return win_moves + ordered_non

    def minimax(b, depth, alpha, beta, maximizing):
        if is_win(b, 1):
            return 10000
        if is_win(b, -1):
            return -10000
        if all(b[0][c] != 0 for c in range(COLS)):
            return 0
        if depth == 0:
            return heuristic(b)
        player = 1 if maximizing else -1
        best = -float('inf') if maximizing else float('inf')
        for c in get_ordered_moves(b, player):
            nb = drop(b, c, player)
            if nb is None:
                continue
            val = minimax(nb, depth - 1, alpha, beta, not maximizing)
            if maximizing:
                best = max(best, val)
                alpha = max(alpha, best)
            else:
                best = min(best, val)
                beta = min(beta, best)
            if beta <= alpha:
                break
        return best

    valid_moves = get_valid_moves(board)

    # Check for immediate win
    for c in valid_moves:
        nb = drop(board, c, 1)
        if nb is not None and is_win(nb, 1):
            return c

    # Check for immediate block
    for c in valid_moves:
        nb = drop(board, c, -1)
        if nb is not None and is_win(nb, -1):
            return c

    # Minimax
    best_score = -float('inf')
    best_col = valid_moves[0]
    move_order = get_ordered_moves(board, 1)
    for c in move_order:
        nb = drop(board, c, 1)
        if nb is None:
            continue
        score = minimax(nb, 10, -float('inf'), float('inf'), False)
        if score > best_score:
            best_score = score
            best_col = c

    return best_col

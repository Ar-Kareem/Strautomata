
def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Perfect-play Tic Tac Toe policy using minimax with alpha-beta pruning.

    board: 3x3 list of lists; 0 = empty, 1 = us, -1 = opponent.
    Returns (row, col) of an empty cell.
    """
    # Preferred move order: center, corners, then edges.
    PREFERENCE = [(1, 1), (0, 0), (0, 2), (2, 0), (2, 2),
                  (0, 1), (1, 0), (1, 2), (2, 1)]

    LINES = [
        ((0, 0), (0, 1), (0, 2)),
        ((1, 0), (1, 1), (1, 2)),
        ((2, 0), (2, 1), (2, 2)),
        ((0, 0), (1, 0), (2, 0)),
        ((0, 1), (1, 1), (2, 1)),
        ((0, 2), (1, 2), (2, 2)),
        ((0, 0), (1, 1), (2, 2)),
        ((0, 2), (1, 1), (2, 0)),
    ]

    def get_winner(b):
        for (a, bb, c) in LINES:
            s = b[a[0]][a[1]] + b[bb[0]][bb[1]] + b[c[0]][c[1]]
            if s == 3:
                return 1
            if s == -3:
                return -1
        return 0

    def ordered_empties(b):
        return [(r, c) for (r, c) in PREFERENCE if b[r][c] == 0]

    def minimax(b, maximizing, depth, alpha, beta):
        w = get_winner(b)
        if w == 1:
            return 10 - depth          # win as quickly as possible
        if w == -1:
            return depth - 10          # lose as slowly as possible
        moves = ordered_empties(b)
        if not moves:
            return 0                   # draw

        if maximizing:
            value = -float('inf')
            for (r, c) in moves:
                b[r][c] = 1
                value = max(value, minimax(b, False, depth + 1, alpha, beta))
                b[r][c] = 0
                alpha = max(alpha, value)
                if beta <= alpha:
                    break
            return value
        else:
            value = float('inf')
            for (r, c) in moves:
                b[r][c] = -1
                value = min(value, minimax(b, True, depth + 1, alpha, beta))
                b[r][c] = 0
                beta = min(beta, value)
                if beta <= alpha:
                    break
            return value

    # Root: choose the move with the best minimax value.
    best_move = None
    best_value = -float('inf')
    alpha = -float('inf')
    beta = float('inf')

    for (r, c) in ordered_empties(board):
        board[r][c] = 1
        value = minimax(board, False, 1, alpha, beta)
        board[r][c] = 0
        if value > best_value:
            best_value = value
            best_move = (r, c)
        alpha = max(alpha, best_value)

    if best_move is not None:
        return best_move

    # Safety fallback: first empty cell (should never be needed).
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                return (r, c)

    # No legal move exists; return something in range (game must be over).
    return (0, 0)

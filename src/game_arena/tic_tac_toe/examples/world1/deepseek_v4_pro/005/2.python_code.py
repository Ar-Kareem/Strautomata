
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Collect all empty cells
    empty_cells = [(i, j) for i in range(3) for j in range(3) if board[i][j] == 0]
    if not empty_cells:
        return (0, 0)  # Fallback (should not be called on a full board)

    def check_winner(b):
        for i in range(3):
            if b[i][0] == b[i][1] == b[i][2] != 0:
                return b[i][0]
            if b[0][i] == b[1][i] == b[2][i] != 0:
                return b[0][i]
        if b[0][0] == b[1][1] == b[2][2] != 0:
            return b[0][0]
        if b[0][2] == b[1][1] == b[2][0] != 0:
            return b[0][2]
        return 0

    def is_full(b):
        return all(b[i][j] != 0 for i in range(3) for j in range(3))

    def get_empty(b):
        return [(i, j) for i in range(3) for j in range(3) if b[i][j] == 0]

    def minimax(b, depth, is_maximizing, alpha, beta):
        winner = check_winner(b)
        if winner == 1:
            return 10 - depth
        if winner == -1:
            return depth - 10
        if is_full(b):
            return 0

        if is_maximizing:
            max_eval = -float('inf')
            for i, j in get_empty(b):
                b[i][j] = 1
                eval = minimax(b, depth + 1, False, alpha, beta)
                b[i][j] = 0
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for i, j in get_empty(b):
                b[i][j] = -1
                eval = minimax(b, depth + 1, True, alpha, beta)
                b[i][j] = 0
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval

    best_score = -float('inf')
    best_move = empty_cells[0]

    for i, j in empty_cells:
        board[i][j] = 1
        score = minimax(board, 0, False, -float('inf'), float('inf'))
        board[i][j] = 0
        if score > best_score:
            best_score = score
            best_move = (i, j)

    return best_move

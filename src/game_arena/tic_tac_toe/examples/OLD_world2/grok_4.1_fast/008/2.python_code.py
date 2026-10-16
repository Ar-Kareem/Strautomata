
def get_winner(board):
    n = 4
    # Check rows
    for i in range(n):
        s = board[i][0]
        if s != 0 and all(board[i][j] == s for j in range(n)):
            return s
    # Check columns
    for j in range(n):
        s = board[0][j]
        if s != 0 and all(board[i][j] == s for i in range(n)):
            return s
    # Check main diagonal (\)
    s = board[0][0]
    if s != 0 and all(board[i][i] == s for i in range(n)):
        return s
    # Check anti diagonal (/)
    s = board[0][n - 1]
    if s != 0 and all(board[i][n - 1 - i] == s for i in range(n)):
        return s
    return 0


def is_full(board):
    return all(cell != 0 for row in board for cell in row)


def minimax(board, player, alpha, beta, depth):
    winner = get_winner(board)
    if winner != 0:
        return (100 - depth) if winner == 1 else (depth - 100)
    if is_full(board):
        return 0

    empties = [(r, c) for r in range(4) for c in range(4) if board[r][c] == 0]
    empties.sort(key=lambda p: abs(p[0] - 1.5) + abs(p[1] - 1.5))

    if player == 1:
        max_eval = float('-inf')
        for r, c in empties:
            board[r][c] = player
            eval_score = minimax(board, -player, alpha, beta, depth + 1)
            board[r][c] = 0
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, max_eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for r, c in empties:
            board[r][c] = player
            eval_score = minimax(board, -player, alpha, beta, depth + 1)
            board[r][c] = 0
            min_eval = min(min_eval, eval_score)
            beta = min(beta, min_eval)
            if beta <= alpha:
                break
        return min_eval


def policy(board: list[list[int]]) -> tuple[int, int]:
    best_score = float('-inf')
    best_move = None
    empties = [(i, j) for i in range(4) for j in range(4) if board[i][j] == 0]
    empties.sort(key=lambda p: abs(p[0] - 1.5) + abs(p[1] - 1.5))
    for i, j in empties:
        board[i][j] = 1
        score = minimax(board, -1, float('-inf'), float('inf'), 0)
        board[i][j] = 0
        if score > best_score:
            best_score = score
            best_move = (i, j)
    return best_move


def get_winner(board: list[list[int]]) -> int:
    players = [1, -1]
    for p in players:
        # rows
        for r in range(4):
            if all(board[r][c] == p for c in range(4)):
                return p
        # columns
        for c in range(4):
            if all(board[r][c] == p for r in range(4)):
                return p
        # main diagonal
        if all(board[r][r] == p for r in range(4)):
            return p
        # anti diagonal
        if all(board[r][3 - r] == p for r in range(4)):
            return p
    return 0

def is_terminal(board: list[list[int]]) -> None:
    winner = get_winner(board)
    if winner != 0:
        return winner
    any_empty = any(board[r][c] == 0 for r in range(4) for c in range(4))
    if not any_empty:
        return 0
    return None

def minimax(board: list[list[int]], maximizing: bool, alpha: float, beta: float) -> int:
    score = is_terminal(board)
    if score is not None:
        return score
    if maximizing:
        max_eval = float('-inf')
        for r in range(4):
            for c in range(4):
                if board[r][c] == 0:
                    board[r][c] = 1
                    eval_score = minimax(board, False, alpha, beta)
                    board[r][c] = 0
                    max_eval = max(max_eval, eval_score)
                    alpha = max(alpha, max_eval)
                    if beta <= alpha:
                        return max_eval
        return max_eval
    else:
        min_eval = float('inf')
        for r in range(4):
            for c in range(4):
                if board[r][c] == 0:
                    board[r][c] = -1
                    eval_score = minimax(board, True, alpha, beta)
                    board[r][c] = 0
                    min_eval = min(min_eval, eval_score)
                    beta = min(beta, min_eval)
                    if beta <= alpha:
                        return min_eval
        return min_eval

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Check for immediate winning move
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                board[r][c] = 1
                if get_winner(board) == 1:
                    board[r][c] = 0
                    return (r, c)
                board[r][c] = 0
    # Check for immediate blocking move
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                board[r][c] = -1
                if get_winner(board) == -1:
                    board[r][c] = 0
                    return (r, c)
                board[r][c] = 0
    # Minimax for best move
    best_score = float('-inf')
    best_move = (0, 0)
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                board[r][c] = 1
                score = minimax(board, False, float('-inf'), float('inf'))
                board[r][c] = 0
                if score > best_score:
                    best_score = score
                    best_move = (r, c)
    return best_move

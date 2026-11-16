
def _check_win(board, player):
    """Check if the specified player has won."""
    # Check rows
    for r in range(3):
        if all(board[r][c] == player for c in range(3)):
            return True
    # Check columns
    for c in range(3):
        if all(board[r][c] == player for r in range(3)):
            return True
    # Check diagonals
    if all(board[i][i] == player for i in range(3)):
        return True
    if all(board[i][2 - i] == player for i in range(3)):
        return True
    return False


def _is_full(board):
    """Check if the board is full."""
    return all(cell != 0 for row in board for cell in row)


def _minimax(board, depth, is_maximizing, alpha, beta):
    """
    Minimax algorithm with alpha-beta pruning.
    Returns a score: positive for AI win, negative for opponent win, 0 for draw.
    """
    # Terminal states
    if _check_win(board, 1):
        return 10 - depth
    if _check_win(board, -1):
        return depth - 10
    if _is_full(board):
        return 0

    if is_maximizing:
        max_eval = float('-inf')
        for r in range(3):
            for c in range(3):
                if board[r][c] == 0:
                    board[r][c] = 1
                    eval = _minimax(board, depth + 1, False, alpha, beta)
                    board[r][c] = 0
                    max_eval = max(max_eval, eval)
                    alpha = max(alpha, eval)
                    if beta <= alpha:
                        break
        return max_eval
    else:
        min_eval = float('inf')
        for r in range(3):
            for c in range(3):
                if board[r][c] == 0:
                    board[r][c] = -1
                    eval = _minimax(board, depth + 1, True, alpha, beta)
                    board[r][c] = 0
                    min_eval = min(min_eval, eval)
                    beta = min(beta, eval)
                    if beta <= alpha:
                        break
        return min_eval


def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Determine the best move for the current board state.
    Player is 1, Opponent is -1.
    """
    # 1. Check for immediate winning move
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                board[r][c] = 1
                if _check_win(board, 1):
                    board[r][c] = 0
                    return (r, c)
                board[r][c] = 0

    # 2. Check for immediate blocking move (opponent would win)
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                board[r][c] = -1
                if _check_win(board, -1):
                    board[r][c] = 0
                    return (r, c)
                board[r][c] = 0

    # 3. Use minimax to find optimal move
    best_score = float('-inf')
    best_move = (0, 0)  # Default fallback

    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                board[r][c] = 1
                score = _minimax(board, 0, False, float('-inf'), float('inf'))
                board[r][c] = 0
                if score > best_score:
                    best_score = score
                    best_move = (r, c)

    return best_move

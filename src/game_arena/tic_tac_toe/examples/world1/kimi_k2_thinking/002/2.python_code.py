
def policy(board):
    """
    Determines the best move using minimax algorithm with alpha-beta pruning.
    Returns a tuple (row, col) representing the move.
    """
    # Check for immediate winning move
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                board[r][c] = 1
                if _check_winner(board) == 1:
                    board[r][c] = 0
                    return (r, c)
                board[r][c] = 0
    
    # Check for immediate block (opponent's winning move)
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                board[r][c] = -1
                if _check_winner(board) == -1:
                    board[r][c] = 0
                    return (r, c)
                board[r][c] = 0
    
    # Use minimax to determine best move
    best_score = -float('inf')
    best_move = None
    
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                board[r][c] = 1
                score = _minimax(board, False, -float('inf'), float('inf'))
                board[r][c] = 0
                
                if score > best_score:
                    best_score = score
                    best_move = (r, c)
    
    # Safety fallback (should never trigger if board has empty cells)
    if best_move is None:
        for r in range(3):
            for c in range(3):
                if board[r][c] == 0:
                    return (r, c)
    
    return best_move

def _check_winner(board):
    """
    Check if there's a winner.
    Returns 1 if player 1 wins, -1 if player -1 wins, 0 otherwise.
    """
    # Check rows
    for r in range(3):
        if board[r][0] == board[r][1] == board[r][2] != 0:
            return board[r][0]
    
    # Check columns
    for c in range(3):
        if board[0][c] == board[1][c] == board[2][c] != 0:
            return board[0][c]
    
    # Check diagonals
    if board[0][0] == board[1][1] == board[2][2] != 0:
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] != 0:
        return board[0][2]
    
    return 0

def _is_full(board):
    """Check if the board is full."""
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                return False
    return True

def _minimax(board, is_maximizing, alpha, beta):
    """
    Minimax with alpha-beta pruning.
    Returns the score of the board state.
    """
    # Check terminal states
    winner = _check_winner(board)
    if winner == 1:
        return 1
    elif winner == -1:
        return -1
    elif _is_full(board):
        return 0
    
    if is_maximizing:
        best_score = -float('inf')
        for r in range(3):
            for c in range(3):
                if board[r][c] == 0:
                    board[r][c] = 1
                    score = _minimax(board, False, alpha, beta)
                    board[r][c] = 0
                    best_score = max(best_score, score)
                    alpha = max(alpha, best_score)
                    if beta <= alpha:
                        break
        return best_score
    else:
        best_score = float('inf')
        for r in range(3):
            for c in range(3):
                if board[r][c] == 0:
                    board[r][c] = -1
                    score = _minimax(board, True, alpha, beta)
                    board[r][c] = 0
                    best_score = min(best_score, score)
                    beta = min(beta, best_score)
                    if beta <= alpha:
                        break
        return best_score

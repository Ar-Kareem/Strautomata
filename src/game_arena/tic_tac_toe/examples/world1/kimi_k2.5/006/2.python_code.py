
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Check for immediate winning move
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                board[r][c] = 1
                if _check_win(board, 1):
                    return (r, c)
                board[r][c] = 0
    
    # Check for opponent's immediate winning move and block it
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                board[r][c] = -1
                if _check_win(board, -1):
                    board[r][c] = 0
                    return (r, c)
                board[r][c] = 0
    
    # Use minimax to find the optimal move
    best_score = -float('inf')
    best_move = (0, 0)  # fallback, should be overwritten
    memo = {}
    
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                board[r][c] = 1
                score = _minimax(board, False, memo)
                board[r][c] = 0
                if score > best_score:
                    best_score = score
                    best_move = (r, c)
    
    return best_move


def _check_win(board: list[list[int]], player: int) -> bool:
    # Check rows
    for r in range(3):
        if board[r][0] == board[r][1] == board[r][2] == player:
            return True
    # Check columns
    for c in range(3):
        if board[0][c] == board[1][c] == board[2][c] == player:
            return True
    # Check diagonals
    if board[0][0] == board[1][1] == board[2][2] == player:
        return True
    if board[0][2] == board[1][1] == board[2][0] == player:
        return True
    return False


def _is_full(board: list[list[int]]) -> bool:
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                return False
    return True


def _minimax(board: list[list[int]], is_maximizing: bool, memo: dict) -> int:
    # Check terminal states
    if _check_win(board, 1):
        return 1
    if _check_win(board, -1):
        return -1
    if _is_full(board):
        return 0
    
    # Memoization key
    key = (tuple(tuple(row) for row in board), is_maximizing)
    if key in memo:
        return memo[key]
    
    if is_maximizing:
        best_score = -float('inf')
        for r in range(3):
            for c in range(3):
                if board[r][c] == 0:
                    board[r][c] = 1
                    score = _minimax(board, False, memo)
                    board[r][c] = 0
                    best_score = max(best_score, score)
    else:
        best_score = float('inf')
        for r in range(3):
            for c in range(3):
                if board[r][c] == 0:
                    board[r][c] = -1
                    score = _minimax(board, True, memo)
                    board[r][c] = 0
                    best_score = min(best_score, score)
    
    memo[key] = best_score
    return best_score

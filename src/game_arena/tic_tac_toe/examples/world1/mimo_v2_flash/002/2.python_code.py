
def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Implements a perfect Tic Tac Toe player using Minimax with Alpha-Beta pruning.
    """
    
    # Determine the player symbol (1 or -1)
    count_1 = sum(row.count(1) for row in board)
    count_minus_1 = sum(row.count(-1) for row in board)
    player = 1 if count_1 == count_minus_1 else -1

    def check_win(b):
        # Check rows and cols
        for i in range(3):
            if b[i][0] == b[i][1] == b[i][2] != 0: return b[i][0]
            if b[0][i] == b[1][i] == b[2][i] != 0: return b[0][i]
        # Check diagonals
        if b[0][0] == b[1][1] == b[2][2] != 0: return b[1][1]
        if b[0][2] == b[1][1] == b[2][0] != 0: return b[1][1]
        return 0

    def minimax(b, depth, alpha, beta, is_maximizing):
        result = check_win(b)
        
        # Terminal states
        if result == player: return 10 - depth
        if result == -player: return -10 + depth
        if all(b[r][c] != 0 for r in range(3) for c in range(3)): return 0

        if is_maximizing:
            max_eval = -float('inf')
            for r in range(3):
                for c in range(3):
                    if b[r][c] == 0:
                        b[r][c] = player
                        eval = minimax(b, depth + 1, alpha, beta, False)
                        b[r][c] = 0
                        max_eval = max(max_eval, eval)
                        alpha = max(alpha, eval)
                        if beta <= alpha:
                            break
            return max_eval
        else:
            min_eval = float('inf')
            for r in range(3):
                for c in range(3):
                    if b[r][c] == 0:
                        b[r][c] = -player
                        eval = minimax(b, depth + 1, alpha, beta, True)
                        b[r][c] = 0
                        min_eval = min(min_eval, eval)
                        beta = min(beta, eval)
                        if beta <= alpha:
                            break
            return min_eval

    best_score = -float('inf')
    best_move = None
    
    # Try all moves to find the best one
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                board[r][c] = player
                score = minimax(board, 0, -float('inf'), float('inf'), False)
                board[r][c] = 0
                
                if score > best_score:
                    best_score = score
                    best_move = (r, c)

    # If board is empty, force a move (minimax might return None if loop is skipped)
    if best_move is None:
        return (1, 1)
        
    return best_move


def policy(board: list[list[int]]) -> tuple[int, int]:
    def check_win(b, player):
        # Check rows and columns
        for i in range(3):
            if all(b[i][j] == player for j in range(3)):
                return True
            if all(b[j][i] == player for j in range(3)):
                return True
        # Check diagonals
        if all(b[i][i] == player for i in range(3)):
            return True
        if all(b[i][2-i] == player for i in range(3)):
            return True
        return False
    
    def is_full(b):
        return all(b[i][j] != 0 for i in range(3) for j in range(3))
    
    def minimax(b, is_maximizing, alpha, beta):
        if check_win(b, 1):
            return 1
        if check_win(b, -1):
            return -1
        if is_full(b):
            return 0
        
        if is_maximizing:
            max_eval = -float('inf')
            for r in range(3):
                for c in range(3):
                    if b[r][c] == 0:
                        b[r][c] = 1
                        eval = minimax(b, False, alpha, beta)
                        b[r][c] = 0
                        max_eval = max(max_eval, eval)
                        alpha = max(alpha, eval)
                        if beta <= alpha:
                            break
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for r in range(3):
                for c in range(3):
                    if b[r][c] == 0:
                        b[r][c] = -1
                        eval = minimax(b, True, alpha, beta)
                        b[r][c] = 0
                        min_eval = min(min_eval, eval)
                        beta = min(beta, eval)
                        if beta <= alpha:
                            break
                if beta <= alpha:
                    break
            return min_eval
    
    # Priority order for tie-breaking: center, corners, edges
    moves = []
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                if (r, c) == (1, 1):
                    priority = 2  # Center
                elif r in [0, 2] and c in [0, 2]:
                    priority = 1  # Corner
                else:
                    priority = 0  # Edge
                moves.append((priority, r, c))
    
    # Sort by priority descending
    moves.sort(reverse=True)
    
    # 1. Check for immediate win
    for _, r, c in moves:
        board[r][c] = 1
        win = check_win(board, 1)
        board[r][c] = 0
        if win:
            return (r, c)
    
    # 2. Check for immediate block (opponent win)
    for _, r, c in moves:
        board[r][c] = -1
        win = check_win(board, -1)
        board[r][c] = 0
        if win:
            return (r, c)
    
    # 3. Use minimax to find best move
    best_score = -float('inf')
    best_move = moves[0][1:] if moves else (0, 0)  # Fallback, should not happen
    
    for _, r, c in moves:
        board[r][c] = 1
        score = minimax(board, False, -float('inf'), float('inf'))
        board[r][c] = 0
        if score > best_score:
            best_score = score
            best_move = (r, c)
    
    return best_move


def policy(board: list[list[int]]) -> tuple[int, int]:
    """Optimal Tic Tac Toe policy using minimax with alpha-beta pruning."""
    
    def check_winner(b):
        for i in range(3):
            row_sum = b[i][0] + b[i][1] + b[i][2]
            col_sum = b[0][i] + b[1][i] + b[2][i]
            if row_sum == 3 or col_sum == 3: return 1
            if row_sum == -3 or col_sum == -3: return -1
        d1 = b[0][0] + b[1][1] + b[2][2]
        d2 = b[0][2] + b[1][1] + b[2][0]
        if d1 == 3 or d2 == 3: return 1
        if d1 == -3 or d2 == -3: return -1
        return 0
    
    def get_empty_cells(b):
        # Strategic order: center, corners, edges (improves alpha-beta pruning)
        priority = [(1,1), (0,0), (0,2), (2,0), (2,2), (0,1), (1,0), (1,2), (2,1)]
        return [(r,c) for r,c in priority if b[r][c] == 0]
    
    def minimax(b, maximizing, alpha, beta, depth):
        winner = check_winner(b)
        if winner == 1: return 10 - depth  # Prefer winning sooner
        if winner == -1: return depth - 10  # Prefer losing later
        
        empty = get_empty_cells(b)
        if not empty: return 0  # Draw
        
        if maximizing:
            best = -100
            for r, c in empty:
                b[r][c] = 1
                score = minimax(b, False, alpha, beta, depth + 1)
                b[r][c] = 0
                best = max(best, score)
                alpha = max(alpha, score)
                if beta <= alpha: break
            return best
        else:
            best = 100
            for r, c in empty:
                b[r][c] = -1
                score = minimax(b, True, alpha, beta, depth + 1)
                b[r][c] = 0
                best = min(best, score)
                beta = min(beta, score)
                if beta <= alpha: break
            return best
    
    # Make a copy to avoid modifying original
    b = [row[:] for row in board]
    empty = get_empty_cells(b)
    
    # Safety fallback: ensure we always return a valid move
    if not empty:
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    return (i, j)
        return (0, 0)
    
    # Find the best move using minimax
    best_move = empty[0]
    best_score = -100
    
    for r, c in empty:
        b[r][c] = 1
        score = minimax(b, False, -100, 100, 1)
        b[r][c] = 0
        if score > best_score:
            best_score = score
            best_move = (r, c)
    
    return best_move

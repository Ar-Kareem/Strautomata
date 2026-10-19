
def policy(board: list[list[int]]) -> tuple[int, int]:
    def check_winner(b):
        # Check rows, cols, diags
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

    def get_empty(b):
        return [(r, c) for r in range(3) for c in range(3) if b[r][c] == 0]

    def minimax(b, is_maximizing, alpha, beta, depth):
        winner = check_winner(b)
        if winner == 1:
            return 10 - depth  # Prefer winning sooner
        if winner == -1:
            return depth - 10  # Prefer losing later
        
        empty = get_empty(b)
        if not empty:
            return 0
        
        if is_maximizing:
            best = -float('inf')
            for r, c in empty:
                b[r][c] = 1
                val = minimax(b, False, alpha, beta, depth + 1)
                b[r][c] = 0
                best = max(best, val)
                alpha = max(alpha, val)
                if beta <= alpha:
                    break
            return best
        else:
            best = float('inf')
            for r, c in empty:
                b[r][c] = -1
                val = minimax(b, True, alpha, beta, depth + 1)
                b[r][c] = 0
                best = min(best, val)
                beta = min(beta, val)
                if beta <= alpha:
                    break
            return best

    # Make a mutable copy of the board
    b = [row[:] for row in board]
    
    empty = get_empty(b)
    
    # Safety: if only one move, take it
    if len(empty) == 1:
        return empty[0]
    
    best_score = -float('inf')
    best_move = empty[0]
    
    for r, c in empty:
        b[r][c] = 1
        score = minimax(b, False, -float('inf'), float('inf'), 1)
        b[r][c] = 0
        if score > best_score:
            best_score = score
            best_move = (r, c)
    
    return best_move

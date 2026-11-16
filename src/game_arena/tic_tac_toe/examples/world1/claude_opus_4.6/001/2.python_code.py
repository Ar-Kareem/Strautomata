
def policy(board: list[list[int]]) -> tuple[int, int]:
    def get_empty_cells(b):
        cells = []
        for i in range(3):
            for j in range(3):
                if b[i][j] == 0:
                    cells.append((i, j))
        return cells

    def check_winner(b):
        # Check rows
        for i in range(3):
            if b[i][0] == b[i][1] == b[i][2] != 0:
                return b[i][0]
        # Check cols
        for j in range(3):
            if b[0][j] == b[1][j] == b[2][j] != 0:
                return b[0][j]
        # Check diagonals
        if b[0][0] == b[1][1] == b[2][2] != 0:
            return b[0][0]
        if b[0][2] == b[1][1] == b[2][0] != 0:
            return b[0][2]
        return 0

    def minimax(b, is_maximizing, alpha, beta):
        winner = check_winner(b)
        if winner == 1:
            return 1
        if winner == -1:
            return -1
        
        empty = get_empty_cells(b)
        if not empty:
            return 0

        if is_maximizing:
            best = -2
            for (r, c) in empty:
                b[r][c] = 1
                val = minimax(b, False, alpha, beta)
                b[r][c] = 0
                best = max(best, val)
                alpha = max(alpha, val)
                if beta <= alpha:
                    break
            return best
        else:
            best = 2
            for (r, c) in empty:
                b[r][c] = -1
                val = minimax(b, True, alpha, beta)
                b[r][c] = 0
                best = min(best, val)
                beta = min(beta, val)
                if beta <= alpha:
                    break
            return best

    # Make a deep copy of the board to avoid modifying the original
    b = [row[:] for row in board]
    
    empty = get_empty_cells(b)
    
    if not empty:
        # Should not happen if called correctly
        return (0, 0)
    
    # We are player 1 (maximizing)
    best_score = -2
    best_move = empty[0]
    
    for (r, c) in empty:
        b[r][c] = 1
        score = minimax(b, False, -2, 2)
        b[r][c] = 0
        if score > best_score:
            best_score = score
            best_move = (r, c)
            if best_score == 1:
                break  # Can't do better than winning
    
    return best_move

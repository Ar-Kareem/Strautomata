
def policy(board):
    def check_winner(b):
        # Check rows, columns, and diagonals for a winner
        lines = [
            [b[0][0], b[0][1], b[0][2]],
            [b[1][0], b[1][1], b[1][2]],
            [b[2][0], b[2][1], b[2][2]],
            [b[0][0], b[1][0], b[2][0]],
            [b[0][1], b[1][1], b[2][1]],
            [b[0][2], b[1][2], b[2][2]],
            [b[0][0], b[1][1], b[2][2]],
            [b[0][2], b[1][1], b[2][0]]
        ]
        for line in lines:
            if line == [1, 1, 1]:
                return 1
            if line == [-1, -1, -1]:
                return -1
        return 0  # No winner
    
    def is_terminal(b):
        if check_winner(b) != 0:
            return True
        for row in b:
            for cell in row:
                if cell == 0:
                    return False
        return True  # Draw
    
    def available_moves(b):
        # Return moves in priority order: center, corners, edges
        move_priority = [
            (1, 1),
            (0, 0), (0, 2), (2, 0), (2, 2),
            (0, 1), (1, 0), (1, 2), (2, 1)
        ]
        return [(i, j) for (i, j) in move_priority if b[i][j] == 0]
    
    def minimax(b, depth, alpha, beta, is_maximizing):
        winner = check_winner(b)
        if winner == 1:
            return 10 - depth
        if winner == -1:
            return -10 + depth
        if is_terminal(b):
            return 0
        
        if is_maximizing:
            best_score = -float('inf')
            for move in available_moves(b):
                i, j = move
                b[i][j] = 1
                score = minimax(b, depth + 1, alpha, beta, False)
                b[i][j] = 0
                best_score = max(score, best_score)
                alpha = max(alpha, best_score)
                if beta <= alpha:
                    break
            return best_score
        else:
            best_score = float('inf')
            for move in available_moves(b):
                i, j = move
                b[i][j] = -1
                score = minimax(b, depth + 1, alpha, beta, True)
                b[i][j] = 0
                best_score = min(score, best_score)
                beta = min(beta, best_score)
                if beta <= alpha:
                    break
            return best_score
    
    best_score = -float('inf')
    best_move = None
    alpha = -float('inf')
    beta = float('inf')
    moves = available_moves(board)
    
    for move in moves:
        i, j = move
        board[i][j] = 1
        score = minimax(board, 0, alpha, beta, False)
        board[i][j] = 0
        if score > best_score:
            best_score = score
            best_move = move
        alpha = max(alpha, best_score)
        if beta <= alpha:
            break
    
    return best_move if best_move else moves[0]  # Fallback to first available

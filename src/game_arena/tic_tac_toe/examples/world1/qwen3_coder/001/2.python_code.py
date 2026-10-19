
import copy

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert board to work with minimax (1 is me, -1 is opponent)
    # We want to maximize for player 1
    
    def check_winner(b):
        # Check rows
        for row in b:
            if row[0] == row[1] == row[2] != 0:
                return row[0]
        
        # Check columns
        for col in range(3):
            if b[0][col] == b[1][col] == b[2][col] != 0:
                return b[0][col]
        
        # Check diagonals
        if b[0][0] == b[1][1] == b[2][2] != 0:
            return b[0][0]
        if b[0][2] == b[1][1] == b[2][0] != 0:
            return b[0][2]
        
        return 0  # No winner
    
    def is_board_full(b):
        for row in b:
            for cell in row:
                if cell == 0:
                    return False
        return True
    
    def minimax(b, depth, is_maximizing, alpha, beta):
        winner = check_winner(b)
        
        # Terminal states
        if winner == 1:  # I win
            return 10 - depth
        elif winner == -1:  # Opponent wins
            return depth - 10
        elif is_board_full(b):  # Tie
            return 0
        
        if is_maximizing:  # My turn (1)
            max_eval = float('-inf')
            for i in range(3):
                for j in range(3):
                    if b[i][j] == 0:
                        b[i][j] = 1
                        eval_score = minimax(b, depth + 1, False, alpha, beta)
                        b[i][j] = 0
                        max_eval = max(max_eval, eval_score)
                        alpha = max(alpha, eval_score)
                        if beta <= alpha:
                            break
                if beta <= alpha:
                    break
            return max_eval
        else:  # Opponent's turn (-1)
            min_eval = float('inf')
            for i in range(3):
                for j in range(3):
                    if b[i][j] == 0:
                        b[i][j] = -1
                        eval_score = minimax(b, depth + 1, True, alpha, beta)
                        b[i][j] = 0
                        min_eval = min(min_eval, eval_score)
                        beta = min(beta, eval_score)
                        if beta <= alpha:
                            break
                if beta <= alpha:
                    break
            return min_eval
    
    # First, check if we can win immediately
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = 1
                if check_winner(board) == 1:
                    board[i][j] = 0  # Reset
                    return (i, j)
                board[i][j] = 0  # Reset
    
    # Second, check if opponent can win and block them
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = -1
                if check_winner(board) == -1:
                    board[i][j] = 0  # Reset
                    return (i, j)
                board[i][j] = 0  # Reset
    
    # Otherwise, use minimax to find the best move
    best_score = float('-inf')
    best_move = None
    
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = 1
                score = minimax(board, 0, False, float('-inf'), float('inf'))
                board[i][j] = 0
                
                if score > best_score:
                    best_score = score
                    best_move = (i, j)
    
    # If no move found (shouldn't happen in normal play), pick first available
    if best_move is None:
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    return (i, j)
    
    return best_move

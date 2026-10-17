
import sys

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Returns the best move for the AI in a 3x3 Tic Tac Toe game.
    The AI plays as player 1 (value 1) and the opponent is -1.
    The function uses the minimax algorithm with alpha-beta pruning to find the optimal move.
    """
    # Determine who the AI is and who the opponent is based on board context.
    # Although the problem statement implies AI is 1, we check counts to handle ambiguity.
    ai_val = 1
    opp_val = -1
    
    # Helper to count existing pieces
    count_ai = sum(row.count(ai_val) for row in board)
    count_opp = sum(row.count(opp_val) for row in board)

    # If counts imply the AI might actually be -1 (if API provider mixed up), switch
    if count_opp > count_ai:
        ai_val, opp_val = -1, 1
    
    # Helper to check for a winner
    def check_winner(b):
        # Rows and Cols
        for i in range(3):
            if b[i][0] == b[i][1] == b[i][2] != 0: return b[i][0]
            if b[0][i] == b[1][i] == b[2][i] != 0: return b[0][i]
        # Diagonals
        if b[0][0] == b[1][1] == b[2][2] != 0: return b[0][0]
        if b[0][2] == b[1][1] == b[2][0] != 0: return b[0][2]
        return 0

    # Minimax algorithm with Alpha-Beta Pruning
    # Returns evaluation score
    def minimax(b, is_maximizing, alpha, beta):
        winner = check_winner(b)
        if winner == ai_val:
            return 10
        if winner == opp_val:
            return -10
        
        # Check for draw (no empty spaces)
        is_full = True
        for r in range(3):
            for c in range(3):
                if b[r][c] == 0:
                    is_full = False
                    break
            if not is_full: break
        if is_full:
            return 0
        
        if is_maximizing:
            max_eval = -float('inf')
            for r in range(3):
                for c in range(3):
                    if b[r][c] == 0:
                        b[r][c] = ai_val
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
                        b[r][c] = opp_val
                        eval = minimax(b, True, alpha, beta)
                        b[r][c] = 0
                        min_eval = min(min_eval, eval)
                        beta = min(beta, eval)
                        if beta <= alpha:
                            break
                if beta <= alpha:
                    break
            return min_eval

    # Check for immediate win
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                board[r][c] = ai_val
                if check_winner(board) == ai_val:
                    board[r][c] = 0
                    return (r, c)
                board[r][c] = 0

    # Check for immediate block
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                board[r][c] = opp_val
                if check_winner(board) == opp_val:
                    board[r][c] = 0
                    return (r, c)
                board[r][c] = 0

    # Find best move using minimax
    best_score = -float('inf')
    best_move = (-1, -1)
    
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                board[r][c] = ai_val
                score = minimax(board, False, -float('inf'), float('inf'))
                board[r][c] = 0
                if score > best_score:
                    best_score = score
                    best_move = (r, c)

    return best_move

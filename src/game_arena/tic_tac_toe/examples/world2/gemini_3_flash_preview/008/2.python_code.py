
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    4x4 Tic Tac Toe AI using Minimax with Alpha-Beta Pruning.
    """
    
    MY_ID = 1
    OPP_ID = -1

    def check_winner(b):
        # Rows and Columns
        for i in range(4):
            if abs(sum(b[i])) == 4:
                return b[i][0]
            col_sum = sum(b[j][i] for j in range(4))
            if abs(col_sum) == 4:
                return b[0][i]
        
        # Diagonals
        diag1 = sum(b[i][i] for i in range(4))
        if abs(diag1) == 4:
            return b[0][0]
        diag2 = sum(b[i][3-i] for i in range(4))
        if abs(diag2) == 4:
            return b[0][3]
            
        return 0

    def evaluate(b):
        winner = check_winner(b)
        if winner == MY_ID: return 1000
        if winner == OPP_ID: return -1000
        
        score = 0
        lines = []
        # Gather all possible lines
        for i in range(4):
            lines.append(b[i]) # Row
            lines.append([b[j][i] for j in range(4)]) # Col
        lines.append([b[i][i] for i in range(4)]) # Diag 1
        lines.append([b[i][3-i] for i in range(4)]) # Diag 2
        
        for line in lines:
            my_count = line.count(MY_ID)
            opp_count = line.count(OPP_ID)
            
            if my_count > 0 and opp_count == 0:
                score += (10 ** (my_count - 1))
            elif opp_count > 0 and my_count == 0:
                score -= (10 ** (opp_count - 1))
        return score

    def minimax(b, depth, alpha, beta, maximizing):
        win = check_winner(b)
        if win != 0 or depth == 0:
            return evaluate(b)
            
        empty_cells = [(r, c) for r in range(4) for c in range(4) if b[r][c] == 0]
        if not empty_cells:
            return 0

        if maximizing:
            max_eval = -float('inf')
            for r, c in empty_cells:
                b[r][c] = MY_ID
                eval = minimax(b, depth - 1, alpha, beta, False)
                b[r][c] = 0
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha: break
            return max_eval
        else:
            min_eval = float('inf')
            for r, c in empty_cells:
                b[r][c] = OPP_ID
                eval = minimax(b, depth - 1, alpha, beta, True)
                b[r][c] = 0
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha: break
            return min_eval

    # Root of the decision tree
    best_move = None
    best_value = -float('inf')
    
    moves = [(r, c) for r in range(4) for c in range(4) if board[r][c] == 0]
    
    # If board is empty, take a center square
    if len(moves) == 16:
        return (1, 1)

    # Heuristic sort moves: check for immediate wins/blocks first to optimize pruning
    for r, c in moves:
        board[r][c] = MY_ID
        if check_winner(board) == MY_ID:
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0

    for r, c in moves:
        board[r][c] = OPP_ID
        if check_winner(board) == OPP_ID:
            board[r][c] = 0
            # We must block this, but continue search to find best overall move
        board[r][c] = 0

    # Normal Minimax Search
    for r, c in moves:
        board[r][c] = MY_ID
        # Depth 4 is safe for 1 second in a 4x4
        move_val = minimax(board, 4, -float('inf'), float('inf'), False)
        board[r][c] = 0
        
        if move_val > best_value:
            best_value = move_val
            best_move = (r, c)
            
    return best_move if best_move else moves[0]

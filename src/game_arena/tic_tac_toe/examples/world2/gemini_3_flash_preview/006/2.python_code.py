
import math

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Determines the best move for the player (1) on a 4x4 board.
    Uses Minimax with Alpha-Beta pruning and a depth-limited heuristic.
    """
    
    def check_winner(b):
        # Rows and Columns
        for i in range(4):
            if abs(sum(b[i])) == 4:
                return b[i][0]
            if abs(sum(b[j][i] for j in range(4))) == 4:
                return b[0][i]
        
        # Diagonals
        if abs(sum(b[i][i] for i in range(4))) == 4:
            return b[0][0]
        if abs(sum(b[i][3-i] for i in range(4))) == 4:
            return b[0][3]
            
        return 0

    def evaluate(b):
        winner = check_winner(b)
        if winner == 1: return 1000
        if winner == -1: return -1000
        
        score = 0
        # Heuristic: Prefer center and count potential threats
        lines = []
        for i in range(4):
            lines.append(b[i]) # Rows
            lines.append([b[j][i] for j in range(4)]) # Cols
        lines.append([b[i][i] for i in range(4)])
        lines.append([b[i][3-i] for i in range(4)])
        
        for line in lines:
            if 1 in line and -1 not in line:
                score += line.count(1) ** 2
            elif -1 in line and 1 not in line:
                score -= line.count(-1) ** 2
        return score

    def minimax(b, depth, alpha, beta, is_maximizing):
        winner = check_winner(b)
        if winner != 0 or depth == 0:
            return evaluate(b)
        
        empty_cells = [(r, c) for r in range(4) for c in range(4) if b[r][c] == 0]
        if not empty_cells:
            return 0

        if is_maximizing:
            max_eval = -math.inf
            for r, c in empty_cells:
                b[r][c] = 1
                eval = minimax(b, depth - 1, alpha, beta, False)
                b[r][c] = 0
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha: break
            return max_eval
        else:
            min_eval = math.inf
            for r, c in empty_cells:
                b[r][c] = -1
                eval = minimax(b, depth - 1, alpha, beta, True)
                b[r][c] = 0
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha: break
            return min_eval

    best_val = -math.inf
    move = (0, 0)
    
    # Increase depth if fewer squares are left
    empty_count = sum(row.count(0) for row in board)
    depth = 5 if empty_count > 10 else 7

    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                board[r][c] = 1
                move_val = minimax(board, depth, -math.inf, math.inf, False)
                board[r][c] = 0
                if move_val > best_val:
                    best_val = move_val
                    move = (r, c)
                    
    return move

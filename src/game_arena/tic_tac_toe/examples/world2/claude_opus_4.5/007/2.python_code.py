
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    board = np.array(board)
    
    def get_lines(b):
        lines = []
        # Rows
        for i in range(4):
            lines.append(b[i, :])
        # Columns
        for j in range(4):
            lines.append(b[:, j])
        # Diagonals
        lines.append(np.diag(b))
        lines.append(np.diag(np.fliplr(b)))
        return lines
    
    def check_winner(b):
        for line in get_lines(b):
            if np.all(line == 1):
                return 1
            if np.all(line == -1):
                return -1
        return 0
    
    def get_empty(b):
        return [(i, j) for i in range(4) for j in range(4) if b[i, j] == 0]
    
    def evaluate_line(line, player):
        count = np.sum(line == player)
        empty = np.sum(line == 0)
        opp = 4 - count - empty
        if opp > 0:
            return 0  # Line is blocked
        if count == 4:
            return 1000
        if count == 3 and empty == 1:
            return 50
        if count == 2 and empty == 2:
            return 5
        if count == 1 and empty == 3:
            return 1
        return 0
    
    def evaluate(b):
        score = 0
        for line in get_lines(b):
            score += evaluate_line(line, 1)
            score -= evaluate_line(line, -1)
        # Slight preference for center positions
        center_bonus = 0
        for i in range(1, 3):
            for j in range(1, 3):
                if b[i, j] == 1:
                    center_bonus += 0.5
                elif b[i, j] == -1:
                    center_bonus -= 0.5
        return score + center_bonus
    
    def minimax(b, depth, alpha, beta, is_maximizing):
        winner = check_winner(b)
        if winner == 1:
            return 10000 + depth, None
        if winner == -1:
            return -10000 - depth, None
        
        empty = get_empty(b)
        if not empty:
            return 0, None  # Draw
        if depth == 0:
            return evaluate(b), None
        
        if is_maximizing:
            max_eval = float('-inf')
            best_move = empty[0]
            for move in empty:
                b[move[0], move[1]] = 1
                eval_score, _ = minimax(b, depth - 1, alpha, beta, False)
                b[move[0], move[1]] = 0
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            min_eval = float('inf')
            best_move = empty[0]
            for move in empty:
                b[move[0], move[1]] = -1
                eval_score, _ = minimax(b, depth - 1, alpha, beta, True)
                b[move[0], move[1]] = 0
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval, best_move
    
    empty = get_empty(board)
    if not empty:
        return (0, 0)
    
    # First move: prefer center-ish positions
    if len(empty) == 16:
        return (1, 1)
    
    # Determine search depth based on number of empty cells
    num_empty = len(empty)
    if num_empty > 12:
        depth = 5
    elif num_empty > 9:
        depth = 6
    elif num_empty > 6:
        depth = 7
    else:
        depth = 10  # Can search to end
    
    _, best_move = minimax(board, depth, float('-inf'), float('inf'), True)
    return best_move

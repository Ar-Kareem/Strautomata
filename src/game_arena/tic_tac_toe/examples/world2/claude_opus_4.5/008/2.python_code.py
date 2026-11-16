
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    board = np.array(board, dtype=np.int8)
    
    def check_winner(b):
        # Rows
        for i in range(4):
            s = np.sum(b[i, :])
            if s == 4: return 1
            if s == -4: return -1
        # Columns
        for j in range(4):
            s = np.sum(b[:, j])
            if s == 4: return 1
            if s == -4: return -1
        # Diagonals
        s = b[0,0] + b[1,1] + b[2,2] + b[3,3]
        if s == 4: return 1
        if s == -4: return -1
        s = b[0,3] + b[1,2] + b[2,1] + b[3,0]
        if s == 4: return 1
        if s == -4: return -1
        return 0
    
    def get_empty(b):
        return [(i, j) for i in range(4) for j in range(4) if b[i, j] == 0]
    
    def evaluate(b):
        score = 0
        # Evaluate all lines
        for i in range(4):
            # Row
            row = b[i, :]
            ones = np.sum(row == 1)
            negs = np.sum(row == -1)
            if negs == 0 and ones > 0:
                score += 10 ** ones
            if ones == 0 and negs > 0:
                score -= 10 ** negs
            # Column
            col = b[:, i]
            ones = np.sum(col == 1)
            negs = np.sum(col == -1)
            if negs == 0 and ones > 0:
                score += 10 ** ones
            if ones == 0 and negs > 0:
                score -= 10 ** negs
        
        # Main diagonal
        diag = np.array([b[i,i] for i in range(4)])
        ones = np.sum(diag == 1)
        negs = np.sum(diag == -1)
        if negs == 0 and ones > 0:
            score += 10 ** ones
        if ones == 0 and negs > 0:
            score -= 10 ** negs
        
        # Anti-diagonal
        adiag = np.array([b[i,3-i] for i in range(4)])
        ones = np.sum(adiag == 1)
        negs = np.sum(adiag == -1)
        if negs == 0 and ones > 0:
            score += 10 ** ones
        if ones == 0 and negs > 0:
            score -= 10 ** negs
        
        return score
    
    def minimax(b, depth, alpha, beta, maximizing):
        winner = check_winner(b)
        if winner == 1:
            return 100000 + depth, None
        if winner == -1:
            return -100000 - depth, None
        
        empty = get_empty(b)
        if not empty:
            return 0, None
        if depth == 0:
            return evaluate(b), None
        
        if maximizing:
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
    
    empty_count = np.sum(board == 0)
    # Adjust depth based on empty squares
    if empty_count > 12:
        depth = 5
    elif empty_count > 8:
        depth = 6
    elif empty_count > 5:
        depth = 8
    else:
        depth = 16  # Can search to end
    
    _, best_move = minimax(board.copy(), depth, float('-inf'), float('inf'), True)
    return best_move

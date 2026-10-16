
import math

def policy(board: list[list[int]]) -> tuple[int, int]:
    # 4x4 tic tac toe, need 4 in a row to win
    
    lines = []
    # Rows
    for r in range(4):
        lines.append([(r, c) for c in range(4)])
    # Columns
    for c in range(4):
        lines.append([(r, c) for r in range(4)])
    # Diagonals
    lines.append([(i, i) for i in range(4)])
    lines.append([(i, 3 - i) for i in range(4)])
    
    def check_winner(bd):
        for line in lines:
            vals = [bd[r][c] for r, c in line]
            if all(v == 1 for v in vals):
                return 1
            if all(v == -1 for v in vals):
                return -1
        return 0
    
    def get_empty(bd):
        return [(r, c) for r in range(4) for c in range(4) if bd[r][c] == 0]
    
    def evaluate(bd):
        w = check_winner(bd)
        if w != 0:
            return w * 10000
        score = 0
        for line in lines:
            vals = [bd[r][c] for r, c in line]
            p1 = vals.count(1)
            p2 = vals.count(-1)
            if p2 == 0 and p1 > 0:
                score += p1 ** 2
            if p1 == 0 and p2 > 0:
                score -= p2 ** 2
        return score
    
    # Move ordering: prefer center-ish squares
    move_priority = {}
    for r in range(4):
        for c in range(4):
            # Distance from center (1.5, 1.5)
            move_priority[(r, c)] = -((r - 1.5)**2 + (c - 1.5)**2)
    
    def ordered_moves(bd):
        empty = get_empty(bd)
        empty.sort(key=lambda m: move_priority[m], reverse=True)
        return empty
    
    def minimax(bd, depth, alpha, beta, maximizing):
        w = check_winner(bd)
        if w == 1:
            return 10000 + depth, None
        if w == -1:
            return -10000 - depth, None
        
        empty = ordered_moves(bd)
        if not empty:
            return 0, None
        if depth == 0:
            return evaluate(bd), None
        
        if maximizing:
            best_val = -math.inf
            best_move = empty[0]
            for r, c in empty:
                bd[r][c] = 1
                val, _ = minimax(bd, depth - 1, alpha, beta, False)
                bd[r][c] = 0
                if val > best_val:
                    best_val = val
                    best_move = (r, c)
                alpha = max(alpha, val)
                if beta <= alpha:
                    break
            return best_val, best_move
        else:
            best_val = math.inf
            best_move = empty[0]
            for r, c in empty:
                bd[r][c] = -1
                val, _ = minimax(bd, depth - 1, alpha, beta, True)
                bd[r][c] = 0
                if val < best_val:
                    best_val = val
                    best_move = (r, c)
                beta = min(beta, val)
                if beta <= alpha:
                    break
            return best_val, best_move
    
    empty_count = sum(1 for r in range(4) for c in range(4) if board[r][c] == 0)
    
    # Adaptive depth based on empty cells
    if empty_count <= 8:
        depth = empty_count  # solve completely
    elif empty_count <= 10:
        depth = 10
    else:
        depth = 8
    
    _, move = minimax(board, depth, -math.inf, math.inf, True)
    
    if move is None or board[move[0]][move[1]] != 0:
        empty = get_empty(board)
        return empty[0]
    
    return move

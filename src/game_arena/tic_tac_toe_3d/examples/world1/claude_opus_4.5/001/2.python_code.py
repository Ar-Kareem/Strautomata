
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    import numpy as np
    
    b = np.array(board)
    
    # Generate all 49 winning lines
    lines = []
    
    # Lines along each axis (27)
    for i in range(3):
        for j in range(3):
            lines.append([(i, j, k) for k in range(3)])
            lines.append([(i, k, j) for k in range(3)])
            lines.append([(k, i, j) for k in range(3)])
    
    # Face diagonals (18)
    for i in range(3):
        lines.append([(0, 0, i), (1, 1, i), (2, 2, i)])
        lines.append([(0, 2, i), (1, 1, i), (2, 0, i)])
        lines.append([(0, i, 0), (1, i, 1), (2, i, 2)])
        lines.append([(0, i, 2), (1, i, 1), (2, i, 0)])
        lines.append([(i, 0, 0), (i, 1, 1), (i, 2, 2)])
        lines.append([(i, 0, 2), (i, 1, 1), (i, 2, 0)])
    
    # Space diagonals (4)
    lines.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
    lines.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
    lines.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
    lines.append([(0, 2, 2), (1, 1, 1), (2, 0, 0)])
    
    def get_empty(board):
        return [(x, y, z) for x in range(3) for y in range(3) for z in range(3) if board[x, y, z] == 0]
    
    def find_winning_move(board, player):
        for line in lines:
            vals = [board[p] for p in line]
            if sum(vals) == 2 * player and vals.count(0) == 1:
                for p in line:
                    if board[p] == 0:
                        return p
        return None
    
    def check_winner(board):
        for line in lines:
            s = sum(board[p] for p in line)
            if s == 3: return 1
            if s == -3: return -1
        return 0
    
    def evaluate(board):
        score = 0
        for line in lines:
            vals = [board[p] for p in line]
            my_c = vals.count(1)
            op_c = vals.count(-1)
            if op_c == 0 and my_c > 0:
                score += 10 ** my_c
            if my_c == 0 and op_c > 0:
                score -= 10 ** op_c
        return score
    
    def minimax(board, depth, alpha, beta, maximizing):
        winner = check_winner(board)
        if winner == 1: return 100000 + depth
        if winner == -1: return -100000 - depth
        
        empty = get_empty(board)
        if not empty or depth == 0:
            return evaluate(board)
        
        if maximizing:
            max_eval = float('-inf')
            for move in empty:
                board[move] = 1
                ev = minimax(board, depth - 1, alpha, beta, False)
                board[move] = 0
                max_eval = max(max_eval, ev)
                alpha = max(alpha, ev)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in empty:
                board[move] = -1
                ev = minimax(board, depth - 1, alpha, beta, True)
                board[move] = 0
                min_eval = min(min_eval, ev)
                beta = min(beta, ev)
                if beta <= alpha:
                    break
            return min_eval
    
    # Immediate win
    win = find_winning_move(b, 1)
    if win: return win
    
    # Block opponent
    block = find_winning_move(b, -1)
    if block: return block
    
    empty = get_empty(b)
    if not empty:
        return (0, 0, 0)
    
    # Adjust depth based on empty cells
    depth = 4 if len(empty) > 15 else 5 if len(empty) > 10 else 6
    
    best_move = empty[0]
    best_val = float('-inf')
    
    # Prioritize center
    if b[1, 1, 1] == 0:
        return (1, 1, 1)
    
    for move in empty:
        b[move] = 1
        val = minimax(b, depth, float('-inf'), float('inf'), False)
        b[move] = 0
        if val > best_val:
            best_val = val
            best_move = move
    
    return best_move

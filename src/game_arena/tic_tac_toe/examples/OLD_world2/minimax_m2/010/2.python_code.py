
import time

LINE_INDICES = [
    [(0, 0), (0, 1), (0, 2), (0, 3)],
    [(1, 0), (1, 1), (1, 2), (1, 3)],
    [(2, 0), (2, 1), (2, 2), (2, 3)],
    [(3, 0), (3, 1), (3, 2), (3, 3)],
    [(0, 0), (1, 0), (2, 0), (3, 0)],
    [(0, 1), (1, 1), (2, 1), (3, 1)],
    [(0, 2), (1, 2), (2, 2), (3, 2)],
    [(0, 3), (1, 3), (2, 3), (3, 3)],
    [(0, 0), (1, 1), (2, 2), (3, 3)],
    [(0, 3), (1, 2), (2, 1), (3, 0)]
]

def get_empty_cells(board):
    empty_cells = []
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                empty_cells.append((i, j))
    return empty_cells

def count_empty_cells(board):
    count = 0
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                count += 1
    return count

def check_winner(board):
    for line in LINE_INDICES:
        ai_count = 0
        op_count = 0
        for (i, j) in line:
            val = board[i][j]
            if val == 1:
                ai_count += 1
            elif val == -1:
                op_count += 1
        if ai_count == 4:
            return 1
        if op_count == 4:
            return -1
    
    if all(board[i][j] != 0 for i in range(4) for j in range(4)):
        return 0
    return None

def evaluate(board):
    score = 0
    for line in LINE_INDICES:
        ai_count = 0
        op_count = 0
        for (i, j) in line:
            val = board[i][j]
            if val == 1:
                ai_count += 1
            elif val == -1:
                op_count += 1
        if ai_count > 0:
            score += 10 ** ai_count
        if op_count > 0:
            score -= 10 ** op_count
    return score

def minimax(board, depth, alpha, beta, maximizing_player):
    winner = check_winner(board)
    if winner is not None:
        return winner * 10000
    if depth == 0:
        return evaluate(board)
    
    moves = get_empty_cells(board)
    
    if maximizing_player:
        max_eval = -float('inf')
        for move in moves:
            board[move[0]][move[1]] = 1
            eval_score = minimax(board, depth - 1, alpha, beta, False)
            board[move[0]][move[1]] = 0
            if eval_score > max_eval:
                max_eval = eval_score
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for move in moves:
            board[move[0]][move[1]] = -1
            eval_score = minimax(board, depth - 1, alpha, beta, True)
            board[move[0]][move[1]] = 0
            if eval_score < min_eval:
                min_eval = eval_score
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval

def policy(board):
    winner = check_winner(board)
    if winner is not None:
        return (0, 0)
    
    start_time = time.time()
    time_limit = 1.0
    
    max_depth = count_empty_cells(board)
    if max_depth == 0:
        return (0, 0)
    
    best_move = None
    best_value = -float('inf')
    
    for depth in range(1, max_depth + 1):
        if time.time() - start_time >= time_limit:
            break
        
        current_best_move = None
        current_best_value = -float('inf')
        
        moves = get_empty_cells(board)
        for move in moves:
            board[move[0]][move[1]] = 1
            value = minimax(board, depth - 1, -float('inf'), float('inf'), False)
            board[move[0]][move[1]] = 0
            
            if value > current_best_value:
                current_best_value = value
                current_best_move = move
        
        if current_best_value > best_value:
            best_value = current_best_value
            best_move = current_best_move
        
        if current_best_value == 10000:
            break
    
    return best_move

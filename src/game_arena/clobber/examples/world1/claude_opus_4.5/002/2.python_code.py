
import numpy as np
import time

DIRECTIONS = {
    'U': (-1, 0),
    'D': (1, 0),
    'L': (0, -1),
    'R': (0, 1)
}
DIR_LIST = ['U', 'D', 'L', 'R']

def get_legal_moves(you, opponent, rows=5, cols=6):
    moves = []
    for r in range(rows):
        for c in range(cols):
            if you[r][c] == 1:
                for d, (dr, dc) in DIRECTIONS.items():
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols and opponent[nr][nc] == 1:
                        moves.append((r, c, d))
    return moves

def apply_move(you, opponent, move):
    r, c, d = move
    dr, dc = DIRECTIONS[d]
    nr, nc = r + dr, c + dc
    
    new_you = [row[:] for row in you]
    new_opp = [row[:] for row in opponent]
    
    new_you[r][c] = 0
    new_you[nr][nc] = 1
    new_opp[nr][nc] = 0
    
    return new_you, new_opp

def evaluate(you, opponent, rows=5, cols=6):
    my_moves = len(get_legal_moves(you, opponent, rows, cols))
    opp_moves = len(get_legal_moves(opponent, you, rows, cols))
    
    if my_moves == 0:
        return -10000
    if opp_moves == 0:
        return 10000
    
    return (my_moves - opp_moves) * 10

def minimax(you, opponent, depth, alpha, beta, maximizing, start_time, time_limit):
    if time.time() - start_time > time_limit:
        return evaluate(you, opponent), None
    
    if maximizing:
        moves = get_legal_moves(you, opponent)
    else:
        moves = get_legal_moves(opponent, you)
    
    if depth == 0 or not moves:
        return evaluate(you, opponent), None
    
    best_move = moves[0] if moves else None
    
    if maximizing:
        max_eval = -float('inf')
        for move in moves:
            new_you, new_opp = apply_move(you, opponent, move)
            eval_score, _ = minimax(new_you, new_opp, depth - 1, alpha, beta, False, start_time, time_limit)
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for move in moves:
            new_opp, new_you = apply_move(opponent, you, move)
            eval_score, _ = minimax(new_you, new_opp, depth - 1, alpha, beta, True, start_time, time_limit)
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval, best_move

def policy(you: list[int], opponent: list[int]) -> str:
    you_list = [list(row) for row in you]
    opp_list = [list(row) for row in opponent]
    
    moves = get_legal_moves(you_list, opp_list)
    
    if not moves:
        # Should not happen if game is valid, but fallback
        for r in range(5):
            for c in range(6):
                if you_list[r][c] == 1:
                    for d in DIR_LIST:
                        return f"{r},{c},{d}"
    
    if len(moves) == 1:
        r, c, d = moves[0]
        return f"{r},{c},{d}"
    
    start_time = time.time()
    time_limit = 0.85
    
    best_move = moves[0]
    
    for depth in range(1, 20):
        if time.time() - start_time > time_limit:
            break
        
        score, move = minimax(you_list, opp_list, depth, -float('inf'), float('inf'), True, start_time, time_limit)
        
        if move is not None:
            best_move = move
        
        if abs(score) >= 9000:
            break
    
    r, c, d = best_move
    return f"{r},{c},{d}"

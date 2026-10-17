
import numpy as np

DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

WEIGHTS = np.array([
    [100, -20, 10,  5,  5, 10, -20, 100],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [ 10,  -2,  1,  1,  1,  1,  -2,  10],
    [  5,  -2,  1,  0,  0,  1,  -2,   5],
    [  5,  -2,  1,  0,  0,  1,  -2,   5],
    [ 10,  -2,  1,  1,  1,  1,  -2,  10],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [100, -20, 10,  5,  5, 10, -20, 100]
])

def get_legal_moves(you, opponent):
    moves = []
    for r in range(8):
        for c in range(8):
            if you[r][c] == 0 and opponent[r][c] == 0:
                if is_valid_move(you, opponent, r, c):
                    moves.append((r, c))
    return moves

def is_valid_move(you, opponent, r, c):
    for dr, dc in DIRECTIONS:
        if flips_in_direction(you, opponent, r, c, dr, dc):
            return True
    return False

def flips_in_direction(you, opponent, r, c, dr, dc):
    nr, nc = r + dr, c + dc
    found_opponent = False
    while 0 <= nr < 8 and 0 <= nc < 8:
        if opponent[nr][nc] == 1:
            found_opponent = True
        elif you[nr][nc] == 1:
            return found_opponent
        else:
            return False
        nr += dr
        nc += dc
    return False

def apply_move(you, opponent, r, c):
    new_you = you.copy()
    new_opp = opponent.copy()
    new_you[r][c] = 1
    for dr, dc in DIRECTIONS:
        if flips_in_direction(you, opponent, r, c, dr, dc):
            nr, nc = r + dr, c + dc
            while new_opp[nr][nc] == 1:
                new_opp[nr][nc] = 0
                new_you[nr][nc] = 1
                nr += dr
                nc += dc
    return new_you, new_opp

def evaluate(you, opponent):
    my_count = np.sum(you)
    opp_count = np.sum(opponent)
    total = my_count + opp_count
    
    pos_score = np.sum(WEIGHTS * you) - np.sum(WEIGHTS * opponent)
    
    my_moves = len(get_legal_moves(you, opponent))
    opp_moves = len(get_legal_moves(opponent, you))
    mobility = (my_moves - opp_moves) * 10
    
    if total > 54:
        return (my_count - opp_count) * 100 + pos_score * 0.5
    elif total > 44:
        return pos_score + mobility + (my_count - opp_count) * 2
    else:
        return pos_score + mobility * 2

def minimax(you, opponent, depth, alpha, beta, maximizing):
    moves = get_legal_moves(you, opponent) if maximizing else get_legal_moves(opponent, you)
    
    if depth == 0:
        return evaluate(you, opponent), None
    
    if maximizing:
        if not moves:
            opp_moves = get_legal_moves(opponent, you)
            if not opp_moves:
                diff = np.sum(you) - np.sum(opponent)
                return diff * 1000, None
            return minimax(you, opponent, depth - 1, alpha, beta, False)[0], None
        
        max_eval = -float('inf')
        best_move = moves[0]
        for r, c in moves:
            new_you, new_opp = apply_move(you, opponent, r, c)
            eval_score, _ = minimax(new_you, new_opp, depth - 1, alpha, beta, False)
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = (r, c)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        if not moves:
            my_moves = get_legal_moves(you, opponent)
            if not my_moves:
                diff = np.sum(you) - np.sum(opponent)
                return diff * 1000, None
            return minimax(you, opponent, depth - 1, alpha, beta, True)[0], None
        
        min_eval = float('inf')
        best_move = moves[0]
        for r, c in moves:
            new_opp, new_you = apply_move(opponent, you, r, c)
            eval_score, _ = minimax(new_you, new_opp, depth - 1, alpha, beta, True)
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = (r, c)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval, best_move

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    moves = get_legal_moves(you, opponent)
    
    if not moves:
        return "pass"
    
    total_discs = np.sum(you) + np.sum(opponent)
    if total_discs > 54:
        depth = 6
    elif total_discs > 48:
        depth = 5
    else:
        depth = 4
    
    _, best_move = minimax(you, opponent, depth, -float('inf'), float('inf'), True)
    
    if best_move is None:
        best_move = moves[0]
    
    r, c = best_move
    col_letter = chr(ord('a') + c)
    row_number = str(r + 1)
    return col_letter + row_number

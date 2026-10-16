
import numpy as np

DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

POSITION_WEIGHTS = np.array([
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
    if not (0 <= nr < 8 and 0 <= nc < 8) or opponent[nr][nc] != 1:
        return False
    nr, nc = nr + dr, nc + dc
    while 0 <= nr < 8 and 0 <= nc < 8:
        if you[nr][nc] == 1:
            return True
        if opponent[nr][nc] != 1:
            return False
        nr, nc = nr + dr, nc + dc
    return False

def make_move(you, opponent, r, c):
    new_you = you.copy()
    new_opp = opponent.copy()
    new_you[r][c] = 1
    for dr, dc in DIRECTIONS:
        if flips_in_direction(you, opponent, r, c, dr, dc):
            nr, nc = r + dr, c + dc
            while new_opp[nr][nc] == 1:
                new_opp[nr][nc] = 0
                new_you[nr][nc] = 1
                nr, nc = nr + dr, nc + dc
    return new_you, new_opp

def evaluate(you, opponent):
    empty = 64 - np.sum(you) - np.sum(opponent)
    
    if empty < 10:
        return np.sum(you) - np.sum(opponent)
    
    pos_score = np.sum(POSITION_WEIGHTS * you) - np.sum(POSITION_WEIGHTS * opponent)
    
    my_moves = len(get_legal_moves(you, opponent))
    opp_moves = len(get_legal_moves(opponent, you))
    mobility = (my_moves - opp_moves) * 5
    
    return pos_score + mobility

def minimax(you, opponent, depth, alpha, beta, maximizing):
    if depth == 0:
        return evaluate(you, opponent), None
    
    moves = get_legal_moves(you, opponent) if maximizing else get_legal_moves(opponent, you)
    
    if not moves:
        other_moves = get_legal_moves(opponent, you) if maximizing else get_legal_moves(you, opponent)
        if not other_moves:
            diff = np.sum(you) - np.sum(opponent)
            return (1000 if diff > 0 else -1000 if diff < 0 else 0), None
        return minimax(you, opponent, depth - 1, alpha, beta, not maximizing)
    
    moves.sort(key=lambda m: POSITION_WEIGHTS[m[0]][m[1]], reverse=maximizing)
    
    best_move = moves[0]
    
    if maximizing:
        max_eval = float('-inf')
        for move in moves:
            new_you, new_opp = make_move(you, opponent, move[0], move[1])
            eval_score, _ = minimax(new_you, new_opp, depth - 1, alpha, beta, False)
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
            new_opp, new_you = make_move(opponent, you, move[0], move[1])
            eval_score, _ = minimax(new_you, new_opp, depth - 1, alpha, beta, True)
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval, best_move

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    moves = get_legal_moves(you, opponent)
    
    if not moves:
        return "pass"
    
    empty = 64 - np.sum(you) - np.sum(opponent)
    if empty > 50:
        depth = 5
    elif empty > 20:
        depth = 6
    elif empty > 12:
        depth = 8
    else:
        depth = 10
    
    _, best_move = minimax(you, opponent, depth, float('-inf'), float('inf'), True)
    
    if best_move is None:
        best_move = moves[0]
    
    r, c = best_move
    col_letter = chr(ord('a') + c)
    row_number = str(r + 1)
    return col_letter + row_number

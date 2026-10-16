
import numpy as np
import time

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
    my_moves = len(get_legal_moves(you, opponent))
    opp_moves = len(get_legal_moves(opponent, you))
    
    pos_score = np.sum(you * WEIGHTS) - np.sum(opponent * WEIGHTS)
    
    if my_moves + opp_moves > 0:
        mobility = 100 * (my_moves - opp_moves) / (my_moves + opp_moves + 1)
    else:
        mobility = 0
    
    total = np.sum(you) + np.sum(opponent)
    if total > 50:
        return np.sum(you) - np.sum(opponent)
    
    return pos_score + 10 * mobility

def minimax(you, opponent, depth, alpha, beta, maximizing, deadline):
    if time.time() > deadline:
        raise TimeoutError
    
    moves = get_legal_moves(you, opponent) if maximizing else get_legal_moves(opponent, you)
    
    if depth == 0 or (not moves and not get_legal_moves(opponent, you) if maximizing else not get_legal_moves(you, opponent)):
        return evaluate(you, opponent), None
    
    if not moves:
        val, _ = minimax(you, opponent, depth - 1, alpha, beta, not maximizing, deadline)
        return val, None
    
    moves.sort(key=lambda m: -WEIGHTS[m[0]][m[1]])
    
    best_move = moves[0]
    if maximizing:
        max_eval = float('-inf')
        for move in moves:
            new_you, new_opp = make_move(you, opponent, move[0], move[1])
            val, _ = minimax(new_you, new_opp, depth - 1, alpha, beta, False, deadline)
            if val > max_eval:
                max_eval = val
                best_move = move
            alpha = max(alpha, val)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for move in moves:
            new_opp, new_you = make_move(opponent, you, move[0], move[1])
            val, _ = minimax(new_you, new_opp, depth - 1, alpha, beta, True, deadline)
            if val < min_eval:
                min_eval = val
                best_move = move
            beta = min(beta, val)
            if beta <= alpha:
                break
        return min_eval, best_move

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    moves = get_legal_moves(you, opponent)
    if not moves:
        return "pass"
    
    deadline = time.time() + 0.9
    best_move = moves[0]
    
    for depth in range(1, 15):
        try:
            _, move = minimax(you, opponent, depth, float('-inf'), float('inf'), True, deadline)
            if move:
                best_move = move
        except TimeoutError:
            break
        if time.time() > deadline:
            break
    
    col_letter = chr(ord('a') + best_move[1])
    row_number = str(best_move[0] + 1)
    return col_letter + row_number

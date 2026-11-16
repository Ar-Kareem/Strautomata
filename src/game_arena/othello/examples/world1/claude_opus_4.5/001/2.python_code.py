
import numpy as np

DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

POSITION_WEIGHTS = np.array([
    [100, -20, 10,  5,  5, 10, -20, 100],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [ 10,  -2,  5,  1,  1,  5,  -2,  10],
    [  5,  -2,  1,  0,  0,  1,  -2,   5],
    [  5,  -2,  1,  0,  0,  1,  -2,   5],
    [ 10,  -2,  5,  1,  1,  5,  -2,  10],
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
    if not (0 <= nr < 8 and 0 <= nc < 8) or opponent[nr][nc] == 0:
        return False
    while 0 <= nr < 8 and 0 <= nc < 8:
        if opponent[nr][nc] == 1:
            nr, nc = nr + dr, nc + dc
        elif you[nr][nc] == 1:
            return True
        else:
            break
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
                nr, nc = nr + dr, nc + dc
    return new_you, new_opp

def evaluate(you, opponent):
    total_pieces = np.sum(you) + np.sum(opponent)
    
    pos_score = np.sum(POSITION_WEIGHTS * you) - np.sum(POSITION_WEIGHTS * opponent)
    
    my_moves = len(get_legal_moves(you, opponent))
    opp_moves = len(get_legal_moves(opponent, you))
    mobility_score = (my_moves - opp_moves) * 10
    
    piece_diff = np.sum(you) - np.sum(opponent)
    
    if total_pieces < 20:
        return pos_score * 2 + mobility_score * 3
    elif total_pieces < 50:
        return pos_score * 1.5 + mobility_score * 2 + piece_diff * 0.5
    else:
        return pos_score + mobility_score + piece_diff * 5

def alphabeta(you, opponent, depth, alpha, beta, maximizing):
    moves = get_legal_moves(you, opponent) if maximizing else get_legal_moves(opponent, you)
    
    if depth == 0:
        return evaluate(you, opponent), None
    
    if maximizing:
        if not moves:
            opp_moves = get_legal_moves(opponent, you)
            if not opp_moves:
                diff = np.sum(you) - np.sum(opponent)
                return (10000 if diff > 0 else -10000 if diff < 0 else 0), None
            val, _ = alphabeta(you, opponent, depth - 1, alpha, beta, False)
            return val, None
        
        moves.sort(key=lambda m: POSITION_WEIGHTS[m[0]][m[1]], reverse=True)
        max_val = float('-inf')
        best_move = moves[0]
        for move in moves:
            new_you, new_opp = apply_move(you, opponent, move[0], move[1])
            val, _ = alphabeta(new_you, new_opp, depth - 1, alpha, beta, False)
            if val > max_val:
                max_val = val
                best_move = move
            alpha = max(alpha, val)
            if beta <= alpha:
                break
        return max_val, best_move
    else:
        if not moves:
            my_moves = get_legal_moves(you, opponent)
            if not my_moves:
                diff = np.sum(you) - np.sum(opponent)
                return (10000 if diff > 0 else -10000 if diff < 0 else 0), None
            val, _ = alphabeta(you, opponent, depth - 1, alpha, beta, True)
            return val, None
        
        moves.sort(key=lambda m: POSITION_WEIGHTS[m[0]][m[1]], reverse=True)
        min_val = float('inf')
        best_move = moves[0]
        for move in moves:
            new_opp, new_you = apply_move(opponent, you, move[0], move[1])
            val, _ = alphabeta(new_you, new_opp, depth - 1, alpha, beta, True)
            if val < min_val:
                min_val = val
                best_move = move
            beta = min(beta, val)
            if beta <= alpha:
                break
        return min_val, best_move

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    moves = get_legal_moves(you, opponent)
    
    if not moves:
        return "pass"
    
    if len(moves) == 1:
        r, c = moves[0]
        return chr(ord('a') + c) + str(r + 1)
    
    best_move = moves[0]
    total_pieces = np.sum(you) + np.sum(opponent)
    
    max_depth = 5 if total_pieces > 50 else 4
    
    for depth in range(1, max_depth + 1):
        _, move = alphabeta(you, opponent, depth, float('-inf'), float('inf'), True)
        if move:
            best_move = move
    
    r, c = best_move
    return chr(ord('a') + c) + str(r + 1)

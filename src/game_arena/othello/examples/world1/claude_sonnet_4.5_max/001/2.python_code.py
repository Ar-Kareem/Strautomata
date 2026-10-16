
import numpy as np

DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

WEIGHTS = np.array([
    [120, -20,  20,   5,   5,  20, -20, 120],
    [-20, -40,  -5,  -5,  -5,  -5, -40, -20],
    [ 20,  -5,  15,   3,   3,  15,  -5,  20],
    [  5,  -5,   3,   3,   3,   3,  -5,   5],
    [  5,  -5,   3,   3,   3,   3,  -5,   5],
    [ 20,  -5,  15,   3,   3,  15,  -5,  20],
    [-20, -40,  -5,  -5,  -5,  -5, -40, -20],
    [120, -20,  20,   5,   5,  20, -20, 120]
])

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    moves = get_legal_moves(you, opponent)
    if not moves:
        return "pass"
    if len(moves) == 1:
        return moves[0]
    
    total = np.sum(you) + np.sum(opponent)
    if total > 54:
        depth = 12
    elif total > 48:
        depth = 9
    elif total > 40:
        depth = 7
    else:
        depth = 6
    
    best_move = minimax_root(you, opponent, depth)
    return best_move if best_move else moves[0]

def get_legal_moves(you, opp):
    moves = []
    for r in range(8):
        for c in range(8):
            if you[r][c] == 0 and opp[r][c] == 0 and is_legal(you, opp, r, c):
                moves.append(chr(ord('a') + c) + str(r + 1))
    return moves

def is_legal(you, opp, r, c):
    for dr, dc in DIRECTIONS:
        if check_dir(you, opp, r, c, dr, dc):
            return True
    return False

def check_dir(you, opp, r, c, dr, dc):
    nr, nc = r + dr, c + dc
    found = False
    while 0 <= nr < 8 and 0 <= nc < 8:
        if opp[nr][nc]:
            found = True
            nr += dr
            nc += dc
        elif you[nr][nc]:
            return found
        else:
            return False
    return False

def make_move(you, opp, r, c):
    new_you, new_opp = you.copy(), opp.copy()
    new_you[r][c] = 1
    for dr, dc in DIRECTIONS:
        if check_dir(you, opp, r, c, dr, dc):
            nr, nc = r + dr, c + dc
            while opp[nr][nc]:
                new_you[nr][nc] = 1
                new_opp[nr][nc] = 0
                nr += dr
                nc += dc
    return new_you, new_opp

def evaluate(you, opp):
    total = np.sum(you) + np.sum(opp)
    score = np.sum(WEIGHTS * you) - np.sum(WEIGHTS * opp)
    
    if total > 48:
        disc_diff = np.sum(you) - np.sum(opp)
        score += disc_diff * 15
    
    return score

def move_priority(m):
    r, c = int(m[1]) - 1, ord(m[0]) - ord('a')
    if (r, c) in [(0,0), (0,7), (7,0), (7,7)]:
        return 0
    if r == 0 or r == 7 or c == 0 or c == 7:
        return 1
    return 2

def minimax_root(you, opp, depth):
    moves = get_legal_moves(you, opp)
    best_move, best_score = moves[0], -float('inf')
    alpha, beta = -float('inf'), float('inf')
    
    for move in sorted(moves, key=move_priority):
        r, c = int(move[1]) - 1, ord(move[0]) - ord('a')
        new_you, new_opp = make_move(you, opp, r, c)
        score = -minimax(new_opp, new_you, depth - 1, -beta, -alpha)
        if score > best_score:
            best_score, best_move = score, move
        alpha = max(alpha, score)
        if alpha >= beta:
            break
    return best_move

def minimax(you, opp, depth, alpha, beta):
    if depth == 0:
        return evaluate(you, opp)
    
    moves = get_legal_moves(you, opp)
    if not moves:
        if not get_legal_moves(opp, you):
            diff = np.sum(you) - np.sum(opp)
            return 10000 * np.sign(diff) if diff != 0 else 0
        return -minimax(opp, you, depth - 1, -beta, -alpha)
    
    max_score = -float('inf')
    moves_ordered = sorted(moves, key=move_priority)
    
    for move in moves_ordered:
        r, c = int(move[1]) - 1, ord(move[0]) - ord('a')
        new_you, new_opp = make_move(you, opp, r, c)
        score = -minimax(new_opp, new_you, depth - 1, -beta, -alpha)
        max_score = max(max_score, score)
        alpha = max(alpha, score)
        if alpha >= beta:
            break
    return max_score

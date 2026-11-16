
import numpy as np

def get_directions():
    return [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

def is_legal_move(r, c, you, opponent):
    if you[r][c] or opponent[r][c]:
        return False
    directions = get_directions()
    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        if not (0 <= nr < 8 and 0 <= nc < 8) or not opponent[nr][nc]:
            continue
        nr, nc = nr + dr, nc + dc
        while 0 <= nr < 8 and 0 <= nc < 8:
            if you[nr][nc]:
                return True
            if not opponent[nr][nc]:
                break
            nr, nc = nr + dr, nc + dc
    return False

def get_legal_moves(you, opponent):
    moves = []
    for r in range(8):
        for c in range(8):
            if is_legal_move(r, c, you, opponent):
                moves.append((r, c))
    return moves

def apply_move(r, c, you, opponent):
    new_you = you.copy()
    new_opponent = opponent.copy()
    new_you[r][c] = 1
    directions = get_directions()
    for dr, dc in directions:
        to_flip = []
        nr, nc = r + dr, c + dc
        while 0 <= nr < 8 and 0 <= nc < 8 and opponent[nr][nc]:
            to_flip.append((nr, nc))
            nr, nc = nr + dr, nc + dc
        if 0 <= nr < 8 and 0 <= nc < 8 and you[nr][nc]:
            for fr, fc in to_flip:
                new_you[fr][fc] = 1
                new_opponent[fr][fc] = 0
    return new_you, new_opponent

def evaluate(you, opponent):
    if not get_legal_moves(you, opponent) and not get_legal_moves(opponent, you):
        you_count = np.sum(you)
        opp_count = np.sum(opponent)
        if you_count > opp_count:
            return 10000
        elif you_count < opp_count:
            return -10000
        else:
            return 0
    board_weights = np.array([
        [120, -20, 20, 5, 5, 20, -20, 120],
        [-20, -40, -5, -5, -5, -5, -40, -20],
        [20, -5, 15, 3, 3, 15, -5, 20],
        [5, -5, 3, 3, 3, 3, -5, 5],
        [5, -5, 3, 3, 3, 3, -5, 5],
        [20, -5, 15, 3, 3, 15, -5, 20],
        [-20, -40, -5, -5, -5, -5, -40, -20],
        [120, -20, 20, 5, 5, 20, -20, 120]
    ])
    score = 0
    for r in range(8):
        for c in range(8):
            if you[r][c]:
                score += board_weights[r][c]
            elif opponent[r][c]:
                score -= board_weights[r][c]
    your_moves = len(get_legal_moves(you, opponent))
    opp_moves = len(get_legal_moves(opponent, you))
    score += your_moves * 10
    score -= opp_moves * 10
    return score

def negamax(you, opponent, depth, alpha, beta):
    if depth == 0:
        return evaluate(you, opponent)
    legal = get_legal_moves(you, opponent)
    if not legal:
        if not get_legal_moves(opponent, you):
            return evaluate(you, opponent)
        return -negamax(opponent, you, depth - 1, -beta, -alpha)
    max_score = -float('inf')
    for r, c in legal:
        new_you, new_opp = apply_move(r, c, you, opponent)
        v = -negamax(new_opp, new_you, depth - 1, -beta, -alpha)
        if v > max_score:
            max_score = v
        if v >= beta:
            break
        alpha = max(alpha, max_score)
    return max_score

def to_move_string(r, c):
    file = chr(ord('a') + c)
    rank = str(r + 1)
    return file + rank

def policy(you, opponent):
    legal = get_legal_moves(you, opponent)
    if not legal:
        return "pass"
    best_move = None
    best_score = -float('inf')
    for r, c in legal:
        new_you, new_opp = apply_move(r, c, you, opponent)
        score = -negamax(new_opp, new_you, 3, -float('inf'), float('inf'))
        if score > best_score:
            best_score = score
            best_move = (r, c)
    return to_move_string(*best_move)

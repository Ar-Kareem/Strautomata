
import numpy as np

# Direction vectors for move generation
DIRS = [(-1,-1), (-1,0), (-1,1),
        (0,-1),         (0,1),
        (1,-1),  (1,0),  (1,1)]

# Positional weights matrix
POS_WEIGHTS = [
    [100, -20, 10, 5, 5, 10, -20, 100],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [10,  -2,  -1, -1, -1, -1,  -2,  10],
    [5,   -2,  -1, -1, -1, -1,  -2,   5],
    [5,   -2,  -1, -1, -1, -1,  -2,   5],
    [10,  -2,  -1, -1, -1, -1,  -2,  10],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [100, -20, 10, 5, 5, 10, -20, 100]
]

def on_board(r, c):
    return 0 <= r < 8 and 0 <= c < 8

def get_flips(you, opp, r, c):
    if you[r][c] or opp[r][c]:
        return []
    flips = []
    for dr, dc in DIRS:
        rr, cc = r + dr, c + dc
        line = []
        while on_board(rr, cc) and opp[rr][cc]:
            line.append((rr, cc))
            rr += dr
            cc += dc
        if line and on_board(rr, cc) and you[rr][cc]:
            flips.extend(line)
    return flips

def legal_moves(you, opp):
    moves = []
    for r in range(8):
        for c in range(8):
            flips = get_flips(you, opp, r, c)
            if flips:
                moves.append((r, c, flips))
    return moves

def apply_move(you, opp, move):
    r, c, flips = move
    new_you = [row[:] for row in you]
    new_opp = [row[:] for row in opp]
    new_you[r][c] = 1
    for rr, cc in flips:
        new_you[rr][cc] = 1
        new_opp[rr][cc] = 0
    return new_you, new_opp

def count_discs(board):
    return sum(sum(row) for row in board)

def evaluate(you, opp):
    pos_score = 0
    for r in range(8):
        for c in range(8):
            if you[r][c]:
                pos_score += POS_WEIGHTS[r][c]
            elif opp[r][c]:
                pos_score -= POS_WEIGHTS[r][c]

    moves_you = len(legal_moves(you, opp))
    moves_opp = len(legal_moves(opp, you))
    mobility = moves_you - moves_opp

    disc_diff = count_discs(you) - count_discs(opp)
    empties = 64 - (count_discs(you) + count_discs(opp))
    disc_weight = 5 if empties < 15 else 1

    return pos_score + mobility * 5 + disc_diff * disc_weight

def negamax(you, opp, depth, alpha, beta):
    moves = legal_moves(you, opp)
    if depth == 0 or not moves:
        # If no moves but opponent has moves, it's a pass
        if depth > 0 and not moves and legal_moves(opp, you):
            return -negamax(opp, you, depth-1, -beta, -alpha)
        return evaluate(you, opp)

    best = -1e9
    for move in moves:
        new_you, new_opp = apply_move(you, opp, move)
        score = -negamax(new_opp, new_you, depth-1, -beta, -alpha)
        if score > best:
            best = score
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    # Convert to lists for faster manipulation
    you = you.tolist()
    opponent = opponent.tolist()

    moves = legal_moves(you, opponent)
    if not moves:
        return "pass"

    empties = 64 - (count_discs(you) + count_discs(opponent))
    if empties <= 10:
        depth = 6
    elif empties <= 20:
        depth = 5
    elif empties <= 40:
        depth = 4
    else:
        depth = 3

    best_score = -1e9
    best_move = moves[0]
    alpha, beta = -1e9, 1e9

    for move in moves:
        new_you, new_opp = apply_move(you, opponent, move)
        score = -negamax(new_opp, new_you, depth-1, -beta, -alpha)
        if score > best_score:
            best_score = score
            best_move = move
        if best_score > alpha:
            alpha = best_score

    r, c, _ = best_move
    return chr(ord('a') + c) + str(r + 1)

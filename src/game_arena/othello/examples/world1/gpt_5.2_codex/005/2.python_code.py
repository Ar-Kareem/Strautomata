
import numpy as np

# Directions for move checking
DIRS = [(-1, -1), (-1, 0), (-1, 1),
        (0, -1),          (0, 1),
        (1, -1),  (1, 0), (1, 1)]

# Positional weights (standard Othello heuristic)
WEIGHTS = [
    [100, -20, 10, 5, 5, 10, -20, 100],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [10, -2, -1, -1, -1, -1, -2, 10],
    [5, -2, -1, -1, -1, -1, -2, 5],
    [5, -2, -1, -1, -1, -1, -2, 5],
    [10, -2, -1, -1, -1, -1, -2, 10],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [100, -20, 10, 5, 5, 10, -20, 100],
]

def in_bounds(r, c):
    return 0 <= r < 8 and 0 <= c < 8

def get_flips(you, opp, r, c):
    if you[r][c] or opp[r][c]:
        return []
    flips = []
    for dr, dc in DIRS:
        rr, cc = r + dr, c + dc
        line = []
        while in_bounds(rr, cc) and opp[rr][cc]:
            line.append((rr, cc))
            rr += dr
            cc += dc
        if line and in_bounds(rr, cc) and you[rr][cc]:
            flips.extend(line)
    return flips

def legal_moves(you, opp):
    moves = []
    for r in range(8):
        for c in range(8):
            if not you[r][c] and not opp[r][c]:
                if get_flips(you, opp, r, c):
                    moves.append((r, c))
    return moves

def apply_move(you, opp, move):
    r, c = move
    flips = get_flips(you, opp, r, c)
    new_you = [row[:] for row in you]
    new_opp = [row[:] for row in opp]
    new_you[r][c] = 1
    for rr, cc in flips:
        new_you[rr][cc] = 1
        new_opp[rr][cc] = 0
    return new_you, new_opp

def evaluate(you, opp):
    score = 0
    my_discs = 0
    opp_discs = 0
    for r in range(8):
        for c in range(8):
            if you[r][c]:
                score += WEIGHTS[r][c]
                my_discs += 1
            elif opp[r][c]:
                score -= WEIGHTS[r][c]
                opp_discs += 1

    # Mobility
    my_moves = len(legal_moves(you, opp))
    opp_moves = len(legal_moves(opp, you))
    score += 5 * (my_moves - opp_moves)

    # Disc difference weight increases in endgame
    empties = 64 - my_discs - opp_discs
    if empties < 12:
        score += 4 * (my_discs - opp_discs)
    else:
        score += 2 * (my_discs - opp_discs)
    return score

def negamax(you, opp, depth, alpha, beta):
    my_moves = legal_moves(you, opp)
    opp_moves = legal_moves(opp, you)
    if depth == 0 or (not my_moves and not opp_moves):
        return evaluate(you, opp)

    if not my_moves:
        # Pass move
        return -negamax(opp, you, depth - 1, -beta, -alpha)

    best = -1e9
    for move in my_moves:
        n_you, n_opp = apply_move(you, opp, move)
        val = -negamax(n_opp, n_you, depth - 1, -beta, -alpha)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    you = you.tolist()
    opponent = opponent.tolist()

    moves = legal_moves(you, opponent)
    if not moves:
        return "pass"

    # Dynamic depth based on empties
    empties = 64 - sum(sum(row) for row in you) - sum(sum(row) for row in opponent)
    if empties > 50:
        depth = 3
    elif empties > 20:
        depth = 4
    else:
        depth = 5

    best_move = moves[0]
    best_score = -1e9
    alpha = -1e9
    beta = 1e9
    for move in moves:
        n_you, n_opp = apply_move(you, opponent, move)
        score = -negamax(n_opp, n_you, depth - 1, -beta, -alpha)
        if score > best_score:
            best_score = score
            best_move = move
        if score > alpha:
            alpha = score

    r, c = best_move
    return chr(ord('a') + c) + str(r + 1)


import numpy as np
import time
import sys

# Positional weights matrix (classic strong Othello weights)
WEIGHTS = np.array([
    [120, -20,  20,   5,   5,  20, -20, 120],
    [-20, -40,  -5,  -5,  -5,  -5, -40, -20],
    [ 20,  -5,  15,   3,   3,  15,  -5,  20],
    [  5,  -5,   3,   3,   3,   3,  -5,   5],
    [  5,  -5,   3,   3,   3,   3,  -5,   5],
    [ 20,  -5,  15,   3,   3,  15,  -5,  20],
    [-20, -40,  -5,  -5,  -5,  -5, -40, -20],
    [120, -20,  20,   5,   5,  20, -20, 120]
], dtype=np.int32)

DIRS = [(-1, -1), (-1, 0), (-1, 1),
        (0, -1),          (0, 1),
        (1, -1),  (1, 0), (1, 1)]

def in_bounds(r, c):
    return 0 <= r < 8 and 0 <= c < 8

def legal_moves(you, opp):
    moves = []
    empty = (you == 0) & (opp == 0)
    empties = np.argwhere(empty)
    for r, c in empties:
        for dr, dc in DIRS:
            rr, cc = r + dr, c + dc
            if not in_bounds(rr, cc):
                continue
            if opp[rr, cc] != 1:
                continue
            # advance along direction
            rr += dr
            cc += dc
            while in_bounds(rr, cc) and opp[rr, cc] == 1:
                rr += dr
                cc += dc
            if in_bounds(rr, cc) and you[rr, cc] == 1:
                moves.append((r, c))
                break
    return moves

def apply_move(you, opp, move):
    r, c = move
    new_you = you.copy()
    new_opp = opp.copy()
    new_you[r, c] = 1
    # flip along all valid directions
    for dr, dc in DIRS:
        rr, cc = r + dr, c + dc
        if not in_bounds(rr, cc) or new_opp[rr, cc] != 1:
            continue
        path = []
        while in_bounds(rr, cc) and new_opp[rr, cc] == 1:
            path.append((rr, cc))
            rr += dr
            cc += dc
        if in_bounds(rr, cc) and new_you[rr, cc] == 1:
            for pr, pc in path:
                new_you[pr, pc] = 1
                new_opp[pr, pc] = 0
    return new_you, new_opp

def evaluate(you, opp):
    # positional weight score
    pos_score = int(np.sum(WEIGHTS * you) - np.sum(WEIGHTS * opp))
    # mobility
    my_moves = len(legal_moves(you, opp))
    opp_moves = len(legal_moves(opp, you))
    mobility = 5 * (my_moves - opp_moves)
    # corners
    corners = [(0,0),(0,7),(7,0),(7,7)]
    corner_score = 25 * sum(you[r,c] - opp[r,c] for r,c in corners)
    # endgame disc diff
    empties = 64 - int(np.sum(you) + np.sum(opp))
    disc_diff = int(np.sum(you) - np.sum(opp))
    if empties <= 10:
        disc_diff *= 10
    else:
        disc_diff = 0
    return pos_score + mobility + corner_score + disc_diff

def negamax(you, opp, depth, alpha, beta, cache):
    key = (you.tobytes(), opp.tobytes(), depth)
    if key in cache:
        return cache[key]

    moves = legal_moves(you, opp)
    if depth == 0:
        val = evaluate(you, opp)
        cache[key] = val
        return val

    if not moves:
        # if opponent also has no moves, game over
        if not legal_moves(opp, you):
            val = evaluate(you, opp)
            cache[key] = val
            return val
        # otherwise pass
        val = -negamax(opp, you, depth - 1, -beta, -alpha, cache)
        cache[key] = val
        return val

    best = -10**9
    for mv in moves:
        y2, o2 = apply_move(you, opp, mv)
        score = -negamax(o2, y2, depth - 1, -beta, -alpha, cache)
        if score > best:
            best = score
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    cache[key] = best
    return best

def move_to_str(move):
    r, c = move
    return chr(ord('a') + c) + str(r + 1)

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    sys.setrecursionlimit(10000)
    moves = legal_moves(you, opponent)
    if not moves:
        return "pass"

    empties = 64 - int(np.sum(you) + np.sum(opponent))
    # dynamic depth selection
    if empties <= 8:
        depth = 6
    elif empties <= 14:
        depth = 5
    else:
        depth = 4

    best_move = moves[0]
    best_score = -10**9
    cache = {}
    alpha = -10**9
    beta = 10**9

    for mv in moves:
        y2, o2 = apply_move(you, opponent, mv)
        score = -negamax(o2, y2, depth - 1, -beta, -alpha, cache)
        if score > best_score:
            best_score = score
            best_move = mv
        if score > alpha:
            alpha = score

    return move_to_str(best_move)


import numpy as np

DIRS = [(-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)]

INF = 10**18

# Standard strong Othello positional weights
PST = np.array([
    [120, -20,  20,   5,   5,  20, -20, 120],
    [-20, -40,  -5,  -5,  -5,  -5, -40, -20],
    [ 20,  -5,  15,   3,   3,  15,  -5,  20],
    [  5,  -5,   3,   3,   3,   3,  -5,   5],
    [  5,  -5,   3,   3,   3,   3,  -5,   5],
    [ 20,  -5,  15,   3,   3,  15,  -5,  20],
    [-20, -40,  -5,  -5,  -5,  -5, -40, -20],
    [120, -20,  20,   5,   5,  20, -20, 120]
], dtype=np.int64)

CORNERS = [(0,0), (0,7), (7,0), (7,7)]
X_SQUARES = {(1,1):(0,0), (1,6):(0,7), (6,1):(7,0), (6,6):(7,7)}
C_SQUARES = {
    (0,1):(0,0), (1,0):(0,0),
    (0,6):(0,7), (1,7):(0,7),
    (6,0):(7,0), (7,1):(7,0),
    (6,7):(7,7), (7,6):(7,7),
}

def inside(r, c):
    return 0 <= r < 8 and 0 <= c < 8

def move_to_str(move):
    if move is None:
        return "pass"
    r, c = move
    return chr(ord('a') + c) + str(r + 1)

def legal_moves(you, opp):
    empty = (you | opp) == 0
    moves = []
    for r in range(8):
        for c in range(8):
            if not empty[r, c]:
                continue
            if is_legal(you, opp, r, c):
                moves.append((r, c))
    return moves

def is_legal(you, opp, r, c):
    if you[r, c] or opp[r, c]:
        return False
    for dr, dc in DIRS:
        rr, cc = r + dr, c + dc
        seen_opp = False
        while inside(rr, cc) and opp[rr, cc]:
            seen_opp = True
            rr += dr
            cc += dc
        if seen_opp and inside(rr, cc) and you[rr, cc]:
            return True
    return False

def apply_move(you, opp, move):
    r, c = move
    ny = you.copy()
    no = opp.copy()
    ny[r, c] = 1
    for dr, dc in DIRS:
        rr, cc = r + dr, c + dc
        line = []
        while inside(rr, cc) and no[rr, cc]:
            line.append((rr, cc))
            rr += dr
            cc += dc
        if line and inside(rr, cc) and ny[rr, cc]:
            for fr, fc in line:
                ny[fr, fc] = 1
                no[fr, fc] = 0
    return ny, no

def count_frontier(you, opp):
    occupied = you | opp
    frontier = 0
    ys = np.argwhere(you == 1)
    for r, c in ys:
        for dr, dc in DIRS:
            rr, cc = r + dr, c + dc
            if inside(rr, cc) and not occupied[rr, cc]:
                frontier += 1
                break
    return frontier

def stable_corner_rays(board_you, board_opp):
    stable = 0
    occupied = board_you | board_opp
    for cr, cc in CORNERS:
        if not board_you[cr, cc]:
            continue
        stable += 1
        # horizontal from corner
        if cc == 0:
            c = 1
            while c < 8 and board_you[cr, c]:
                stable += 1
                c += 1
        else:
            c = 6
            while c >= 0 and board_you[cr, c]:
                stable += 1
                c -= 1
        # vertical from corner
        if cr == 0:
            r = 1
            while r < 8 and board_you[r, cc]:
                stable += 1
                r += 1
        else:
            r = 6
            while r >= 0 and board_you[r, cc]:
                stable += 1
                r -= 1
    return stable

def evaluate(you, opp):
    occupied = you | opp
    empties = 64 - int(np.sum(occupied))
    my_discs = int(np.sum(you))
    opp_discs = int(np.sum(opp))

    my_moves = legal_moves(you, opp)
    opp_moves = legal_moves(opp, you)

    my_mob = len(my_moves)
    opp_mob = len(opp_moves)

    if my_mob == 0 and opp_mob == 0:
        # terminal
        if my_discs > opp_discs:
            return 10_000_000 + (my_discs - opp_discs)
        if my_discs < opp_discs:
            return -10_000_000 + (my_discs - opp_discs)
        return 0

    score = 0

    # Positional score
    score += int(np.sum(PST * you) - np.sum(PST * opp))

    # Corners
    my_corners = sum(int(you[r, c]) for r, c in CORNERS)
    opp_corners = sum(int(opp[r, c]) for r, c in CORNERS)
    score += 300 * (my_corners - opp_corners)

    # X-squares and C-squares: punish if adjacent corner is empty
    for (r, c), (cr, cc) in X_SQUARES.items():
        if not occupied[cr, cc]:
            if you[r, c]:
                score -= 120
            elif opp[r, c]:
                score += 120
    for (r, c), (cr, cc) in C_SQUARES.items():
        if not occupied[cr, cc]:
            if you[r, c]:
                score -= 50
            elif opp[r, c]:
                score += 50

    # Mobility
    if my_mob + opp_mob > 0:
        score += 140 * (my_mob - opp_mob)

    # Potential-ish frontier control
    my_front = count_frontier(you, opp)
    opp_front = count_frontier(opp, you)
    score += -35 * (my_front - opp_front)

    # Edge/corner stability approximation
    score += 40 * (stable_corner_rays(you, opp) - stable_corner_rays(opp, you))

    # Disc differential: de-emphasize early, emphasize late
    disc_diff = my_discs - opp_discs
    if empties > 40:
        score += 2 * disc_diff
    elif empties > 16:
        score += 8 * disc_diff
    else:
        score += 40 * disc_diff

    return int(score)

def move_order_key(you, opp, move):
    r, c = move
    key = 0

    # Immediate corner is best
    if (r, c) in CORNERS:
        key += 1_000_000

    # Avoid dangerous squares if corner empty
    if (r, c) in X_SQUARES:
        cr, cc = X_SQUARES[(r, c)]
        if not (you[cr, cc] or opp[cr, cc]):
            key -= 200_000
    if (r, c) in C_SQUARES:
        cr, cc = C_SQUARES[(r, c)]
        if not (you[cr, cc] or opp[cr, cc]):
            key -= 80_000

    key += int(PST[r, c]) * 100

    ny, no = apply_move(you, opp, move)
    opp_mob = len(legal_moves(no, ny))
    my_mob = len(legal_moves(ny, no))
    key += 500 * (my_mob - opp_mob)

    flips_gain = int(np.sum(ny) - np.sum(you))
    key += 10 * flips_gain

    return key

def alphabeta(you, opp, depth, alpha, beta, passed=False):
    my_moves = legal_moves(you, opp)

    if depth == 0:
        return evaluate(you, opp), None

    if not my_moves:
        opp_moves = legal_moves(opp, you)
        if not opp_moves:
            return evaluate(you, opp), None
        val, _ = alphabeta(opp, you, depth, -beta, -alpha, passed=True)
        return -val, None

    ordered = sorted(my_moves, key=lambda m: move_order_key(you, opp, m), reverse=True)

    best_move = ordered[0]
    best_val = -INF

    for mv in ordered:
        ny, no = apply_move(you, opp, mv)
        val, _ = alphabeta(no, ny, depth - 1, -beta, -alpha, passed=False)
        val = -val
        if val > best_val:
            best_val = val
            best_move = mv
        if best_val > alpha:
            alpha = best_val
        if alpha >= beta:
            break

    return best_val, best_move

def choose_depth(you, opp, num_moves):
    empties = 64 - int(np.sum(you | opp))
    if empties <= 10:
        return 8
    if empties <= 14:
        return 7
    if empties <= 20:
        return 6
    if empties <= 32:
        return 5 if num_moves <= 10 else 4
    return 4 if num_moves <= 8 else 3

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    you = np.asarray(you, dtype=np.uint8)
    opponent = np.asarray(opponent, dtype=np.uint8)

    moves = legal_moves(you, opponent)
    if not moves:
        return "pass"

    # Immediate corner grab
    for mv in moves:
        if mv in CORNERS:
            return move_to_str(mv)

    # If only one legal move, play it
    if len(moves) == 1:
        return move_to_str(moves[0])

    depth = choose_depth(you, opponent, len(moves))
    _, best = alphabeta(you, opponent, depth, -INF, INF)

    if best is None or best not in moves:
        # Safe fallback: best ordered legal move
        best = max(moves, key=lambda m: move_order_key(you, opponent, m))

    return move_to_str(best)

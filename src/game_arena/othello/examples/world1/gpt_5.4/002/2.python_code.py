
import numpy as np
import time

DIRS = [(-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)]

COLS = "abcdefgh"

# Standard strong Othello square weights
PST = np.array([
    [120, -20,  20,  5,  5, 20, -20, 120],
    [-20, -40,  -5, -5, -5, -5, -40, -20],
    [ 20,  -5,  15,  3,  3, 15,  -5,  20],
    [  5,  -5,   3,  3,  3,  3,  -5,   5],
    [  5,  -5,   3,  3,  3,  3,  -5,   5],
    [ 20,  -5,  15,  3,  3, 15,  -5,  20],
    [-20, -40,  -5, -5, -5, -5, -40, -20],
    [120, -20,  20,  5,  5, 20, -20, 120],
], dtype=np.int16)

CORNERS = [(0,0), (0,7), (7,0), (7,7)]
X_SQUARES = {
    (0,0): (1,1),
    (0,7): (1,6),
    (7,0): (6,1),
    (7,7): (6,6),
}
C_SQUARES = {
    (0,0): [(0,1), (1,0)],
    (0,7): [(0,6), (1,7)],
    (7,0): [(6,0), (7,1)],
    (7,7): [(6,7), (7,6)],
}

def inside(r, c):
    return 0 <= r < 8 and 0 <= c < 8

def rc_to_move(r, c):
    return COLS[c] + str(r + 1)

def legal_moves(you, opp):
    empty = ~(you | opp)
    moves = []
    for r in range(8):
        for c in range(8):
            if not empty[r, c]:
                continue
            if is_legal_move(you, opp, r, c):
                moves.append((r, c))
    return moves

def is_legal_move(you, opp, r, c):
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
    new_you = you.copy()
    new_opp = opp.copy()
    new_you[r, c] = True

    for dr, dc in DIRS:
        rr, cc = r + dr, c + dc
        path = []
        while inside(rr, cc) and new_opp[rr, cc]:
            path.append((rr, cc))
            rr += dr
            cc += dc
        if path and inside(rr, cc) and new_you[rr, cc]:
            for pr, pc in path:
                new_you[pr, pc] = True
                new_opp[pr, pc] = False
    return new_opp, new_you  # swap perspective: opponent to move next

def game_over(you, opp):
    if not np.any(~(you | opp)):
        return True
    if legal_moves(you, opp):
        return False
    if legal_moves(opp, you):
        return False
    return True

def disc_diff(you, opp):
    return int(np.sum(you) - np.sum(opp))

def frontier_count(board, other):
    occupied = board | other
    count = 0
    for r in range(8):
        for c in range(8):
            if not board[r, c]:
                continue
            for dr, dc in DIRS:
                rr, cc = r + dr, c + dc
                if inside(rr, cc) and not occupied[rr, cc]:
                    count += 1
                    break
    return count

def potential_mobility(you, opp):
    occupied = you | opp
    pot = 0
    seen = np.zeros((8, 8), dtype=bool)
    for r in range(8):
        for c in range(8):
            if not opp[r, c]:
                continue
            for dr, dc in DIRS:
                rr, cc = r + dr, c + dc
                if inside(rr, cc) and not occupied[rr, cc] and not seen[rr, cc]:
                    seen[rr, cc] = True
                    pot += 1
    return pot

def stable_corner_term(you, opp):
    score = 0
    for cr, cc in CORNERS:
        if you[cr, cc]:
            score += 1
        elif opp[cr, cc]:
            score -= 1
    return score

def corner_adjacency_term(you, opp):
    score = 0
    for corner in CORNERS:
        cr, cc = corner
        if you[cr, cc] or opp[cr, cc]:
            continue
        xr, xc = X_SQUARES[corner]
        if you[xr, xc]:
            score -= 1
        elif opp[xr, xc]:
            score += 1
        for rr, cc2 in C_SQUARES[corner]:
            if you[rr, cc2]:
                score -= 1
            elif opp[rr, cc2]:
                score += 1
    return score

def evaluate(you, opp):
    occupied = int(np.sum(you | opp))
    empties = 64 - occupied

    my_moves = legal_moves(you, opp)
    opp_moves = legal_moves(opp, you)
    my_mob = len(my_moves)
    opp_mob = len(opp_moves)

    if game_over(you, opp):
        d = disc_diff(you, opp)
        if d > 0:
            return 100000 + d
        elif d < 0:
            return -100000 + d
        else:
            return 0

    pos = int(np.sum(PST[you]) - np.sum(PST[opp]))
    corners = stable_corner_term(you, opp)
    adj = corner_adjacency_term(you, opp)

    my_front = frontier_count(you, opp)
    opp_front = frontier_count(opp, you)

    my_pmob = potential_mobility(you, opp)
    opp_pmob = potential_mobility(opp, you)

    discs = disc_diff(you, opp)

    if empties > 40:
        score = (
            8 * pos +
            80 * corners +
            35 * (my_mob - opp_mob) +
            10 * (my_pmob - opp_pmob) -
            12 * (my_front - opp_front) +
            60 * adj
        )
    elif empties > 14:
        score = (
            6 * pos +
            120 * corners +
            45 * (my_mob - opp_mob) +
            8 * (my_pmob - opp_pmob) -
            14 * (my_front - opp_front) +
            80 * adj +
            2 * discs
        )
    else:
        score = (
            3 * pos +
            180 * corners +
            25 * (my_mob - opp_mob) -
            8 * (my_front - opp_front) +
            100 * discs +
            40 * adj
        )
    return int(score)

def move_heuristic(you, opp, move):
    r, c = move
    score = int(PST[r, c]) * 10

    if (r, c) in CORNERS:
        score += 10000

    for corner in CORNERS:
        if (r, c) == X_SQUARES[corner]:
            cr, cc = corner
            if not you[cr, cc] and not opp[cr, cc]:
                score -= 3000
        if (r, c) in C_SQUARES[corner]:
            cr, cc = corner
            if not you[cr, cc] and not opp[cr, cc]:
                score -= 1500

    nopp, nyou = apply_move(you, opp, move)
    # Since apply_move swaps perspective, nyou is side that just moved
    # and nopp is opponent after move in original frame:
    # evaluate resulting state from mover perspective = evaluate(nyou, nopp)
    score += evaluate(nyou, nopp) // 20
    return score

def ordered_moves(you, opp):
    moves = legal_moves(you, opp)
    moves.sort(key=lambda m: move_heuristic(you, opp, m), reverse=True)
    return moves

def alphabeta(you, opp, depth, alpha, beta, end_time, passed=False):
    if time.perf_counter() >= end_time:
        raise TimeoutError

    moves = ordered_moves(you, opp)

    if depth == 0 or game_over(you, opp):
        return evaluate(you, opp), None

    if not moves:
        if passed:
            return evaluate(you, opp), None
        val, _ = alphabeta(opp, you, depth, -beta, -alpha, end_time, passed=True)
        return -val, None

    best_move = moves[0]
    best_val = -10**18

    for mv in moves:
        nopp, nyou = apply_move(you, opp, mv)
        val, _ = alphabeta(nopp, nyou, depth - 1, -beta, -alpha, end_time, passed=False)
        val = -val

        if val > best_val:
            best_val = val
            best_move = mv
        if best_val > alpha:
            alpha = best_val
        if alpha >= beta:
            break

    return best_val, best_move

def choose_move(you, opp):
    moves = legal_moves(you, opp)
    if not moves:
        return "pass"
    if len(moves) == 1:
        r, c = moves[0]
        return rc_to_move(r, c)

    occupied = int(np.sum(you | opp))
    empties = 64 - occupied

    # Immediate corner grab
    for mv in moves:
        if mv in CORNERS:
            return rc_to_move(mv[0], mv[1])

    # Time management
    start = time.perf_counter()
    budget = 0.92
    end_time = start + budget

    best_move = max(moves, key=lambda m: move_heuristic(you, opp, m))

    # Search depth selection by phase
    if empties <= 10:
        max_depth = 12
    elif empties <= 14:
        max_depth = 10
    elif empties <= 20:
        max_depth = 7
    elif empties <= 32:
        max_depth = 5
    else:
        max_depth = 4

    for depth in range(2, max_depth + 1):
        try:
            _, mv = alphabeta(you, opp, depth, -10**18, 10**18, end_time, passed=False)
            if mv is not None:
                best_move = mv
        except TimeoutError:
            break

    return rc_to_move(best_move[0], best_move[1])

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    you_b = np.asarray(you, dtype=bool)
    opp_b = np.asarray(opponent, dtype=bool)

    # Safety: if somehow invalid overlap appears, remove overlap from opponent
    overlap = you_b & opp_b
    if np.any(overlap):
        opp_b = opp_b & (~overlap)

    move = choose_move(you_b, opp_b)

    # Final legality safeguard
    legal = legal_moves(you_b, opp_b)
    if not legal:
        return "pass"
    legal_strs = {rc_to_move(r, c) for r, c in legal}
    if move in legal_strs:
        return move
    r, c = legal[0]
    return rc_to_move(r, c)

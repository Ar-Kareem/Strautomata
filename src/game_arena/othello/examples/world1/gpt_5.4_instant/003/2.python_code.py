
import numpy as np

# Othello / Reversi policy
# API:
# def policy(you: np.ndarray, opponent: np.ndarray) -> str

DIRS = [(-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)]

COLS = "abcdefgh"

# Classic-ish positional weights
PST = np.array([
    [120, -20,  20,   5,   5,  20, -20, 120],
    [-20, -40,  -5,  -5,  -5,  -5, -40, -20],
    [ 20,  -5,  15,   3,   3,  15,  -5,  20],
    [  5,  -5,   3,   3,   3,   3,  -5,   5],
    [  5,  -5,   3,   3,   3,   3,  -5,   5],
    [ 20,  -5,  15,   3,   3,  15,  -5,  20],
    [-20, -40,  -5,  -5,  -5,  -5, -40, -20],
    [120, -20,  20,   5,   5,  20, -20, 120],
], dtype=np.int32)

CORNERS = [(0, 0), (0, 7), (7, 0), (7, 7)]
X_SQUARES = {(1, 1): (0, 0), (1, 6): (0, 7), (6, 1): (7, 0), (6, 6): (7, 7)}
C_SQUARES = {
    (0, 1): (0, 0), (1, 0): (0, 0),
    (0, 6): (0, 7), (1, 7): (0, 7),
    (6, 0): (7, 0), (7, 1): (7, 0),
    (6, 7): (7, 7), (7, 6): (7, 7),
}

INF = 10**9


def in_bounds(r, c):
    return 0 <= r < 8 and 0 <= c < 8


def move_to_str(move):
    r, c = move
    return f"{COLS[c]}{r+1}"


def legal_moves(you, opp):
    empties = (you | opp) == 0
    moves = []
    for r in range(8):
        for c in range(8):
            if not empties[r, c]:
                continue
            if is_legal_move(you, opp, r, c):
                moves.append((r, c))
    return moves


def is_legal_move(you, opp, r, c):
    for dr, dc in DIRS:
        rr, cc = r + dr, c + dc
        seen_opp = False
        while in_bounds(rr, cc) and opp[rr, cc]:
            seen_opp = True
            rr += dr
            cc += dc
        if seen_opp and in_bounds(rr, cc) and you[rr, cc]:
            return True
    return False


def apply_move(you, opp, move):
    r, c = move
    new_you = you.copy()
    new_opp = opp.copy()
    new_you[r, c] = 1

    for dr, dc in DIRS:
        rr, cc = r + dr, c + dc
        path = []
        while in_bounds(rr, cc) and new_opp[rr, cc]:
            path.append((rr, cc))
            rr += dr
            cc += dc
        if path and in_bounds(rr, cc) and new_you[rr, cc]:
            for fr, fc in path:
                new_you[fr, fc] = 1
                new_opp[fr, fc] = 0
    return new_opp, new_you  # swap perspective: next player to move first


def count_frontier(arr, occupied):
    cnt = 0
    for r in range(8):
        for c in range(8):
            if arr[r, c]:
                for dr, dc in DIRS:
                    rr, cc = r + dr, c + dc
                    if in_bounds(rr, cc) and not occupied[rr, cc]:
                        cnt += 1
                        break
    return cnt


def corner_count(arr):
    return sum(int(arr[r, c]) for r, c in CORNERS)


def evaluate(you, opp):
    occupied = (you | opp).astype(np.uint8)
    empties = 64 - int(occupied.sum())
    my_discs = int(you.sum())
    opp_discs = int(opp.sum())

    my_moves = legal_moves(you, opp)
    opp_moves = legal_moves(opp, you)
    my_mob = len(my_moves)
    opp_mob = len(opp_moves)

    if my_mob == 0 and opp_mob == 0:
        diff = my_discs - opp_discs
        if diff > 0:
            return 100000 + diff
        elif diff < 0:
            return -100000 + diff
        else:
            return 0

    # Game phase interpolation
    progress = (64 - empties) / 64.0

    # Disc diff: low weight early, higher late
    disc_score = 0
    if my_discs + opp_discs > 0:
        disc_score = 100 * (my_discs - opp_discs) / (my_discs + opp_discs)

    # Mobility
    mob_score = 0
    if my_mob + opp_mob > 0:
        mob_score = 100 * (my_mob - opp_mob) / (my_mob + opp_mob)

    # Positional table
    pst_score = int((PST * you).sum() - (PST * opp).sum())

    # Corners
    my_corners = corner_count(you)
    opp_corners = corner_count(opp)
    corner_score = 25 * (my_corners - opp_corners)

    # Frontier discs
    my_front = count_frontier(you, occupied)
    opp_front = count_frontier(opp, occupied)
    frontier_score = 0
    if my_front + opp_front > 0:
        frontier_score = -100 * (my_front - opp_front) / (my_front + opp_front)

    # Corner-adjacent danger if corner is empty
    adj_score = 0
    for (r, c), corner in X_SQUARES.items():
        cr, cc = corner
        if not occupied[cr, cc]:
            if you[r, c]:
                adj_score -= 18
            elif opp[r, c]:
                adj_score += 18
    for (r, c), corner in C_SQUARES.items():
        cr, cc = corner
        if not occupied[cr, cc]:
            if you[r, c]:
                adj_score -= 10
            elif opp[r, c]:
                adj_score += 10

    # Blend weights by phase
    score = (
        (8 + 20 * progress) * disc_score +
        (85 - 25 * progress) * mob_score +
        1.2 * pst_score +
        80 * corner_score +
        (40 - 15 * progress) * frontier_score +
        12 * adj_score
    )

    return int(score)


def move_heuristic(you, opp, move):
    r, c = move
    score = PST[r, c] * 10

    if (r, c) in CORNERS:
        score += 100000

    if (r, c) in X_SQUARES:
        cr, cc = X_SQUARES[(r, c)]
        if not (you[cr, cc] or opp[cr, cc]):
            score -= 5000
    if (r, c) in C_SQUARES:
        cr, cc = C_SQUARES[(r, c)]
        if not (you[cr, cc] or opp[cr, cc]):
            score -= 2500

    # Prefer moves that reduce opponent mobility
    next_opp, next_you = apply_move(you, opp, move)
    opp_moves = legal_moves(next_opp, next_you)
    score -= 120 * len(opp_moves)

    # Slight preference for disc gain later
    flips_gain = int(next_you.sum() - you.sum())
    occupied = int((you | opp).sum())
    if occupied > 44:
        score += 30 * flips_gain
    else:
        score -= 5 * flips_gain  # early greedy flips often bad

    return score


def ordered_moves(you, opp, moves):
    return sorted(moves, key=lambda mv: move_heuristic(you, opp, mv), reverse=True)


def negamax(you, opp, depth, alpha, beta, passed):
    moves = legal_moves(you, opp)

    if depth == 0:
        return evaluate(you, opp), None

    if not moves:
        opp_moves = legal_moves(opp, you)
        if not opp_moves:
            return evaluate(you, opp), None
        if passed:
            return evaluate(you, opp), None
        score, _ = negamax(opp, you, depth, -beta, -alpha, True)
        return -score, None

    best_move = moves[0]
    best_score = -INF

    for mv in ordered_moves(you, opp, moves):
        next_opp, next_you = apply_move(you, opp, mv)
        score, _ = negamax(next_opp, next_you, depth - 1, -beta, -alpha, False)
        score = -score

        if score > best_score:
            best_score = score
            best_move = mv

        if best_score > alpha:
            alpha = best_score
        if alpha >= beta:
            break

    return best_score, best_move


def choose_depth(you, opp):
    occupied = int((you | opp).sum())
    empties = 64 - occupied

    if empties <= 10:
        return 8
    if empties <= 14:
        return 7
    if empties <= 20:
        return 6
    if empties <= 30:
        return 5
    return 4


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    you = np.asarray(you, dtype=np.uint8)
    opponent = np.asarray(opponent, dtype=np.uint8)

    moves = legal_moves(you, opponent)
    if not moves:
        return "pass"

    # Immediate corner if available
    for mv in moves:
        if mv in CORNERS:
            return move_to_str(mv)

    depth = choose_depth(you, opponent)
    _, best_move = negamax(you, opponent, depth, -INF, INF, False)

    if best_move is None:
        # Safe fallback: strongest ordered legal move
        best_move = ordered_moves(you, opponent, moves)[0]

    return move_to_str(best_move)

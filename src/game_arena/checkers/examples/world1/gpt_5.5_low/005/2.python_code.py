
import time
import math

TIME_LIMIT = 0.92

def policy(my_men, my_kings, opp_men, opp_kings, color):
    start = time.time()

    my_men = tuple(my_men)
    my_kings = tuple(my_kings)
    opp_men = tuple(opp_men)
    opp_kings = tuple(opp_kings)

    root = (my_men, my_kings, opp_men, opp_kings, color)

    moves = generate_moves(my_men, my_kings, opp_men, opp_kings, color)
    if not moves:
        # No legal move exists. This should only occur in a lost position.
        pieces = list(my_men) + list(my_kings)
        if pieces:
            return (pieces[0], pieces[0])
        return ((0, 0), (0, 0))

    if len(moves) == 1:
        return moves[0]

    best_move = moves[0]
    best_score = -10**18

    ordered = order_moves(moves, my_men, my_kings, opp_men, opp_kings, color)

    # Iterative deepening. Usually reaches depth 5-7 within the time limit.
    depth = 1
    max_depth = 8

    while depth <= max_depth:
        if time.time() - start > TIME_LIMIT:
            break

        current_best = best_move
        current_score = -10**18
        alpha = -10**18
        beta = 10**18

        completed = True

        for mv in ordered:
            if time.time() - start > TIME_LIMIT:
                completed = False
                break

            child = make_move(my_men, my_kings, opp_men, opp_kings, color, mv)
            score = -negamax(child, depth - 1, -beta, -alpha, start)

            if score > current_score:
                current_score = score
                current_best = mv

            if score > alpha:
                alpha = score

        if completed:
            best_move = current_best
            best_score = current_score
            ordered = [best_move] + [m for m in ordered if m != best_move]
            depth += 1
        else:
            break

    return best_move


def inside(r, c):
    return 0 <= r < 8 and 0 <= c < 8


def opponent_color(color):
    return 'w' if color == 'b' else 'b'


def man_dirs(color):
    if color == 'b':
        return [(-1, -1), (-1, 1)]
    return [(1, -1), (1, 1)]


KING_DIRS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]


def generate_moves(my_men, my_kings, opp_men, opp_kings, color):
    occupied = set(my_men) | set(my_kings) | set(opp_men) | set(opp_kings)
    opp = set(opp_men) | set(opp_kings)

    captures = []

    for r, c in my_men:
        for dr, dc in man_dirs(color):
            mr, mc = r + dr, c + dc
            tr, tc = r + 2 * dr, c + 2 * dc
            if inside(tr, tc) and (mr, mc) in opp and (tr, tc) not in occupied:
                captures.append(((r, c), (tr, tc)))

    for r, c in my_kings:
        for dr, dc in KING_DIRS:
            mr, mc = r + dr, c + dc
            tr, tc = r + 2 * dr, c + 2 * dc
            if inside(tr, tc) and (mr, mc) in opp and (tr, tc) not in occupied:
                captures.append(((r, c), (tr, tc)))

    if captures:
        return captures

    moves = []

    for r, c in my_men:
        for dr, dc in man_dirs(color):
            tr, tc = r + dr, c + dc
            if inside(tr, tc) and (tr, tc) not in occupied:
                moves.append(((r, c), (tr, tc)))

    for r, c in my_kings:
        for dr, dc in KING_DIRS:
            tr, tc = r + dr, c + dc
            if inside(tr, tc) and (tr, tc) not in occupied:
                moves.append(((r, c), (tr, tc)))

    return moves


def make_move(my_men, my_kings, opp_men, opp_kings, color, mv):
    frm, to = mv
    fr, fc = frm
    tr, tc = to

    my_men = set(my_men)
    my_kings = set(my_kings)
    opp_men = set(opp_men)
    opp_kings = set(opp_kings)

    is_king = frm in my_kings

    if is_king:
        my_kings.remove(frm)
    else:
        my_men.remove(frm)

    if abs(tr - fr) == 2:
        cap = ((fr + tr) // 2, (fc + tc) // 2)
        opp_men.discard(cap)
        opp_kings.discard(cap)

    if is_king:
        my_kings.add(to)
    else:
        if (color == 'b' and tr == 0) or (color == 'w' and tr == 7):
            my_kings.add(to)
        else:
            my_men.add(to)

    # Return from the next player's perspective.
    return (
        tuple(opp_men),
        tuple(opp_kings),
        tuple(my_men),
        tuple(my_kings),
        opponent_color(color)
    )


def negamax(state, depth, alpha, beta, start):
    if time.time() - start > TIME_LIMIT:
        return evaluate(*state)

    my_men, my_kings, opp_men, opp_kings, color = state

    moves = generate_moves(my_men, my_kings, opp_men, opp_kings, color)

    if not moves:
        return -1000000 - depth

    if depth <= 0:
        return quiescence(state, alpha, beta, start, 3)

    moves = order_moves(moves, my_men, my_kings, opp_men, opp_kings, color)

    best = -10**18

    for mv in moves:
        child = make_move(my_men, my_kings, opp_men, opp_kings, color, mv)
        score = -negamax(child, depth - 1, -beta, -alpha, start)

        if score > best:
            best = score

        if best > alpha:
            alpha = best

        if alpha >= beta:
            break

        if time.time() - start > TIME_LIMIT:
            break

    return best


def quiescence(state, alpha, beta, start, qdepth):
    my_men, my_kings, opp_men, opp_kings, color = state

    stand_pat = evaluate(my_men, my_kings, opp_men, opp_kings, color)

    if qdepth <= 0 or time.time() - start > TIME_LIMIT:
        return stand_pat

    if stand_pat >= beta:
        return beta

    if alpha < stand_pat:
        alpha = stand_pat

    moves = generate_moves(my_men, my_kings, opp_men, opp_kings, color)
    captures = [m for m in moves if abs(m[0][0] - m[1][0]) == 2]

    if not captures:
        return stand_pat

    captures = order_moves(captures, my_men, my_kings, opp_men, opp_kings, color)

    for mv in captures:
        child = make_move(my_men, my_kings, opp_men, opp_kings, color, mv)
        score = -quiescence(child, -beta, -alpha, start, qdepth - 1)

        if score >= beta:
            return beta

        if score > alpha:
            alpha = score

    return alpha


def order_moves(moves, my_men, my_kings, opp_men, opp_kings, color):
    opp_kings_set = set(opp_kings)
    my_men_set = set(my_men)

    def score_move(mv):
        frm, to = mv
        fr, fc = frm
        tr, tc = to
        score = 0

        if abs(tr - fr) == 2:
            score += 1000
            cap = ((fr + tr) // 2, (fc + tc) // 2)
            if cap in opp_kings_set:
                score += 300

        if frm in my_men_set and ((color == 'b' and tr == 0) or (color == 'w' and tr == 7)):
            score += 500

        # Prefer central destinations.
        score += 20 - abs(3.5 - tr) * 3 - abs(3.5 - tc) * 3

        # Slightly prefer advancing men.
        if frm in my_men_set:
            if color == 'b':
                score += (fr - tr) * 5
            else:
                score += (tr - fr) * 5

        return score

    return sorted(moves, key=score_move, reverse=True)


def evaluate(my_men, my_kings, opp_men, opp_kings, color):
    score = 0

    my_men_set = set(my_men)
    my_kings_set = set(my_kings)
    opp_men_set = set(opp_men)
    opp_kings_set = set(opp_kings)

    my_all = my_men_set | my_kings_set
    opp_all = opp_men_set | opp_kings_set
    occupied = my_all | opp_all

    # Material.
    score += 100 * len(my_men_set)
    score += 180 * len(my_kings_set)
    score -= 100 * len(opp_men_set)
    score -= 180 * len(opp_kings_set)

    # Promotion progress and back-row guards.
    for r, c in my_men_set:
        progress = (7 - r) if color == 'b' else r
        score += progress * 7

        if (color == 'b' and r == 7) or (color == 'w' and r == 0):
            score += 10

    opp_color = opponent_color(color)
    for r, c in opp_men_set:
        progress = (7 - r) if opp_color == 'b' else r
        score -= progress * 7

        if (opp_color == 'b' and r == 7) or (opp_color == 'w' and r == 0):
            score -= 10

    # Center control.
    for r, c in my_all:
        score += int(10 - 2 * (abs(3.5 - r) + abs(3.5 - c)))

    for r, c in opp_all:
        score -= int(10 - 2 * (abs(3.5 - r) + abs(3.5 - c)))

    # Mobility.
    my_moves = len(generate_moves(my_men, my_kings, opp_men, opp_kings, color))
    opp_moves = len(generate_moves(opp_men, opp_kings, my_men, my_kings, opp_color))
    score += 4 * my_moves
    score -= 4 * opp_moves

    # Tactical exposure: pieces that can be captured soon.
    score -= 25 * count_vulnerable(my_men_set, my_kings_set, opp_men_set, opp_kings_set, color)
    score += 25 * count_vulnerable(opp_men_set, opp_kings_set, my_men_set, my_kings_set, opp_color)

    # Endgame: kings become more valuable when material is low.
    total_pieces = len(my_all) + len(opp_all)
    if total_pieces <= 8:
        score += 20 * len(my_kings_set)
        score -= 20 * len(opp_kings_set)

    return score


def count_vulnerable(my_men, my_kings, opp_men, opp_kings, color):
    my_all = my_men | my_kings
    opp_all = opp_men | opp_kings
    occupied = my_all | opp_all

    opp_color = opponent_color(color)
    vulnerable = set()

    for r, c in opp_men:
        for dr, dc in man_dirs(opp_color):
            mr, mc = r + dr, c + dc
            lr, lc = r + 2 * dr, c + 2 * dc
            if (mr, mc) in my_all and inside(lr, lc) and (lr, lc) not in occupied:
                vulnerable.add((mr, mc))

    for r, c in opp_kings:
        for dr, dc in KING_DIRS:
            mr, mc = r + dr, c + dc
            lr, lc = r + 2 * dr, c + 2 * dc
            if (mr, mc) in my_all and inside(lr, lc) and (lr, lc) not in occupied:
                vulnerable.add((mr, mc))

    return len(vulnerable)

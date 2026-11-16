
import time
import math
from functools import lru_cache

# Checkers policy for 8x8 American/English-style draughts:
# - Men move forward only.
# - Men capture forward only in this implementation.
# - Kings move/capture in all diagonal directions.
# - Captures are mandatory.
# The API asks for a single from/to move. If a multi-jump is available in the
# arena, the game engine will typically call policy again after the first jump.

INF = 10**9
TIME_LIMIT = 0.88

DIRS_KING = ((1, 1), (1, -1), (-1, 1), (-1, -1))


def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    start = time.perf_counter()

    my_men = tuple(sorted(tuple(x) for x in my_men))
    my_kings = tuple(sorted(tuple(x) for x in my_kings))
    opp_men = tuple(sorted(tuple(x) for x in opp_men))
    opp_kings = tuple(sorted(tuple(x) for x in opp_kings))

    root = (my_men, my_kings, opp_men, opp_kings, color)
    moves = legal_moves_side(my_men, my_kings, opp_men, opp_kings, color)
    if not moves:
        # Should not happen in normal play, but return a syntactically valid move
        # from one of our pieces if possible.
        if my_men:
            p = my_men[0]
            return (p, p)
        if my_kings:
            p = my_kings[0]
            return (p, p)
        return ((0, 0), (0, 0))

    best_move = order_moves(moves, root)[0]
    depth = 1

    # Iterative deepening. Typical arena positions fit depth 5-7 in Python.
    while True:
        if time.perf_counter() - start > TIME_LIMIT:
            break
        try:
            val, mv = alphabeta_root(root, depth, start)
            if mv is not None:
                best_move = mv
            depth += 1
            if depth > 8:
                break
        except TimeoutError:
            break

    return best_move


def inside(r, c):
    return 0 <= r < 8 and 0 <= c < 8


def forward_dirs(color):
    # User spec: black moves downwards to lower row values; white upwards.
    return ((-1, 1), (-1, -1)) if color == 'b' else ((1, 1), (1, -1))


def opp_color(color):
    return 'w' if color == 'b' else 'b'


def legal_moves_side(my_men, my_kings, opp_men, opp_kings, color):
    mine = set(my_men) | set(my_kings)
    opp = set(opp_men) | set(opp_kings)
    occ = mine | opp

    captures = []

    # Men captures: forward only.
    for r, c in my_men:
        for dr, dc in forward_dirs(color):
            mr, mc = r + dr, c + dc
            tr, tc = r + 2 * dr, c + 2 * dc
            if inside(tr, tc) and (mr, mc) in opp and (tr, tc) not in occ:
                captures.append(((r, c), (tr, tc)))

    # King captures.
    for r, c in my_kings:
        for dr, dc in DIRS_KING:
            mr, mc = r + dr, c + dc
            tr, tc = r + 2 * dr, c + 2 * dc
            if inside(tr, tc) and (mr, mc) in opp and (tr, tc) not in occ:
                captures.append(((r, c), (tr, tc)))

    if captures:
        return captures

    moves = []

    # Men quiet moves.
    for r, c in my_men:
        for dr, dc in forward_dirs(color):
            tr, tc = r + dr, c + dc
            if inside(tr, tc) and (tr, tc) not in occ:
                moves.append(((r, c), (tr, tc)))

    # King quiet moves.
    for r, c in my_kings:
        for dr, dc in DIRS_KING:
            tr, tc = r + dr, c + dc
            if inside(tr, tc) and (tr, tc) not in occ:
                moves.append(((r, c), (tr, tc)))

    return moves


def apply_move(state, move):
    my_men, my_kings, opp_men, opp_kings, color = state
    frm, to = move
    fr, fc = frm
    tr, tc = to

    my_men = list(my_men)
    my_kings = list(my_kings)
    opp_men = list(opp_men)
    opp_kings = list(opp_kings)

    is_king = frm in my_kings
    if is_king:
        my_kings.remove(frm)
    else:
        my_men.remove(frm)

    # Capture removal.
    if abs(tr - fr) == 2:
        cap = ((fr + tr) // 2, (fc + tc) // 2)
        if cap in opp_men:
            opp_men.remove(cap)
        elif cap in opp_kings:
            opp_kings.remove(cap)

    # Promotion.
    promote_row = 0 if color == 'b' else 7
    if (not is_king) and tr == promote_row:
        my_kings.append(to)
    elif is_king:
        my_kings.append(to)
    else:
        my_men.append(to)

    # Swap perspective: returned state is for next player to move.
    return (
        tuple(sorted(opp_men)),
        tuple(sorted(opp_kings)),
        tuple(sorted(my_men)),
        tuple(sorted(my_kings)),
        opp_color(color),
    )


def alphabeta_root(state, depth, start):
    moves = legal_moves_side(*state)
    if not moves:
        return -INF, None

    alpha = -INF
    beta = INF
    best_val = -INF
    best_move = None

    for mv in order_moves(moves, state):
        if time.perf_counter() - start > TIME_LIMIT:
            raise TimeoutError
        nxt = apply_move(state, mv)
        val = -alphabeta(nxt, depth - 1, -beta, -alpha, start)
        if val > best_val:
            best_val = val
            best_move = mv
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

    return best_val, best_move


def alphabeta(state, depth, alpha, beta, start):
    if time.perf_counter() - start > TIME_LIMIT:
        raise TimeoutError

    moves = legal_moves_side(*state)
    if not moves:
        return -50000 - depth

    if depth <= 0:
        return quiesce(state, alpha, beta, start, 2)

    for mv in order_moves(moves, state):
        nxt = apply_move(state, mv)
        val = -alphabeta(nxt, depth - 1, -beta, -alpha, start)
        if val >= beta:
            return beta
        if val > alpha:
            alpha = val

    return alpha


def quiesce(state, alpha, beta, start, qdepth):
    stand = evaluate(state)
    if stand >= beta:
        return beta
    if stand > alpha:
        alpha = stand
    if qdepth <= 0:
        return alpha

    moves = legal_moves_side(*state)
    captures = [m for m in moves if abs(m[0][0] - m[1][0]) == 2]
    if not captures:
        return alpha

    for mv in order_moves(captures, state):
        if time.perf_counter() - start > TIME_LIMIT:
            raise TimeoutError
        val = -quiesce(apply_move(state, mv), -beta, -alpha, start, qdepth - 1)
        if val >= beta:
            return beta
        if val > alpha:
            alpha = val
    return alpha


def evaluate(state):
    my_men, my_kings, opp_men, opp_kings, color = state

    score = 0

    # Material.
    score += 100 * len(my_men) + 175 * len(my_kings)
    score -= 100 * len(opp_men) + 175 * len(opp_kings)

    my_occ = set(my_men) | set(my_kings)
    opp_occ = set(opp_men) | set(opp_kings)
    occ = my_occ | opp_occ

    # Men advancement / promotion pressure.
    for r, c in my_men:
        adv = r if color == 'w' else 7 - r
        score += 7 * adv
        if c in (2, 3, 4, 5):
            score += 4
        if r in (0, 7):
            score += 2

    ocolor = opp_color(color)
    for r, c in opp_men:
        adv = r if ocolor == 'w' else 7 - r
        score -= 7 * adv
        if c in (2, 3, 4, 5):
            score -= 4
        if r in (0, 7):
            score -= 2

    # Kings prefer central active squares.
    for r, c in my_kings:
        score += 8 - (abs(3.5 - r) + abs(3.5 - c))
    for r, c in opp_kings:
        score -= 8 - (abs(3.5 - r) + abs(3.5 - c))

    # Back-row guard is useful when pieces remain unkinged.
    my_home = 0 if color == 'w' else 7
    opp_home = 0 if color == 'b' else 7
    score += 6 * sum(1 for p in my_men if p[0] == my_home)
    score -= 6 * sum(1 for p in opp_men if p[0] == opp_home)

    # Mobility.
    my_mob = len(legal_moves_side(my_men, my_kings, opp_men, opp_kings, color))
    opp_mob = len(legal_moves_side(opp_men, opp_kings, my_men, my_kings, opp_color(color)))
    score += 3 * my_mob - 3 * opp_mob

    # Immediate tactical danger/opportunity.
    my_caps = count_captures(my_men, my_kings, opp_men, opp_kings, color)
    opp_caps = count_captures(opp_men, opp_kings, my_men, my_kings, opp_color(color))
    score += 22 * my_caps - 26 * opp_caps

    # Edge safety: pieces on edges are harder to capture, but too many edge
    # kings can be passive, so keep this modest.
    score += 3 * sum(1 for r, c in my_occ if c == 0 or c == 7)
    score -= 3 * sum(1 for r, c in opp_occ if c == 0 or c == 7)

    return int(score)


def count_captures(my_men, my_kings, opp_men, opp_kings, color):
    mine = set(my_men) | set(my_kings)
    opp = set(opp_men) | set(opp_kings)
    occ = mine | opp
    n = 0

    for r, c in my_men:
        for dr, dc in forward_dirs(color):
            mr, mc = r + dr, c + dc
            tr, tc = r + 2 * dr, c + 2 * dc
            if inside(tr, tc) and (mr, mc) in opp and (tr, tc) not in occ:
                n += 1

    for r, c in my_kings:
        for dr, dc in DIRS_KING:
            mr, mc = r + dr, c + dc
            tr, tc = r + 2 * dr, c + 2 * dc
            if inside(tr, tc) and (mr, mc) in opp and (tr, tc) not in occ:
                n += 1

    return n


def order_moves(moves, state):
    my_men, my_kings, opp_men, opp_kings, color = state
    opp_set = set(opp_men) | set(opp_kings)
    my_kset = set(my_kings)

    def key(mv):
        (fr, fc), (tr, tc) = mv
        s = 0
        if abs(tr - fr) == 2:
            cap = ((fr + tr) // 2, (fc + tc) // 2)
            s += 1000
            if cap in opp_kings:
                s += 250
            else:
                s += 120
        if (fr, fc) not in my_kset and tr == (0 if color == 'b' else 7):
            s += 500
        # Prefer center and forward-progress moves.
        s += 8 - int(abs(3.5 - tr) + abs(3.5 - tc))
        if (fr, fc) not in my_kset:
            s += (tr - fr) if color == 'w' else (fr - tr)
        # Avoid voluntarily moving to extreme edge unless tactically useful.
        if tc in (0, 7):
            s += 2
        return -s

    return sorted(moves, key=key)

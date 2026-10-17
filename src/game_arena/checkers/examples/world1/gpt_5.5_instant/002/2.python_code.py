
import time
import math
from functools import lru_cache

# Checkers policy for 8x8 American checkers / English draughts-like rules.
# Coordinates: row 0 bottom, row 7 top.
# color: 'b' moves toward lower row values, 'w' toward higher row values.

INF = 10**9
TIME_LIMIT = 0.92

# Tunable evaluation weights
MAN_VAL = 100
KING_VAL = 175


def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    start_time = time.time()
    my_men = tuple(sorted(tuple(x) for x in my_men))
    my_kings = tuple(sorted(tuple(x) for x in my_kings))
    opp_men = tuple(sorted(tuple(x) for x in opp_men))
    opp_kings = tuple(sorted(tuple(x) for x in opp_kings))
    root = (frozenset(my_men), frozenset(my_kings), frozenset(opp_men), frozenset(opp_kings), color)

    legal = generate_moves(root)
    if not legal:
        # Should not happen in normal arena use. Return syntactically valid own-piece fallback if possible.
        if my_men:
            p = my_men[0]
            return (p, p)
        if my_kings:
            p = my_kings[0]
            return (p, p)
        return ((0, 0), (0, 0))

    # Immediate fallback: best ordered legal move.
    legal = order_moves(root, legal)
    best_move = legal[0][0]

    tt = {}

    def time_up():
        return time.time() - start_time > TIME_LIMIT

    def terminal_eval(state, ply):
        moves = generate_moves(state)
        if not moves:
            return -500000 + ply
        return None

    def alphabeta(state, depth, alpha, beta, ply):
        if time_up():
            raise TimeoutError

        key = (state, depth)
        if key in tt:
            tt_depth, tt_val, tt_flag = tt[key]
            if tt_depth >= depth:
                if tt_flag == 0:
                    return tt_val
                if tt_flag == -1 and tt_val <= alpha:
                    return tt_val
                if tt_flag == 1 and tt_val >= beta:
                    return tt_val

        moves = generate_moves(state)
        if not moves:
            return -500000 + ply

        if depth <= 0:
            return quiescence(state, alpha, beta, ply, 3)

        orig_alpha = alpha
        best = -INF
        for mv, child, score_hint in order_moves(state, moves):
            val = -alphabeta(child, depth - 1, -beta, -alpha, ply + 1)
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

        flag = 0
        if best <= orig_alpha:
            flag = -1
        elif best >= beta:
            flag = 1
        tt[key] = (depth, best, flag)
        return best

    def quiescence(state, alpha, beta, ply, qdepth):
        if time_up():
            raise TimeoutError

        stand = evaluate(state)
        if stand >= beta:
            return beta
        if alpha < stand:
            alpha = stand
        if qdepth <= 0:
            return alpha

        moves = generate_moves(state)
        cap_moves = [(m, c, h) for (m, c, h) in moves if abs(m[0][0] - m[1][0]) == 2]
        if not cap_moves:
            return alpha

        for mv, child, score_hint in order_moves(state, cap_moves):
            val = -quiescence(child, -beta, -alpha, ply + 1, qdepth - 1)
            if val >= beta:
                return beta
            if val > alpha:
                alpha = val
        return alpha

    # Iterative deepening; depth counts full turns.
    max_depth = 8
    for depth in range(1, max_depth + 1):
        try:
            alpha = -INF
            beta = INF
            current_best = best_move
            current_val = -INF
            for mv, child, hint in order_moves(root, legal):
                if time_up():
                    raise TimeoutError
                val = -alphabeta(child, depth - 1, -beta, -alpha, 1)
                if val > current_val:
                    current_val = val
                    current_best = mv
                if val > alpha:
                    alpha = val
            best_move = current_best
        except TimeoutError:
            break

    return best_move


def opponent_color(color):
    return 'w' if color == 'b' else 'b'


def man_dirs(color):
    # Black moves downwards to lower row values; white upwards.
    if color == 'b':
        return [(-1, -1), (-1, 1)]
    return [(1, -1), (1, 1)]


KING_DIRS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]


def in_bounds(r, c):
    return 0 <= r < 8 and 0 <= c < 8


def promote_row(color):
    return 0 if color == 'b' else 7


def state_key_parts(state):
    return state


@lru_cache(maxsize=200000)
def generate_moves(state):
    my_men, my_kings, opp_men, opp_kings, color = state
    occupied = set(my_men) | set(my_kings) | set(opp_men) | set(opp_kings)
    opp_all = set(opp_men) | set(opp_kings)

    captures = []

    # Generate all full capture sequences but return only initial from-to, with final child state.
    for p in my_men:
        dirs = man_dirs(color)
        _gen_piece_captures(
            start=p, pos=p, is_king=False, color=color,
            my_men=set(my_men), my_kings=set(my_kings),
            opp_men=set(opp_men), opp_kings=set(opp_kings),
            captured_any=False, first_to=None, results=captures,
            dirs=dirs
        )

    for p in my_kings:
        _gen_piece_captures(
            start=p, pos=p, is_king=True, color=color,
            my_men=set(my_men), my_kings=set(my_kings),
            opp_men=set(opp_men), opp_kings=set(opp_kings),
            captured_any=False, first_to=None, results=captures,
            dirs=KING_DIRS
        )

    if captures:
        # Deduplicate identical initial move + resulting state.
        seen = set()
        out = []
        for mv, child, hint in captures:
            key = (mv, child)
            if key not in seen:
                seen.add(key)
                out.append((mv, child, hint))
        return tuple(out)

    quiets = []
    for p in my_men:
        for dr, dc in man_dirs(color):
            nr, nc = p[0] + dr, p[1] + dc
            if in_bounds(nr, nc) and (nr, nc) not in occupied:
                n_my_men = set(my_men)
                n_my_kings = set(my_kings)
                n_my_men.remove(p)
                if nr == promote_row(color):
                    n_my_kings.add((nr, nc))
                    promo = 50
                else:
                    n_my_men.add((nr, nc))
                    promo = 0
                child = make_child(n_my_men, n_my_kings, set(opp_men), set(opp_kings), color)
                quiets.append(((p, (nr, nc)), child, promo + center_bonus((nr, nc))))
    for p in my_kings:
        for dr, dc in KING_DIRS:
            nr, nc = p[0] + dr, p[1] + dc
            if in_bounds(nr, nc) and (nr, nc) not in occupied:
                n_my_kings = set(my_kings)
                n_my_kings.remove(p)
                n_my_kings.add((nr, nc))
                child = make_child(set(my_men), n_my_kings, set(opp_men), set(opp_kings), color)
                quiets.append(((p, (nr, nc)), child, 10 + center_bonus((nr, nc))))
    return tuple(quiets)


def _gen_piece_captures(start, pos, is_king, color, my_men, my_kings, opp_men, opp_kings,
                        captured_any, first_to, results, dirs):
    opp_all = opp_men | opp_kings
    occupied = my_men | my_kings | opp_all
    found = False

    # In American checkers, men capture only forward; kings capture all directions.
    use_dirs = KING_DIRS if is_king else man_dirs(color)

    for dr, dc in use_dirs:
        mr, mc = pos[0] + dr, pos[1] + dc
        lr, lc = pos[0] + 2 * dr, pos[1] + 2 * dc
        if not in_bounds(lr, lc) or not in_bounds(mr, mc):
            continue
        mid = (mr, mc)
        land = (lr, lc)
        if mid in opp_all and land not in occupied:
            found = True
            nm = set(my_men)
            nk = set(my_kings)
            om = set(opp_men)
            ok = set(opp_kings)

            if is_king:
                nk.remove(pos)
            else:
                nm.remove(pos)

            if mid in om:
                om.remove(mid)
                cap_val = MAN_VAL
            else:
                ok.remove(mid)
                cap_val = KING_VAL

            became_king = False
            # Men promote when they land on last row; turn ends on promotion in American checkers.
            if (not is_king) and lr == promote_row(color):
                nk.add(land)
                became_king = True
            else:
                if is_king:
                    nk.add(land)
                else:
                    nm.add(land)

            new_first = first_to if first_to is not None else land

            if became_king:
                child = make_child(nm, nk, om, ok, color)
                hint = 1000 + cap_val + 80 + center_bonus(land)
                results.append(((start, new_first), child, hint))
            else:
                before_len = len(results)
                _gen_piece_captures(
                    start=start, pos=land, is_king=is_king, color=color,
                    my_men=nm, my_kings=nk, opp_men=om, opp_kings=ok,
                    captured_any=True, first_to=new_first, results=results,
                    dirs=KING_DIRS if is_king else man_dirs(color)
                )
                # If no continuation was appended from this branch, append terminal child.
                if len(results) == before_len:
                    child = make_child(nm, nk, om, ok, color)
                    hint = 1000 + cap_val + center_bonus(land)
                    results.append(((start, new_first), child, hint))

    if captured_any and not found:
        return


def make_child(my_men, my_kings, opp_men, opp_kings, color):
    # After my move, perspective swaps: child "my" pieces are opponent pieces.
    return (
        frozenset(opp_men),
        frozenset(opp_kings),
        frozenset(my_men),
        frozenset(my_kings),
        opponent_color(color),
    )


def center_bonus(p):
    r, c = p
    return 8 - (abs(r - 3.5) + abs(c - 3.5))


def order_moves(state, moves):
    # Higher hints first, plus shallow static child eval.
    scored = []
    for mv, child, hint in moves:
        cap = 2000 if abs(mv[0][0] - mv[1][0]) == 2 else 0
        scored.append((hint + cap + 0.02 * evaluate(child), mv, child))
    scored.sort(reverse=True, key=lambda x: x[0])
    return [(mv, child, hint) for hint, mv, child in scored]


@lru_cache(maxsize=200000)
def evaluate(state):
    my_men, my_kings, opp_men, opp_kings, color = state
    my_men_s = set(my_men)
    my_kings_s = set(my_kings)
    opp_men_s = set(opp_men)
    opp_kings_s = set(opp_kings)

    score = 0
    score += MAN_VAL * (len(my_men_s) - len(opp_men_s))
    score += KING_VAL * (len(my_kings_s) - len(opp_kings_s))

    # Advancement and promotion pressure
    for r, c in my_men_s:
        adv = (7 - r) if color == 'b' else r
        score += 5 * adv
        if r == promote_row(color):
            score += 30
        score += center_bonus((r, c)) * 2
        # Back row guard can be valuable before endgame
        if (color == 'b' and r == 7) or (color == 'w' and r == 0):
            score += 8
    opp_color = opponent_color(color)
    for r, c in opp_men_s:
        adv = (7 - r) if opp_color == 'b' else r
        score -= 5 * adv
        score -= center_bonus((r, c)) * 2
        if (opp_color == 'b' and r == 7) or (opp_color == 'w' and r == 0):
            score -= 8

    for p in my_kings_s:
        score += center_bonus(p) * 3
    for p in opp_kings_s:
        score -= center_bonus(p) * 3

    # Mobility
    my_mob = rough_mobility(my_men_s, my_kings_s, opp_men_s, opp_kings_s, color)
    opp_mob = rough_mobility(opp_men_s, opp_kings_s, my_men_s, my_kings_s, opp_color)
    score += 3 * (my_mob - opp_mob)

    # Immediate capture threats/safety
    my_caps = rough_capture_count(my_men_s, my_kings_s, opp_men_s, opp_kings_s, color)
    opp_caps = rough_capture_count(opp_men_s, opp_kings_s, my_men_s, my_kings_s, opp_color)
    score += 18 * my_caps
    score -= 22 * opp_caps

    # Endgame: kings and active pieces matter more
    total = len(my_men_s) + len(my_kings_s) + len(opp_men_s) + len(opp_kings_s)
    if total <= 8:
        score += 8 * (len(my_kings_s) - len(opp_kings_s))
        score += 2 * my_mob - 2 * opp_mob

    return score


def rough_mobility(my_men, my_kings, opp_men, opp_kings, color):
    occ = my_men | my_kings | opp_men | opp_kings
    n = 0
    for r, c in my_men:
        for dr, dc in man_dirs(color):
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc) and (nr, nc) not in occ:
                n += 1
    for r, c in my_kings:
        for dr, dc in KING_DIRS:
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc) and (nr, nc) not in occ:
                n += 1
    return n


def rough_capture_count(my_men, my_kings, opp_men, opp_kings, color):
    occ = my_men | my_kings | opp_men | opp_kings
    opp = opp_men | opp_kings
    n = 0
    for r, c in my_men:
        for dr, dc in man_dirs(color):
            mr, mc = r + dr, c + dc
            lr, lc = r + 2 * dr, c + 2 * dc
            if in_bounds(lr, lc) and (mr, mc) in opp and (lr, lc) not in occ:
                n += 1
    for r, c in my_kings:
        for dr, dc in KING_DIRS:
            mr, mc = r + dr, c + dc
            lr, lc = r + 2 * dr, c + 2 * dc
            if in_bounds(lr, lc) and (mr, mc) in opp and (lr, lc) not in occ:
                n += 1
    return n

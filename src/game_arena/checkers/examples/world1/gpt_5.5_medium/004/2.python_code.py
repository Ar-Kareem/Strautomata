
import time

INF = 10**9
WIN = 10**6

ALL_DIRS = ((1, 1), (1, -1), (-1, 1), (-1, -1))


def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    """
    Return one legal checkers move for the side to move.

    Coordinates are (row, col). Black men move toward lower rows.
    White men move toward higher rows. Captures are mandatory.
    """
    if color not in ("b", "w"):
        color = "b"

    start = time.perf_counter()
    deadline = start + 0.84

    my_men = tuple(sorted(tuple(x) for x in my_men))
    my_kings = tuple(sorted(tuple(x) for x in my_kings))
    opp_men = tuple(sorted(tuple(x) for x in opp_men))
    opp_kings = tuple(sorted(tuple(x) for x in opp_kings))

    moves = legal_moves(my_men, my_kings, opp_men, opp_kings, color)
    if not moves:
        return emergency_fallback(my_men, my_kings, color)

    moves = order_moves(moves, my_men, my_kings, opp_men, opp_kings, color)

    if len(moves) == 1:
        return moves[0][0], moves[0][1]

    best_move = moves[0]
    total_pieces = len(my_men) + len(my_kings) + len(opp_men) + len(opp_kings)

    if total_pieces >= 20:
        max_depth = 5
    elif total_pieces >= 14:
        max_depth = 6
    elif total_pieces >= 8:
        max_depth = 8
    else:
        max_depth = 10

    tt = {}

    for depth in range(1, max_depth + 1):
        try:
            alpha = -INF
            beta = INF
            depth_best = best_move
            depth_best_score = -INF

            current_moves = order_moves(moves, my_men, my_kings, opp_men, opp_kings, color)

            for mv in current_moves:
                if time.perf_counter() > deadline:
                    raise TimeoutError

                nm, nk, om, ok = apply_move(mv, my_men, my_kings, opp_men, opp_kings, color)
                score = -negamax(
                    om, ok, nm, nk, other(color),
                    depth - 1,
                    -beta,
                    -alpha,
                    3,
                    deadline,
                    tt,
                    1,
                )

                if score > depth_best_score:
                    depth_best_score = score
                    depth_best = mv

                if score > alpha:
                    alpha = score

            best_move = depth_best

        except TimeoutError:
            break

    return best_move[0], best_move[1]


def other(color):
    return "w" if color == "b" else "b"


def in_bounds(r, c):
    return 0 <= r < 8 and 0 <= c < 8


def man_dirs(color):
    if color == "b":
        return ((-1, 1), (-1, -1))
    return ((1, 1), (1, -1))


def promotes(row, color):
    return row == 0 if color == "b" else row == 7


def legal_moves(my_men, my_kings, opp_men, opp_kings, color):
    occupied = set(my_men) | set(my_kings) | set(opp_men) | set(opp_kings)
    opp_occ = set(opp_men) | set(opp_kings)

    captures = []

    for r, c in my_men:
        for dr, dc in man_dirs(color):
            mr, mc = r + dr, c + dc
            tr, tc = r + 2 * dr, c + 2 * dc
            if in_bounds(tr, tc) and (mr, mc) in opp_occ and (tr, tc) not in occupied:
                captures.append(((r, c), (tr, tc), False, (mr, mc)))

    for r, c in my_kings:
        for dr, dc in ALL_DIRS:
            mr, mc = r + dr, c + dc
            tr, tc = r + 2 * dr, c + 2 * dc
            if in_bounds(tr, tc) and (mr, mc) in opp_occ and (tr, tc) not in occupied:
                captures.append(((r, c), (tr, tc), True, (mr, mc)))

    if captures:
        return captures

    moves = []

    for r, c in my_men:
        for dr, dc in man_dirs(color):
            tr, tc = r + dr, c + dc
            if in_bounds(tr, tc) and (tr, tc) not in occupied:
                moves.append(((r, c), (tr, tc), False, None))

    for r, c in my_kings:
        for dr, dc in ALL_DIRS:
            tr, tc = r + dr, c + dc
            if in_bounds(tr, tc) and (tr, tc) not in occupied:
                moves.append(((r, c), (tr, tc), True, None))

    return moves


def apply_move(mv, my_men, my_kings, opp_men, opp_kings, color):
    frm, to, was_king, captured = mv

    my_men_l = list(my_men)
    my_kings_l = list(my_kings)
    opp_men_l = list(opp_men)
    opp_kings_l = list(opp_kings)

    if was_king:
        my_kings_l.remove(frm)
    else:
        my_men_l.remove(frm)

    if captured is not None:
        if captured in opp_men_l:
            opp_men_l.remove(captured)
        elif captured in opp_kings_l:
            opp_kings_l.remove(captured)

    if was_king or promotes(to[0], color):
        my_kings_l.append(to)
    else:
        my_men_l.append(to)

    return (
        tuple(sorted(my_men_l)),
        tuple(sorted(my_kings_l)),
        tuple(sorted(opp_men_l)),
        tuple(sorted(opp_kings_l)),
    )


def negamax(my_men, my_kings, opp_men, opp_kings, color, depth, alpha, beta, qdepth, deadline, tt, ply):
    if time.perf_counter() > deadline:
        raise TimeoutError

    key = (my_men, my_kings, opp_men, opp_kings, color, depth, qdepth)
    if key in tt:
        return tt[key]

    moves = legal_moves(my_men, my_kings, opp_men, opp_kings, color)

    if not moves:
        return -WIN + ply

    if depth <= 0:
        has_capture = moves[0][3] is not None
        if not has_capture or qdepth <= 0:
            return evaluate(my_men, my_kings, opp_men, opp_kings, color)

    moves = order_moves(moves, my_men, my_kings, opp_men, opp_kings, color)

    best = -INF
    full_search = True

    next_depth = depth - 1 if depth > 0 else 0
    next_q = qdepth if depth > 0 else qdepth - 1

    for mv in moves:
        nm, nk, om, ok = apply_move(mv, my_men, my_kings, opp_men, opp_kings, color)
        score = -negamax(
            om, ok, nm, nk, other(color),
            next_depth,
            -beta,
            -alpha,
            next_q,
            deadline,
            tt,
            ply + 1,
        )

        if score > best:
            best = score
        if best > alpha:
            alpha = best
        if alpha >= beta:
            full_search = False
            break

    if full_search:
        tt[key] = best

    return best


def evaluate(my_men, my_kings, opp_men, opp_kings, color):
    opp_color = other(color)

    score = 0

    score += 100 * (len(my_men) - len(opp_men))
    score += 178 * (len(my_kings) - len(opp_kings))

    for p in my_men:
        score += man_positional_value(p, color)
    for p in opp_men:
        score -= man_positional_value(p, opp_color)

    for p in my_kings:
        score += king_positional_value(p)
    for p in opp_kings:
        score -= king_positional_value(p)

    my_moves = legal_moves(my_men, my_kings, opp_men, opp_kings, color)
    opp_moves = legal_moves(opp_men, opp_kings, my_men, my_kings, opp_color)

    score += 4 * (len(my_moves) - len(opp_moves))

    if my_moves and my_moves[0][3] is not None:
        score += 28 * len(my_moves)
    if opp_moves and opp_moves[0][3] is not None:
        score -= 28 * len(opp_moves)

    score += vulnerability_balance(my_men, my_kings, opp_men, opp_kings, color)

    return score


def man_positional_value(p, color):
    r, c = p

    if color == "b":
        advance = 7 - r
        back_row = 7
        near_promo = r == 1
    else:
        advance = r
        back_row = 0
        near_promo = r == 6

    val = 6 * advance
    val += center_bonus(p)

    if near_promo:
        val += 20

    if r == back_row:
        val += 8

    if c == 0 or c == 7:
        val += 3

    return val


def king_positional_value(p):
    val = 2 * center_bonus(p)
    r, c = p

    if c == 0 or c == 7:
        val += 2

    if 2 <= r <= 5 and 2 <= c <= 5:
        val += 6

    return val


def center_bonus(p):
    r, c = p
    return 14 - (abs(2 * r - 7) + abs(2 * c - 7))


def vulnerability_balance(my_men, my_kings, opp_men, opp_kings, color):
    score = 0
    opp_color = other(color)

    for p in my_men:
        if vulnerable_to_capture(p, my_men, my_kings, opp_men, opp_kings, opp_color):
            score -= 22

    for p in my_kings:
        if vulnerable_to_capture(p, my_men, my_kings, opp_men, opp_kings, opp_color):
            score -= 34

    for p in opp_men:
        if vulnerable_to_capture(p, opp_men, opp_kings, my_men, my_kings, color):
            score += 22

    for p in opp_kings:
        if vulnerable_to_capture(p, opp_men, opp_kings, my_men, my_kings, color):
            score += 34

    return score


def vulnerable_to_capture(pos, friend_men, friend_kings, enemy_men, enemy_kings, enemy_color):
    r, c = pos
    occupied = set(friend_men) | set(friend_kings) | set(enemy_men) | set(enemy_kings)
    enemy_men_s = set(enemy_men)
    enemy_kings_s = set(enemy_kings)

    for dr, dc in man_dirs(enemy_color):
        er, ec = r - dr, c - dc
        lr, lc = r + dr, c + dc
        if in_bounds(er, ec) and in_bounds(lr, lc):
            if (er, ec) in enemy_men_s and (lr, lc) not in occupied:
                return True

    for dr, dc in ALL_DIRS:
        er, ec = r - dr, c - dc
        lr, lc = r + dr, c + dc
        if in_bounds(er, ec) and in_bounds(lr, lc):
            if (er, ec) in enemy_kings_s and (lr, lc) not in occupied:
                return True

    return False


def order_moves(moves, my_men, my_kings, opp_men, opp_kings, color):
    opp_kings_s = set(opp_kings)

    def key(mv):
        frm, to, was_king, captured = mv
        score = 0

        if captured is not None:
            score += 1000
            score += 170 if captured in opp_kings_s else 100

        if not was_king and promotes(to[0], color):
            score += 240

        score += center_bonus(to)

        if not was_king:
            if color == "b":
                score += 4 * (frm[0] - to[0])
            else:
                score += 4 * (to[0] - frm[0])

        if to[1] == 0 or to[1] == 7:
            score += 4

        return score

    return sorted(moves, key=key, reverse=True)


def emergency_fallback(my_men, my_kings, color):
    """
    Should only be used in already-lost/no-move positions.
    Returns a syntactically valid tuple even if the game is over.
    """
    occupied = set(my_men) | set(my_kings)

    for r, c in my_men:
        for dr, dc in man_dirs(color):
            tr, tc = r + dr, c + dc
            if in_bounds(tr, tc) and (tr, tc) not in occupied:
                return (r, c), (tr, tc)

    for r, c in my_kings:
        for dr, dc in ALL_DIRS:
            tr, tc = r + dr, c + dc
            if in_bounds(tr, tc) and (tr, tc) not in occupied:
                return (r, c), (tr, tc)

    if my_men:
        return my_men[0], my_men[0]
    if my_kings:
        return my_kings[0], my_kings[0]

    return (0, 0), (0, 0)

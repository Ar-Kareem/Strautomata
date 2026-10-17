
import time

INF = 10**9
_deadline = 0.0
_nodes = 0
_tt = {}


def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    global _deadline, _nodes, _tt

    _deadline = time.perf_counter() + 0.92
    _nodes = 0
    _tt = {}

    state = (
        tuple(sorted(my_men)),
        tuple(sorted(my_kings)),
        tuple(sorted(opp_men)),
        tuple(sorted(opp_kings)),
        color,
    )

    moves = _generate_moves(*state)
    if not moves:
        # Should only happen if the game is already lost/stalemated.
        # There is no legal move in such a position, but return a harmless tuple.
        if my_men:
            p = my_men[0]
            return (p, p)
        if my_kings:
            p = my_kings[0]
            return (p, p)
        return ((0, 0), (0, 0))

    moves = _order_moves(moves, state)
    best_move = moves[0]

    piece_count = len(my_men) + len(my_kings) + len(opp_men) + len(opp_kings)
    max_depth = 10 if piece_count <= 8 else 8 if piece_count <= 14 else 7

    try:
        for depth in range(1, max_depth + 1):
            if time.perf_counter() >= _deadline:
                break

            alpha = -INF
            beta = INF
            local_best = best_move
            local_score = -INF

            ordered_root = [best_move] + [m for m in moves if m != best_move]

            for mv in ordered_root:
                if time.perf_counter() >= _deadline:
                    raise TimeoutError

                nxt = _apply_move(state, mv)
                score = -_negamax(nxt, depth - 1, -beta, -alpha, 1)

                if score > local_score:
                    local_score = score
                    local_best = mv

                if score > alpha:
                    alpha = score

            best_move = local_best

    except TimeoutError:
        pass
    except Exception:
        # Safety: never risk returning something illegal if search has an unexpected issue.
        best_move = moves[0]

    return (best_move[0], best_move[1])


def _other(color):
    return "w" if color == "b" else "b"


def _inside(r, c):
    return 0 <= r < 8 and 0 <= c < 8


def _man_dirs(color):
    if color == "b":
        return [(-1, -1), (-1, 1)]
    return [(1, -1), (1, 1)]


KING_DIRS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]


def _generate_moves(my_men, my_kings, opp_men, opp_kings, color):
    my_men_s = set(my_men)
    my_kings_s = set(my_kings)
    opp_men_s = set(opp_men)
    opp_kings_s = set(opp_kings)

    my_all = my_men_s | my_kings_s
    opp_all = opp_men_s | opp_kings_s
    occupied = my_all | opp_all

    captures = []

    for fr in my_men_s:
        r, c = fr
        for dr, dc in _man_dirs(color):
            mr, mc = r + dr, c + dc
            tr, tc = r + 2 * dr, c + 2 * dc
            mid = (mr, mc)
            to = (tr, tc)
            if _inside(tr, tc) and mid in opp_all and to not in occupied:
                captures.append((fr, to, mid, False))

    for fr in my_kings_s:
        r, c = fr
        for dr, dc in KING_DIRS:
            mr, mc = r + dr, c + dc
            tr, tc = r + 2 * dr, c + 2 * dc
            mid = (mr, mc)
            to = (tr, tc)
            if _inside(tr, tc) and mid in opp_all and to not in occupied:
                captures.append((fr, to, mid, True))

    if captures:
        return captures

    moves = []

    for fr in my_men_s:
        r, c = fr
        for dr, dc in _man_dirs(color):
            tr, tc = r + dr, c + dc
            to = (tr, tc)
            if _inside(tr, tc) and to not in occupied:
                moves.append((fr, to, None, False))

    for fr in my_kings_s:
        r, c = fr
        for dr, dc in KING_DIRS:
            tr, tc = r + dr, c + dc
            to = (tr, tc)
            if _inside(tr, tc) and to not in occupied:
                moves.append((fr, to, None, True))

    return moves


def _apply_move(state, mv):
    my_men, my_kings, opp_men, opp_kings, color = state
    my_men_s = set(my_men)
    my_kings_s = set(my_kings)
    opp_men_s = set(opp_men)
    opp_kings_s = set(opp_kings)

    fr, to, cap, was_king = mv
    tr, tc = to

    if was_king:
        my_kings_s.remove(fr)
        my_kings_s.add(to)
    else:
        my_men_s.remove(fr)
        if (color == "b" and tr == 0) or (color == "w" and tr == 7):
            my_kings_s.add(to)
        else:
            my_men_s.add(to)

    if cap is not None:
        if cap in opp_men_s:
            opp_men_s.remove(cap)
        else:
            opp_kings_s.remove(cap)

    return (
        tuple(sorted(opp_men_s)),
        tuple(sorted(opp_kings_s)),
        tuple(sorted(my_men_s)),
        tuple(sorted(my_kings_s)),
        _other(color),
    )


def _order_moves(moves, state):
    my_men, my_kings, opp_men, opp_kings, color = state
    opp_kings_s = set(opp_kings)

    def score(mv):
        fr, to, cap, was_king = mv
        tr, tc = to
        s = 0

        if cap is not None:
            s += 10000
            if cap in opp_kings_s:
                s += 750
            else:
                s += 350

        if not was_king and ((color == "b" and tr == 0) or (color == "w" and tr == 7)):
            s += 900

        if 2 <= tr <= 5 and 2 <= tc <= 5:
            s += 40

        if was_king:
            s += 20

        # Slightly prefer edge landings for non-kings when no capture exists;
        # edges are harder to capture from.
        if cap is None and (tc == 0 or tc == 7):
            s += 15

        return s

    return sorted(moves, key=score, reverse=True)


def _negamax(state, depth, alpha, beta, ply):
    global _nodes, _tt

    _nodes += 1
    if (_nodes & 511) == 0 and time.perf_counter() >= _deadline:
        raise TimeoutError

    key = (state, depth)
    entry = _tt.get(key)
    if entry is not None:
        ent_depth, ent_value, ent_flag = entry
        if ent_depth >= depth:
            if ent_flag == 0:
                return ent_value
            if ent_flag == 1:
                alpha = max(alpha, ent_value)
            elif ent_flag == 2:
                beta = min(beta, ent_value)
            if alpha >= beta:
                return ent_value

    moves = _generate_moves(*state)
    if not moves:
        return -900000 + ply

    if depth <= 0:
        return _evaluate(state)

    orig_alpha = alpha
    best = -INF

    for mv in _order_moves(moves, state):
        nxt = _apply_move(state, mv)
        val = -_negamax(nxt, depth - 1, -beta, -alpha, ply + 1)

        if val > best:
            best = val
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

    if best <= orig_alpha:
        flag = 2   # upper bound
    elif best >= beta:
        flag = 1   # lower bound
    else:
        flag = 0   # exact

    _tt[key] = (depth, best, flag)
    return best


def _evaluate(state):
    my_men, my_kings, opp_men, opp_kings, color = state
    opp_color = _other(color)

    score = _side_value(my_men, my_kings, color) - _side_value(opp_men, opp_kings, opp_color)

    my_moves = _generate_moves(my_men, my_kings, opp_men, opp_kings, color)
    opp_moves = _generate_moves(opp_men, opp_kings, my_men, my_kings, opp_color)

    score += 3 * (len(my_moves) - len(opp_moves))

    my_caps = {m[2] for m in my_moves if m[2] is not None}
    opp_caps = {m[2] for m in opp_moves if m[2] is not None}

    # Pieces we can capture are good; pieces the opponent can capture are bad.
    score += 45 * (len(my_caps) - len(opp_caps))

    if my_caps:
        score += 25
    if opp_caps:
        score -= 25

    return score


def _side_value(men, kings, color):
    val = 100 * len(men) + 175 * len(kings)

    for r, c in men:
        if color == "b":
            advance = 7 - r
            home_row = 7
        else:
            advance = r
            home_row = 0

        val += 6 * advance

        if r == home_row:
            val += 10

        if 2 <= r <= 5 and 2 <= c <= 5:
            val += 8

        if c == 0 or c == 7:
            val += 4

        # Men close to promotion are valuable, especially if unobstructed enough
        # for search to notice tactical support.
        if advance >= 5:
            val += 10

    for r, c in kings:
        val += 0

        if 2 <= r <= 5 and 2 <= c <= 5:
            val += 12

        if c == 0 or c == 7 or r == 0 or r == 7:
            val += 3

    return val

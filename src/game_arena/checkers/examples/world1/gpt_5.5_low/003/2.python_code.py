
import time
import math

# Checkers policy for an 8x8 board.
# Coordinates: row 0 is bottom, row 7 is top.
# Black moves toward lower rows; white moves toward higher rows.

TIME_LIMIT = 0.90


def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    start_time = time.time()

    my_men = frozenset(tuple(x) for x in my_men)
    my_kings = frozenset(tuple(x) for x in my_kings)
    opp_men = frozenset(tuple(x) for x in opp_men)
    opp_kings = frozenset(tuple(x) for x in opp_kings)

    root_state = (my_men, my_kings, opp_men, opp_kings)
    root_moves = legal_moves(root_state, 0, color)

    # Absolute safety fallback: if somehow no legal moves exist, return any own piece to any adjacent square.
    # In normal arena states this should never be used.
    if not root_moves:
        fallback = emergency_fallback(my_men, my_kings, opp_men, opp_kings, color)
        return fallback

    best_move = order_moves(root_state, root_moves, 0, color)[0]
    best_score = -10**18

    # Iterative deepening. Usually reaches depth 5-7 in simple positions.
    for depth in range(1, 8):
        if time.time() - start_time > TIME_LIMIT:
            break

        current_best = best_move
        current_score = -10**18

        ordered = order_moves(root_state, root_moves, 0, color)

        try:
            alpha = -10**18
            beta = 10**18

            for mv in ordered:
                if time.time() - start_time > TIME_LIMIT:
                    raise TimeoutError

                child = apply_move(root_state, mv, 0, color)
                score = alphabeta(child, depth - 1, alpha, beta, 1, color, start_time)

                if score > current_score:
                    current_score = score
                    current_best = mv

                alpha = max(alpha, current_score)

            best_move = current_best
            best_score = current_score

        except TimeoutError:
            break

    return best_move


def opponent_color(color):
    return 'w' if color == 'b' else 'b'


def side_color(root_color, side):
    return root_color if side == 0 else opponent_color(root_color)


def man_dirs(color):
    # Black moves down toward row 0, white moves up toward row 7.
    if color == 'b':
        return [(-1, -1), (-1, 1)]
    return [(1, -1), (1, 1)]


KING_DIRS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]


def in_bounds(r, c):
    return 0 <= r < 8 and 0 <= c < 8


def promotion_row(color):
    return 0 if color == 'b' else 7


def unpack_state(state, side):
    m0, k0, m1, k1 = state
    if side == 0:
        return m0, k0, m1, k1
    return m1, k1, m0, k0


def legal_moves(state, side, root_color):
    my_men, my_kings, opp_men, opp_kings = unpack_state(state, side)
    occupied = my_men | my_kings | opp_men | opp_kings
    opp_all = opp_men | opp_kings
    color = side_color(root_color, side)

    captures = []

    # Men captures.
    for r, c in my_men:
        for dr, dc in man_dirs(color):
            mr, mc = r + dr, c + dc
            tr, tc = r + 2 * dr, c + 2 * dc
            if in_bounds(tr, tc) and (mr, mc) in opp_all and (tr, tc) not in occupied:
                captures.append(((r, c), (tr, tc)))

    # King captures.
    for r, c in my_kings:
        for dr, dc in KING_DIRS:
            mr, mc = r + dr, c + dc
            tr, tc = r + 2 * dr, c + 2 * dc
            if in_bounds(tr, tc) and (mr, mc) in opp_all and (tr, tc) not in occupied:
                captures.append(((r, c), (tr, tc)))

    if captures:
        return captures

    moves = []

    # Men quiet moves.
    for r, c in my_men:
        for dr, dc in man_dirs(color):
            tr, tc = r + dr, c + dc
            if in_bounds(tr, tc) and (tr, tc) not in occupied:
                moves.append(((r, c), (tr, tc)))

    # King quiet moves.
    for r, c in my_kings:
        for dr, dc in KING_DIRS:
            tr, tc = r + dr, c + dc
            if in_bounds(tr, tc) and (tr, tc) not in occupied:
                moves.append(((r, c), (tr, tc)))

    return moves


def apply_move(state, move, side, root_color):
    m0, k0, m1, k1 = map(set, state)
    src, dst = move
    sr, sc = src
    tr, tc = dst

    if side == 0:
        my_men, my_kings, opp_men, opp_kings = m0, k0, m1, k1
    else:
        my_men, my_kings, opp_men, opp_kings = m1, k1, m0, k0

    color = side_color(root_color, side)
    was_king = src in my_kings

    if was_king:
        my_kings.remove(src)
    else:
        my_men.remove(src)

    # Capture removal.
    if abs(tr - sr) == 2:
        mid = ((sr + tr) // 2, (sc + tc) // 2)
        if mid in opp_men:
            opp_men.remove(mid)
        elif mid in opp_kings:
            opp_kings.remove(mid)

    # Promotion.
    if (not was_king) and tr == promotion_row(color):
        my_kings.add(dst)
    else:
        if was_king:
            my_kings.add(dst)
        else:
            my_men.add(dst)

    if side == 0:
        return (frozenset(my_men), frozenset(my_kings), frozenset(opp_men), frozenset(opp_kings))
    else:
        return (frozenset(opp_men), frozenset(opp_kings), frozenset(my_men), frozenset(my_kings))


def alphabeta(state, depth, alpha, beta, side, root_color, start_time):
    if time.time() - start_time > TIME_LIMIT:
        raise TimeoutError

    moves = legal_moves(state, side, root_color)

    if not moves:
        # Side to move has lost.
        return -1000000 if side == 0 else 1000000

    if depth <= 0:
        return evaluate(state, root_color)

    ordered = order_moves(state, moves, side, root_color)

    if side == 0:
        value = -10**18
        for mv in ordered:
            child = apply_move(state, mv, side, root_color)
            value = max(value, alphabeta(child, depth - 1, alpha, beta, 1, root_color, start_time))
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value
    else:
        value = 10**18
        for mv in ordered:
            child = apply_move(state, mv, side, root_color)
            value = min(value, alphabeta(child, depth - 1, alpha, beta, 0, root_color, start_time))
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value


def evaluate(state, root_color):
    my_men, my_kings, opp_men, opp_kings = state

    score = 0

    # Material.
    score += 100 * len(my_men)
    score += 180 * len(my_kings)
    score -= 100 * len(opp_men)
    score -= 180 * len(opp_kings)

    # Advancement, center, edge safety.
    score += positional_score(my_men, my_kings, root_color)
    score -= positional_score(opp_men, opp_kings, opponent_color(root_color))

    # Mobility.
    my_moves = len(legal_moves(state, 0, root_color))
    opp_moves = len(legal_moves(state, 1, root_color))
    score += 3 * (my_moves - opp_moves)

    # Tempo and conversion bonus.
    if len(opp_men) + len(opp_kings) == 0:
        score += 100000
    if len(my_men) + len(my_kings) == 0:
        score -= 100000

    return score


def positional_score(men, kings, color):
    s = 0

    for r, c in men:
        # Advancement toward kinging.
        if color == 'b':
            advance = 7 - r
            dist_to_king = r
        else:
            advance = r
            dist_to_king = 7 - r

        s += 6 * advance
        s += max(0, 14 - 2 * dist_to_king)

        # Center control.
        if 2 <= r <= 5 and 2 <= c <= 5:
            s += 8
        if 3 <= c <= 4:
            s += 3

        # Back row guard before kinging.
        if (color == 'b' and r == 7) or (color == 'w' and r == 0):
            s += 7

        # Edges are safer but less mobile.
        if c == 0 or c == 7:
            s += 2

    for r, c in kings:
        # Kings prefer central mobility.
        if 2 <= r <= 5 and 2 <= c <= 5:
            s += 12
        if 1 <= r <= 6 and 1 <= c <= 6:
            s += 5
        if c == 0 or c == 7 or r == 0 or r == 7:
            s -= 3

    return s


def order_moves(state, moves, side, root_color):
    def key(mv):
        src, dst = mv
        sr, sc = src
        tr, tc = dst
        val = 0

        # Captures first.
        if abs(tr - sr) == 2:
            val += 10000

        color = side_color(root_color, side)

        my_men, my_kings, opp_men, opp_kings = unpack_state(state, side)

        # Promotion.
        if src in my_men and tr == promotion_row(color):
            val += 5000

        # Prefer central destinations.
        if 2 <= tr <= 5 and 2 <= tc <= 5:
            val += 50

        # Prefer advancement for men.
        if src in my_men:
            if color == 'b':
                val += (sr - tr) * 20
            else:
                val += (tr - sr) * 20

        # Avoid obvious destination vulnerability if it is a quiet move.
        if abs(tr - sr) == 1 and destination_can_be_captured(state, mv, side, root_color):
            val -= 300

        return val

    return sorted(moves, key=key, reverse=True)


def destination_can_be_captured(state, move, side, root_color):
    # Lightweight blunder detector: after making a quiet move, see if opponent has a capture landing over dst.
    child = apply_move(state, move, side, root_color)
    opp_side = 1 - side
    opp_moves = legal_moves(child, opp_side, root_color)

    dst = move[1]
    for mv in opp_moves:
        src, to = mv
        if abs(to[0] - src[0]) == 2:
            mid = ((src[0] + to[0]) // 2, (src[1] + to[1]) // 2)
            if mid == dst:
                return True
    return False


def emergency_fallback(my_men, my_kings, opp_men, opp_kings, color):
    occupied = set(my_men) | set(my_kings) | set(opp_men) | set(opp_kings)

    # Try a legal-looking man move.
    for r, c in my_men:
        for dr, dc in man_dirs(color):
            tr, tc = r + dr, c + dc
            if in_bounds(tr, tc) and (tr, tc) not in occupied:
                return ((r, c), (tr, tc))

    # Try a legal-looking king move.
    for r, c in my_kings:
        for dr, dc in KING_DIRS:
            tr, tc = r + dr, c + dc
            if in_bounds(tr, tc) and (tr, tc) not in occupied:
                return ((r, c), (tr, tc))

    # Last resort, should never happen in a valid non-terminal call.
    if my_men:
        p = next(iter(my_men))
        return (p, p)
    if my_kings:
        p = next(iter(my_kings))
        return (p, p)

    return ((0, 0), (0, 0))

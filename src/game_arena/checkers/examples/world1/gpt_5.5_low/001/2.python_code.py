
import time
import math
import random

# Checkers policy for an 8x8 board.
# Coordinates: (row, col), row 0 is bottom, row 7 is top.
# Black ('b') men move toward lower row numbers.
# White ('w') men move toward higher row numbers.

TIME_LIMIT = 0.90


def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    start_time = time.time()

    my_men = tuple(sorted(tuple(x) for x in my_men))
    my_kings = tuple(sorted(tuple(x) for x in my_kings))
    opp_men = tuple(sorted(tuple(x) for x in opp_men))
    opp_kings = tuple(sorted(tuple(x) for x in opp_kings))

    legal = generate_moves(my_men, my_kings, opp_men, opp_kings, color)
    if not legal:
        # Should never happen in a normal game state, but return a syntactically valid move if forced.
        if my_men:
            p = my_men[0]
            return (p, p)
        if my_kings:
            p = my_kings[0]
            return (p, p)
        return ((0, 0), (0, 0))

    # If only one legal move, take it immediately.
    if len(legal) == 1:
        return legal[0][0], legal[0][1]

    best_move = legal[0]
    best_score = -10**18

    # Iterative deepening. Depth 6 is usually safe; timeout guard handles tactical explosions.
    max_depth = 6
    try:
        for depth in range(1, max_depth + 1):
            if time.time() - start_time > TIME_LIMIT:
                break

            current_best = best_move
            current_score = -10**18

            # Move ordering: captures first, promotions, then central moves.
            ordered = order_moves(legal, color)

            alpha = -10**18
            beta = 10**18

            for mv in ordered:
                if time.time() - start_time > TIME_LIMIT:
                    raise TimeoutError

                n_my_men, n_my_kings, n_opp_men, n_opp_kings = apply_move(
                    my_men, my_kings, opp_men, opp_kings, color, mv
                )

                score = -negamax(
                    n_opp_men,
                    n_opp_kings,
                    n_my_men,
                    n_my_kings,
                    other(color),
                    depth - 1,
                    -beta,
                    -alpha,
                    start_time,
                )

                if score > current_score:
                    current_score = score
                    current_best = mv

                alpha = max(alpha, score)

            best_move = current_best
            best_score = current_score

    except TimeoutError:
        pass
    except Exception:
        # Absolute safety: never fail to return a legal move.
        return legal[0][0], legal[0][1]

    return best_move[0], best_move[1]


def other(color):
    return "w" if color == "b" else "b"


def in_bounds(r, c):
    return 0 <= r < 8 and 0 <= c < 8


def man_dirs(color):
    return [(-1, -1), (-1, 1)] if color == "b" else [(1, -1), (1, 1)]


def king_dirs():
    return [(-1, -1), (-1, 1), (1, -1), (1, 1)]


def generate_moves(my_men, my_kings, opp_men, opp_kings, color):
    occupied = set(my_men) | set(my_kings) | set(opp_men) | set(opp_kings)
    opponents = set(opp_men) | set(opp_kings)

    captures = []

    # Men captures.
    for r, c in my_men:
        for dr, dc in man_dirs(color):
            mr, mc = r + dr, c + dc
            tr, tc = r + 2 * dr, c + 2 * dc
            if in_bounds(tr, tc) and (mr, mc) in opponents and (tr, tc) not in occupied:
                captures.append(((r, c), (tr, tc)))

    # King captures.
    for r, c in my_kings:
        for dr, dc in king_dirs():
            mr, mc = r + dr, c + dc
            tr, tc = r + 2 * dr, c + 2 * dc
            if in_bounds(tr, tc) and (mr, mc) in opponents and (tr, tc) not in occupied:
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
        for dr, dc in king_dirs():
            tr, tc = r + dr, c + dc
            if in_bounds(tr, tc) and (tr, tc) not in occupied:
                moves.append(((r, c), (tr, tc)))

    return moves


def apply_move(my_men, my_kings, opp_men, opp_kings, color, move):
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

    # Capture.
    if abs(tr - fr) == 2:
        mr, mc = (fr + tr) // 2, (fc + tc) // 2
        if (mr, mc) in opp_men:
            opp_men.remove((mr, mc))
        elif (mr, mc) in opp_kings:
            opp_kings.remove((mr, mc))

    # Promotion.
    if not is_king and ((color == "b" and tr == 0) or (color == "w" and tr == 7)):
        my_kings.append(to)
    elif is_king:
        my_kings.append(to)
    else:
        my_men.append(to)

    return (
        tuple(sorted(my_men)),
        tuple(sorted(my_kings)),
        tuple(sorted(opp_men)),
        tuple(sorted(opp_kings)),
    )


def negamax(my_men, my_kings, opp_men, opp_kings, color, depth, alpha, beta, start_time):
    if time.time() - start_time > TIME_LIMIT:
        raise TimeoutError

    moves = generate_moves(my_men, my_kings, opp_men, opp_kings, color)

    if not moves:
        return -1000000 - depth

    if depth <= 0:
        return evaluate(my_men, my_kings, opp_men, opp_kings, color)

    ordered = order_moves(moves, color)

    best = -10**18
    opp_color = other(color)

    for mv in ordered:
        n_my_men, n_my_kings, n_opp_men, n_opp_kings = apply_move(
            my_men, my_kings, opp_men, opp_kings, color, mv
        )

        score = -negamax(
            n_opp_men,
            n_opp_kings,
            n_my_men,
            n_my_kings,
            opp_color,
            depth - 1,
            -beta,
            -alpha,
            start_time,
        )

        if score > best:
            best = score

        alpha = max(alpha, score)
        if alpha >= beta:
            break

    return best


def evaluate(my_men, my_kings, opp_men, opp_kings, color):
    score = 0

    # Material.
    score += 100 * len(my_men)
    score += 175 * len(my_kings)
    score -= 100 * len(opp_men)
    score -= 175 * len(opp_kings)

    # Advancement toward promotion.
    if color == "b":
        for r, c in my_men:
            score += (7 - r) * 6
        for r, c in opp_men:
            score -= r * 6
    else:
        for r, c in my_men:
            score += r * 6
        for r, c in opp_men:
            score -= (7 - r) * 6

    # Center control.
    for r, c in my_men:
        if 2 <= r <= 5 and 2 <= c <= 5:
            score += 8
        if 3 <= r <= 4 and 3 <= c <= 4:
            score += 5

    for r, c in my_kings:
        if 2 <= r <= 5 and 2 <= c <= 5:
            score += 10
        if 3 <= r <= 4 and 3 <= c <= 4:
            score += 6

    for r, c in opp_men:
        if 2 <= r <= 5 and 2 <= c <= 5:
            score -= 8
        if 3 <= r <= 4 and 3 <= c <= 4:
            score -= 5

    for r, c in opp_kings:
        if 2 <= r <= 5 and 2 <= c <= 5:
            score -= 10
        if 3 <= r <= 4 and 3 <= c <= 4:
            score -= 6

    # Back row guard: useful in many checkers positions.
    if color == "b":
        for p in my_men:
            if p[0] == 7:
                score += 7
        for p in opp_men:
            if p[0] == 0:
                score -= 7
    else:
        for p in my_men:
            if p[0] == 0:
                score += 7
        for p in opp_men:
            if p[0] == 7:
                score -= 7

    # Edge penalty for kings; kings are more powerful near the center.
    for r, c in my_kings:
        if c == 0 or c == 7 or r == 0 or r == 7:
            score -= 5
    for r, c in opp_kings:
        if c == 0 or c == 7 or r == 0 or r == 7:
            score += 5

    # Mobility, lightly weighted.
    my_mob = len(generate_moves(my_men, my_kings, opp_men, opp_kings, color))
    opp_mob = len(generate_moves(opp_men, opp_kings, my_men, my_kings, other(color)))
    score += 3 * (my_mob - opp_mob)

    return score


def order_moves(moves, color):
    def key(mv):
        (fr, fc), (tr, tc) = mv
        capture = 1 if abs(tr - fr) == 2 else 0
        promotion = 1 if ((color == "b" and tr == 0) or (color == "w" and tr == 7)) else 0
        center = -((tr - 3.5) ** 2 + (tc - 3.5) ** 2)
        advance = (fr - tr) if color == "b" else (tr - fr)
        return (capture, promotion, advance, center)

    return sorted(moves, key=key, reverse=True)

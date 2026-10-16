
import time
import math
from functools import lru_cache

BOARD_SIZE = 8
INF = 10 ** 9


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    """
    Breakthrough policy for an 8x8 board.

    color:
      'b' moves toward lower row numbers, goal row 0.
      'w' moves toward higher row numbers, goal row 7.
    """

    start_time = time.perf_counter()
    time_limit = 0.88

    me_t = tuple(sorted(me))
    opp_t = tuple(sorted(opp))

    my_moves = generate_moves(me_t, opp_t, color)
    if not my_moves:
        # Should not happen in valid Breakthrough positions, but keep API safe.
        return ((me[0][0], me[0][1]), (me[0][0], me[0][1]))

    # Always keep a legal fallback.
    best_move = my_moves[0]

    # If we can win immediately, do it.
    for mv in my_moves:
        _, dst = mv
        if dst[0] == goal_row(color):
            return mv
        if dst in set(opp_t) and len(opp_t) == 1:
            return mv

    opp_color = other_color(color)

    # Iterative deepening. Depth 4 is usually safe; depth 5+ when positions are small.
    max_depth = 5
    if len(me_t) + len(opp_t) <= 16:
        max_depth = 6
    if len(me_t) + len(opp_t) <= 10:
        max_depth = 7

    trans = {}

    def out_of_time():
        return time.perf_counter() - start_time > time_limit

    def negamax(side, enemy, side_color, depth, alpha, beta):
        if out_of_time():
            raise TimeoutError

        key = (side, enemy, side_color, depth, alpha, beta)
        if key in trans:
            return trans[key]

        term = terminal_score(side, enemy, side_color)
        if term is not None:
            return term

        if depth == 0:
            return evaluate(side, enemy, side_color)

        moves = generate_moves(side, enemy, side_color)
        if not moves:
            # Being unable to move is very bad in practice.
            return -INF // 2

        moves = order_moves(moves, side, enemy, side_color)

        best = -INF
        next_color = other_color(side_color)

        for mv in moves:
            ns, ne = make_move(side, enemy, mv)
            score = -negamax(ne, ns, next_color, depth - 1, -beta, -alpha)

            if score > best:
                best = score
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

        trans[key] = best
        return best

    for depth in range(1, max_depth + 1):
        try:
            alpha = -INF
            beta = INF
            local_best = best_move
            local_score = -INF

            ordered = order_moves(my_moves, me_t, opp_t, color)
            for mv in ordered:
                if out_of_time():
                    raise TimeoutError

                ns, ne = make_move(me_t, opp_t, mv)
                score = -negamax(ne, ns, opp_color, depth - 1, -beta, -alpha)

                if score > local_score:
                    local_score = score
                    local_best = mv

                if score > alpha:
                    alpha = score

            best_move = local_best

        except TimeoutError:
            break

    return best_move


def other_color(color):
    return 'w' if color == 'b' else 'b'


def direction(color):
    return -1 if color == 'b' else 1


def goal_row(color):
    return 0 if color == 'b' else 7


def progress(row, color):
    """How far a pawn has advanced from its home side."""
    return 7 - row if color == 'b' else row


def generate_moves(side, enemy, color):
    side_set = set(side)
    enemy_set = set(enemy)
    occupied = side_set | enemy_set
    d = direction(color)

    moves = []

    for r, c in side:
        nr = r + d
        if nr < 0 or nr >= BOARD_SIZE:
            continue

        # Straight forward: only if empty.
        if (nr, c) not in occupied:
            moves.append(((r, c), (nr, c)))

        # Diagonal forward: legal if not occupied by own piece.
        for dc in (-1, 1):
            nc = c + dc
            if 0 <= nc < BOARD_SIZE and (nr, nc) not in side_set:
                moves.append(((r, c), (nr, nc)))

    return moves


def make_move(side, enemy, move):
    src, dst = move
    side_list = list(side)
    enemy_set = set(enemy)

    try:
        side_list.remove(src)
    except ValueError:
        pass

    side_list.append(dst)

    if dst in enemy_set:
        enemy_set.remove(dst)

    return tuple(sorted(side_list)), tuple(sorted(enemy_set))


def terminal_score(side, enemy, color):
    g = goal_row(color)
    og = goal_row(other_color(color))

    if not enemy:
        return INF - 1

    for r, _ in side:
        if r == g:
            return INF - 1

    for r, _ in enemy:
        if r == og:
            return -INF + 1

    if not side:
        return -INF + 1

    return None


def order_moves(moves, side, enemy, color):
    enemy_set = set(enemy)
    g = goal_row(color)

    def key(mv):
        src, dst = mv
        score = 0

        # Immediate win.
        if dst[0] == g:
            score += 100000

        # Captures.
        if dst in enemy_set:
            score += 10000

        # Advancement.
        score += progress(dst[0], color) * 100

        # Prefer center columns slightly.
        score += 10 * (4 - abs(3.5 - dst[1]))

        # Prefer diagonal moves over straight a little, since they create threats.
        if src[1] != dst[1]:
            score += 25

        return score

    return sorted(moves, key=key, reverse=True)


def evaluate(side, enemy, color):
    """
    Evaluation from the perspective of `side` to move with `color`.
    Positive is good for `side`.
    """
    term = terminal_score(side, enemy, color)
    if term is not None:
        return term

    enemy_color = other_color(color)

    side_set = set(side)
    enemy_set = set(enemy)

    score = 0

    # Material.
    score += 1200 * (len(side) - len(enemy))

    # Advancement and race potential.
    side_best = 0
    enemy_best = 0

    for r, c in side:
        p = progress(r, color)
        side_best = max(side_best, p)
        score += 90 * p
        score += 8 * (4 - abs(3.5 - c))

        # Connected/supporting pawns.
        back_r = r - direction(color)
        for dc in (-1, 1):
            if (back_r, c + dc) in side_set:
                score += 35

        # Passed pawn bonus.
        if is_passed_pawn((r, c), enemy_set, color):
            score += 220 + 70 * p

        # One-step winning threat.
        if r + direction(color) == goal_row(color):
            score += 600

        # Safety / defended.
        if is_defended((r, c), side_set, color):
            score += 25

        # Penalty if enemy can capture this pawn.
        if is_attacked_by_enemy((r, c), enemy_set, enemy_color):
            score -= 55

    for r, c in enemy:
        p = progress(r, enemy_color)
        enemy_best = max(enemy_best, p)
        score -= 90 * p
        score -= 8 * (4 - abs(3.5 - c))

        if is_passed_pawn((r, c), side_set, enemy_color):
            score -= 220 + 70 * p

        if r + direction(enemy_color) == goal_row(enemy_color):
            score -= 600

        if is_defended((r, c), enemy_set, enemy_color):
            score -= 25

        if is_attacked_by_enemy((r, c), side_set, color):
            score += 55

    # Race urgency.
    score += 160 * side_best
    score -= 180 * enemy_best

    # Mobility.
    score += 6 * len(generate_moves(side, enemy, color))
    score -= 6 * len(generate_moves(enemy, side, enemy_color))

    return int(score)


def is_passed_pawn(pawn, enemies, color):
    r, c = pawn
    d = direction(color)

    # Enemy pawns in same or adjacent files ahead of this pawn can stop it.
    nr = r + d
    while 0 <= nr < BOARD_SIZE:
        for dc in (-1, 0, 1):
            nc = c + dc
            if 0 <= nc < BOARD_SIZE and (nr, nc) in enemies:
                return False
        nr += d

    return True


def is_defended(pawn, friends, color):
    r, c = pawn
    back_r = r - direction(color)
    for dc in (-1, 1):
        if (back_r, c + dc) in friends:
            return True
    return False


def is_attacked_by_enemy(pawn, enemies, enemy_color):
    r, c = pawn
    back_r = r - direction(enemy_color)
    for dc in (-1, 1):
        if (back_r, c + dc) in enemies:
            return True
    return False

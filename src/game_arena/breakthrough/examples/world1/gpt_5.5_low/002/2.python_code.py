
import time
import math

BOARD_SIZE = 8
INF = 10 ** 9


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    """
    Return a legal Breakthrough move for the side to move.

    color:
      'b' moves toward row 0
      'w' moves toward row 7
    """
    start_time = time.time()
    time_limit = 0.92

    direction = -1 if color == "b" else 1

    my_set = frozenset(me)
    op_set = frozenset(opp)

    legal = generate_moves(my_set, op_set, direction)
    if not legal:
        # This should not happen in valid non-terminal Breakthrough positions,
        # but return a harmless tuple-shaped fallback.
        if me:
            return (me[0], me[0])
        return ((0, 0), (0, 0))

    # Always keep a legal fallback.
    best_move = legal[0]

    # If there is an immediate winning move, play it.
    for mv in legal:
        new_my, new_op = apply_move(my_set, op_set, mv)
        if is_win_for(new_my, new_op, direction):
            return mv

    # If opponent has a one-move win, moves that stop it will naturally score high,
    # but we also search with ordered alpha-beta.
    max_depth = 1

    try:
        while True:
            if time.time() - start_time > time_limit:
                break

            alpha = -INF
            beta = INF
            current_best = best_move
            current_score = -INF

            ordered = order_moves(legal, my_set, op_set, direction)

            for mv in ordered:
                if time.time() - start_time > time_limit:
                    raise TimeoutError

                new_my, new_op = apply_move(my_set, op_set, mv)

                score = -negamax(
                    new_op,
                    new_my,
                    -direction,
                    max_depth - 1,
                    -beta,
                    -alpha,
                    start_time,
                    time_limit,
                    1,
                )

                if score > current_score:
                    current_score = score
                    current_best = mv

                if score > alpha:
                    alpha = score

            best_move = current_best
            max_depth += 1

            # Searching too deeply is unnecessary under a 1 second limit.
            if max_depth > 7:
                break

    except TimeoutError:
        pass
    except Exception:
        # Never risk returning an illegal/non-move because of an unexpected issue.
        pass

    if best_move in legal:
        return best_move

    return legal[0]


def goal_row(direction: int) -> int:
    return 7 if direction == 1 else 0


def in_bounds(r: int, c: int) -> bool:
    return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE


def generate_moves(my_set: frozenset, op_set: frozenset, direction: int):
    occupied = my_set | op_set
    moves = []

    # Sorting improves determinism.
    for r, c in sorted(my_set):
        nr = r + direction
        if not 0 <= nr < BOARD_SIZE:
            continue

        # Straight forward: only if empty.
        to = (nr, c)
        if to not in occupied:
            moves.append(((r, c), to))

        # Diagonal forward: empty move or capture, but not onto own piece.
        for dc in (-1, 1):
            nc = c + dc
            if 0 <= nc < BOARD_SIZE:
                to = (nr, nc)
                if to not in my_set:
                    moves.append(((r, c), to))

    return moves


def apply_move(my_set: frozenset, op_set: frozenset, move):
    src, dst = move
    new_my = set(my_set)
    new_op = set(op_set)

    new_my.remove(src)
    new_my.add(dst)

    if dst in new_op:
        new_op.remove(dst)

    return frozenset(new_my), frozenset(new_op)


def is_win_for(my_set: frozenset, op_set: frozenset, direction: int) -> bool:
    if not op_set:
        return True
    g = goal_row(direction)
    return any(r == g for r, _ in my_set)


def terminal_score(my_set: frozenset, op_set: frozenset, direction: int, ply: int):
    """
    Score terminal positions from the perspective of the side represented by my_set.
    """
    if not op_set:
        return INF - ply
    if any(r == goal_row(direction) for r, _ in my_set):
        return INF - ply

    if not my_set:
        return -INF + ply
    if any(r == goal_row(-direction) for r, _ in op_set):
        return -INF + ply

    return None


def negamax(my_set: frozenset, op_set: frozenset, direction: int, depth: int,
            alpha: int, beta: int, start_time: float, time_limit: float, ply: int) -> int:
    if time.time() - start_time > time_limit:
        raise TimeoutError

    term = terminal_score(my_set, op_set, direction, ply)
    if term is not None:
        return term

    if depth <= 0:
        return evaluate(my_set, op_set, direction)

    moves = generate_moves(my_set, op_set, direction)
    if not moves:
        return -INF + ply

    best = -INF

    for mv in order_moves(moves, my_set, op_set, direction):
        new_my, new_op = apply_move(my_set, op_set, mv)
        score = -negamax(
            new_op,
            new_my,
            -direction,
            depth - 1,
            -beta,
            -alpha,
            start_time,
            time_limit,
            ply + 1,
        )

        if score > best:
            best = score

        if score > alpha:
            alpha = score

        if alpha >= beta:
            break

    return best


def order_moves(moves, my_set: frozenset, op_set: frozenset, direction: int):
    g = goal_row(direction)

    def key(mv):
        src, dst = mv
        sr, sc = src
        dr, dc = dst

        score = 0

        # Winning move first.
        if dr == g:
            score += 100000

        # Captures are usually valuable.
        if dst in op_set:
            score += 10000

        # Prefer advanced movement.
        score += progress_of_row(dr, direction) * 100

        # Central files are often safer and more flexible.
        score += 20 - abs(dc - 3.5) * 4

        # Prefer moves that create immediate goal threats.
        if abs(g - dr) == 1:
            score += 1500

        # Prefer protected destinations.
        if is_protected(dst, my_set, direction):
            score += 300

        # Penalize walking into simple capture if unprotected.
        if is_attacked_by(dst, op_set, -direction) and not is_protected(dst, my_set, direction):
            score -= 900

        # Slightly favor diagonal mobility.
        if dc != sc:
            score += 25

        return score

    return sorted(moves, key=key, reverse=True)


def progress_of_row(r: int, direction: int) -> int:
    """
    0 near own home row, 7 at opponent home row.
    """
    if direction == 1:
        return r
    return 7 - r


def distance_to_goal(r: int, direction: int) -> int:
    return abs(goal_row(direction) - r)


def evaluate(my_set: frozenset, op_set: frozenset, direction: int) -> int:
    """
    Static evaluation from the perspective of my_set.
    """
    term = terminal_score(my_set, op_set, direction, 0)
    if term is not None:
        return term

    score = 0

    # Material.
    score += 140 * (len(my_set) - len(op_set))

    # Advancement and race potential.
    my_progress = sum(progress_of_row(r, direction) for r, _ in my_set)
    op_progress = sum(progress_of_row(r, -direction) for r, _ in op_set)
    score += 18 * (my_progress - op_progress)

    # Closest pawn to promotion.
    my_best_dist = min(distance_to_goal(r, direction) for r, _ in my_set)
    op_best_dist = min(distance_to_goal(r, -direction) for r, _ in op_set)
    score += 85 * (op_best_dist - my_best_dist)

    # Piece-specific structure.
    for p in my_set:
        r, c = p

        # Advanced pawns become increasingly dangerous.
        prog = progress_of_row(r, direction)
        score += prog * prog * 4

        # Passed pawns are very strong in Breakthrough.
        if is_passed_pawn(p, op_set, direction):
            score += 220 + 45 * prog

        # Protected pieces are more stable.
        if is_protected(p, my_set, direction):
            score += 35

        # Unprotected attacked pieces are vulnerable.
        if is_attacked_by(p, op_set, -direction) and not is_protected(p, my_set, direction):
            score -= 80

        # Immediate promotion threat.
        if distance_to_goal(r, direction) == 1:
            score += 450

        # Central pawns have more diagonal options.
        score += int(12 - abs(c - 3.5) * 3)

    for p in op_set:
        r, c = p
        prog = progress_of_row(r, -direction)

        if is_passed_pawn(p, my_set, -direction):
            score -= 220 + 45 * prog

        if is_protected(p, op_set, -direction):
            score -= 25

        if is_attacked_by(p, my_set, direction) and not is_protected(p, op_set, -direction):
            score += 60

        if distance_to_goal(r, -direction) == 1:
            score -= 500

    # Mobility.
    my_mob = len(generate_moves(my_set, op_set, direction))
    op_mob = len(generate_moves(op_set, my_set, -direction))
    score += 5 * (my_mob - op_mob)

    return int(score)


def is_protected(square: tuple[int, int], own_set: frozenset, direction: int) -> bool:
    """
    A piece on square is protected by own pawns one row behind it diagonally.
    If own pieces move in 'direction', protectors are at row - direction.
    """
    r, c = square
    back_r = r - direction
    return (back_r, c - 1) in own_set or (back_r, c + 1) in own_set


def is_attacked_by(square: tuple[int, int], enemy_set: frozenset, enemy_direction: int) -> bool:
    """
    Whether enemy pawns could capture square on their next move.
    Enemy attackers are one row behind square relative to their movement.
    """
    r, c = square
    back_r = r - enemy_direction
    return (back_r, c - 1) in enemy_set or (back_r, c + 1) in enemy_set


def is_passed_pawn(piece: tuple[int, int], enemy_set: frozenset, direction: int) -> bool:
    """
    A pawn is considered passed if there are no enemy pawns in the same or adjacent
    files ahead of it.
    """
    r, c = piece

    for er, ec in enemy_set:
        if abs(ec - c) <= 1:
            if direction == 1:
                if er > r:
                    return False
            else:
                if er < r:
                    return False

    return True

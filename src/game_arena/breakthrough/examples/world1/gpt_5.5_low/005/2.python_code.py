
from math import inf
import time


BOARD_SIZE = 8
TIME_LIMIT = 0.92


class SearchTimeout(Exception):
    pass


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    """
    Return a legal Breakthrough move for the side to move.

    color:
      'b' moves toward row 0
      'w' moves toward row 7
    """
    start_time = time.perf_counter()

    my_color = color
    op_color = 'w' if color == 'b' else 'b'
    my_dir = -1 if my_color == 'b' else 1
    op_dir = -my_dir
    my_goal = 0 if my_color == 'b' else 7
    op_goal = 7 if my_color == 'b' else 0

    root_me = frozenset(me)
    root_opp = frozenset(opp)

    legal = generate_moves(root_me, root_opp, my_dir)
    if not legal:
        # In normal Breakthrough this should not happen if the game is still active.
        # Return a syntactically valid tuple as a last resort.
        return ((0, 0), (0, 0))

    # Immediate win if available.
    for mv in legal:
        if mv[1][0] == my_goal:
            return mv

    legal = order_moves(legal, root_me, root_opp, my_dir, my_goal)

    best_move = legal[0]

    def check_time():
        if time.perf_counter() - start_time > TIME_LIMIT:
            raise SearchTimeout()

    def terminal_value(my_set, op_set):
        if not op_set:
            return 1_000_000
        if not my_set:
            return -1_000_000
        if any(r == my_goal for r, _ in my_set):
            return 1_000_000
        if any(r == op_goal for r, _ in op_set):
            return -1_000_000
        return None

    def static_eval(my_set, op_set):
        tv = terminal_value(my_set, op_set)
        if tv is not None:
            return tv

        score = 0

        # Material is very important.
        score += 115 * (len(my_set) - len(op_set))

        # Advancement toward goal.
        my_adv = 0
        op_adv = 0
        for r, c in my_set:
            adv = r if my_color == 'w' else 7 - r
            my_adv += adv
            score += adv * 11
            # Center columns are usually more flexible.
            score += 3 * (3.5 - abs(c - 3.5))
        for r, c in op_set:
            adv = r if op_color == 'w' else 7 - r
            op_adv += adv
            score -= adv * 11
            score -= 3 * (3.5 - abs(c - 3.5))

        # Closest runner matters.
        my_best_dist = min(abs(my_goal - r) for r, _ in my_set)
        op_best_dist = min(abs(op_goal - r) for r, _ in op_set)
        score += 35 * (op_best_dist - my_best_dist)

        # Passed pawns / breakthrough threats.
        for r, c in my_set:
            dist = abs(my_goal - r)
            if is_passed_pawn((r, c), op_set, my_dir):
                score += 80 + 20 * (7 - dist)
            if dist <= 2:
                score += 25 * (3 - dist)

        for r, c in op_set:
            dist = abs(op_goal - r)
            if is_passed_pawn((r, c), my_set, op_dir):
                score -= 80 + 20 * (7 - dist)
            if dist <= 2:
                score -= 25 * (3 - dist)

        # Tactical safety: pieces that can be captured next turn are less valuable;
        # pieces defended by friendly diagonals are more valuable.
        for p in my_set:
            if is_attacked_by(p, op_set, op_dir):
                score -= 28
            if is_defended_by(p, my_set, my_dir):
                score += 12

        for p in op_set:
            if is_attacked_by(p, my_set, my_dir):
                score += 28
            if is_defended_by(p, op_set, op_dir):
                score -= 12

        return int(score)

    def apply_move(my_set, op_set, mv):
        frm, to = mv
        new_my = set(my_set)
        new_op = set(op_set)
        new_my.remove(frm)
        new_my.add(to)
        if to in new_op:
            new_op.remove(to)
        return frozenset(new_my), frozenset(new_op)

    def alphabeta(my_set, op_set, depth, alpha, beta, maximizing):
        check_time()

        tv = terminal_value(my_set, op_set)
        if tv is not None:
            return tv

        if depth <= 0:
            return static_eval(my_set, op_set)

        if maximizing:
            moves = generate_moves(my_set, op_set, my_dir)
            if not moves:
                return static_eval(my_set, op_set)
            moves = order_moves(moves, my_set, op_set, my_dir, my_goal)

            value = -inf
            for mv in moves:
                nmy, nop = apply_move(my_set, op_set, mv)
                value = max(value, alphabeta(nmy, nop, depth - 1, alpha, beta, False))
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value
        else:
            # Opponent move. From the root perspective, opponent positions are op_set.
            moves = generate_moves(op_set, my_set, op_dir)
            if not moves:
                return static_eval(my_set, op_set)
            moves = order_moves(moves, op_set, my_set, op_dir, op_goal)

            value = inf
            for mv in moves:
                nop, nmy = apply_move(op_set, my_set, mv)
                value = min(value, alphabeta(nmy, nop, depth - 1, alpha, beta, True))
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return value

    # Adaptive depth target. Iterative deepening ensures a legal move is always ready.
    total_pieces = len(root_me) + len(root_opp)
    if total_pieces <= 10:
        max_depth = 6
    elif total_pieces <= 18:
        max_depth = 5
    else:
        max_depth = 4

    try:
        for depth in range(1, max_depth + 1):
            check_time()
            current_best = best_move
            current_score = -inf
            alpha = -inf
            beta = inf

            for mv in legal:
                check_time()
                nme, nopp = apply_move(root_me, root_opp, mv)
                score = alphabeta(nme, nopp, depth - 1, alpha, beta, False)

                # Tiny deterministic preference for forward progress breaks ties.
                score += progress_of_move(mv, my_dir) * 0.01

                if score > current_score:
                    current_score = score
                    current_best = mv

                alpha = max(alpha, current_score)

            best_move = current_best

            # Forced win found.
            if current_score >= 900_000:
                break

    except SearchTimeout:
        pass

    # Final legality guard.
    if best_move in generate_moves(root_me, root_opp, my_dir):
        return best_move
    return legal[0]


def generate_moves(me_set, opp_set, direction):
    """
    Generate all legal moves for me_set moving in direction.
    direction is +1 or -1.
    Rules used:
      - straight forward only into an empty square
      - diagonal forward into any square not occupied by own piece;
        if occupied by opponent it captures, otherwise it is a quiet diagonal move
    """
    moves = []
    occupied = me_set | opp_set

    for r, c in me_set:
        nr = r + direction
        if nr < 0 or nr >= BOARD_SIZE:
            continue

        # Straight forward.
        to = (nr, c)
        if to not in occupied:
            moves.append(((r, c), to))

        # Diagonal forward left/right.
        for dc in (-1, 1):
            nc = c + dc
            if 0 <= nc < BOARD_SIZE:
                to = (nr, nc)
                if to not in me_set:
                    moves.append(((r, c), to))

    return moves


def order_moves(moves, me_set, opp_set, direction, goal_row):
    scored = []
    for mv in moves:
        frm, to = mv
        score = 0

        # Immediate promotion.
        if to[0] == goal_row:
            score += 100000

        # Captures.
        if to in opp_set:
            score += 2000

        # Advancement.
        score += 20 * progress_of_move(mv, direction)

        # Prefer central destination slightly.
        score += int(4 - abs(to[1] - 3.5))

        # Passed pawn potential.
        if is_passed_pawn(to, opp_set - {to}, direction):
            score += 250

        # Avoid moving onto a square immediately capturable unless it wins/captures.
        opp_dir = -direction
        if is_attacked_by(to, opp_set - {to}, opp_dir):
            score -= 120

        # Prefer defended destinations.
        temp_me = set(me_set)
        temp_me.discard(frm)
        temp_me.add(to)
        if is_defended_by(to, temp_me, direction):
            score += 45

        scored.append((score, mv))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [mv for _, mv in scored]


def progress_of_move(mv, direction):
    frm, to = mv
    return (to[0] - frm[0]) * direction


def is_attacked_by(square, attackers, attacker_dir):
    """
    True if a piece in attackers could capture square by a diagonal forward move.
    """
    r, c = square
    source_row = r - attacker_dir
    if source_row < 0 or source_row >= BOARD_SIZE:
        return False
    return (source_row, c - 1) in attackers or (source_row, c + 1) in attackers


def is_defended_by(square, friends, direction):
    """
    True if square is protected by a friendly piece one row behind diagonally.
    """
    r, c = square
    back_row = r - direction
    if back_row < 0 or back_row >= BOARD_SIZE:
        return False
    return (back_row, c - 1) in friends or (back_row, c + 1) in friends


def is_passed_pawn(piece, enemies, direction):
    """
    A simple passed-pawn test: no enemy in the same or adjacent file ahead.
    """
    r, c = piece
    nr = r + direction
    while 0 <= nr < BOARD_SIZE:
        for dc in (-1, 0, 1):
            nc = c + dc
            if 0 <= nc < BOARD_SIZE and (nr, nc) in enemies:
                return False
        nr += direction
    return True

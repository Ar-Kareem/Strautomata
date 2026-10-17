
import time
import math

# Checkers policy for an 8x8 board.
# Coordinates: row 0 bottom, row 7 top.
# Black ('b') men move downward: row - 1.
# White ('w') men move upward: row + 1.


def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    start_time = time.time()
    TIME_LIMIT = 0.88

    my_men = tuple(my_men)
    my_kings = tuple(my_kings)
    opp_men = tuple(opp_men)
    opp_kings = tuple(opp_kings)

    opp_color = 'w' if color == 'b' else 'b'
    root_state = (frozenset(my_men), frozenset(my_kings), frozenset(opp_men), frozenset(opp_kings))

    def in_bounds(r, c):
        return 0 <= r < 8 and 0 <= c < 8

    def forward_dir(col):
        return -1 if col == 'b' else 1

    def promote_row(col):
        return 0 if col == 'b' else 7

    def piece_dirs(is_king, col):
        if is_king:
            return ((1, 1), (1, -1), (-1, 1), (-1, -1))
        d = forward_dir(col)
        return ((d, 1), (d, -1))

    def generate_moves_for(men, kings, enemy_men, enemy_kings, col):
        """Return legal moves for side: list of (from, to, is_capture). Captures mandatory."""
        occupied = men | kings | enemy_men | enemy_kings
        enemies = enemy_men | enemy_kings

        captures = []

        for p in men:
            r, c = p
            for dr, dc in piece_dirs(False, col):
                mr, mc = r + dr, c + dc
                tr, tc = r + 2 * dr, c + 2 * dc
                if in_bounds(tr, tc) and (mr, mc) in enemies and (tr, tc) not in occupied:
                    captures.append((p, (tr, tc), True))

        for p in kings:
            r, c = p
            for dr, dc in piece_dirs(True, col):
                mr, mc = r + dr, c + dc
                tr, tc = r + 2 * dr, c + 2 * dc
                if in_bounds(tr, tc) and (mr, mc) in enemies and (tr, tc) not in occupied:
                    captures.append((p, (tr, tc), True))

        if captures:
            return captures

        moves = []

        for p in men:
            r, c = p
            for dr, dc in piece_dirs(False, col):
                tr, tc = r + dr, c + dc
                if in_bounds(tr, tc) and (tr, tc) not in occupied:
                    moves.append((p, (tr, tc), False))

        for p in kings:
            r, c = p
            for dr, dc in piece_dirs(True, col):
                tr, tc = r + dr, c + dc
                if in_bounds(tr, tc) and (tr, tc) not in occupied:
                    moves.append((p, (tr, tc), False))

        return moves

    def apply_move(state, move, side):
        """side 0 = root player, side 1 = opponent."""
        mm, mk, om, ok = state
        frm, to, is_cap = move

        if side == 0:
            men, kings, emen, ekings = set(mm), set(mk), set(om), set(ok)
            col = color
        else:
            men, kings, emen, ekings = set(om), set(ok), set(mm), set(mk)
            col = opp_color

        was_king = frm in kings

        if was_king:
            kings.remove(frm)
        else:
            men.remove(frm)

        if is_cap:
            jr = (frm[0] + to[0]) // 2
            jc = (frm[1] + to[1]) // 2
            jumped = (jr, jc)
            if jumped in emen:
                emen.remove(jumped)
            elif jumped in ekings:
                ekings.remove(jumped)

        if was_king:
            kings.add(to)
        else:
            if to[0] == promote_row(col):
                kings.add(to)
            else:
                men.add(to)

        if side == 0:
            return (frozenset(men), frozenset(kings), frozenset(emen), frozenset(ekings))
        else:
            return (frozenset(emen), frozenset(ekings), frozenset(men), frozenset(kings))

    def legal_moves(state, side):
        mm, mk, om, ok = state
        if side == 0:
            return generate_moves_for(mm, mk, om, ok, color)
        return generate_moves_for(om, ok, mm, mk, opp_color)

    def advancement_score(men, col):
        if col == 'w':
            return sum(r for r, _ in men)
        return sum(7 - r for r, _ in men)

    def center_score(pieces):
        score = 0
        for r, c in pieces:
            # Prefer central dark squares.
            score += 4 - abs(3.5 - r) - abs(3.5 - c)
        return score

    def back_row_score(men, col):
        row = 7 if col == 'b' else 0
        return sum(1 for r, _ in men if r == row)

    def evaluate(state):
        mm, mk, om, ok = state

        # Terminal-ish material.
        if not mm and not mk:
            return -100000
        if not om and not ok:
            return 100000

        my_material = 100 * len(mm) + 175 * len(mk)
        op_material = 100 * len(om) + 175 * len(ok)

        score = my_material - op_material

        score += 7 * (advancement_score(mm, color) - advancement_score(om, opp_color))
        score += 5 * (center_score(mm | mk) - center_score(om | ok))
        score += 8 * (back_row_score(mm, color) - back_row_score(om, opp_color))

        # Mobility and tactical availability.
        my_moves = legal_moves(state, 0)
        op_moves = legal_moves(state, 1)

        if not my_moves:
            return -100000
        if not op_moves:
            return 100000

        score += 3 * (len(my_moves) - len(op_moves))

        my_caps = sum(1 for m in my_moves if m[2])
        op_caps = sum(1 for m in op_moves if m[2])
        score += 18 * (my_caps - op_caps)

        # Prefer having pieces protected by friendly pieces behind them.
        def protected_count(men, kings, col):
            friends = men | kings
            total = 0
            for r, c in friends:
                for dr, dc in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
                    if (r - dr, c - dc) in friends:
                        total += 1
                        break
            return total

        score += 4 * (protected_count(mm, mk, color) - protected_count(om, ok, opp_color))

        return score

    def move_order_key(state, move, side):
        frm, to, is_cap = move
        val = 0
        if is_cap:
            val += 1000
        # Promotion bonus.
        col = color if side == 0 else opp_color
        own_men = state[0] if side == 0 else state[2]
        if frm in own_men and to[0] == promote_row(col):
            val += 700
        # Centering.
        val += int(20 - 3 * (abs(3.5 - to[0]) + abs(3.5 - to[1])))
        return val

    def alphabeta(state, depth, alpha, beta, side):
        if time.time() - start_time > TIME_LIMIT:
            raise TimeoutError

        moves = legal_moves(state, side)
        if depth == 0 or not moves:
            return evaluate(state)

        moves.sort(key=lambda m: move_order_key(state, m, side), reverse=True)

        if side == 0:
            value = -math.inf
            for mv in moves:
                ns = apply_move(state, mv, 0)
                value = max(value, alphabeta(ns, depth - 1, alpha, beta, 1))
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value
        else:
            value = math.inf
            for mv in moves:
                ns = apply_move(state, mv, 1)
                value = min(value, alphabeta(ns, depth - 1, alpha, beta, 0))
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return value

    root_moves = legal_moves(root_state, 0)

    # In a valid game this should not happen. Return a syntactically valid fallback.
    if not root_moves:
        if my_men:
            p = my_men[0]
            return (p, p)
        if my_kings:
            p = my_kings[0]
            return (p, p)
        return ((0, 0), (0, 0))

    # Immediate safe fallback: ordered first legal move.
    root_moves.sort(key=lambda m: move_order_key(root_state, m, 0), reverse=True)
    best_move = root_moves[0]
    best_score = -math.inf

    # Iterative deepening. Depths are modest to fit 1 second reliably.
    max_depth = 7
    try:
        for depth in range(1, max_depth + 1):
            current_best = best_move
            current_score = -math.inf

            ordered = list(root_moves)
            ordered.sort(key=lambda m: move_order_key(root_state, m, 0), reverse=True)

            for mv in ordered:
                if time.time() - start_time > TIME_LIMIT:
                    raise TimeoutError
                ns = apply_move(root_state, mv, 0)
                sc = alphabeta(ns, depth - 1, -math.inf, math.inf, 1)

                # Tiny deterministic tie-breaker: prefer captures, promotion, center.
                if sc > current_score:
                    current_score = sc
                    current_best = mv

            best_move = current_best
            best_score = current_score

    except TimeoutError:
        pass

    return (best_move[0], best_move[1])

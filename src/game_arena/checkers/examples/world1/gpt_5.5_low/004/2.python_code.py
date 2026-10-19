
import time
import math
from functools import lru_cache

def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    """
    Checkers policy for an 8x8 board.

    Coordinates:
      row 0 is bottom, row 7 is top.
      black ('b') moves downward: row - 1
      white ('w') moves upward: row + 1

    Returns:
      ((from_row, from_col), (to_row, to_col))

    Captures are mandatory.
    """

    start_time = time.time()
    TIME_LIMIT = 0.88

    my_color = color
    opp_color = 'w' if color == 'b' else 'b'

    # Normalize to tuples for hashing.
    root = (
        tuple(sorted(my_men)),
        tuple(sorted(my_kings)),
        tuple(sorted(opp_men)),
        tuple(sorted(opp_kings)),
    )

    def in_bounds(r, c):
        return 0 <= r < 8 and 0 <= c < 8

    def forward_dirs(side_color):
        if side_color == 'b':
            return [(-1, -1), (-1, 1)]
        else:
            return [(1, -1), (1, 1)]

    KING_DIRS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]

    def side_sets(state, side):
        mm, mk, om, ok = state
        if side == 0:
            return set(mm), set(mk), set(om), set(ok)
        else:
            return set(om), set(ok), set(mm), set(mk)

    def pack_sets(my_m, my_k, op_m, op_k, side):
        if side == 0:
            return (
                tuple(sorted(my_m)),
                tuple(sorted(my_k)),
                tuple(sorted(op_m)),
                tuple(sorted(op_k)),
            )
        else:
            return (
                tuple(sorted(op_m)),
                tuple(sorted(op_k)),
                tuple(sorted(my_m)),
                tuple(sorted(my_k)),
            )

    def generate_moves(state, side):
        """
        side 0 = root player, side 1 = opponent.
        Returns list of moves: ((fr,fc), (tr,tc), is_capture)
        """
        my_m, my_k, op_m, op_k = side_sets(state, side)
        occupied = my_m | my_k | op_m | op_k
        enemies = op_m | op_k
        side_color = my_color if side == 0 else opp_color

        captures = []

        # Men captures.
        for r, c in my_m:
            for dr, dc in forward_dirs(side_color):
                mr, mc = r + dr, c + dc
                tr, tc = r + 2 * dr, c + 2 * dc
                if in_bounds(tr, tc) and (mr, mc) in enemies and (tr, tc) not in occupied:
                    captures.append(((r, c), (tr, tc), True))

        # King captures.
        for r, c in my_k:
            for dr, dc in KING_DIRS:
                mr, mc = r + dr, c + dc
                tr, tc = r + 2 * dr, c + 2 * dc
                if in_bounds(tr, tc) and (mr, mc) in enemies and (tr, tc) not in occupied:
                    captures.append(((r, c), (tr, tc), True))

        if captures:
            return captures

        moves = []

        # Men quiet moves.
        for r, c in my_m:
            for dr, dc in forward_dirs(side_color):
                tr, tc = r + dr, c + dc
                if in_bounds(tr, tc) and (tr, tc) not in occupied:
                    moves.append(((r, c), (tr, tc), False))

        # King quiet moves.
        for r, c in my_k:
            for dr, dc in KING_DIRS:
                tr, tc = r + dr, c + dc
                if in_bounds(tr, tc) and (tr, tc) not in occupied:
                    moves.append(((r, c), (tr, tc), False))

        return moves

    def apply_move(state, side, move):
        my_m, my_k, op_m, op_k = side_sets(state, side)
        fr, fc = move[0]
        tr, tc = move[1]
        is_cap = abs(tr - fr) == 2

        side_color = my_color if side == 0 else opp_color
        promote_row = 0 if side_color == 'b' else 7

        was_king = (fr, fc) in my_k

        if was_king:
            my_k.remove((fr, fc))
        else:
            my_m.remove((fr, fc))

        if is_cap:
            mr, mc = (fr + tr) // 2, (fc + tc) // 2
            if (mr, mc) in op_m:
                op_m.remove((mr, mc))
            elif (mr, mc) in op_k:
                op_k.remove((mr, mc))

        if was_king or tr == promote_row:
            my_k.add((tr, tc))
        else:
            my_m.add((tr, tc))

        return pack_sets(my_m, my_k, op_m, op_k, side)

    def advancement_score(piece, side_color):
        r, c = piece
        if side_color == 'w':
            return r
        else:
            return 7 - r

    def evaluate(state):
        mm, mk, om, ok = state

        # Terminal-ish material.
        if not mm and not mk:
            return -100000
        if not om and not ok:
            return 100000

        score = 0

        # Material.
        score += 100 * len(mm)
        score += 175 * len(mk)
        score -= 100 * len(om)
        score -= 175 * len(ok)

        # Advancement toward kinging.
        for p in mm:
            score += 5 * advancement_score(p, my_color)
        for p in om:
            score -= 5 * advancement_score(p, opp_color)

        # Center control and edge penalty.
        for r, c in mm:
            if 2 <= r <= 5 and 2 <= c <= 5:
                score += 8
            if c == 0 or c == 7:
                score -= 2
        for r, c in mk:
            if 2 <= r <= 5 and 2 <= c <= 5:
                score += 12
        for r, c in om:
            if 2 <= r <= 5 and 2 <= c <= 5:
                score -= 8
            if c == 0 or c == 7:
                score += 2
        for r, c in ok:
            if 2 <= r <= 5 and 2 <= c <= 5:
                score -= 12

        # Back-row guard: useful early/mid game.
        my_back = 7 if my_color == 'b' else 0
        opp_back = 7 if opp_color == 'b' else 0
        score += 6 * sum(1 for r, c in mm if r == my_back)
        score -= 6 * sum(1 for r, c in om if r == opp_back)

        # Mobility.
        my_moves = len(generate_moves(state, 0))
        op_moves = len(generate_moves(state, 1))
        score += 3 * my_moves
        score -= 3 * op_moves

        # If opponent has an immediate capture, this is dangerous.
        opp_gen = generate_moves(state, 1)
        if opp_gen and opp_gen[0][2]:
            score -= 35 * len(opp_gen)

        my_gen = generate_moves(state, 0)
        if my_gen and my_gen[0][2]:
            score += 35 * len(my_gen)

        return score

    def move_order_key(move):
        fr, fc = move[0]
        tr, tc = move[1]
        cap = abs(tr - fr) == 2
        # Prefer captures, promotion moves, central destinations.
        promo = (my_color == 'b' and tr == 0) or (my_color == 'w' and tr == 7)
        center = -((tr - 3.5) ** 2 + (tc - 3.5) ** 2)
        return (1 if cap else 0, 1 if promo else 0, center)

    @lru_cache(maxsize=200000)
    def alphabeta_cached(state, side, depth, alpha_i, beta_i):
        # Cache wrapper uses integer alpha/beta buckets to avoid huge cache misses.
        alpha = alpha_i
        beta = beta_i
        return alphabeta_uncached(state, side, depth, alpha, beta)

    def alphabeta_uncached(state, side, depth, alpha, beta):
        if time.time() - start_time > TIME_LIMIT:
            raise TimeoutError

        moves = generate_moves(state, side)

        if depth == 0 or not moves:
            if not moves:
                return -100000 + depth if side == 0 else 100000 - depth
            return evaluate(state)

        if side == 0:
            best = -math.inf
            moves.sort(key=move_order_key, reverse=True)
            for mv in moves:
                ns = apply_move(state, side, mv)
                val = alphabeta_uncached(ns, 1, depth - 1, alpha, beta)
                if val > best:
                    best = val
                if best > alpha:
                    alpha = best
                if alpha >= beta:
                    break
            return best
        else:
            best = math.inf
            # Opponent also prefers tactically forcing moves.
            moves.sort(key=lambda m: (1 if m[2] else 0), reverse=True)
            for mv in moves:
                ns = apply_move(state, side, mv)
                val = alphabeta_uncached(ns, 0, depth - 1, alpha, beta)
                if val < best:
                    best = val
                if best < beta:
                    beta = best
                if alpha >= beta:
                    break
            return best

    # Root legal moves. Mandatory captures handled here.
    legal = generate_moves(root, 0)

    # Absolute safety fallback. If somehow no legal move exists, return a syntactically
    # valid move from any own piece; normal game states should never reach this.
    if not legal:
        if my_men:
            r, c = my_men[0]
            dirs = forward_dirs(my_color)
            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                if in_bounds(nr, nc):
                    return ((r, c), (nr, nc))
            return ((r, c), (r, c))
        if my_kings:
            r, c = my_kings[0]
            for dr, dc in KING_DIRS:
                nr, nc = r + dr, c + dc
                if in_bounds(nr, nc):
                    return ((r, c), (nr, nc))
            return ((r, c), (r, c))
        return ((0, 0), (1, 1))

    # If only one move, return immediately.
    if len(legal) == 1:
        return (legal[0][0], legal[0][1])

    legal.sort(key=move_order_key, reverse=True)
    best_move = legal[0]
    best_score = -math.inf

    total_pieces = len(my_men) + len(my_kings) + len(opp_men) + len(opp_kings)

    # Adaptive iterative deepening.
    if total_pieces <= 8:
        max_depth = 8
    elif total_pieces <= 14:
        max_depth = 7
    elif total_pieces <= 20:
        max_depth = 6
    else:
        max_depth = 5

    try:
        for depth in range(1, max_depth + 1):
            current_best = best_move
            current_score = -math.inf
            alpha = -math.inf
            beta = math.inf

            for mv in legal:
                if time.time() - start_time > TIME_LIMIT:
                    raise TimeoutError

                ns = apply_move(root, 0, mv)
                val = alphabeta_uncached(ns, 1, depth - 1, alpha, beta)

                # Small root bonuses for tactical/common-sense preferences.
                fr, fc = mv[0]
                tr, tc = mv[1]
                if abs(tr - fr) == 2:
                    val += 20
                if (my_color == 'b' and tr == 0) or (my_color == 'w' and tr == 7):
                    val += 25
                if 2 <= tr <= 5 and 2 <= tc <= 5:
                    val += 4

                if val > current_score:
                    current_score = val
                    current_best = mv

                if val > alpha:
                    alpha = val

            best_move = current_best
            best_score = current_score

    except TimeoutError:
        pass
    except Exception:
        # Never risk disqualification: fall back to legal move.
        best_move = legal[0]

    return (best_move[0], best_move[1])

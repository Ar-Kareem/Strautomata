
import time
from math import inf

# American checkers / English draughts style movement:
# black moves toward smaller row numbers, white toward larger row numbers.
MAN_DIRS = {
    "b": [(-1, -1), (-1, 1)],
    "w": [(1, -1), (1, 1)],
}
KING_DIRS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
OPP = {"b": "w", "w": "b"}

WIN_SCORE = 1000000


def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    start_time = time.perf_counter()
    deadline = start_time + 0.88

    root_color = color
    opp_color = OPP[color]

    if color == "b":
        root_state = (
            frozenset(tuple(x) for x in my_men),
            frozenset(tuple(x) for x in my_kings),
            frozenset(tuple(x) for x in opp_men),
            frozenset(tuple(x) for x in opp_kings),
        )
    else:
        root_state = (
            frozenset(tuple(x) for x in opp_men),
            frozenset(tuple(x) for x in opp_kings),
            frozenset(tuple(x) for x in my_men),
            frozenset(tuple(x) for x in my_kings),
        )

    eval_cache = {}
    nodes = [0]

    class Timeout(Exception):
        pass

    def in_board(r, c):
        return 0 <= r < 8 and 0 <= c < 8

    def get_sets(state, side):
        bm, bk, wm, wk = state
        if side == "b":
            return bm, bk, wm, wk
        return wm, wk, bm, bk

    def is_promotion(side, row):
        return (side == "b" and row == 0) or (side == "w" and row == 7)

    def generate_moves(state, side):
        bm, bk, wm, wk = state
        if side == "b":
            own_men, own_kings = bm, bk
            opp_pieces = wm | wk
        else:
            own_men, own_kings = wm, wk
            opp_pieces = bm | bk

        occupied = bm | bk | wm | wk
        captures = []
        quiets = []

        for r, c in sorted(own_men):
            for dr, dc in MAN_DIRS[side]:
                mr, mc = r + dr, c + dc
                lr, lc = r + 2 * dr, c + 2 * dc
                if in_board(lr, lc) and (mr, mc) in opp_pieces and (lr, lc) not in occupied:
                    captures.append(((r, c), (lr, lc), (mr, mc)))
            if not captures:
                for dr, dc in MAN_DIRS[side]:
                    nr, nc = r + dr, c + dc
                    if in_board(nr, nc) and (nr, nc) not in occupied:
                        quiets.append(((r, c), (nr, nc), None))

        for r, c in sorted(own_kings):
            for dr, dc in KING_DIRS:
                mr, mc = r + dr, c + dc
                lr, lc = r + 2 * dr, c + 2 * dc
                if in_board(lr, lc) and (mr, mc) in opp_pieces and (lr, lc) not in occupied:
                    captures.append(((r, c), (lr, lc), (mr, mc)))
            if not captures:
                for dr, dc in KING_DIRS:
                    nr, nc = r + dr, c + dc
                    if in_board(nr, nc) and (nr, nc) not in occupied:
                        quiets.append(((r, c), (nr, nc), None))

        return captures if captures else quiets

    def apply_move(state, side, move):
        src, dst, cap = move
        bm, bk, wm, wk = map(set, state)

        if side == "b":
            own_men, own_kings = bm, bk
            opp_men_set, opp_kings_set = wm, wk
        else:
            own_men, own_kings = wm, wk
            opp_men_set, opp_kings_set = bm, bk

        was_king = src in own_kings

        if was_king:
            own_kings.remove(src)
        else:
            own_men.remove(src)

        if cap is not None:
            if cap in opp_men_set:
                opp_men_set.remove(cap)
            elif cap in opp_kings_set:
                opp_kings_set.remove(cap)

        if was_king or is_promotion(side, dst[0]):
            own_kings.add(dst)
        else:
            own_men.add(dst)

        return (
            frozenset(bm),
            frozenset(bk),
            frozenset(wm),
            frozenset(wk),
        )

    def captured_value(state, side, cap_square):
        bm, bk, wm, wk = state
        if cap_square is None:
            return 0
        if side == "b":
            return 190 if cap_square in wk else 105
        return 190 if cap_square in bk else 105

    def local_move_score(state, side, move):
        src, dst, cap = move
        bm, bk, wm, wk = state

        score = 0
        score += captured_value(state, side, cap) * 10

        own_kings = bk if side == "b" else wk
        own_men = bm if side == "b" else wm

        if src in own_men and is_promotion(side, dst[0]):
            score += 900

        # Prefer central, flexible destinations.
        r, c = dst
        score += int(20 - 4 * abs(c - 3.5) - 2 * abs(r - 3.5))

        # Encourage men to advance, but do not overdo it.
        if src in own_men:
            if side == "b":
                score += (src[0] - dst[0]) * 8
            else:
                score += (dst[0] - src[0]) * 8

        # Edges are safer but less mobile; small safety bonus.
        if c == 0 or c == 7:
            score += 5

        return score

    def order_moves(state, side, moves):
        return sorted(moves, key=lambda m: local_move_score(state, side, m), reverse=True)

    def side_static_score(men, kings, side):
        score = 0

        for r, c in men:
            progress = (7 - r) if side == "b" else r
            piece_score = 100 + 6 * progress

            # Very near promotion is valuable.
            if (side == "b" and r == 1) or (side == "w" and r == 6):
                piece_score += 18

            # Back-row guards can prevent easy opposing kings.
            if (side == "b" and r == 7) or (side == "w" and r == 0):
                piece_score += 7

            # Center control.
            piece_score += int(7 - 2 * abs(c - 3.5))
            if 2 <= r <= 5 and 2 <= c <= 5:
                piece_score += 5

            # Edge safety.
            if c == 0 or c == 7:
                piece_score += 3

            score += piece_score

        for r, c in kings:
            piece_score = 178

            # Kings like the center where they have maximum mobility.
            piece_score += int(12 - 3 * abs(c - 3.5) - 2 * abs(r - 3.5))
            if 2 <= r <= 5 and 2 <= c <= 5:
                piece_score += 8
            if c == 0 or c == 7:
                piece_score += 2

            score += piece_score

        return score

    def evaluate(state):
        cached = eval_cache.get(state)
        if cached is not None:
            return cached

        bm, bk, wm, wk = state

        black_score = side_static_score(bm, bk, "b")
        white_score = side_static_score(wm, wk, "w")

        b_moves = generate_moves(state, "b")
        w_moves = generate_moves(state, "w")

        # Mobility and tempo.
        black_score += 4 * len(b_moves)
        white_score += 4 * len(w_moves)

        # Having captures available is usually tactically good.
        if b_moves and b_moves[0][2] is not None:
            black_score += 25 + 4 * len(b_moves)
        if w_moves and w_moves[0][2] is not None:
            white_score += 25 + 4 * len(w_moves)

        # Penalize pieces that are immediately capturable.
        b_captured = set(m[2] for m in w_moves if m[2] is not None)
        w_captured = set(m[2] for m in b_moves if m[2] is not None)

        for sq in b_captured:
            if sq in bk:
                black_score -= 58
            elif sq in bm:
                black_score -= 38

        for sq in w_captured:
            if sq in wk:
                white_score -= 58
            elif sq in wm:
                white_score -= 38

        # If one side has no legal moves, that is almost decisive.
        if not b_moves:
            black_score -= 5000
        if not w_moves:
            white_score -= 5000

        raw = black_score - white_score
        val = raw if root_color == "b" else -raw
        eval_cache[state] = val
        return val

    def check_time():
        nodes[0] += 1
        if (nodes[0] & 1023) == 0 and time.perf_counter() > deadline:
            raise Timeout()

    def alphabeta(state, turn, depth, alpha, beta, qdepth):
        check_time()

        moves = generate_moves(state, turn)

        if not moves:
            if turn == root_color:
                return -WIN_SCORE
            return WIN_SCORE

        # Quiescence: if the horizon lands on a forced capture, search a little deeper.
        if depth <= 0:
            if qdepth <= 0 or moves[0][2] is None:
                return evaluate(state)
            qdepth -= 1

        maximizing = turn == root_color
        ordered = order_moves(state, turn, moves)
        next_turn = OPP[turn]

        if maximizing:
            value = -inf
            for mv in ordered:
                child = apply_move(state, turn, mv)
                value = max(value, alphabeta(child, next_turn, depth - 1, alpha, beta, qdepth))
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value
        else:
            value = inf
            for mv in ordered:
                child = apply_move(state, turn, mv)
                value = min(value, alphabeta(child, next_turn, depth - 1, alpha, beta, qdepth))
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return value

    root_moves = generate_moves(root_state, root_color)

    # Terminal positions should normally not call policy. If they do, no legal move exists.
    # Return a harmless placeholder as a last resort.
    if not root_moves:
        if my_men:
            p = tuple(my_men[0])
            return (p, p)
        if my_kings:
            p = tuple(my_kings[0])
            return (p, p)
        return ((0, 0), (0, 0))

    root_moves = order_moves(root_state, root_color, root_moves)

    # Guaranteed legal fallback.
    best_move = root_moves[0]
    best_val = -inf
    for mv in root_moves:
        child = apply_move(root_state, root_color, mv)
        val = evaluate(child)
        if val > best_val:
            best_val = val
            best_move = mv

    total_pieces = (
        len(root_state[0]) + len(root_state[1]) +
        len(root_state[2]) + len(root_state[3])
    )

    if total_pieces >= 20:
        max_depth = 5
    elif total_pieces >= 15:
        max_depth = 6
    elif total_pieces >= 10:
        max_depth = 7
    else:
        max_depth = 9

    # Forced-capture positions have lower branching, so try a bit deeper.
    if root_moves and root_moves[0][2] is not None:
        max_depth += 2

    try:
        for depth in range(1, max_depth + 1):
            if time.perf_counter() > deadline:
                break

            current_best = best_move
            current_best_val = -inf
            alpha = -inf
            beta = inf

            for mv in root_moves:
                if time.perf_counter() > deadline:
                    raise Timeout()

                child = apply_move(root_state, root_color, mv)
                val = alphabeta(child, opp_color, depth - 1, alpha, beta, 2)

                if val > current_best_val:
                    current_best_val = val
                    current_best = mv

                alpha = max(alpha, current_best_val)

            best_move = current_best
            best_val = current_best_val

            # Found a forced win; no need to spend more time.
            if best_val > WIN_SCORE // 2:
                break

    except Timeout:
        pass

    return (best_move[0], best_move[1])

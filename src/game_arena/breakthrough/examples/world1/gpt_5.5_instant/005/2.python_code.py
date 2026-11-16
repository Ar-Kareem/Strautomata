
import time
import math
from functools import lru_cache

BOARD_N = 8
TIME_LIMIT = 0.92

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    start_time = time.time()
    deadline = start_time + TIME_LIMIT

    direction = -1 if color == 'b' else 1
    win_row = 0 if color == 'b' else 7

    me_t = tuple(sorted(me))
    opp_t = tuple(sorted(opp))

    def in_bounds(r, c):
        return 0 <= r < 8 and 0 <= c < 8

    def gen_moves(my_pieces, op_pieces, d):
        my_set = set(my_pieces)
        op_set = set(op_pieces)
        occ = my_set | op_set
        moves = []

        # Prefer advanced pieces first for better alpha-beta ordering.
        pieces = sorted(my_pieces, key=lambda p: p[0] * d, reverse=True)

        for r, c in pieces:
            nr = r + d
            if not (0 <= nr < 8):
                continue

            # Diagonal moves/captures.
            for dc in (-1, 1):
                nc = c + dc
                if 0 <= nc < 8 and (nr, nc) not in my_set:
                    # Diagonal move is legal whether empty or occupied by opponent.
                    moves.append(((r, c), (nr, nc)))

            # Straight move only to empty square.
            if (nr, c) not in occ:
                moves.append(((r, c), (nr, c)))

        return moves

    def apply_move(my_pieces, op_pieces, move):
        fr, to = move
        my_list = list(my_pieces)
        op_list = list(op_pieces)
        try:
            idx = my_list.index(fr)
            my_list[idx] = to
        except ValueError:
            return my_pieces, op_pieces

        if to in op_list:
            op_list.remove(to)

        return tuple(sorted(my_list)), tuple(sorted(op_list))

    def is_win(my_pieces, op_pieces, my_win_row):
        if not op_pieces:
            return True
        for r, c in my_pieces:
            if r == my_win_row:
                return True
        return False

    def static_move_score(mv, my_pieces, op_pieces, d, my_win_row):
        fr, to = mv
        score = 0
        if to in op_pieces:
            score += 500
        if to[0] == my_win_row:
            score += 100000
        # Advancement.
        score += (fr[0] - to[0]) * 20 if d == -1 else (to[0] - fr[0]) * 20
        # Center preference.
        score += 4 - abs(3.5 - to[1])
        return score

    def ordered_moves(my_pieces, op_pieces, d, my_win_row):
        moves = gen_moves(my_pieces, op_pieces, d)
        moves.sort(key=lambda m: static_move_score(m, my_pieces, op_pieces, d, my_win_row), reverse=True)
        return moves

    def evaluate(my_pieces, op_pieces, d, my_win_row):
        op_d = -d
        op_win_row = 7 if my_win_row == 0 else 0

        if is_win(my_pieces, op_pieces, my_win_row):
            return 10000000
        if is_win(op_pieces, my_pieces, op_win_row):
            return -10000000

        my_set = set(my_pieces)
        op_set = set(op_pieces)
        score = 0

        # Material.
        score += 180 * (len(my_pieces) - len(op_pieces))

        # Mobility.
        score += 8 * (len(gen_moves(my_pieces, op_pieces, d)) - len(gen_moves(op_pieces, my_pieces, op_d)))

        # Piece-specific features.
        for r, c in my_pieces:
            progress = (7 - r) if d == -1 else r
            dist = 7 - progress
            score += 35 * progress
            score += 8 * (4 - abs(3.5 - c))

            # Passed pawn: no opponent ahead in same/adjacent columns.
            passed = True
            for orow, ocol in op_pieces:
                if abs(ocol - c) <= 1:
                    if (d == -1 and orow < r) or (d == 1 and orow > r):
                        passed = False
                        break
            if passed:
                score += 80 + 25 * progress
                if dist <= 2:
                    score += 250 * (3 - dist)

            # Threatened by opponent diagonals.
            br = r - d
            threatened = False
            for dc in (-1, 1):
                if (br, c + dc) in op_set:
                    threatened = True
            if threatened:
                score -= 35 + 8 * progress

            # Protected by friendly diagonals behind.
            pr = r - d
            protected = False
            for dc in (-1, 1):
                if (pr, c + dc) in my_set:
                    protected = True
            if protected:
                score += 22

            # Immediate attacking options.
            ar = r + d
            for dc in (-1, 1):
                if (ar, c + dc) in op_set:
                    score += 45

        for r, c in op_pieces:
            progress = r if d == -1 else (7 - r)
            dist = 7 - progress
            score -= 35 * progress
            score -= 8 * (4 - abs(3.5 - c))

            passed = True
            for mr, mc in my_pieces:
                if abs(mc - c) <= 1:
                    if (op_d == -1 and mr < r) or (op_d == 1 and mr > r):
                        passed = False
                        break
            if passed:
                score -= 80 + 25 * progress
                if dist <= 2:
                    score -= 300 * (3 - dist)

        return score

    # Fallback move: guaranteed if any legal move exists.
    legal = ordered_moves(me_t, opp_t, direction, win_row)
    if not legal:
        # Should not occur in legal Breakthrough states, but return a harmless tuple if forced.
        if me:
            r, c = me[0]
            nr = max(0, min(7, r + direction))
            return ((r, c), (nr, c))
        return ((0, 0), (0, 0))

    # Immediate win.
    for mv in legal:
        new_me, new_opp = apply_move(me_t, opp_t, mv)
        if is_win(new_me, new_opp, win_row):
            return mv

    best_move = max(legal, key=lambda m: evaluate(*apply_move(me_t, opp_t, m), direction, win_row))

    # Try to block opponent immediate wins: prefer moves after which opponent has no immediate win.
    safe_moves = []
    opp_win_row = 7 if win_row == 0 else 0
    for mv in legal:
        new_me, new_opp = apply_move(me_t, opp_t, mv)
        opp_moves = gen_moves(new_opp, new_me, -direction)
        opp_can_win = False
        for om in opp_moves:
            oo, mm = apply_move(new_opp, new_me, om)
            if is_win(oo, mm, opp_win_row):
                opp_can_win = True
                break
        if not opp_can_win:
            safe_moves.append(mv)
    if safe_moves:
        best_move = max(safe_moves, key=lambda m: evaluate(*apply_move(me_t, opp_t, m), direction, win_row))

    @lru_cache(maxsize=200000)
    def search(my_pieces, op_pieces, d, depth, alpha, beta):
        if time.time() > deadline:
            raise TimeoutError

        my_win = 0 if d == -1 else 7
        op_win = 7 if d == -1 else 0

        if is_win(my_pieces, op_pieces, my_win):
            return 10000000 + depth
        if is_win(op_pieces, my_pieces, op_win):
            return -10000000 - depth
        if depth == 0:
            return evaluate(my_pieces, op_pieces, d, my_win)

        moves = ordered_moves(my_pieces, op_pieces, d, my_win)
        if not moves:
            return -9999999

        value = -math.inf
        for mv in moves:
            nmy, nop = apply_move(my_pieces, op_pieces, mv)
            score = -search(nop, nmy, -d, depth - 1, -beta, -alpha)
            if score > value:
                value = score
            if value > alpha:
                alpha = value
            if alpha >= beta:
                break
        return value

    # Iterative deepening. Depths beyond 5 are only reached in reduced positions.
    for depth in range(1, 7):
        if time.time() > deadline:
            break
        try:
            current_best = best_move
            current_score = -math.inf
            alpha = -math.inf
            beta = math.inf

            for mv in ordered_moves(me_t, opp_t, direction, win_row):
                if time.time() > deadline:
                    raise TimeoutError
                nme, nopp = apply_move(me_t, opp_t, mv)
                score = -search(nopp, nme, -direction, depth - 1, -beta, -alpha)
                if score > current_score:
                    current_score = score
                    current_best = mv
                if score > alpha:
                    alpha = score

            best_move = current_best
        except TimeoutError:
            break
        except Exception:
            break

    # Final legality guard.
    if best_move in gen_moves(me_t, opp_t, direction):
        return best_move
    return legal[0]

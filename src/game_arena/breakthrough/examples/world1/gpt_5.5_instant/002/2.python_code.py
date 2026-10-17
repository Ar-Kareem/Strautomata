
from functools import lru_cache
import time
import math

BOARD_N = 8
INF = 10**9

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    start_time = time.perf_counter()
    TIME_LIMIT = 0.88

    my_dir = -1 if color == 'b' else 1
    opp_color = 'w' if color == 'b' else 'b'
    my_goal = 0 if color == 'b' else 7

    me_t = tuple(sorted(me))
    opp_t = tuple(sorted(opp))

    def direction(c):
        return -1 if c == 'b' else 1

    def goal_row(c):
        return 0 if c == 'b' else 7

    def inb(r, c):
        return 0 <= r < 8 and 0 <= c < 8

    def gen_moves_side(my_pieces, op_pieces, c):
        d = direction(c)
        my_set = set(my_pieces)
        op_set = set(op_pieces)
        moves = []
        for r, col in my_pieces:
            nr = r + d
            if not (0 <= nr < 8):
                continue
            # Diagonal moves/captures
            for dc in (-1, 1):
                nc = col + dc
                if 0 <= nc < 8 and (nr, nc) not in my_set:
                    moves.append(((r, col), (nr, nc)))
            # Straight forward only if empty
            if (nr, col) not in my_set and (nr, col) not in op_set:
                moves.append(((r, col), (nr, col)))
        return moves

    legal = gen_moves_side(me_t, opp_t, color)
    if not legal:
        # Extremely unlikely in Breakthrough, but API requires a legal-looking return.
        return ((me[0][0], me[0][1]), (me[0][0] + my_dir, me[0][1])) if me else ((0, 0), (0, 0))

    def apply_move(my_pieces, op_pieces, mv):
        frm, to = mv
        mp = list(my_pieces)
        try:
            mp.remove(frm)
        except ValueError:
            pass
        mp.append(to)
        if to in op_pieces:
            op = list(op_pieces)
            try:
                op.remove(to)
            except ValueError:
                pass
        else:
            op = list(op_pieces)
        return tuple(sorted(mp)), tuple(sorted(op))

    # Immediate win
    for mv in legal:
        nm, no = apply_move(me_t, opp_t, mv)
        if mv[1][0] == my_goal or not no:
            return mv

    # Block opponent immediate promotion if possible.
    opp_legal_now = gen_moves_side(opp_t, me_t, opp_color)
    opp_goal = goal_row(opp_color)
    danger_squares = set()
    for omv in opp_legal_now:
        if omv[1][0] == opp_goal:
            danger_squares.add(omv[1])
            danger_squares.add(omv[0])
    if danger_squares:
        best_block = None
        best_block_score = -INF
        for mv in legal:
            nm, no = apply_move(me_t, opp_t, mv)
            opp_after = gen_moves_side(no, nm, opp_color)
            if not any(x[1][0] == opp_goal for x in opp_after):
                sc = 1000 + (1 if mv[1] in opp_t else 0) * 500
                sc += progress_score(mv[1][0], color) * 10
                if sc > best_block_score:
                    best_block_score = sc
                    best_block = mv
        if best_block is not None:
            return best_block

    def terminal_score(my_pieces, op_pieces, side_color, root_color):
        # State is from side_color perspective to move, but terminal winner is absolute.
        if not op_pieces:
            return INF - 1000
        if not my_pieces:
            return -INF + 1000
        g_my = goal_row(side_color)
        g_op = goal_row('w' if side_color == 'b' else 'b')
        if any(r == g_my for r, c in my_pieces):
            return INF - 1000
        if any(r == g_op for r, c in op_pieces):
            return -INF + 1000
        return None

    def progress_score(r, c):
        return (7 - r) if c == 'b' else r

    def is_passed(piece, my_c, enemy_pieces):
        r, col = piece
        d = direction(my_c)
        for er, ec in enemy_pieces:
            if abs(ec - col) <= 1:
                if my_c == 'b':
                    if er < r:
                        return False
                else:
                    if er > r:
                        return False
        return True

    def threatened_by(piece, enemy_pieces, enemy_c):
        r, col = piece
        ed = direction(enemy_c)
        # Enemy at (r-ed, col +/- 1) attacks this square.
        return ((r - ed, col - 1) in enemy_pieces) or ((r - ed, col + 1) in enemy_pieces)

    def protected_by(piece, own_pieces, own_c):
        r, col = piece
        d = direction(own_c)
        # Own at (r-d, col +/- 1) protects this square.
        return ((r - d, col - 1) in own_pieces) or ((r - d, col + 1) in own_pieces)

    def static_eval(my_pieces, op_pieces, side_c):
        # Positive for side_c.
        other_c = 'w' if side_c == 'b' else 'b'
        my_set = set(my_pieces)
        op_set = set(op_pieces)

        term = terminal_score(my_pieces, op_pieces, side_c, side_c)
        if term is not None:
            return term

        score = 0
        score += 120 * (len(my_pieces) - len(op_pieces))

        for p in my_pieces:
            r, col = p
            prog = progress_score(r, side_c)
            score += 18 * prog + 3 * prog * prog
            score += 5 * (3.5 - abs(3.5 - col))
            if is_passed(p, side_c, op_set):
                score += 55 + 12 * prog
            if protected_by(p, my_set, side_c):
                score += 12
            if threatened_by(p, op_set, other_c):
                score -= 18
            if r == goal_row(side_c):
                score += INF // 2

        for p in op_pieces:
            r, col = p
            prog = progress_score(r, other_c)
            score -= 18 * prog + 3 * prog * prog
            score -= 5 * (3.5 - abs(3.5 - col))
            if is_passed(p, other_c, my_set):
                score -= 60 + 14 * prog
            if protected_by(p, op_set, other_c):
                score -= 10
            if threatened_by(p, my_set, side_c):
                score += 14
            if r == goal_row(other_c):
                score -= INF // 2

        # Mobility
        score += 2 * (len(gen_moves_side(my_pieces, op_pieces, side_c)) -
                      len(gen_moves_side(op_pieces, my_pieces, other_c)))
        return int(score)

    def move_order(moves, my_pieces, op_pieces, c):
        g = goal_row(c)
        d = direction(c)
        op_set = set(op_pieces)
        other_c = 'w' if c == 'b' else 'b'

        def key(mv):
            frm, to = mv
            val = 0
            if to[0] == g:
                val += 100000
            if to in op_set:
                val += 5000
            val += progress_score(to[0], c) * 80
            val += int(20 * (3.5 - abs(3.5 - to[1])))
            # Prefer moves that create a one-step promotion threat.
            if to[0] + d == g:
                val += 1500
            # Slightly avoid walking into capture unless protected.
            new_my, new_op = apply_move(tuple(my_pieces), tuple(op_pieces), mv)
            ns = set(new_my)
            os = set(new_op)
            if threatened_by(to, os, other_c) and not protected_by(to, ns, c):
                val -= 700
            return -val

        return sorted(moves, key=key)

    @lru_cache(maxsize=200000)
    def negamax(my_pieces, op_pieces, c, depth, alpha, beta):
        if time.perf_counter() - start_time > TIME_LIMIT:
            return static_eval(my_pieces, op_pieces, c)

        other_c = 'w' if c == 'b' else 'b'
        term = terminal_score(my_pieces, op_pieces, c, color)
        if term is not None:
            return term
        if depth <= 0:
            return static_eval(my_pieces, op_pieces, c)

        moves = gen_moves_side(my_pieces, op_pieces, c)
        if not moves:
            return -INF + 500

        best = -INF
        for mv in move_order(moves, my_pieces, op_pieces, c):
            nm, no = apply_move(my_pieces, op_pieces, mv)
            val = -negamax(no, nm, other_c, depth - 1, -beta, -alpha)
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        return best

    best_move = legal[0]
    best_score = -INF

    # Iterative deepening; small positions can go deeper.
    max_depth = 4
    total_pieces = len(me_t) + len(opp_t)
    if total_pieces <= 18:
        max_depth = 5
    if total_pieces <= 10:
        max_depth = 6

    try:
        for depth in range(1, max_depth + 1):
            if time.perf_counter() - start_time > TIME_LIMIT:
                break
            current_best = best_move
            current_score = -INF
            for mv in move_order(legal, me_t, opp_t, color):
                if time.perf_counter() - start_time > TIME_LIMIT:
                    break
                nm, no = apply_move(me_t, opp_t, mv)
                val = -negamax(no, nm, opp_color, depth - 1, -INF, INF)
                # Tiny deterministic tiebreakers
                val += progress_score(mv[1][0], color)
                if mv[1] in opp_t:
                    val += 3
                if val > current_score:
                    current_score = val
                    current_best = mv
            if current_score > -INF:
                best_move = current_best
                best_score = current_score
    except Exception:
        pass

    # Final legality guard
    if best_move in legal:
        return best_move
    return legal[0]

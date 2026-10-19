
from __future__ import annotations

import time
from typing import List, Tuple

Move = Tuple[Tuple[int, int], Tuple[int, int]]

INF = 10**9


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    start = time.perf_counter()
    time_limit = 0.92  # stay under 1 second with margin

    me_t = tuple(sorted(me))
    opp_t = tuple(sorted(opp))
    legal = generate_moves(me_t, opp_t, color)
    if not legal:
        # Should be rare in valid Breakthrough positions, but always return something legal if possible.
        # If somehow no legal moves exist, return a dummy self-move from an existing piece if any.
        if me_t:
            p = me_t[0]
            return (p, p)
        return ((0, 0), (0, 0))

    fallback = legal[0]

    # Immediate winning move
    for mv in legal:
        me2, opp2 = apply_move(me_t, opp_t, mv)
        if is_win_state(me2, opp2, color):
            return mv

    # If only one legal move, play it.
    if len(legal) == 1:
        return legal[0]

    trans = {}
    best_move = fallback

    # Good root ordering
    ordered = order_moves(me_t, opp_t, color, legal)

    # Iterative deepening
    depth = 1
    while depth <= 5:
        if time.perf_counter() - start > time_limit:
            break
        try:
            val, mv = search_root(me_t, opp_t, color, ordered, depth, start, time_limit, trans)
            if mv is not None:
                best_move = mv
                # Put best move first for next iteration
                ordered = [mv] + [m for m in ordered if m != mv]
            depth += 1
        except TimeoutError:
            break

    return best_move


def opponent_color(color: str) -> str:
    return 'b' if color == 'w' else 'w'


def forward_dir(color: str) -> int:
    return 1 if color == 'w' else -1


def goal_row(color: str) -> int:
    return 7 if color == 'w' else 0


def progress(row: int, color: str) -> int:
    return row if color == 'w' else 7 - row


def is_win_state(me: tuple[tuple[int, int], ...], opp: tuple[tuple[int, int], ...], color: str) -> bool:
    if not opp:
        return True
    g = goal_row(color)
    for r, c in me:
        if r == g:
            return True
    return False


def generate_moves(me: tuple[tuple[int, int], ...], opp: tuple[tuple[int, int], ...], color: str) -> List[Move]:
    occ_me = set(me)
    occ_opp = set(opp)
    moves: List[Move] = []
    d = forward_dir(color)

    for r, c in me:
        nr = r + d
        if not (0 <= nr < 8):
            continue

        # forward
        if (nr, c) not in occ_me and (nr, c) not in occ_opp:
            moves.append(((r, c), (nr, c)))

        # diagonal left
        nc = c - 1
        if 0 <= nc < 8:
            if (nr, nc) not in occ_me:
                if (nr, nc) in occ_opp or ((nr, nc) not in occ_opp):
                    # diagonal move allowed whether empty or capture, as long as not own piece
                    moves.append(((r, c), (nr, nc)))

        # diagonal right
        nc = c + 1
        if 0 <= nc < 8:
            if (nr, nc) not in occ_me:
                if (nr, nc) in occ_opp or ((nr, nc) not in occ_opp):
                    moves.append(((r, c), (nr, nc)))

    return moves


def apply_move(me: tuple[tuple[int, int], ...], opp: tuple[tuple[int, int], ...], mv: Move):
    frm, to = mv
    me_list = list(me)
    idx = me_list.index(frm)
    me_list[idx] = to

    opp_list = list(opp)
    if to in opp_list:
        opp_list.remove(to)

    me2 = tuple(sorted(me_list))
    opp2 = tuple(sorted(opp_list))
    return me2, opp2


def search_root(me, opp, color, moves, depth, start, time_limit, trans):
    alpha = -INF
    beta = INF
    best_val = -INF
    best_move = moves[0] if moves else None

    for mv in moves:
        if time.perf_counter() - start > time_limit:
            raise TimeoutError
        me2, opp2 = apply_move(me, opp, mv)

        if is_win_state(me2, opp2, color):
            return INF - 1, mv

        val = -negamax(
            opp2, me2, opponent_color(color),
            depth - 1, -beta, -alpha,
            start, time_limit, trans
        )

        if val > best_val:
            best_val = val
            best_move = mv
        if val > alpha:
            alpha = val

    return best_val, best_move


def negamax(me, opp, color, depth, alpha, beta, start, time_limit, trans):
    if time.perf_counter() - start > time_limit:
        raise TimeoutError

    key = (me, opp, color, depth)
    if key in trans:
        return trans[key]

    # Terminal checks from current player's perspective
    if is_win_state(me, opp, color):
        return INF - (5 - depth)
    if is_win_state(opp, me, opponent_color(color)):
        return -INF + (5 - depth)

    moves = generate_moves(me, opp, color)
    if not moves:
        # No move => losing practical terminal
        return -INF + (5 - depth)

    if depth == 0:
        val = evaluate(me, opp, color, moves)
        trans[key] = val
        return val

    ordered = order_moves(me, opp, color, moves)

    best = -INF
    for mv in ordered:
        me2, opp2 = apply_move(me, opp, mv)

        if is_win_state(me2, opp2, color):
            val = INF - (5 - depth)
        else:
            val = -negamax(
                opp2, me2, opponent_color(color),
                depth - 1, -beta, -alpha,
                start, time_limit, trans
            )

        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    trans[key] = best
    return best


def order_moves(me, opp, color, moves):
    opp_set = set(opp)
    g = goal_row(color)

    def score(mv):
        (r1, c1), (r2, c2) = mv
        s = 0
        # Immediate win
        if r2 == g:
            s += 100000
        # Capture
        if (r2, c2) in opp_set:
            s += 20000
        # Advance
        s += 300 * progress(r2, color)
        # Central columns slightly preferred
        s += 20 * (3 - abs(3.5 - c2))
        # Diagonal move slightly preferred for flexibility
        if c1 != c2:
            s += 5
        return s

    return sorted(moves, key=score, reverse=True)


def evaluate(me, opp, color, my_moves=None):
    # Perspective: current player "me"
    if is_win_state(me, opp, color):
        return INF // 2
    if is_win_state(opp, me, opponent_color(color)):
        return -INF // 2

    me_set = set(me)
    opp_set = set(opp)
    ocolor = opponent_color(color)

    if my_moves is None:
        my_moves = generate_moves(me, opp, color)
    opp_moves = generate_moves(opp, me, ocolor)

    score = 0

    # Material
    score += 220 * (len(me) - len(opp))

    # Mobility
    score += 8 * (len(my_moves) - len(opp_moves))

    # Advancement and promotion race
    my_max_prog = 0
    opp_max_prog = 0

    for r, c in me:
        p = progress(r, color)
        my_max_prog = max(my_max_prog, p)
        score += 35 * p
        # Central control
        score += 8 * (3 - abs(3.5 - c))
        # Near promotion gets extra weight
        if p >= 5:
            score += 25 * (p - 4)
        # Protected by rear diagonal friendly piece
        bd = -forward_dir(color)
        rr = r + bd
        protected = False
        if 0 <= rr < 8:
            if c - 1 >= 0 and (rr, c - 1) in me_set:
                protected = True
            if c + 1 < 8 and (rr, c + 1) in me_set:
                protected = True
        if protected:
            score += 12
        # Vulnerable to immediate capture
        if is_piece_hanging((r, c), me_set, opp_set, color):
            score -= 22
        # Passed-runner style bonus: few enemy blockers ahead in adjacent lanes
        score += 10 * clear_lane_bonus((r, c), opp_set, color)

    for r, c in opp:
        p = progress(r, ocolor)
        opp_max_prog = max(opp_max_prog, p)
        score -= 35 * p
        score -= 8 * (3 - abs(3.5 - c))
        if p >= 5:
            score -= 25 * (p - 4)
        bd = -forward_dir(ocolor)
        rr = r + bd
        protected = False
        if 0 <= rr < 8:
            if c - 1 >= 0 and (rr, c - 1) in opp_set:
                protected = True
            if c + 1 < 8 and (rr, c + 1) in opp_set:
                protected = True
        if protected:
            score -= 12
        if is_piece_hanging((r, c), opp_set, me_set, ocolor):
            score += 22
        score -= 10 * clear_lane_bonus((r, c), me_set, ocolor)

    # Race urgency
    score += 60 * (my_max_prog - opp_max_prog)

    # Threats: can we capture next / can they capture next
    my_caps = count_captures(me, opp, color)
    opp_caps = count_captures(opp, me, ocolor)
    score += 18 * (my_caps - opp_caps)

    # Strong tactical concern: imminent promotions
    my_dist = 7 - my_max_prog
    opp_dist = 7 - opp_max_prog
    score += 45 * (opp_dist - my_dist)

    return int(score)


def count_captures(me, opp, color):
    opp_set = set(opp)
    d = forward_dir(color)
    total = 0
    for r, c in me:
        nr = r + d
        if 0 <= nr < 8:
            if c - 1 >= 0 and (nr, c - 1) in opp_set:
                total += 1
            if c + 1 < 8 and (nr, c + 1) in opp_set:
                total += 1
    return total


def is_piece_hanging(piece, own_set, enemy_set, own_color):
    # Can enemy capture this piece immediately?
    r, c = piece
    ecolor = opponent_color(own_color)
    ed = forward_dir(ecolor)
    # Enemy from one row behind relative to their motion:
    # enemy moves from er to r where er + ed = r => er = r - ed
    er = r - ed
    if not (0 <= er < 8):
        return False
    # Enemy can capture diagonally onto (r,c) from (er, c-1) or (er, c+1)
    if c - 1 >= 0 and (er, c - 1) in enemy_set:
        return True
    if c + 1 < 8 and (er, c + 1) in enemy_set:
        return True
    return False


def clear_lane_bonus(piece, enemy_set, color):
    # Bonus for having fewer enemy pieces ahead in same/adjacent files
    r, c = piece
    d = forward_dir(color)
    bonus = 0
    rr = r + d
    steps = 0
    blockers = 0
    while 0 <= rr < 8:
        steps += 1
        for cc in (c - 1, c, c + 1):
            if 0 <= cc < 8 and (rr, cc) in enemy_set:
                blockers += 1
        rr += d
    # More open lane => larger bonus
    bonus = max(0, 6 - blockers) + steps // 2
    return bonus

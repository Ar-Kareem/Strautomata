
from time import perf_counter
from typing import List, Tuple, Optional

Move = Tuple[Tuple[int, int], Tuple[int, int], Optional[Tuple[int, int]]]
State = Tuple[frozenset, frozenset, frozenset, frozenset]

INF = 10**9
MATE = 10**6


def _opp(side: str) -> str:
    return 'w' if side == 'b' else 'b'


def _in_bounds(r: int, c: int) -> bool:
    return 0 <= r < 8 and 0 <= c < 8


def _man_dirs(side: str):
    return ((-1, -1), (-1, 1)) if side == 'b' else ((1, -1), (1, 1))


def _king_dirs():
    return ((-1, -1), (-1, 1), (1, -1), (1, 1))


def _generate_moves(state: State, side: str) -> List[Move]:
    b_men, b_kings, w_men, w_kings = state

    if side == 'b':
        my_men, my_kings = b_men, b_kings
        opp_men, opp_kings = w_men, w_kings
    else:
        my_men, my_kings = w_men, w_kings
        opp_men, opp_kings = b_men, b_kings

    occupied = b_men | b_kings | w_men | w_kings
    opp_all = opp_men | opp_kings

    captures: List[Move] = []
    quiets: List[Move] = []

    md = _man_dirs(side)
    kd = _king_dirs()

    for r, c in my_men:
        for dr, dc in md:
            r1, c1 = r + dr, c + dc
            r2, c2 = r + 2 * dr, c + 2 * dc
            if _in_bounds(r2, c2) and (r1, c1) in opp_all and (r2, c2) not in occupied:
                captures.append(((r, c), (r2, c2), (r1, c1)))

    for r, c in my_kings:
        for dr, dc in kd:
            r1, c1 = r + dr, c + dc
            r2, c2 = r + 2 * dr, c + 2 * dc
            if _in_bounds(r2, c2) and (r1, c1) in opp_all and (r2, c2) not in occupied:
                captures.append(((r, c), (r2, c2), (r1, c1)))

    if captures:
        return captures

    for r, c in my_men:
        for dr, dc in md:
            r1, c1 = r + dr, c + dc
            if _in_bounds(r1, c1) and (r1, c1) not in occupied:
                quiets.append(((r, c), (r1, c1), None))

    for r, c in my_kings:
        for dr, dc in kd:
            r1, c1 = r + dr, c + dc
            if _in_bounds(r1, c1) and (r1, c1) not in occupied:
                quiets.append(((r, c), (r1, c1), None))

    return quiets


def _apply_move(state: State, side: str, move: Move) -> State:
    b_men, b_kings, w_men, w_kings = state
    fr, to, cap = move

    b_men = set(b_men)
    b_kings = set(b_kings)
    w_men = set(w_men)
    w_kings = set(w_kings)

    if side == 'b':
        if fr in b_men:
            b_men.remove(fr)
            is_king = False
        else:
            b_kings.remove(fr)
            is_king = True

        if cap is not None:
            if cap in w_men:
                w_men.remove(cap)
            else:
                w_kings.remove(cap)

        if is_king or to[0] != 0:
            if is_king:
                b_kings.add(to)
            else:
                b_men.add(to)
        else:
            b_kings.add(to)

    else:
        if fr in w_men:
            w_men.remove(fr)
            is_king = False
        else:
            w_kings.remove(fr)
            is_king = True

        if cap is not None:
            if cap in b_men:
                b_men.remove(cap)
            else:
                b_kings.remove(cap)

        if is_king or to[0] != 7:
            if is_king:
                w_kings.add(to)
            else:
                w_men.add(to)
        else:
            w_kings.add(to)

    return (frozenset(b_men), frozenset(b_kings), frozenset(w_men), frozenset(w_kings))


def _score_side(men: frozenset, kings: frozenset, color: str, total_pieces: int) -> int:
    score = 0
    king_value = 190 + (10 if total_pieces <= 10 else 0)
    home_row = 7 if color == 'b' else 0

    for r, c in men:
        score += 100

        progress = 7 - r if color == 'b' else r
        score += 7 * progress

        if 2 <= r <= 5 and 2 <= c <= 5:
            score += 4
        if 3 <= r <= 4 and 3 <= c <= 4:
            score += 2
        if c == 0 or c == 7:
            score -= 2

        if r == home_row and total_pieces > 8:
            score += 8

        if (color == 'b' and r == 1) or (color == 'w' and r == 6):
            score += 18

    for r, c in kings:
        score += king_value
        if 2 <= r <= 5 and 2 <= c <= 5:
            score += 6
        if 3 <= r <= 4 and 3 <= c <= 4:
            score += 3
        if c == 0 or c == 7:
            score -= 1

    own = men | kings
    for r, c in own:
        if (r + 1, c - 1) in own:
            score += 2
        if (r + 1, c + 1) in own:
            score += 2

    return score


def _evaluate(state: State, side: str) -> int:
    b_men, b_kings, w_men, w_kings = state
    total = len(b_men) + len(b_kings) + len(w_men) + len(w_kings)

    black_score = _score_side(b_men, b_kings, 'b', total)
    white_score = _score_side(w_men, w_kings, 'w', total)

    val = black_score - white_score

    if total <= 12:
        val += 3 * (len(_generate_moves(state, 'b')) - len(_generate_moves(state, 'w')))

    return val if side == 'b' else -val


def _move_order_score(state: State, side: str, move: Move) -> int:
    fr, to, cap = move
    score = 0

    if side == 'b':
        my_men, my_kings = state[0], state[1]
        opp_kings = state[3]
    else:
        my_men, my_kings = state[2], state[3]
        opp_kings = state[1]

    if cap is not None:
        score += 1000
        score += 160 if cap in opp_kings else 110
        if fr in my_men:
            if (side == 'b' and to[0] == 0) or (side == 'w' and to[0] == 7):
                score += 140
    else:
        if fr in my_men:
            if (side == 'b' and to[0] == 0) or (side == 'w' and to[0] == 7):
                score += 220
            score += 10 * (fr[0] - to[0] if side == 'b' else to[0] - fr[0])

    if 2 <= to[0] <= 5 and 2 <= to[1] <= 5:
        score += 10
    if 3 <= to[0] <= 4 and 3 <= to[1] <= 4:
        score += 5

    if fr in my_kings and cap is None:
        score += 2

    return score


def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    if color == 'b':
        state: State = (
            frozenset(my_men),
            frozenset(my_kings),
            frozenset(opp_men),
            frozenset(opp_kings),
        )
    else:
        state = (
            frozenset(opp_men),
            frozenset(opp_kings),
            frozenset(my_men),
            frozenset(my_kings),
        )

    root_moves = _generate_moves(state, color)
    if not root_moves:
        pieces = list(my_men) + list(my_kings)
        if pieces:
            p = pieces[0]
            return (p, p)
        return ((0, 0), (0, 0))

    best_move = max(root_moves, key=lambda m: _move_order_score(state, color, m))

    total_pieces = len(state[0]) + len(state[1]) + len(state[2]) + len(state[3])
    if total_pieces <= 6:
        max_depth = 10
    elif total_pieces <= 10:
        max_depth = 9
    elif total_pieces <= 14:
        max_depth = 8
    elif total_pieces <= 20:
        max_depth = 7
    else:
        max_depth = 6

    deadline = perf_counter() + 0.92
    node_counter = [0]
    pv_move = {}

    def check_time():
        node_counter[0] += 1
        if (node_counter[0] & 1023) == 0 and perf_counter() > deadline:
            raise TimeoutError

    def ordered_moves(s: State, side: str, moves: List[Move]) -> List[Move]:
        hint = pv_move.get((s, side))
        if hint in moves:
            return [hint] + sorted((m for m in moves if m != hint),
                                   key=lambda m: _move_order_score(s, side, m),
                                   reverse=True)
        return sorted(moves, key=lambda m: _move_order_score(s, side, m), reverse=True)

    def negamax(s: State, side: str, depth: int, alpha: int, beta: int, ply: int) -> int:
        check_time()

        moves = _generate_moves(s, side)
        if not moves:
            return -MATE + ply

        if depth == 0 and moves[0][2] is None:
            return _evaluate(s, side)

        if depth == 0:
            depth = 1

        best_val = -INF
        best_local = None

        for mv in ordered_moves(s, side, moves):
            child = _apply_move(s, side, mv)
            val = -negamax(child, _opp(side), depth - 1, -beta, -alpha, ply + 1)
            if val > best_val:
                best_val = val
                best_local = mv
            if best_val > alpha:
                alpha = best_val
            if alpha >= beta:
                break

        if best_local is not None:
            pv_move[(s, side)] = best_local

        return best_val

    def search_root(depth: int, current_best: Move) -> Move:
        moves = ordered_moves(state, color, root_moves)
        if current_best in moves:
            moves = [current_best] + [m for m in moves if m != current_best]

        alpha = -INF
        beta = INF
        local_best = current_best
        local_best_val = -INF

        for mv in moves:
            check_time()
            child = _apply_move(state, color, mv)
            val = -negamax(child, _opp(color), depth - 1, -beta, -alpha, 1)
            if val > local_best_val:
                local_best_val = val
                local_best = mv
            if val > alpha:
                alpha = val

        pv_move[(state, color)] = local_best
        return local_best

    for depth in range(1, max_depth + 1):
        try:
            best_move = search_root(depth, best_move)
        except TimeoutError:
            break

    return best_move[0], best_move[1]

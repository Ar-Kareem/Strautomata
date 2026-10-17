
from __future__ import annotations

from functools import lru_cache

WIN_SCORE = 10**9
INF = 10**12


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    me_t = tuple(sorted(me))
    opp_t = tuple(sorted(opp))

    moves = generate_moves(me_t, opp_t, color)
    if not moves:
        # Should not normally happen in Breakthrough, but return a legal-format fallback.
        # If somehow no move exists, just return a dummy self-move on one of our pieces.
        p = me[0]
        return (p, p)

    # 1) Immediate win
    for mv in moves:
        nme, nopp = apply_move(me_t, opp_t, mv)
        if is_win_for(nme, nopp, color):
            return mv

    # 2) Immediate tactical filter:
    # Prefer moves that do not allow an immediate opponent win, if such moves exist.
    safe_moves = []
    opp_color = other(color)
    for mv in moves:
        nme, nopp = apply_move(me_t, opp_t, mv)
        opp_moves = generate_moves(nopp, nme, opp_color)
        losing = False
        for omv in opp_moves:
            nnopp, nnme = apply_move(nopp, nme, omv)
            if is_win_for(nnopp, nnme, opp_color):
                losing = True
                break
        if not losing:
            safe_moves.append(mv)

    candidate_moves = safe_moves if safe_moves else moves

    # 3) Adaptive depth
    total_pieces = len(me_t) + len(opp_t)
    if total_pieces <= 8:
        depth = 5
    elif total_pieces <= 14:
        depth = 4
    else:
        depth = 3

    best_move = candidate_moves[0]
    best_val = -INF
    alpha = -INF
    beta = INF

    ordered = sorted(candidate_moves, key=lambda mv: move_order_score(me_t, opp_t, color, mv), reverse=True)

    for mv in ordered:
        nme, nopp = apply_move(me_t, opp_t, mv)
        val = -negamax(nopp, nme, opp_color, depth - 1, -beta, -alpha)
        if val > best_val:
            best_val = val
            best_move = mv
        if val > alpha:
            alpha = val

    return best_move


def other(color: str) -> str:
    return 'b' if color == 'w' else 'w'


def direction(color: str) -> int:
    return 1 if color == 'w' else -1


def goal_row(color: str) -> int:
    return 7 if color == 'w' else 0


def progress_of_piece(r: int, color: str) -> int:
    return r if color == 'w' else (7 - r)


def is_win_for(me: tuple[tuple[int, int], ...], opp: tuple[tuple[int, int], ...], color: str) -> bool:
    if not opp:
        return True
    g = goal_row(color)
    for r, _ in me:
        if r == g:
            return True
    return False


def generate_moves(
    me: tuple[tuple[int, int], ...],
    opp: tuple[tuple[int, int], ...],
    color: str
) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    occ_me = set(me)
    occ_opp = set(opp)
    occ = occ_me | occ_opp
    d = direction(color)

    moves = []
    for r, c in me:
        nr = r + d
        if not (0 <= nr < 8):
            continue

        # Straight forward: only if empty
        if (nr, c) not in occ:
            moves.append(((r, c), (nr, c)))

        # Diagonal forward left/right: allowed if empty or occupied by opponent, but not own piece
        nc = c - 1
        if 0 <= nc < 8 and (nr, nc) not in occ_me:
            moves.append(((r, c), (nr, nc)))

        nc = c + 1
        if 0 <= nc < 8 and (nr, nc) not in occ_me:
            moves.append(((r, c), (nr, nc)))

    return moves


def apply_move(
    me: tuple[tuple[int, int], ...],
    opp: tuple[tuple[int, int], ...],
    mv: tuple[tuple[int, int], tuple[int, int]]
) -> tuple[tuple[tuple[int, int], ...], tuple[tuple[int, int], ...]]:
    frm, to = mv
    me_list = list(me)
    idx = me_list.index(frm)
    me_list[idx] = to
    opp_set = set(opp)
    if to in opp_set:
        opp_set.remove(to)
    return tuple(sorted(me_list)), tuple(sorted(opp_set))


def move_order_score(
    me: tuple[tuple[int, int], ...],
    opp: tuple[tuple[int, int], ...],
    color: str,
    mv: tuple[tuple[int, int], tuple[int, int]]
) -> int:
    frm, to = mv
    score = 0
    if to in set(opp):
        score += 5000

    # Promotion
    if to[0] == goal_row(color):
        score += 1000000

    # Advance
    score += 30 * (progress_of_piece(to[0], color) - progress_of_piece(frm[0], color))

    # Center
    score -= abs(to[1] - 3.5) * 4

    # Safer supported squares are preferred
    if is_supported(to, me, color):
        score += 40
    if is_attackable_by_opp(to, opp, color):
        score -= 60

    return int(score)


def is_supported(pos: tuple[int, int], me: tuple[tuple[int, int], ...], color: str) -> bool:
    r, c = pos
    back = r - direction(color)
    if not (0 <= back < 8):
        return False
    me_set = set(me)
    return ((back, c - 1) in me_set) or ((back, c + 1) in me_set)


def is_attackable_by_opp(pos: tuple[int, int], opp: tuple[tuple[int, int], ...], my_color: str) -> bool:
    # Can opponent capture onto pos next move?
    # Opponent color moves in opposite direction.
    opp_color = other(my_color)
    d = direction(opp_color)
    r, c = pos
    src_r = r - d
    if not (0 <= src_r < 8):
        return False
    opp_set = set(opp)
    return ((src_r, c - 1) in opp_set) or ((src_r, c + 1) in opp_set)


@lru_cache(maxsize=200000)
def negamax(
    me: tuple[tuple[int, int], ...],
    opp: tuple[tuple[int, int], ...],
    color: str,
    depth: int,
    alpha: int,
    beta: int
) -> int:
    # Terminal
    if is_win_for(me, opp, color):
        return WIN_SCORE
    if is_win_for(opp, me, other(color)):
        return -WIN_SCORE

    if depth == 0:
        return evaluate(me, opp, color)

    moves = generate_moves(me, opp, color)
    if not moves:
        # Extremely unlikely in Breakthrough, but treat as losing.
        return -WIN_SCORE + 1

    # Strong tactical shortcut: if any immediate winning move exists
    for mv in moves:
        nme, nopp = apply_move(me, opp, mv)
        if is_win_for(nme, nopp, color):
            return WIN_SCORE - 1

    ordered = sorted(moves, key=lambda mv: move_order_score(me, opp, color, mv), reverse=True)

    best = -INF
    opp_color = other(color)
    for mv in ordered:
        nme, nopp = apply_move(me, opp, mv)
        val = -negamax(nopp, nme, opp_color, depth - 1, -beta, -alpha)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best


def evaluate(
    me: tuple[tuple[int, int], ...],
    opp: tuple[tuple[int, int], ...],
    color: str
) -> int:
    # Terminal first
    if is_win_for(me, opp, color):
        return WIN_SCORE
    if is_win_for(opp, me, other(color)):
        return -WIN_SCORE

    me_set = set(me)
    opp_set = set(opp)

    score = 0

    # Material
    score += 220 * (len(me) - len(opp))

    # Mobility
    my_moves = len(generate_moves(me, opp, color))
    opp_moves = len(generate_moves(opp, me, other(color)))
    score += 8 * (my_moves - opp_moves)

    # Piece features
    for r, c in me:
        prog = progress_of_piece(r, color)
        dist = 7 - prog
        score += 32 * prog
        score -= 3 * abs(c - 3.5)

        # Near-promotion threats
        if dist == 1:
            score += 180
        elif dist == 2:
            score += 70

        # Supported / vulnerable
        if is_supported((r, c), me, color):
            score += 20
        if is_attackable_by_opp((r, c), opp, color):
            score -= 26

        # Passed-ish bonus: no opponent directly in front lanes ahead
        if is_clear_lane((r, c), opp_set, color):
            score += 24 + 8 * prog

    for r, c in opp:
        prog = progress_of_piece(r, other(color))
        dist = 7 - prog
        score -= 32 * prog
        score += 3 * abs(c - 3.5)

        if dist == 1:
            score -= 180
        elif dist == 2:
            score -= 70

        if is_supported((r, c), opp, other(color)):
            score -= 20
        if is_attackable_by_opp((r, c), me, other(color)):
            score += 26

        if is_clear_lane((r, c), me_set, other(color)):
            score -= 24 + 8 * prog

    # Frontmost piece bonus
    if me:
        score += 18 * max(progress_of_piece(r, color) for r, _ in me)
    if opp:
        score -= 18 * max(progress_of_piece(r, other(color)) for r, _ in opp)

    return int(score)


def is_clear_lane(pos: tuple[int, int], enemy_set: set[tuple[int, int]], color: str) -> bool:
    # Heuristic "passed pawn" style check on same and adjacent files ahead.
    r, c = pos
    d = direction(color)
    rr = r + d
    while 0 <= rr < 8:
        for cc in (c - 1, c, c + 1):
            if 0 <= cc < 8 and (rr, cc) in enemy_set:
                return False
        rr += d
    return True

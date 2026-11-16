
import time
from typing import List, Tuple

ROWS = 5
COLS = 6
DIRS = [(-1, 0, 'U'), (0, 1, 'R'), (1, 0, 'D'), (0, -1, 'L')]

def _to_bitboards(you: List[List[int]], opponent: List[List[int]]) -> Tuple[int, int]:
    y = 0
    o = 0
    bit = 1
    for r in range(ROWS):
        rowy = you[r]
        rowo = opponent[r]
        for c in range(COLS):
            if rowy[c]:
                y |= bit
            elif rowo[c]:
                o |= bit
            bit <<= 1
    return y, o

def _rc_to_idx(r: int, c: int) -> int:
    return r * COLS + c

def _idx_to_rc(i: int) -> Tuple[int, int]:
    return divmod(i, COLS)

def _move_to_str(src: int, dst: int) -> str:
    r, c = _idx_to_rc(src)
    dr = dst - src
    if dr == -COLS:
        d = 'U'
    elif dr == COLS:
        d = 'D'
    elif dr == 1:
        d = 'R'
    else:
        d = 'L'
    return f"{r},{c},{d}"

def _generate_moves(me: int, opp: int) -> List[Tuple[int, int]]:
    moves = []
    occupied_by_opp = opp
    for i in range(ROWS * COLS):
        if (me >> i) & 1:
            r, c = _idx_to_rc(i)
            if r > 0:
                j = i - COLS
                if (occupied_by_opp >> j) & 1:
                    moves.append((i, j))
            if c + 1 < COLS:
                j = i + 1
                if (occupied_by_opp >> j) & 1:
                    moves.append((i, j))
            if r + 1 < ROWS:
                j = i + COLS
                if (occupied_by_opp >> j) & 1:
                    moves.append((i, j))
            if c > 0:
                j = i - 1
                if (occupied_by_opp >> j) & 1:
                    moves.append((i, j))
    return moves

def _apply_move(me: int, opp: int, move: Tuple[int, int]) -> Tuple[int, int]:
    src, dst = move
    me2 = me & ~(1 << src)
    me2 |= (1 << dst)
    opp2 = opp & ~(1 << dst)
    return opp2, me2  # swap side to move

def _adjacent_enemy_count(pos: int, opp: int) -> int:
    r, c = _idx_to_rc(pos)
    cnt = 0
    if r > 0 and ((opp >> (pos - COLS)) & 1):
        cnt += 1
    if c + 1 < COLS and ((opp >> (pos + 1)) & 1):
        cnt += 1
    if r + 1 < ROWS and ((opp >> (pos + COLS)) & 1):
        cnt += 1
    if c > 0 and ((opp >> (pos - 1)) & 1):
        cnt += 1
    return cnt

def _adjacent_friend_count(pos: int, me: int) -> int:
    r, c = _idx_to_rc(pos)
    cnt = 0
    if r > 0 and ((me >> (pos - COLS)) & 1):
        cnt += 1
    if c + 1 < COLS and ((me >> (pos + 1)) & 1):
        cnt += 1
    if r + 1 < ROWS and ((me >> (pos + COLS)) & 1):
        cnt += 1
    if c > 0 and ((me >> (pos - 1)) & 1):
        cnt += 1
    return cnt

def _evaluate(me: int, opp: int) -> int:
    my_moves = _generate_moves(me, opp)
    if not my_moves:
        return -100000
    opp_moves = _generate_moves(opp, me)
    if not opp_moves:
        return 100000

    my_piece_count = me.bit_count()
    opp_piece_count = opp.bit_count()

    score = 0
    score += 120 * (len(my_moves) - len(opp_moves))
    score += 18 * (my_piece_count - opp_piece_count)

    my_pressure = 0
    my_support = 0
    for i in range(ROWS * COLS):
        if (me >> i) & 1:
            my_pressure += _adjacent_enemy_count(i, opp)
            my_support += _adjacent_friend_count(i, me)

    opp_pressure = 0
    opp_support = 0
    for i in range(ROWS * COLS):
        if (opp >> i) & 1:
            opp_pressure += _adjacent_enemy_count(i, me)
            opp_support += _adjacent_friend_count(i, opp)

    score += 14 * (my_pressure - opp_pressure)
    score += 4 * (my_support - opp_support)

    center_bonus = 0
    for i in range(ROWS * COLS):
        if ((me >> i) & 1) or ((opp >> i) & 1):
            r, c = _idx_to_rc(i)
            centrality = 4 - abs(r - 2) - abs(c - 2.5)
            if (me >> i) & 1:
                center_bonus += centrality
            else:
                center_bonus -= centrality
    score += int(3 * center_bonus)

    return score

def _ordered_moves(me: int, opp: int) -> List[Tuple[int, int]]:
    moves = _generate_moves(me, opp)
    scored = []
    for mv in moves:
        src, dst = mv
        new_me = (me & ~(1 << src)) | (1 << dst)
        new_opp = opp & ~(1 << dst)

        immediate_win = 1 if not _generate_moves(new_opp, new_me) else 0
        dst_enemy_adj = _adjacent_enemy_count(dst, new_opp)
        dst_friend_adj = _adjacent_friend_count(dst, new_me)
        src_enemy_adj = _adjacent_enemy_count(src, opp)
        delta_contact = dst_enemy_adj - src_enemy_adj
        centrality = 4 - abs((dst // COLS) - 2) - abs((dst % COLS) - 2.5)

        s = (
            100000 * immediate_win +
            200 * delta_contact +
            40 * dst_friend_adj +
            int(10 * centrality)
        )
        scored.append((s, mv))
    scored.sort(reverse=True)
    return [mv for _, mv in scored]

def _alphabeta(me: int, opp: int, depth: int, alpha: int, beta: int, end_time: float) -> int:
    if time.perf_counter() >= end_time:
        raise TimeoutError

    moves = _ordered_moves(me, opp)
    if not moves:
        return -100000 + (10 - depth)

    if depth == 0:
        return _evaluate(me, opp)

    best = -10**9
    for mv in moves:
        nme, nopp = _apply_move(me, opp, mv)
        val = -_alphabeta(nme, nopp, depth - 1, -beta, -alpha, end_time)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best

def _best_move(me: int, opp: int, time_limit: float = 0.95) -> Tuple[int, int]:
    start = time.perf_counter()
    end_time = start + time_limit

    legal = _ordered_moves(me, opp)
    if not legal:
        return (0, 0)

    for mv in legal:
        nme, nopp = _apply_move(me, opp, mv)
        if not _generate_moves(nme, nopp):
            return mv

    best_move = legal[0]
    best_score = -10**9
    depth = 1

    while True:
        if time.perf_counter() >= end_time:
            break
        current_best_move = best_move
        current_best_score = -10**9
        alpha = -10**9
        beta = 10**9
        try:
            ordered = _ordered_moves(me, opp)
            for mv in ordered:
                nme, nopp = _apply_move(me, opp, mv)
                val = -_alphabeta(nme, nopp, depth - 1, -beta, -alpha, end_time)
                if val > current_best_score:
                    current_best_score = val
                    current_best_move = mv
                if val > alpha:
                    alpha = val
        except TimeoutError:
            break

        best_move = current_best_move
        best_score = current_best_score
        depth += 1
        if abs(best_score) >= 99990:
            break

    return best_move

def policy(you: List[List[int]], opponent: List[List[int]]) -> str:
    me, opp = _to_bitboards(you, opponent)
    legal = _generate_moves(me, opp)
    if not legal:
        # Should not happen in valid arena states, but return a syntactically valid string.
        return "0,0,R"

    mv = _best_move(me, opp, 0.95)
    if mv not in legal:
        mv = legal[0]
    return _move_to_str(mv[0], mv[1])

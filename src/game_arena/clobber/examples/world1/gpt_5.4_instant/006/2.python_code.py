
from typing import List, Tuple, Dict

ROWS = 5
COLS = 6
DIRS = [(-1, 0, 'U'), (0, 1, 'R'), (1, 0, 'D'), (0, -1, 'L')]

# Transposition table
TT: Dict[Tuple[int, int, int, int], Tuple[int, int]] = {}

WIN_SCORE = 10**8


def _bit(r: int, c: int) -> int:
    return 1 << (r * COLS + c)


def _to_bits(arr) -> int:
    bits = 0
    # Works for list-of-lists or numpy arrays
    for r in range(ROWS):
        row = arr[r]
        for c in range(COLS):
            if row[c]:
                bits |= _bit(r, c)
    return bits


def _moves(me: int, opp: int) -> List[Tuple[int, int, str]]:
    res = []
    occupied_opp = opp
    for r in range(ROWS):
        base = r * COLS
        for c in range(COLS):
            pos = 1 << (base + c)
            if me & pos:
                if r > 0 and (occupied_opp & _bit(r - 1, c)):
                    res.append((r, c, 'U'))
                if c + 1 < COLS and (occupied_opp & _bit(r, c + 1)):
                    res.append((r, c, 'R'))
                if r + 1 < ROWS and (occupied_opp & _bit(r + 1, c)):
                    res.append((r, c, 'D'))
                if c > 0 and (occupied_opp & _bit(r, c - 1)):
                    res.append((r, c, 'L'))
    return res


def _apply(me: int, opp: int, move: Tuple[int, int, str]) -> Tuple[int, int]:
    r, c, d = move
    src = _bit(r, c)
    if d == 'U':
        nr, nc = r - 1, c
    elif d == 'R':
        nr, nc = r, c + 1
    elif d == 'D':
        nr, nc = r + 1, c
    else:
        nr, nc = r, c - 1
    dst = _bit(nr, nc)
    me2 = (me ^ src) | dst
    opp2 = opp ^ dst
    return opp2, me2  # side to move swaps


def _popcount(x: int) -> int:
    return x.bit_count()


def _adj_enemy_count(me: int, opp: int, r: int, c: int) -> int:
    cnt = 0
    if r > 0 and (opp & _bit(r - 1, c)):
        cnt += 1
    if c + 1 < COLS and (opp & _bit(r, c + 1)):
        cnt += 1
    if r + 1 < ROWS and (opp & _bit(r + 1, c)):
        cnt += 1
    if c > 0 and (opp & _bit(r, c - 1)):
        cnt += 1
    return cnt


def _adj_friend_count(me: int, r: int, c: int) -> int:
    cnt = 0
    if r > 0 and (me & _bit(r - 1, c)):
        cnt += 1
    if c + 1 < COLS and (me & _bit(r, c + 1)):
        cnt += 1
    if r + 1 < ROWS and (me & _bit(r + 1, c)):
        cnt += 1
    if c > 0 and (me & _bit(r, c - 1)):
        cnt += 1
    return cnt


def _evaluate(me: int, opp: int) -> int:
    my_moves = _moves(me, opp)
    if not my_moves:
        return -WIN_SCORE
    opp_moves = _moves(opp, me)
    if not opp_moves:
        return WIN_SCORE

    score = 0

    # Mobility is very important in Clobber
    score += 120 * (len(my_moves) - len(opp_moves))

    # Piece count matters less than mobility, but still useful
    score += 18 * (_popcount(me) - _popcount(opp))

    # Structural features
    my_safe = my_hot = my_supported = 0
    opp_safe = opp_hot = opp_supported = 0

    for r in range(ROWS):
        for c in range(COLS):
            b = _bit(r, c)
            if me & b:
                e = _adj_enemy_count(me, opp, r, c)
                f = _adj_friend_count(me, r, c)
                if e == 0:
                    my_safe += 1
                my_hot += e
                my_supported += f
            elif opp & b:
                e = _adj_enemy_count(opp, me, r, c)
                f = _adj_friend_count(opp, r, c)
                if e == 0:
                    opp_safe += 1
                opp_hot += e
                opp_supported += f

    # Safe pieces can become dead weight if side to move loses mobility,
    # but generally reducing opponent mobility is favorable.
    score += 14 * (my_safe - opp_safe)
    score += 10 * (my_hot - opp_hot)
    score += 4 * (my_supported - opp_supported)

    # Mild centrality preference
    centers = [
        [2, 3, 4, 4, 3, 2],
        [3, 4, 5, 5, 4, 3],
        [4, 5, 6, 6, 5, 4],
        [3, 4, 5, 5, 4, 3],
        [2, 3, 4, 4, 3, 2],
    ]
    cent = 0
    for r in range(ROWS):
        for c in range(COLS):
            b = _bit(r, c)
            if me & b:
                cent += centers[r][c]
            elif opp & b:
                cent -= centers[r][c]
    score += cent

    return score


def _ordered_moves(me: int, opp: int) -> List[Tuple[int, int, str]]:
    moves = _moves(me, opp)
    scored = []

    current_my_mob = len(moves)
    current_opp_mob = len(_moves(opp, me))

    for mv in moves:
        nme, nopp = _apply(me, opp, mv)  # returns swapped: opponent-to-move position
        # In new orientation, nme is opponent, nopp is us.
        opp_reply_count = len(_moves(nme, nopp))
        our_next_count = len(_moves(nopp, nme))

        r, c, d = mv
        if d == 'U':
            nr, nc = r - 1, c
        elif d == 'R':
            nr, nc = r, c + 1
        elif d == 'D':
            nr, nc = r + 1, c
        else:
            nr, nc = r, c - 1

        # Tactical priorities:
        # - immediate win first
        # - minimize opponent replies
        # - keep our future mobility
        # - move onto squares with options / support
        loc_pressure = _adj_enemy_count(nopp, nme, nr, nc)
        support = _adj_friend_count(nopp, nr, nc)

        s = 0
        if opp_reply_count == 0:
            s += 10**7
        s += 500 * (current_opp_mob - opp_reply_count)
        s += 180 * (our_next_count - current_my_mob)
        s += 35 * loc_pressure
        s += 10 * support

        scored.append((s, mv))

    scored.sort(reverse=True)
    return [mv for _, mv in scored]


def _alphabeta(me: int, opp: int, depth: int, alpha: int, beta: int) -> int:
    key = (me, opp, depth, 1)
    tt = TT.get(key)
    if tt is not None:
        stored_depth, stored_val = tt
        if stored_depth >= depth:
            return stored_val

    legal = _ordered_moves(me, opp)
    if not legal:
        return -WIN_SCORE

    if depth == 0:
        val = _evaluate(me, opp)
        TT[key] = (depth, val)
        return val

    best = -10**18
    for mv in legal:
        nme, nopp = _apply(me, opp, mv)
        val = -_alphabeta(nme, nopp, depth - 1, -beta, -alpha)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    TT[key] = (depth, best)
    return best


def _solve_exact(me: int, opp: int, alpha: int = -WIN_SCORE, beta: int = WIN_SCORE) -> int:
    key = (me, opp, -1, 1)
    tt = TT.get(key)
    if tt is not None:
        return tt[1]

    legal = _ordered_moves(me, opp)
    if not legal:
        return -WIN_SCORE

    best = -WIN_SCORE
    for mv in legal:
        nme, nopp = _apply(me, opp, mv)
        val = -_solve_exact(nme, nopp, -beta, -alpha)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    TT[key] = (-1, best)
    return best


def policy(you: List[List[int]], opponent: List[List[int]]) -> str:
    me = _to_bits(you)
    opp = _to_bits(opponent)

    legal = _ordered_moves(me, opp)
    if not legal:
        # No legal move exists; arena says must always return a legal move string,
        # but this should only occur in terminal losing states.
        # Return a syntactically valid fallback.
        return "0,0,R"

    total_pieces = _popcount(me | opp)

    # 1) Exact solve when position is small enough.
    if total_pieces <= 14:
        best_move = legal[0]
        best_val = -10**18
        alpha = -WIN_SCORE
        beta = WIN_SCORE
        for mv in legal:
            nme, nopp = _apply(me, opp, mv)
            val = -_solve_exact(nme, nopp, -beta, -alpha)
            if val > best_val:
                best_val = val
                best_move = mv
            if val > alpha:
                alpha = val
        r, c, d = best_move
        return f"{r},{c},{d}"

    # 2) Iterative deepening alpha-beta for larger positions.
    best_move = legal[0]
    best_val = -10**18

    # Depth schedule chosen to stay fast on 5x6.
    for depth in (3, 5, 7):
        local_best_move = best_move
        local_best_val = -10**18
        alpha = -10**18
        beta = 10**18

        ordered = _ordered_moves(me, opp)
        for mv in ordered:
            nme, nopp = _apply(me, opp, mv)
            val = -_alphabeta(nme, nopp, depth - 1, -beta, -alpha)
            if val > local_best_val:
                local_best_val = val
                local_best_move = mv
            if val > alpha:
                alpha = val

        best_move = local_best_move
        best_val = local_best_val

        # Proven win/loss style cutoff
        if abs(best_val) >= WIN_SCORE // 2:
            break

    r, c, d = best_move
    return f"{r},{c},{d}"

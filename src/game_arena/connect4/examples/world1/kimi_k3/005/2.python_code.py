
import time

ROWS = 6
COLS = 7
ORDER = (3, 2, 4, 1, 5, 0, 6)
MOVE_PREF = (1, 3, 5, 7, 5, 3, 1)

WIN_SCORE = 1_000_000_000
EVAL_WIN = 250_000_000
INF = 10**18
EXACT, LOWER, UPPER = 0, 1, 2
TIME_LIMIT = 0.92

class _Timeout(Exception):
    pass

try:
    _popcount = int.bit_count
except AttributeError:  # very old Python fallback
    _POP = [bin(i).count("1") for i in range(256)]
    def _popcount(x):
        n = 0
        while x:
            n += _POP[x & 255]
            x >>= 8
        return n

def _cell(c, h):
    return 1 << (c * 7 + h)

def _build_windows():
    wins = []
    # Horizontal
    for h in range(ROWS):
        for c in range(COLS - 3):
            wins.append(_cell(c, h) | _cell(c + 1, h) | _cell(c + 2, h) | _cell(c + 3, h))
    # Vertical
    for c in range(COLS):
        for h in range(ROWS - 3):
            wins.append(_cell(c, h) | _cell(c, h + 1) | _cell(c, h + 2) | _cell(c, h + 3))
    # Diagonal up-right
    for c in range(COLS - 3):
        for h in range(ROWS - 3):
            wins.append(_cell(c, h) | _cell(c + 1, h + 1) | _cell(c + 2, h + 2) | _cell(c + 3, h + 3))
    # Diagonal down-right
    for c in range(COLS - 3):
        for h in range(3, ROWS):
            wins.append(_cell(c, h) | _cell(c + 1, h - 1) | _cell(c + 2, h - 2) | _cell(c + 3, h - 3))
    return tuple(wins)

WINDOWS = _build_windows()
WINDOW_VAL = (0, 1, 10, 100, 10000)
CENTER_MASK = 0
INNER_MASK = 0
for _h in range(ROWS):
    CENTER_MASK |= _cell(3, _h)
    INNER_MASK |= _cell(2, _h) | _cell(4, _h)

def _has_won(bb):
    m = bb & (bb >> 1)
    if m & (m >> 2):
        return True
    m = bb & (bb >> 7)
    if m & (m >> 14):
        return True
    m = bb & (bb >> 6)
    if m & (m >> 12):
        return True
    m = bb & (bb >> 8)
    if m & (m >> 16):
        return True
    return False

def _winning_columns(bb, heights):
    out = []
    for c in ORDER:
        h = heights[c]
        if h < ROWS and _has_won(bb | (1 << (c * 7 + h))):
            out.append(c)
    return out

def _evaluate(me, op, heights):
    # Side to move already has a finishing move.
    if _winning_columns(me, heights):
        return EVAL_WIN

    score = 0
    for w in WINDOWS:
        m = me & w
        o = op & w
        if m:
            if not o:
                score += WINDOW_VAL[_popcount(m)]
        elif o:
            score -= WINDOW_VAL[_popcount(o)]

    score += 5 * (_popcount(me & CENTER_MASK) - _popcount(op & CENTER_MASK))
    score += 2 * (_popcount(me & INNER_MASK) - _popcount(op & INNER_MASK))

    ow = _winning_columns(op, heights)
    if len(ow) >= 2:
        return -EVAL_WIN + score
    if ow:
        return (-EVAL_WIN // 2) + score
    return score

def _order_moves(me, op, heights, tt_move=None, forced=None, block_cols=()):
    if forced is not None and heights[forced] < ROWS:
        return [forced]

    blocks = set(block_cols)
    scored = []
    for c in ORDER:
        h = heights[c]
        if h >= ROWS:
            continue
        bit = 1 << (c * 7 + h)
        s = MOVE_PREF[c]
        if c == tt_move:
            s += 1_000_000
        if c in blocks:
            s += 500_000
        if h < ROWS - 1:
            above = bit << 1
            # Do not play directly under an opponent winning cell unless forced.
            if _has_won(op | above):
                s -= 2_000_000
            elif _has_won((me | bit) | above):
                s += 100_000
        scored.append((s, c))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored]

def _search(me, op, heights, depth, alpha, beta, ply, tt, deadline, stats):
    stats[0] += 1
    if (stats[0] & 2047) == 0 and time.perf_counter() > deadline:
        raise _Timeout()

    if depth <= 0:
        return _evaluate(me, op, heights)

    key = (me, op)
    ent = tt.get(key)
    tt_move = None
    if ent is not None:
        ed, ev, ef, em = ent
        if ed >= depth:
            if ef == EXACT:
                return ev
            if ef == LOWER:
                if ev > alpha:
                    alpha = ev
            elif ef == UPPER:
                if ev < beta:
                    beta = ev
            if alpha >= beta:
                return ev
        tt_move = em

    my_wins = _winning_columns(me, heights)
    if my_wins:
        val = WIN_SCORE - ply - 1
        tt[key] = (depth, val, EXACT, my_wins[0])
        return val

    opp_wins = _winning_columns(op, heights)
    forced = None
    if len(opp_wins) >= 2:
        val = -WIN_SCORE + ply + 2
        tt[key] = (depth, val, EXACT, None)
        return val
    if len(opp_wins) == 1:
        forced = opp_wins[0]

    moves = _order_moves(me, op, heights, tt_move, forced)
    if not moves:
        return 0

    alpha_orig = alpha
    best = -INF
    best_move = moves[0]

    for c in moves:
        h = heights[c]
        bit = 1 << (c * 7 + h)
        heights[c] = h + 1
        try:
            score = -_search(op, me | bit, heights, depth - 1, -beta, -alpha, ply + 1, tt, deadline, stats)
        finally:
            heights[c] = h

        if score > best:
            best = score
            best_move = c
            if score > alpha:
                alpha = score
                if alpha >= beta:
                    break

    if best <= alpha_orig:
        flag = UPPER
    elif best >= beta:
        flag = LOWER
    else:
        flag = EXACT
    tt[key] = (depth, best, flag, best_move)
    return best

def _search_root(me, op, heights, depth, tt, deadline, stats, pv_move):
    legal = [c for c in ORDER if heights[c] < ROWS]
    if not legal:
        return None, 0

    my_wins = _winning_columns(me, heights)
    if my_wins:
        return my_wins[0], WIN_SCORE - 1

    opp_wins = _winning_columns(op, heights)
    moves = _order_moves(me, op, heights, pv_move, None, opp_wins)

    best_col = moves[0]
    best_score = -INF
    alpha = -INF
    beta = INF

    for c in moves:
        h = heights[c]
        bit = 1 << (c * 7 + h)
        heights[c] = h + 1
        try:
            score = -_search(op, me | bit, heights, depth - 1, -beta, -alpha, 1, tt, deadline, stats)
        finally:
            heights[c] = h

        if score > best_score:
            best_score = score
            best_col = c
            if score > alpha:
                alpha = score

    return best_col, best_score

def _heuristic_move(me, op, heights, legal):
    best_col = legal[0]
    best_val = -INF
    for c in legal:
        h = heights[c]
        bit = 1 << (c * 7 + h)
        heights[c] = h + 1
        try:
            if _has_won(me | bit):
                val = WIN_SCORE
            elif _winning_columns(op, heights):
                val = -EVAL_WIN
            else:
                val = -_evaluate(op, me | bit, heights)
        finally:
            heights[c] = h
        if val > best_val:
            best_val = val
            best_col = c
    return best_col

def _convert(board):
    me = 0
    op = 0
    heights = [0] * COLS
    for c in range(COLS):
        h = 0
        for r in range(ROWS - 1, -1, -1):
            v = board[r][c]
            if v == 0:
                break
            bit = 1 << (c * 7 + h)
            if v == 1:
                me |= bit
            else:
                op |= bit
            h += 1
        heights[c] = h
    return me, op, heights

def policy(board: list[list[int]]) -> int:
    start = time.perf_counter()
    deadline = start + TIME_LIMIT

    me, op, heights = _convert(board)
    legal = [c for c in ORDER if heights[c] < ROWS]
    if not legal:
        return 0

    wins = _winning_columns(me, heights)
    if wins:
        return int(wins[0])

    opp_wins = _winning_columns(op, heights)
    if len(opp_wins) == 1:
        fallback = opp_wins[0]
    else:
        fallback = _heuristic_move(me, op, heights, legal)

    best_col = fallback
    best_score = -INF
    tt = {}
    stats = [0]
    remaining = sum(ROWS - h for h in heights)

    depth = 1
    while depth <= remaining:
        if time.perf_counter() > deadline - 0.004:
            break
        try:
            col, score = _search_root(me, op, heights, depth, tt, deadline, stats, best_col)
        except _Timeout:
            break

        if col is not None and 0 <= col < COLS and heights[col] < ROWS:
            best_col = col
            best_score = score

        if best_score >= WIN_SCORE - 1000:
            return int(best_col)

        depth += 1

    if best_col is None or not (0 <= best_col < COLS) or heights[best_col] >= ROWS:
        best_col = legal[0]
    return int(best_col)

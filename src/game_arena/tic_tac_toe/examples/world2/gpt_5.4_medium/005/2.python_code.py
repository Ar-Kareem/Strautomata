
import time

FULL_MASK = (1 << 16) - 1
INF = 10**9
WIN_SCORE = 10**6

# Positional preference: central cells and diagonal-capable cells are better.
WEIGHTS = (
    3, 4, 4, 3,
    4, 6, 6, 4,
    4, 6, 6, 4,
    3, 4, 4, 3,
)

LINE_SCORE = (0, 4, 18, 140, 0)
OPP_LINE_SCORE = (0, 4, 20, 160, 0)

WIN_MASKS = []

# Rows
for r in range(4):
    m = 0
    for c in range(4):
        m |= 1 << (r * 4 + c)
    WIN_MASKS.append(m)

# Cols
for c in range(4):
    m = 0
    for r in range(4):
        m |= 1 << (r * 4 + c)
    WIN_MASKS.append(m)

# Diagonals
m = 0
for i in range(4):
    m |= 1 << (i * 4 + i)
WIN_MASKS.append(m)

m = 0
for i in range(4):
    m |= 1 << (i * 4 + (3 - i))
WIN_MASKS.append(m)

WIN_MASKS = tuple(WIN_MASKS)

CELL_LINES = [[] for _ in range(16)]
for wm in WIN_MASKS:
    for i in range(16):
        if (wm >> i) & 1:
            CELL_LINES[i].append(wm)
CELL_LINES = tuple(tuple(x) for x in CELL_LINES)


def has_win(mask: int) -> bool:
    for wm in WIN_MASKS:
        if (mask & wm) == wm:
            return True
    return False


def winning_moves(player_mask: int, other_mask: int):
    empty = FULL_MASK ^ (player_mask | other_mask)
    out = []
    m = empty
    while m:
        b = m & -m
        if has_win(player_mask | b):
            out.append(b)
        m -= b
    return out


def heuristic(me: int, opp: int) -> int:
    score = 0

    # Open-line evaluation
    for wm in WIN_MASKS:
        mc = (me & wm).bit_count()
        oc = (opp & wm).bit_count()
        if mc and oc:
            continue
        if mc:
            score += LINE_SCORE[mc]
        elif oc:
            score -= OPP_LINE_SCORE[oc]

    # Immediate threat counts
    empty = FULL_MASK ^ (me | opp)
    my_threats = 0
    opp_threats = 0
    m = empty
    while m:
        b = m & -m
        if has_win(me | b):
            my_threats += 1
        if has_win(opp | b):
            opp_threats += 1
        m -= b
    score += 220 * my_threats
    score -= 240 * opp_threats

    # Positional weights
    x = me
    while x:
        b = x & -x
        score += WEIGHTS[b.bit_length() - 1]
        x -= b

    x = opp
    while x:
        b = x & -x
        score -= WEIGHTS[b.bit_length() - 1]
        x -= b

    return score


def ordered_moves(me: int, opp: int):
    empty = FULL_MASK ^ (me | opp)
    opp_wins = set(winning_moves(opp, me))
    moves = []

    m = empty
    while m:
        b = m & -m
        idx = b.bit_length() - 1
        s = WEIGHTS[idx]

        if has_win(me | b):
            s += 1_000_000
        if b in opp_wins:
            s += 50_000

        temp = me | b
        for wm in CELL_LINES[idx]:
            mc = (temp & wm).bit_count()
            oc = (opp & wm).bit_count()
            if oc == 0:
                s += (0, 1, 6, 30, 0)[mc]
            elif mc == 0:
                s -= (0, 1, 7, 35, 0)[oc]

        moves.append((s, b))
        m -= b

    moves.sort(key=lambda x: x[0], reverse=True)
    return [b for _, b in moves]


def negamax(me: int, opp: int, depth: int, alpha: int, beta: int, tt: dict, end_time: float) -> int:
    if time.perf_counter() >= end_time:
        raise TimeoutError

    if has_win(me):
        return WIN_SCORE + depth
    if has_win(opp):
        return -WIN_SCORE - depth

    empty = FULL_MASK ^ (me | opp)
    if empty == 0:
        return 0
    if depth == 0:
        return heuristic(me, opp)

    key = (me, opp, depth)
    if key in tt:
        return tt[key]

    my_wins = winning_moves(me, opp)
    if my_wins:
        val = WIN_SCORE + depth
        tt[key] = val
        return val

    opp_wins = winning_moves(opp, me)
    if len(opp_wins) > 1:
        val = -WIN_SCORE - depth
        tt[key] = val
        return val

    if len(opp_wins) == 1:
        moves = opp_wins
    else:
        moves = ordered_moves(me, opp)

    best = -INF
    for b in moves:
        score = -negamax(opp, me | b, depth - 1, -beta, -alpha, tt, end_time)
        if score > best:
            best = score
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    tt[key] = best
    return best


def board_to_masks(board):
    me = 0
    opp = 0
    for r in range(4):
        for c in range(4):
            v = board[r][c]
            idx = r * 4 + c
            if v == 1:
                me |= 1 << idx
            elif v == -1:
                opp |= 1 << idx
    return me, opp


def bit_to_move(bit: int):
    idx = bit.bit_length() - 1
    return (idx // 4, idx % 4)


def first_legal(board):
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                return (r, c)
    return (0, 0)


def policy(board: list[list[int]]) -> tuple[int, int]:
    me, opp = board_to_masks(board)
    occupied = me | opp
    empty = FULL_MASK ^ occupied

    if empty == 0:
        return (0, 0)

    legal_moves = ordered_moves(me, opp)
    if not legal_moves:
        return first_legal(board)

    # Fast tactical checks
    my_wins = winning_moves(me, opp)
    if my_wins:
        return bit_to_move(max(my_wins, key=lambda b: WEIGHTS[b.bit_length() - 1]))

    opp_wins = winning_moves(opp, me)
    if len(opp_wins) == 1:
        return bit_to_move(opp_wins[0])

    if len(opp_wins) > 1:
        # Probably lost, but at least play one blocking square.
        best_block = max(opp_wins, key=lambda b: WEIGHTS[b.bit_length() - 1])
        return bit_to_move(best_block)

    # Fallback move before search
    best_move = legal_moves[0]

    empties = empty.bit_count()
    if empties >= 14:
        max_depth = 5
    elif empties >= 12:
        max_depth = 6
    elif empties >= 10:
        max_depth = 7
    elif empties >= 8:
        max_depth = 8
    else:
        max_depth = empties

    end_time = time.perf_counter() + 0.92
    tt = {}

    try:
        for depth in range(1, max_depth + 1):
            current_best = best_move
            current_score = -INF
            alpha = -INF
            beta = INF

            root_moves = ordered_moves(me, opp)

            for b in root_moves:
                if time.perf_counter() >= end_time:
                    raise TimeoutError

                if has_win(me | b):
                    current_best = b
                    current_score = WIN_SCORE + depth
                    break

                score = -negamax(opp, me | b, depth - 1, -beta, -alpha, tt, end_time)

                if score > current_score:
                    current_score = score
                    current_best = b

                if score > alpha:
                    alpha = score

            best_move = current_best

    except TimeoutError:
        pass

    r, c = bit_to_move(best_move)
    if 0 <= r < 4 and 0 <= c < 4 and board[r][c] == 0:
        return (r, c)
    return first_legal(board)

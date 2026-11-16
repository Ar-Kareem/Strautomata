
import time

FULL = (1 << 16) - 1

WIN_MASKS = (
    0b0000000000001111,
    0b0000000011110000,
    0b0000111100000000,
    0b1111000000000000,
    0b0001000100010001,
    0b0010001000100010,
    0b0100010001000100,
    0b1000100010001000,
    0b1000010000100001,
    0b0001001001001000,
)

CELL_WEIGHTS = (
    4, 3, 3, 4,
    3, 7, 7, 3,
    3, 7, 7, 3,
    4, 3, 3, 4,
)

CENTER_PREF = ((1, 1), (1, 2), (2, 1), (2, 2), (0, 0), (0, 3), (3, 0), (3, 3))

BIT_INDEX = {1 << i: i for i in range(16)}

LINES_BY_CELL = [[] for _ in range(16)]
for m in WIN_MASKS:
    for i in range(16):
        if m & (1 << i):
            LINES_BY_CELL[i].append(m)


class _Timeout(Exception):
    pass


def _is_win(mask):
    for w in WIN_MASKS:
        if mask & w == w:
            return True
    return False


def _bits(mask):
    while mask:
        b = mask & -mask
        yield b
        mask -= b


def _bit_to_move(bit):
    i = BIT_INDEX[bit]
    return (i // 4, i % 4)


def _winning_moves(my_mask, occ):
    empty = FULL & ~occ
    out = []
    for b in _bits(empty):
        if _is_win(my_mask | b):
            out.append(b)
    return out


def _evaluate(xmask, omask):
    if _is_win(xmask):
        return 1_000_000
    if _is_win(omask):
        return -1_000_000

    score = 0
    weights = (0, 2, 20, 350, 100000)

    for w in WIN_MASKS:
        xc = (xmask & w).bit_count()
        oc = (omask & w).bit_count()

        if xc and oc:
            continue
        if xc:
            score += weights[xc]
        elif oc:
            score -= weights[oc]

    return score


def _move_order(xmask, omask, turn):
    occ = xmask | omask
    empty = FULL & ~occ

    if turn == 1:
        my = xmask
        opp = omask
    else:
        my = omask
        opp = xmask

    scored = []

    for b in _bits(empty):
        i = BIT_INDEX[b]
        s = CELL_WEIGHTS[i]

        if _is_win(my | b):
            s += 100000
        if _is_win(opp | b):
            s += 60000

        for line in LINES_BY_CELL[i]:
            mc = (my & line).bit_count()
            oc = (opp & line).bit_count()

            if oc == 0:
                s += 12 * (mc + 1) * (mc + 1)
            if mc == 0:
                s += 10 * (oc + 1) * (oc + 1)

        scored.append((s, b))

    scored.sort(reverse=True)
    return [b for _, b in scored]


def _heuristic_move(xmask, omask):
    occ = xmask | omask
    empty = FULL & ~occ

    legal = list(_bits(empty))
    if not legal:
        return 1

    xwins = _winning_moves(xmask, occ)
    if xwins:
        return xwins[0]

    owins = _winning_moves(omask, occ)
    if owins:
        best_block = None
        best_score = -10**18

        for b in legal:
            nx = xmask | b
            nocc = nx | omask
            remaining_owins = _winning_moves(omask, nocc)

            if not remaining_owins:
                s = _evaluate(nx, omask) + CELL_WEIGHTS[BIT_INDEX[b]]
                if s > best_score:
                    best_score = s
                    best_block = b

        if best_block is not None:
            return best_block

        return owins[0]

    best = legal[0]
    best_score = -10**18

    for b in legal:
        nx = xmask | b
        nocc = nx | omask

        s = _evaluate(nx, omask)
        s += CELL_WEIGHTS[BIT_INDEX[b]] * 4

        my_threats = len(_winning_moves(nx, nocc))
        opp_threats = len(_winning_moves(omask, nocc))

        s += my_threats * 25000
        s -= opp_threats * 35000

        if my_threats >= 2 and opp_threats == 0:
            s += 150000

        worst_opp_fork = 0
        after_empty = FULL & ~nocc
        for ob in _bits(after_empty):
            no = omask | ob
            if _is_win(no):
                worst_opp_fork = max(worst_opp_fork, 3)
            else:
                worst_opp_fork = max(worst_opp_fork, len(_winning_moves(no, nx | no)))

        if worst_opp_fork >= 2:
            s -= 45000 * worst_opp_fork

        if s > best_score:
            best_score = s
            best = b

    return best


def policy(board: list[list[int]]) -> tuple[int, int]:
    xmask = 0
    omask = 0

    for r in range(4):
        for c in range(4):
            v = board[r][c]
            bit = 1 << (r * 4 + c)
            if v == 1:
                xmask |= bit
            elif v == -1:
                omask |= bit

    occ = xmask | omask
    empty = FULL & ~occ

    if empty == 0:
        return (0, 0)

    legal = list(_bits(empty))

    xwins = _winning_moves(xmask, occ)
    if xwins:
        return _bit_to_move(xwins[0])

    owins = _winning_moves(omask, occ)
    if owins:
        safe_blocks = []
        for b in legal:
            nx = xmask | b
            if not _winning_moves(omask, nx | omask):
                safe_blocks.append(b)

        if safe_blocks:
            best = max(safe_blocks, key=lambda b: _evaluate(xmask | b, omask) + CELL_WEIGHTS[BIT_INDEX[b]])
            return _bit_to_move(best)

        return _bit_to_move(owins[0])

    total_moves = occ.bit_count()

    if total_moves <= 1:
        for r, c in CENTER_PREF:
            b = 1 << (r * 4 + c)
            if empty & b:
                return (r, c)

    for b in legal:
        nx = xmask | b
        if len(_winning_moves(nx, nx | omask)) >= 2:
            if not _winning_moves(omask, nx | omask):
                return _bit_to_move(b)

    fallback = _heuristic_move(xmask, omask)

    deadline = time.perf_counter() + 0.86
    nodes = [0]
    tt = {}

    def search(x, o, turn, depth, alpha, beta):
        nodes[0] += 1
        if nodes[0] & 2047 == 0:
            if time.perf_counter() > deadline:
                raise _Timeout()

        rem = 16 - (x | o).bit_count()

        if _is_win(x):
            return 1_000_000 + rem
        if _is_win(o):
            return -1_000_000 - rem
        if rem == 0:
            return 0
        if depth <= 0:
            return _evaluate(x, o)

        key = (x, o, turn, depth)
        cached = tt.get(key)
        if cached is not None:
            return cached

        cut = False

        if turn == 1:
            best_val = -10**18
            for b in _move_order(x, o, 1):
                val = search(x | b, o, -1, depth - 1, alpha, beta)
                if val > best_val:
                    best_val = val
                if best_val > alpha:
                    alpha = best_val
                if alpha >= beta:
                    cut = True
                    break
        else:
            best_val = 10**18
            for b in _move_order(x, o, -1):
                val = search(x, o | b, 1, depth - 1, alpha, beta)
                if val < best_val:
                    best_val = val
                if best_val < beta:
                    beta = best_val
                if alpha >= beta:
                    cut = True
                    break

        if not cut:
            tt[key] = best_val

        return best_val

    best_move = fallback
    root_moves = _move_order(xmask, omask, 1)
    max_depth = empty.bit_count()

    try:
        for depth in range(1, max_depth + 1):
            if time.perf_counter() > deadline:
                break

            alpha = -10**18
            beta = 10**18
            depth_best = best_move
            depth_best_score = -10**18

            for b in root_moves:
                val = search(xmask | b, omask, -1, depth - 1, alpha, beta)

                if val > depth_best_score:
                    depth_best_score = val
                    depth_best = b

                if val > alpha:
                    alpha = val

            best_move = depth_best

            root_moves.sort(
                key=lambda b: (
                    b == best_move,
                    CELL_WEIGHTS[BIT_INDEX[b]],
                    _evaluate(xmask | b, omask),
                ),
                reverse=True,
            )

            if depth_best_score > 900000:
                break

    except _Timeout:
        pass

    if not (empty & best_move):
        best_move = fallback

    if not (empty & best_move):
        best_move = legal[0]

    return _bit_to_move(best_move)

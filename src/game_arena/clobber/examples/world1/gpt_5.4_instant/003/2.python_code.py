
from typing import List, Tuple

# 5x6 board => 30 cells, indexed by idx = r*6 + c
ROWS = 5
COLS = 6
N = ROWS * COLS

DIRS = [(-1, 0, 'U'), (0, 1, 'R'), (1, 0, 'D'), (0, -1, 'L')]
DIR_TO_DELTA = {'U': -COLS, 'R': 1, 'D': COLS, 'L': -1}

# Precompute neighbors and centrality
NEI = [[] for _ in range(N)]          # (to_idx, dir_char)
ADJ_MASK = [0] * N
CENTER_SCORE = [0] * N

for r in range(ROWS):
    for c in range(COLS):
        i = r * COLS + c
        CENTER_SCORE[i] = -(abs(r - 2) + abs(c - 2.5))
        for dr, dc, ch in DIRS:
            rr, cc = r + dr, c + dc
            if 0 <= rr < ROWS and 0 <= cc < COLS:
                j = rr * COLS + cc
                NEI[i].append((j, ch))
                ADJ_MASK[i] |= 1 << j

# Zobrist-like deterministic hash helpers
HASH_CONST1 = 0x9E3779B185EBCA87
HASH_CONST2 = 0xC2B2AE3D27D4EB4F

INF = 10**9


def _to_bitboards(you: List[int], opp: List[int]) -> Tuple[int, int]:
    yb = 0
    ob = 0
    # Supports nested lists or numpy arrays
    for r in range(ROWS):
        for c in range(COLS):
            idx = r * COLS + c
            if int(you[r][c]) == 1:
                yb |= 1 << idx
            elif int(opp[r][c]) == 1:
                ob |= 1 << idx
    return yb, ob


def _moves(yb: int, ob: int):
    res = []
    x = yb
    while x:
        lsb = x & -x
        i = lsb.bit_length() - 1
        for j, ch in NEI[i]:
            if (ob >> j) & 1:
                res.append((i, j, ch))
        x ^= lsb
    return res


def _count_moves(yb: int, ob: int) -> int:
    cnt = 0
    x = yb
    while x:
        lsb = x & -x
        i = lsb.bit_length() - 1
        cnt += ((ADJ_MASK[i] & ob).bit_count())
        x ^= lsb
    return cnt


def _apply(yb: int, ob: int, move: Tuple[int, int, str]) -> Tuple[int, int]:
    i, j, _ = move
    yb2 = (yb ^ (1 << i)) | (1 << j)
    ob2 = ob ^ (1 << j)
    return yb2, ob2


def _move_to_str(move: Tuple[int, int, str]) -> str:
    i, _, ch = move
    r, c = divmod(i, COLS)
    return f"{r},{c},{ch}"


def _hash(yb: int, ob: int) -> int:
    return ((yb * HASH_CONST1) ^ (ob * HASH_CONST2)) & ((1 << 64) - 1)


def _evaluate(yb: int, ob: int) -> int:
    mym = _count_moves(yb, ob)
    oppm = _count_moves(ob, yb)
    if mym == 0:
        return -100000
    if oppm == 0:
        return 100000

    score = 50 * (mym - oppm)

    # Piece-square / tactical adjacency
    x = yb
    while x:
        lsb = x & -x
        i = lsb.bit_length() - 1
        score += 3 * CENTER_SCORE[i]
        score += 2 * ((ADJ_MASK[i] & ob).bit_count())
        x ^= lsb

    x = ob
    while x:
        lsb = x & -x
        i = lsb.bit_length() - 1
        score -= 3 * CENTER_SCORE[i]
        score -= 2 * ((ADJ_MASK[i] & yb).bit_count())
        x ^= lsb

    # Small parity preference in low-piece positions
    total = yb.bit_count() + ob.bit_count()
    if total <= 10:
        score += 3 if (total % 2 == 1) else -3

    return int(score)


def _ordered_moves(yb: int, ob: int):
    ms = _moves(yb, ob)
    scored = []
    for mv in ms:
        i, j, _ = mv
        y2, o2 = _apply(yb, ob, mv)

        opp_replies = _count_moves(o2, y2)
        my_future = _count_moves(y2, o2)

        # Immediate tactical features around destination
        pressure = (ADJ_MASK[j] & o2).bit_count()
        support_loss = (ADJ_MASK[i] & ob).bit_count()

        # Strongly prefer moves that may leave opponent with no move
        s = 0
        if opp_replies == 0:
            s += 1000000
        s += 120 * my_future
        s -= 150 * opp_replies
        s += 20 * pressure
        s += 8 * CENTER_SCORE[j]
        s -= 5 * support_loss

        scored.append((s, mv))

    scored.sort(reverse=True, key=lambda t: t[0])
    return [mv for _, mv in scored]


TT = {}


def _negamax(yb: int, ob: int, depth: int, alpha: int, beta: int) -> int:
    key = (_hash(yb, ob), depth)
    if key in TT:
        val, flag = TT[key]
        if flag == 0:
            return val
        elif flag == -1 and val <= alpha:
            return val
        elif flag == 1 and val >= beta:
            return val

    ms = _ordered_moves(yb, ob)
    if not ms:
        return -100000 - depth

    if depth == 0:
        return _evaluate(yb, ob)

    orig_alpha = alpha
    best = -INF

    # Immediate win pruning
    for mv in ms:
        y2, o2 = _apply(yb, ob, mv)
        if _count_moves(o2, y2) == 0:
            return 100000 + depth

    for mv in ms:
        y2, o2 = _apply(yb, ob, mv)
        val = -_negamax(o2, y2, depth - 1, -beta, -alpha)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    flag = 0
    if best <= orig_alpha:
        flag = -1
    elif best >= beta:
        flag = 1
    TT[key] = (best, flag)
    return best


def policy(you: list[int], opponent: list[int]) -> str:
    yb, ob = _to_bitboards(you, opponent)
    legal = _ordered_moves(yb, ob)

    # Guaranteed-format fallback if somehow no legal move exists.
    # Arena says a legal string is required; when no legal move exists,
    # return a syntactically valid default.
    if not legal:
        # Try to find any own piece and emit a plausible move string.
        for r in range(ROWS):
            for c in range(COLS):
                if int(you[r][c]) == 1:
                    return f"{r},{c},R"
        return "0,0,R"

    # Immediate winning move
    for mv in legal:
        y2, o2 = _apply(yb, ob, mv)
        if _count_moves(o2, y2) == 0:
            return _move_to_str(mv)

    # Adaptive depth
    mym = len(legal)
    oppm = _count_moves(ob, yb)
    total_moves = mym + oppm
    pieces = yb.bit_count() + ob.bit_count()

    if pieces <= 8 or total_moves <= 6:
        depth = 10
    elif pieces <= 12 or total_moves <= 10:
        depth = 8
    elif total_moves <= 16:
        depth = 7
    else:
        depth = 6

    TT.clear()

    best_move = legal[0]
    best_val = -INF
    alpha = -INF
    beta = INF

    for mv in legal:
        y2, o2 = _apply(yb, ob, mv)
        val = -_negamax(o2, y2, depth - 1, -beta, -alpha)
        if val > best_val:
            best_val = val
            best_move = mv
        if val > alpha:
            alpha = val

    return _move_to_str(best_move)

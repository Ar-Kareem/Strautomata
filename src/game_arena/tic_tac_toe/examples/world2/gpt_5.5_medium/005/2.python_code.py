
import time

# 4x4 Tic Tac Toe / connect-4-on-4 policy.
# Board values:  1 = us, -1 = opponent, 0 = empty.
# Returns: (row, col)

N = 4
ALL_MASK = (1 << 16) - 1
WIN_SCORE = 1_000_000
INF = 10_000_000

# Winning lines: 4 rows, 4 columns, 2 diagonals.
WIN_MASKS = []

for r in range(4):
    m = 0
    for c in range(4):
        m |= 1 << (4 * r + c)
    WIN_MASKS.append(m)

for c in range(4):
    m = 0
    for r in range(4):
        m |= 1 << (4 * r + c)
    WIN_MASKS.append(m)

m = 0
for i in range(4):
    m |= 1 << (4 * i + i)
WIN_MASKS.append(m)

m = 0
for i in range(4):
    m |= 1 << (4 * i + (3 - i))
WIN_MASKS.append(m)

# Precomputed popcount and win table for all 16-bit boards.
POPCOUNT = [0] * (1 << 16)
for i in range(1, 1 << 16):
    POPCOUNT[i] = POPCOUNT[i >> 1] + (i & 1)

IS_WIN = [False] * (1 << 16)
for b in range(1 << 16):
    for wm in WIN_MASKS:
        if (b & wm) == wm:
            IS_WIN[b] = True
            break

CELL_LINES = [[] for _ in range(16)]
for i in range(16):
    bit = 1 << i
    for wm in WIN_MASKS:
        if wm & bit:
            CELL_LINES[i].append(wm)

# Positional preference. Diagonal-center cells and corners are strongest.
MOVE_PRIOR = [
    34, 18, 18, 34,
    18, 36, 36, 18,
    18, 36, 36, 18,
    34, 18, 18, 34,
]

LINE_WEIGHTS = [0, 3, 35, 800, WIN_SCORE]
ORDER_OWN = [0, 2, 15, 500, 100000]
ORDER_BLOCK = [0, 2, 18, 650, 100000]

# Transposition table.
# key: (side_to_move_bits, other_side_bits, depth)
# val: (score, flag), flag 0 exact, 1 lower bound, 2 upper bound
_TT = {}
EXACT, LOWER, UPPER = 0, 1, 2


class _Timeout(Exception):
    pass


def _bit_to_move(bit):
    idx = bit.bit_length() - 1
    return idx // 4, idx % 4


def _count_winning_moves(bits, empties, limit=99):
    count = 0
    e = empties
    while e:
        m = e & -e
        if IS_WIN[bits | m]:
            count += 1
            if count >= limit:
                return count
        e ^= m
    return count


def _evaluate(my, opp):
    """Static evaluation from the perspective of side to move."""
    if IS_WIN[my]:
        return WIN_SCORE
    if IS_WIN[opp]:
        return -WIN_SCORE

    empties = ALL_MASK ^ (my | opp)

    # Immediate threats matter a lot.
    my_wins = _count_winning_moves(my, empties, 3)
    opp_wins = _count_winning_moves(opp, empties, 3)

    score = 6000 * my_wins - 7500 * opp_wins

    for wm in WIN_MASKS:
        a = POPCOUNT[my & wm]
        b = POPCOUNT[opp & wm]

        if a and b:
            continue
        if a:
            score += LINE_WEIGHTS[a]
        elif b:
            score -= LINE_WEIGHTS[b]

    return score


def _ordered_moves(my, opp, preferred=0):
    empties = ALL_MASK ^ (my | opp)
    scored = []

    e = empties
    while e:
        bit = e & -e
        idx = bit.bit_length() - 1

        s = MOVE_PRIOR[idx]

        if bit == preferred:
            s += 2_000_000

        # Winning immediately is best.
        if IS_WIN[my | bit]:
            s += 1_000_000

        # Blocking an opponent immediate win is also urgent.
        if IS_WIN[opp | bit]:
            s += 700_000

        # Local line-building / blocking score.
        for wm in CELL_LINES[idx]:
            my_count = POPCOUNT[my & wm]
            opp_count = POPCOUNT[opp & wm]

            if opp_count == 0:
                s += ORDER_OWN[my_count + 1]
            if my_count == 0:
                s += ORDER_BLOCK[opp_count + 1]

        scored.append((s, bit))
        e ^= bit

    scored.sort(reverse=True)
    return [b for _, b in scored]


def _negamax(my, opp, depth, alpha, beta, deadline, node_counter):
    node_counter[0] += 1
    if (node_counter[0] & 2047) == 0 and time.perf_counter() > deadline:
        raise _Timeout()

    # Previous player has won.
    if IS_WIN[opp]:
        return -WIN_SCORE

    empties = ALL_MASK ^ (my | opp)
    if empties == 0:
        return 0

    if depth <= 0:
        return _evaluate(my, opp)

    key = (my, opp, depth)
    ent = _TT.get(key)
    if ent is not None:
        val, flag = ent
        if flag == EXACT:
            return val
        if flag == LOWER and val >= beta:
            return val
        if flag == UPPER and val <= alpha:
            return val

    orig_alpha = alpha
    best = -INF

    for bit in _ordered_moves(my, opp):
        score = -_negamax(opp, my | bit, depth - 1, -beta, -alpha, deadline, node_counter)

        if score > best:
            best = score
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break

    if best <= orig_alpha:
        flag = UPPER
    elif best >= beta:
        flag = LOWER
    else:
        flag = EXACT

    _TT[key] = (best, flag)
    return best


def _root_search(my, opp, depth, deadline, preferred):
    alpha = -INF
    beta = INF
    best_score = -INF
    best_move = 0
    node_counter = [0]

    for bit in _ordered_moves(my, opp, preferred):
        if time.perf_counter() > deadline:
            raise _Timeout()

        score = -_negamax(opp, my | bit, depth - 1, -beta, -alpha, deadline, node_counter)

        if score > best_score:
            best_score = score
            best_move = bit

        if score > alpha:
            alpha = score

    return best_score, best_move


def policy(board: list[list[int]]) -> tuple[int, int]:
    # Always establish a legal fallback first.
    fallback = None
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0 and fallback is None:
                fallback = (r, c)

    if fallback is None:
        # No legal move exists; should not be called on a full board.
        return (0, 0)

    try:
        my = 0
        opp = 0

        for r in range(4):
            for c in range(4):
                v = board[r][c]
                bit = 1 << (4 * r + c)
                if v == 1:
                    my |= bit
                elif v == -1:
                    opp |= bit

        empties = ALL_MASK ^ (my | opp)
        if empties == 0:
            return fallback

        # Strong opening.
        if my == 0 and opp == 0 and board[1][1] == 0:
            return (1, 1)

        # Clear the table occasionally to avoid unbounded growth.
        if len(_TT) > 300_000:
            _TT.clear()

        ordered = _ordered_moves(my, opp)
        best_move = ordered[0] if ordered else (1 << (4 * fallback[0] + fallback[1]))

        # 1. Win immediately if possible.
        for bit in ordered:
            if IS_WIN[my | bit]:
                return _bit_to_move(bit)

        # 2. If opponent has exactly one immediate win, block it.
        opp_winning_bits = []
        e = empties
        while e:
            bit = e & -e
            if IS_WIN[opp | bit]:
                opp_winning_bits.append(bit)
            e ^= bit

        if len(opp_winning_bits) == 1:
            return _bit_to_move(opp_winning_bits[0])

        # 3. Take an immediate fork that creates at least two winning moves,
        # provided opponent cannot win immediately after our move.
        for bit in ordered:
            rem = empties ^ bit
            if _count_winning_moves(opp, rem, 1) == 0:
                if _count_winning_moves(my | bit, rem, 2) >= 2:
                    return _bit_to_move(bit)

        # 4. Iterative-deepening alpha-beta search.
        deadline = time.perf_counter() + 0.88
        preferred = best_move
        max_depth = POPCOUNT[empties]

        for depth in range(1, max_depth + 1):
            if time.perf_counter() > deadline:
                break

            try:
                score, move = _root_search(my, opp, depth, deadline, preferred)
            except _Timeout:
                break

            if move:
                best_move = move
                preferred = move

            # Proven win or loss/draw result at full tactical certainty.
            if abs(score) >= WIN_SCORE:
                break

        return _bit_to_move(best_move)

    except Exception:
        # Absolute safety: never fail to return a legal empty cell.
        return fallback

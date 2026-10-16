
import time

ROWS = 5
COLS = 6
N = ROWS * COLS
FULL_MASK = (1 << N) - 1

INF = 10**9
MATE = 10**6

EXACT = 0
LOWER = 1
UPPER = 2

# Board masks
ROW0 = sum(1 << i for i in range(0, 6))
ROW4 = sum(1 << i for i in range(24, 30))
COL0 = sum(1 << (r * COLS) for r in range(ROWS))
COL5 = sum(1 << (r * COLS + 5) for r in range(ROWS))

NOT_ROW0 = FULL_MASK ^ ROW0
NOT_ROW4 = FULL_MASK ^ ROW4
NOT_COL0 = FULL_MASK ^ COL0
NOT_COL5 = FULL_MASK ^ COL5

# Positional masks
CORNERS = (1 << 0) | (1 << 5) | (1 << 24) | (1 << 29)
INTERIOR = 0
for r in range(1, ROWS - 1):
    for c in range(1, COLS - 1):
        INTERIOR |= 1 << (r * COLS + c)
EDGE_NONCORNER = FULL_MASK ^ CORNERS ^ INTERIOR

# Precomputed move ids
MOVE_STRS = []
R_ID = [-1] * N
L_ID = [-1] * N
U_ID = [-1] * N
D_ID = [-1] * N

for r in range(ROWS):
    for c in range(COLS):
        idx = r * COLS + c
        if r > 0:
            U_ID[idx] = len(MOVE_STRS)
            MOVE_STRS.append(f"{r},{c},U")
        if c < COLS - 1:
            R_ID[idx] = len(MOVE_STRS)
            MOVE_STRS.append(f"{r},{c},R")
        if r < ROWS - 1:
            D_ID[idx] = len(MOVE_STRS)
            MOVE_STRS.append(f"{r},{c},D")
        if c > 0:
            L_ID[idx] = len(MOVE_STRS)
            MOVE_STRS.append(f"{r},{c},L")

NUM_MOVES = len(MOVE_STRS)

# Search globals (reset every policy call)
TT = {}
HISTORY = [0] * NUM_MOVES
KILLERS = [[-1, -1] for _ in range(64)]
END_TIME = 0.0
NODES = 0


def board_to_bits(board):
    bits = 0
    try:
        if len(board) == N and not hasattr(board[0], "__len__"):
            for i, v in enumerate(board):
                if int(v):
                    bits |= 1 << i
            return bits
    except Exception:
        pass

    try:
        for r in range(ROWS):
            row = board[r]
            for c in range(COLS):
                if int(row[c]):
                    bits |= 1 << (r * COLS + c)
        return bits
    except Exception:
        pass

    # Fallback for array-like objects that prefer board[r, c]
    for r in range(ROWS):
        for c in range(COLS):
            if int(board[r, c]):
                bits |= 1 << (r * COLS + c)
    return bits


def count_moves(you_bits, opp_bits):
    return (
        (you_bits & NOT_COL5 & (opp_bits >> 1)).bit_count()
        + (you_bits & NOT_COL0 & (opp_bits << 1)).bit_count()
        + (you_bits & NOT_ROW4 & (opp_bits >> 6)).bit_count()
        + (you_bits & NOT_ROW0 & (opp_bits << 6)).bit_count()
    )


def active_count(you_bits, opp_bits):
    active = (
        (you_bits & NOT_COL5 & (opp_bits >> 1))
        | (you_bits & NOT_COL0 & (opp_bits << 1))
        | (you_bits & NOT_ROW4 & (opp_bits >> 6))
        | (you_bits & NOT_ROW0 & (opp_bits << 6))
    )
    return active.bit_count()


def clump_edges(bits):
    return (
        (bits & NOT_COL5 & (bits >> 1)).bit_count()
        + (bits & NOT_ROW4 & (bits >> 6)).bit_count()
    )


def degree_score(bits):
    return (
        2 * (bits & CORNERS).bit_count()
        + 3 * (bits & EDGE_NONCORNER).bit_count()
        + 4 * (bits & INTERIOR).bit_count()
    )


def evaluate(you_bits, opp_bits, my_moves=None):
    if my_moves is None:
        my_moves = count_moves(you_bits, opp_bits)
    opp_moves = count_moves(opp_bits, you_bits)

    my_active = active_count(you_bits, opp_bits)
    opp_active = active_count(opp_bits, you_bits)

    my_pieces = you_bits.bit_count()
    opp_pieces = opp_bits.bit_count()
    total = my_pieces + opp_pieces

    my_clump = clump_edges(you_bits)
    opp_clump = clump_edges(opp_bits)

    my_deg = degree_score(you_bits)
    opp_deg = degree_score(opp_bits)

    if total >= 20:
        piece_w = 4
        pos_w = 4
        clump_w = 8
    elif total >= 12:
        piece_w = 7
        pos_w = 3
        clump_w = 6
    else:
        piece_w = 10
        pos_w = 2
        clump_w = 4

    score = (
        160 * (my_moves - opp_moves)
        + 45 * (my_active - opp_active)
        + piece_w * (my_pieces - opp_pieces)
        + clump_w * (opp_clump - my_clump)
        + pos_w * (my_deg - opp_deg)
    )
    return score


def collect_moves(you_bits, opp_bits, tt_move=-1, ply=0):
    moves = []
    append = moves.append
    hist = HISTORY
    k0, k1 = KILLERS[ply]

    # Right
    mask = you_bits & NOT_COL5 & (opp_bits >> 1)
    while mask:
        b = mask & -mask
        src = b.bit_length() - 1
        mid = R_ID[src]
        dst = b << 1
        child_you = opp_bits ^ dst
        child_opp = (you_bits ^ b) | dst

        opp_m = count_moves(child_you, child_opp)
        fut_m = count_moves(child_opp, child_you)

        score = hist[mid]
        if mid == tt_move:
            score += 10_000_000
        elif mid == k0:
            score += 5_000_000
        elif mid == k1:
            score += 4_000_000

        if opp_m == 0:
            score += 3_000_000

        score += 96 * fut_m - 192 * opp_m
        append((score, mid, child_you, child_opp))
        mask ^= b

    # Left
    mask = you_bits & NOT_COL0 & (opp_bits << 1)
    while mask:
        b = mask & -mask
        src = b.bit_length() - 1
        mid = L_ID[src]
        dst = b >> 1
        child_you = opp_bits ^ dst
        child_opp = (you_bits ^ b) | dst

        opp_m = count_moves(child_you, child_opp)
        fut_m = count_moves(child_opp, child_you)

        score = hist[mid]
        if mid == tt_move:
            score += 10_000_000
        elif mid == k0:
            score += 5_000_000
        elif mid == k1:
            score += 4_000_000

        if opp_m == 0:
            score += 3_000_000

        score += 96 * fut_m - 192 * opp_m
        append((score, mid, child_you, child_opp))
        mask ^= b

    # Down
    mask = you_bits & NOT_ROW4 & (opp_bits >> 6)
    while mask:
        b = mask & -mask
        src = b.bit_length() - 1
        mid = D_ID[src]
        dst = b << 6
        child_you = opp_bits ^ dst
        child_opp = (you_bits ^ b) | dst

        opp_m = count_moves(child_you, child_opp)
        fut_m = count_moves(child_opp, child_you)

        score = hist[mid]
        if mid == tt_move:
            score += 10_000_000
        elif mid == k0:
            score += 5_000_000
        elif mid == k1:
            score += 4_000_000

        if opp_m == 0:
            score += 3_000_000

        score += 96 * fut_m - 192 * opp_m
        append((score, mid, child_you, child_opp))
        mask ^= b

    # Up
    mask = you_bits & NOT_ROW0 & (opp_bits << 6)
    while mask:
        b = mask & -mask
        src = b.bit_length() - 1
        mid = U_ID[src]
        dst = b >> 6
        child_you = opp_bits ^ dst
        child_opp = (you_bits ^ b) | dst

        opp_m = count_moves(child_you, child_opp)
        fut_m = count_moves(child_opp, child_you)

        score = hist[mid]
        if mid == tt_move:
            score += 10_000_000
        elif mid == k0:
            score += 5_000_000
        elif mid == k1:
            score += 4_000_000

        if opp_m == 0:
            score += 3_000_000

        score += 96 * fut_m - 192 * opp_m
        append((score, mid, child_you, child_opp))
        mask ^= b

    if len(moves) > 1:
        moves.sort(reverse=True)
    return moves


def search(you_bits, opp_bits, depth, alpha, beta, ply):
    global NODES

    NODES += 1
    if (NODES & 1023) == 0 and time.perf_counter() >= END_TIME:
        raise TimeoutError

    key = you_bits | (opp_bits << N)
    orig_alpha = alpha
    orig_beta = beta

    tt_move = -1
    entry = TT.get(key)
    if entry is not None:
        e_depth, e_flag, e_score, e_move = entry
        tt_move = e_move
        if e_depth >= depth:
            if e_flag == EXACT:
                return e_score
            if e_flag == LOWER:
                if e_score > alpha:
                    alpha = e_score
            else:
                if e_score < beta:
                    beta = e_score
            if alpha >= beta:
                return e_score

    my_moves = count_moves(you_bits, opp_bits)
    if my_moves == 0:
        val = -MATE + ply
        TT[key] = (depth, EXACT, val, -1)
        return val

    if depth <= 0:
        val = evaluate(you_bits, opp_bits, my_moves)
        TT[key] = (depth, EXACT, val, -1)
        return val

    children = collect_moves(you_bits, opp_bits, tt_move, ply)

    best_score = -INF
    best_move = -1
    first = True

    for idx, (_, mid, child_you, child_opp) in enumerate(children):
        if first:
            score = -search(child_you, child_opp, depth - 1, -beta, -alpha, ply + 1)
            first = False
        else:
            reduced = depth >= 4 and idx >= 4
            if reduced:
                score = -search(child_you, child_opp, depth - 2, -alpha - 1, -alpha, ply + 1)
                if score > alpha:
                    score = -search(child_you, child_opp, depth - 1, -beta, -alpha, ply + 1)
            else:
                score = -search(child_you, child_opp, depth - 1, -alpha - 1, -alpha, ply + 1)
                if alpha < score < beta:
                    score = -search(child_you, child_opp, depth - 1, -beta, -alpha, ply + 1)

        if score > best_score:
            best_score = score
            best_move = mid

        if score > alpha:
            alpha = score

        if alpha >= beta:
            HISTORY[mid] += 32 * depth * depth
            if ply < len(KILLERS):
                if KILLERS[ply][0] != mid:
                    KILLERS[ply][1] = KILLERS[ply][0]
                    KILLERS[ply][0] = mid
            break

    flag = EXACT
    if best_score <= orig_alpha:
        flag = UPPER
    elif best_score >= orig_beta:
        flag = LOWER

    TT[key] = (depth, flag, best_score, best_move)
    return best_score


def root_search(you_bits, opp_bits, depth, hint_move):
    children = collect_moves(you_bits, opp_bits, hint_move, 0)
    if not children:
        return -MATE, -1

    alpha = -INF
    beta = INF
    best_score = -INF
    best_move = children[0][1]
    first = True

    for _, mid, child_you, child_opp in children:
        if first:
            score = -search(child_you, child_opp, depth - 1, -beta, -alpha, 1)
            first = False
        else:
            score = -search(child_you, child_opp, depth - 1, -alpha - 1, -alpha, 1)
            if alpha < score < beta:
                score = -search(child_you, child_opp, depth - 1, -beta, -alpha, 1)

        if score > best_score:
            best_score = score
            best_move = mid

        if score > alpha:
            alpha = score

    key = you_bits | (opp_bits << N)
    TT[key] = (depth, EXACT, best_score, best_move)
    return best_score, best_move


def policy(you: list[int], opponent: list[int]) -> str:
    global TT, HISTORY, KILLERS, END_TIME, NODES

    you_bits = board_to_bits(you)
    opp_bits = board_to_bits(opponent)

    TT = {}
    HISTORY = [0] * NUM_MOVES
    KILLERS = [[-1, -1] for _ in range(64)]
    NODES = 0
    END_TIME = time.perf_counter() + 0.94

    initial_moves = collect_moves(you_bits, opp_bits, -1, 0)
    if not initial_moves:
        # Terminal positions should normally not be passed in.
        return "0,0,U"

    # Immediate tactical win
    for _, mid, child_you, child_opp in initial_moves:
        if count_moves(child_you, child_opp) == 0:
            return MOVE_STRS[mid]

    if len(initial_moves) == 1:
        return MOVE_STRS[initial_moves[0][1]]

    best_move = initial_moves[0][1]
    prev_best = best_move

    total_pieces = you_bits.bit_count() + opp_bits.bit_count()

    depth = 1
    while depth <= total_pieces:
        try:
            score, move = root_search(you_bits, opp_bits, depth, prev_best)
            if move != -1:
                best_move = move
                prev_best = move
            # A mate score means we've proven the result within the horizon.
            if abs(score) > MATE // 2:
                break
            depth += 1
        except TimeoutError:
            break

    return MOVE_STRS[best_move]

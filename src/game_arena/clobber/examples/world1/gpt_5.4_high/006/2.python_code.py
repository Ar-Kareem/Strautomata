
import time

ROWS = 5
COLS = 6
N = ROWS * COLS

DIR_CHARS = ("U", "R", "D", "L")

MATE = 1_000_000
INF = 10_000_000

TT_EXACT = 0
TT_LOWER = 1
TT_UPPER = 2

MAX_TT = 150_000

ALL = (1 << N) - 1

LEFT_COL = 0
RIGHT_COL = 0
for r in range(ROWS):
    LEFT_COL |= 1 << (r * COLS)
    RIGHT_COL |= 1 << (r * COLS + COLS - 1)

TOP_ROW = (1 << COLS) - 1
BOTTOM_ROW = TOP_ROW << ((ROWS - 1) * COLS)

SRC_CAN_U = ALL ^ TOP_ROW
SRC_CAN_R = ALL ^ RIGHT_COL
SRC_CAN_D = ALL ^ BOTTOM_ROW
SRC_CAN_L = ALL ^ LEFT_COL

# Mild centrality bonus.
POS_W = [
    0, 1, 2, 2, 1, 0,
    1, 2, 3, 3, 2, 1,
    1, 2, 4, 4, 2, 1,
    1, 2, 3, 3, 2, 1,
    0, 1, 2, 2, 1, 0,
]

NEI_MASK = [0] * N
DEST = [-1] * (N * 4)
MOVE_STR = [""] * (N * 4)
DEST_NEI_MASK = [0] * (N * 4)
DEST_POS_W = [0] * (N * 4)

for src in range(N):
    r, c = divmod(src, COLS)
    mask = 0
    if r > 0:
        mask |= 1 << (src - COLS)
    if c < COLS - 1:
        mask |= 1 << (src + 1)
    if r < ROWS - 1:
        mask |= 1 << (src + COLS)
    if c > 0:
        mask |= 1 << (src - 1)
    NEI_MASK[src] = mask

    for d, ch in enumerate(DIR_CHARS):
        mv = (src << 2) | d
        MOVE_STR[mv] = f"{r},{c},{ch}"

    if r > 0:
        mv = (src << 2) | 0
        dst = src - COLS
        DEST[mv] = dst
        DEST_NEI_MASK[mv] = NEI_MASK[dst]
        DEST_POS_W[mv] = POS_W[dst]
    if c < COLS - 1:
        mv = (src << 2) | 1
        dst = src + 1
        DEST[mv] = dst
        DEST_NEI_MASK[mv] = NEI_MASK[dst]
        DEST_POS_W[mv] = POS_W[dst]
    if r < ROWS - 1:
        mv = (src << 2) | 2
        dst = src + COLS
        DEST[mv] = dst
        DEST_NEI_MASK[mv] = NEI_MASK[dst]
        DEST_POS_W[mv] = POS_W[dst]
    if c > 0:
        mv = (src << 2) | 3
        dst = src - 1
        DEST[mv] = dst
        DEST_NEI_MASK[mv] = NEI_MASK[dst]
        DEST_POS_W[mv] = POS_W[dst]

SEARCH_TT = {}
HISTORY = [0] * (N * 4)
KILLERS = [(-1, -1) for _ in range(64)]

NODE_COUNT = 0
DEADLINE = 0.0


def board_to_bits(board) -> int:
    try:
        if len(board) == N and not hasattr(board[0], "__iter__"):
            flat = board
        else:
            flat = []
            for row in board:
                try:
                    flat.extend(row)
                except TypeError:
                    flat.append(row)
    except Exception:
        flat = list(board)

    bits = 0
    i = 0
    for v in flat:
        if i >= N:
            break
        if int(v):
            bits |= 1 << i
        i += 1
    return bits


def count_legal(y: int, o: int) -> int:
    return (
        (y & SRC_CAN_U & (o << COLS)).bit_count()
        + (y & SRC_CAN_R & (o >> 1)).bit_count()
        + (y & SRC_CAN_D & (o >> COLS)).bit_count()
        + (y & SRC_CAN_L & (o << 1)).bit_count()
    )


def active_bits(y: int, o: int) -> int:
    return (
        (y & SRC_CAN_U & (o << COLS))
        | (y & SRC_CAN_R & (o >> 1))
        | (y & SRC_CAN_D & (o >> COLS))
        | (y & SRC_CAN_L & (o << 1))
    )


def active_count(y: int, o: int) -> int:
    return active_bits(y, o).bit_count()


def generate_moves(y: int, o: int):
    moves = []
    for d, m in (
        (0, y & SRC_CAN_U & (o << COLS)),
        (1, y & SRC_CAN_R & (o >> 1)),
        (2, y & SRC_CAN_D & (o >> COLS)),
        (3, y & SRC_CAN_L & (o << 1)),
    ):
        while m:
            lsb = m & -m
            src = lsb.bit_length() - 1
            moves.append((src << 2) | d)
            m ^= lsb
    return moves


def apply_move(y: int, o: int, mv: int):
    src = mv >> 2
    dst = DEST[mv]
    srcb = 1 << src
    dstb = 1 << dst
    # Next state is from the next player's perspective.
    next_you = o ^ dstb
    next_opp = (y ^ srcb) | dstb
    return next_you, next_opp


def piece_stats(bits: int, opp: int):
    active = 0
    degsq = 0
    pos = 0
    while bits:
        lsb = bits & -bits
        idx = lsb.bit_length() - 1
        bits ^= lsb
        deg = (NEI_MASK[idx] & opp).bit_count()
        active += 1 if deg else 0
        degsq += deg * deg
        pos += POS_W[idx]
    return active, degsq, pos


def evaluate(y: int, o: int) -> int:
    py = y.bit_count()
    po = o.bit_count()

    ay, sqy, cy = piece_stats(y, o)
    ao, sqo, co = piece_stats(o, y)

    return (
        100 * (ay - ao)
        + 20 * (sqy - sqo)
        + 10 * (py - po)
        + 4 * (cy - co)
    )


def ordered_children(y: int, o: int, tt_move: int, ply: int):
    scored = []
    if ply < len(KILLERS):
        killer0, killer1 = KILLERS[ply]
    else:
        killer0, killer1 = -1, -1

    for d, m in (
        (0, y & SRC_CAN_U & (o << COLS)),
        (1, y & SRC_CAN_R & (o >> 1)),
        (2, y & SRC_CAN_D & (o >> COLS)),
        (3, y & SRC_CAN_L & (o << 1)),
    ):
        while m:
            lsb = m & -m
            src = lsb.bit_length() - 1
            mv = (src << 2) | d
            cy, co = apply_move(y, o, mv)

            contacts = count_legal(cy, co)
            if contacts == 0:
                score = 4_000_000
            else:
                score = HISTORY[mv]
                if mv == tt_move:
                    score += 3_000_000
                if mv == killer0:
                    score += 5000
                elif mv == killer1:
                    score += 4500

                score -= 60 * contacts
                score -= 25 * active_count(cy, co)
                score += 18 * active_count(co, cy)
                score -= 14 * (DEST_NEI_MASK[mv] & cy).bit_count()
                score += 2 * DEST_POS_W[mv]

            scored.append((score, mv, cy, co))
            m ^= lsb

    scored.sort(key=lambda t: t[0], reverse=True)
    return scored


def search(y: int, o: int, depth: int, alpha: int, beta: int, ply: int) -> int:
    global NODE_COUNT

    NODE_COUNT += 1
    if (NODE_COUNT & 511) == 0 and time.perf_counter() >= DEADLINE:
        raise TimeoutError

    moves_count = count_legal(y, o)
    if moves_count == 0:
        return -MATE

    total = (y | o).bit_count()
    if depth < total and (total <= 12 or (total <= 16 and moves_count <= 6)):
        depth = total

    if depth == 0:
        return evaluate(y, o)

    key = y | (o << N)
    alpha_orig = alpha
    beta_orig = beta

    entry = SEARCH_TT.get(key)
    tt_move = -1
    if entry is not None:
        e_depth, e_flag, e_score, e_move = entry
        tt_move = e_move
        if e_depth >= depth:
            if e_flag == TT_EXACT:
                return e_score
            if e_flag == TT_LOWER and e_score > alpha:
                alpha = e_score
            elif e_flag == TT_UPPER and e_score < beta:
                beta = e_score
            if alpha >= beta:
                return e_score

    children = ordered_children(y, o, tt_move, ply)

    best = -INF
    best_move = children[0][1]
    first = True

    for _, mv, cy, co in children:
        if first:
            score = -search(cy, co, depth - 1, -beta, -alpha, ply + 1)
            first = False
        else:
            score = -search(cy, co, depth - 1, -alpha - 1, -alpha, ply + 1)
            if alpha < score < beta:
                score = -search(cy, co, depth - 1, -beta, -alpha, ply + 1)

        if score > best:
            best = score
            best_move = mv

        if score > alpha:
            alpha = score

        if alpha >= beta:
            if mv != tt_move:
                HISTORY[mv] += depth * depth
                if ply < len(KILLERS):
                    k0, k1 = KILLERS[ply]
                    if mv != k0:
                        KILLERS[ply] = (mv, k0)
            break

    flag = TT_EXACT
    if best <= alpha_orig:
        flag = TT_UPPER
    elif best >= beta_orig:
        flag = TT_LOWER

    if len(SEARCH_TT) < MAX_TT:
        SEARCH_TT[key] = (depth, flag, best, best_move)

    return best


def search_root(y: int, o: int, depth: int, initial_move: int):
    key = y | (o << N)
    tt_move = initial_move

    entry = SEARCH_TT.get(key)
    if tt_move == -1 and entry is not None:
        tt_move = entry[3]

    children = ordered_children(y, o, tt_move, 0)

    best = -INF
    best_move = children[0][1]
    alpha = -INF
    beta = INF
    first = True

    for _, mv, cy, co in children:
        if time.perf_counter() >= DEADLINE:
            raise TimeoutError

        if first:
            score = -search(cy, co, depth - 1, -beta, -alpha, 1)
            first = False
        else:
            score = -search(cy, co, depth - 1, -alpha - 1, -alpha, 1)
            if alpha < score < beta:
                score = -search(cy, co, depth - 1, -beta, -alpha, 1)

        if score > best:
            best = score
            best_move = mv

        if score > alpha:
            alpha = score

        if best == MATE:
            break

    if len(SEARCH_TT) < MAX_TT:
        SEARCH_TT[key] = (depth, TT_EXACT, best, best_move)

    return best, best_move


def policy(you: list[int], opponent: list[int]) -> str:
    global DEADLINE, NODE_COUNT, KILLERS

    if len(SEARCH_TT) > MAX_TT:
        SEARCH_TT.clear()

    if max(HISTORY) > 1_000_000:
        for i in range(len(HISTORY)):
            HISTORY[i] //= 2

    KILLERS = [(-1, -1) for _ in range(64)]

    y = board_to_bits(you) & ALL
    o = board_to_bits(opponent) & ALL
    o &= ~y  # sanitize overlap if any malformed input occurs

    root_moves = generate_moves(y, o)

    # Arena should not call policy on terminal states, but keep a fallback anyway.
    if not root_moves:
        return "0,0,U"

    if len(root_moves) == 1:
        return MOVE_STR[root_moves[0]]

    start = time.perf_counter()
    DEADLINE = start + 0.93
    NODE_COUNT = 0

    # Always keep a legal fallback ready.
    best_move = root_moves[0]
    best_score = -INF

    # Immediate win check + quick heuristic fallback.
    for mv in root_moves:
        cy, co = apply_move(y, o, mv)
        if count_legal(cy, co) == 0:
            return MOVE_STR[mv]

        score = -evaluate(cy, co)
        score -= 18 * (DEST_NEI_MASK[mv] & cy).bit_count()
        score += DEST_POS_W[mv]

        if score > best_score:
            best_score = score
            best_move = mv

    total = (y | o).bit_count()
    depth = 1 if total <= 12 else 2

    try:
        while depth <= total and time.perf_counter() < DEADLINE:
            score, mv = search_root(y, o, depth, best_move)
            best_move = mv
            best_score = score

            if abs(score) == MATE:
                break

            depth += 1
    except TimeoutError:
        pass

    return MOVE_STR[best_move]

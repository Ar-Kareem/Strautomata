
import time

# ----------------------------
# Precomputed constants
# ----------------------------

DIRS = ("L", "R")
FULL_MASK = (1 << 36) - 1
WIN_SCORE = 10**9
INF = WIN_SCORE * 2

# Heuristic weights for uncontested 5-cell windows
# index = number of stones in that window
WINDOW_WEIGHTS = (0, 3, 15, 120, 2000, 0)

# Precompute all 5-cell winning masks on a 6x6 board
def _build_win_masks():
    masks = []

    # Horizontal: 6 rows, 2 windows per row
    for r in range(6):
        for c in range(2):
            m = 0
            for k in range(5):
                m |= 1 << (r * 6 + c + k)
            masks.append(m)

    # Vertical: 6 cols, 2 windows per col
    for c in range(6):
        for r in range(2):
            m = 0
            for k in range(5):
                m |= 1 << ((r + k) * 6 + c)
            masks.append(m)

    # Diagonal down-right: starts (r,c) with r in {0,1}, c in {0,1}
    for r in range(2):
        for c in range(2):
            m = 0
            for k in range(5):
                m |= 1 << ((r + k) * 6 + (c + k))
            masks.append(m)

    # Diagonal down-left: starts (r,c) with r in {0,1}, c in {4,5}
    for r in range(2):
        for c in range(4, 6):
            m = 0
            for k in range(5):
                m |= 1 << ((r + k) * 6 + (c - k))
            masks.append(m)

    return tuple(masks)


WIN_MASKS = _build_win_masks()
BITS = tuple(1 << i for i in range(36))

# Cell scores: number of winning windows passing through each cell
CELL_SCORE = [0] * 36
for mask in WIN_MASKS:
    x = mask
    while x:
        b = x & -x
        idx = b.bit_length() - 1
        CELL_SCORE[idx] += 1
        x ^= b

# Small bonus for quadrant centers (stable under rotation)
for idx in (7, 10, 25, 28):
    CELL_SCORE[idx] += 2

# Prefer searching better cells first
CELL_ORDER = tuple(sorted(range(36), key=lambda i: CELL_SCORE[i], reverse=True))

# Cell -> quadrant
CELL_QUAD = []
for idx in range(36):
    r, c = divmod(idx, 6)
    q = (0 if r < 3 else 2) + (0 if c < 3 else 1)
    CELL_QUAD.append(q)
CELL_QUAD = tuple(CELL_QUAD)

# For each cell, prefer rotating other quadrants first, then its own quadrant
QUAD_ORDER_BY_CELL = []
for idx in range(36):
    own_q = CELL_QUAD[idx]
    order = [q for q in range(4) if q != own_q] + [own_q]
    QUAD_ORDER_BY_CELL.append(tuple(order))
QUAD_ORDER_BY_CELL = tuple(QUAD_ORDER_BY_CELL)

# Precompute move strings
MOVE_STRINGS = tuple(
    tuple(
        tuple(f"{idx // 6 + 1},{idx % 6 + 1},{q},{DIRS[d]}" for d in range(2))
        for q in range(4)
    )
    for idx in range(36)
)

# Precompute positional score tables on 3 chunks of 12 bits each
POS_FACTOR = 2
POS_TABLES = []
for chunk in range(3):
    base = chunk * 12
    table = [0] * 4096
    for pat in range(1, 4096):
        lsb = pat & -pat
        bit = lsb.bit_length() - 1
        table[pat] = table[pat ^ lsb] + POS_FACTOR * CELL_SCORE[base + bit]
    POS_TABLES.append(tuple(table))
POS_TABLES = tuple(POS_TABLES)


def positional_score(bits):
    return (
        POS_TABLES[0][bits & 0xFFF]
        + POS_TABLES[1][(bits >> 12) & 0xFFF]
        + POS_TABLES[2][(bits >> 24) & 0xFFF]
    )


# ----------------------------
# Rotation precomputation
# ----------------------------

def _build_local_rotations():
    # local 3x3 bit pattern rotations for L/R
    rots = [[0] * 512 for _ in range(2)]  # 0=L, 1=R
    for state in range(512):
        left = 0
        right = 0
        for old in range(9):
            if (state >> old) & 1:
                r, c = divmod(old, 3)

                # Left / CCW: (r,c) -> (2-c, r)
                nr, nc = 2 - c, r
                left |= 1 << (nr * 3 + nc)

                # Right / CW: (r,c) -> (c, 2-r)
                nr, nc = c, 2 - r
                right |= 1 << (nr * 3 + nc)

        rots[0][state] = left
        rots[1][state] = right
    return tuple(tuple(x) for x in rots)


LOCAL_ROT = _build_local_rotations()

QUAD_MASKS = []
QUAD_CLEAR_MASKS = []
EXTRACTORS = []      # per quad: list of (global_bit, local_bit)
ROTATED_GLOBAL = []  # per quad, dir, local_state -> global bitmask

for q in range(4):
    br = 0 if q < 2 else 3
    bc = 0 if (q % 2) == 0 else 3

    positions = []
    mask = 0
    extract = []

    for lr in range(3):
        for lc in range(3):
            idx = (br + lr) * 6 + (bc + lc)
            positions.append(idx)
            gbit = 1 << idx
            lbit = 1 << (lr * 3 + lc)
            mask |= gbit
            extract.append((gbit, lbit))

    QUAD_MASKS.append(mask)
    QUAD_CLEAR_MASKS.append(FULL_MASK ^ mask)
    EXTRACTORS.append(tuple(extract))

    quad_maps = []
    for d in range(2):
        arr = [0] * 512
        for state in range(512):
            rotated_local = LOCAL_ROT[d][state]
            gmask = 0
            for local in range(9):
                if (rotated_local >> local) & 1:
                    gmask |= 1 << positions[local]
            arr[state] = gmask
        quad_maps.append(tuple(arr))
    ROTATED_GLOBAL.append(tuple(quad_maps))

QUAD_MASKS = tuple(QUAD_MASKS)
QUAD_CLEAR_MASKS = tuple(QUAD_CLEAR_MASKS)
EXTRACTORS = tuple(EXTRACTORS)
ROTATED_GLOBAL = tuple(ROTATED_GLOBAL)


def rotate_bits(bits, quad, dir_idx,
                extractors=EXTRACTORS,
                clear_masks=QUAD_CLEAR_MASKS,
                rotated_global=ROTATED_GLOBAL):
    state = 0
    for gbit, lbit in extractors[quad]:
        if bits & gbit:
            state |= lbit
    return (bits & clear_masks[quad]) | rotated_global[quad][dir_idx][state]


def apply_move_bit(player_bits, other_bits, place_bit, quad, dir_idx):
    new_player = rotate_bits(player_bits | place_bit, quad, dir_idx)
    new_other = rotate_bits(other_bits, quad, dir_idx)
    return new_player, new_other


# ----------------------------
# Evaluation
# ----------------------------

def evaluate_state(me, op,
                   win_masks=WIN_MASKS,
                   weights=WINDOW_WEIGHTS):
    # Heuristic part
    score = positional_score(me) - positional_score(op)

    me_win = False
    op_win = False

    for mask in win_masks:
        m = me & mask
        o = op & mask

        if m == mask:
            me_win = True
            if op_win:
                return True, 0
        if o == mask:
            op_win = True
            if me_win:
                return True, 0

        if o == 0:
            score += weights[m.bit_count()]
        elif m == 0:
            score -= weights[o.bit_count()]

    if me_win:
        return True, WIN_SCORE
    if op_win:
        return True, -WIN_SCORE
    if (me | op) == FULL_MASK:
        return True, 0

    return False, score


# ----------------------------
# Board conversion / fallbacks
# ----------------------------

def board_to_bits(board):
    bits = 0
    for r in range(6):
        row = board[r]
        base = r * 6
        for c in range(6):
            if row[c]:
                bits |= 1 << (base + c)
    return bits


def first_legal_move_bits(me, op):
    occ = me | op
    for idx in CELL_ORDER:
        if not (occ & BITS[idx]):
            q = QUAD_ORDER_BY_CELL[idx][0]
            return MOVE_STRINGS[idx][q][0]
    return "1,1,0,L"


# ----------------------------
# Search
# ----------------------------

def opponent_reply_value(me, op, alpha, deadline):
    # Position after our move; opponent to move.
    occ = me | op
    best = INF
    checked_cells = 0

    for idx in CELL_ORDER:
        place_bit = BITS[idx]
        if occ & place_bit:
            continue

        for quad in QUAD_ORDER_BY_CELL[idx]:
            for dir_idx in (0, 1):
                op2, me2 = apply_move_bit(op, me, place_bit, quad, dir_idx)
                terminal, val = evaluate_state(me2, op2)

                # If opponent has an immediate win, that's enough.
                if terminal and val == -WIN_SCORE:
                    return -WIN_SCORE

                if val < best:
                    best = val
                    if best <= alpha:
                        return best

        checked_cells += 1
        if (checked_cells & 7) == 0 and time.perf_counter() > deadline:
            raise TimeoutError

    return best


def choose_move(me, op):
    occ = me | op

    # Simple opening book: stable quadrant center, rotate elsewhere.
    if occ == 0:
        return "2,2,3,L"

    deadline = time.perf_counter() + 0.92
    fallback = first_legal_move_bits(me, op)

    moves = []

    # Root move generation and ordering
    try:
        checked_cells = 0
        for idx in CELL_ORDER:
            place_bit = BITS[idx]
            if occ & place_bit:
                continue

            for quad in QUAD_ORDER_BY_CELL[idx]:
                for dir_idx in (0, 1):
                    me1, op1 = apply_move_bit(me, op, place_bit, quad, dir_idx)
                    terminal, val = evaluate_state(me1, op1)

                    # Immediate winning move: play it now.
                    if terminal and val == WIN_SCORE:
                        return MOVE_STRINGS[idx][quad][dir_idx]

                    moves.append((val, idx, quad, dir_idx, me1, op1, terminal))

            checked_cells += 1
            if (checked_cells & 7) == 0 and time.perf_counter() > deadline:
                raise TimeoutError
    except TimeoutError:
        pass

    if not moves:
        return fallback

    moves.sort(key=lambda x: x[0], reverse=True)

    # If time gets very tight, at least return the best heuristic move
    best_move = MOVE_STRINGS[moves[0][1]][moves[0][2]][moves[0][3]]
    best_value = -INF
    alpha = -INF

    try:
        for heur, idx, quad, dir_idx, me1, op1, terminal in moves:
            if time.perf_counter() > deadline:
                raise TimeoutError

            if terminal:
                value = heur
            else:
                value = opponent_reply_value(me1, op1, alpha, deadline)

            if value > best_value:
                best_value = value
                best_move = MOVE_STRINGS[idx][quad][dir_idx]
                alpha = value

                # Forced win found
                if best_value == WIN_SCORE:
                    return best_move
    except TimeoutError:
        pass

    return best_move


# ----------------------------
# Required API
# ----------------------------

def policy(you, opponent) -> str:
    me = None
    op = None
    try:
        me = board_to_bits(you)
        op = board_to_bits(opponent)
        return choose_move(me, op)
    except Exception:
        # Strong fallback: still return a legal move if anything unexpected happens.
        try:
            if me is not None and op is not None:
                return first_legal_move_bits(me, op)
        except Exception:
            pass

        try:
            for r in range(6):
                for c in range(6):
                    if not you[r][c] and not opponent[r][c]:
                        cell_q = (0 if r < 3 else 2) + (0 if c < 3 else 1)
                        q = (cell_q + 1) % 4
                        return f"{r+1},{c+1},{q},L"
        except Exception:
            pass

        return "1,1,0,L"

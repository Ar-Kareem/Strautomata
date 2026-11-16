
import time
import numpy as np

# =========================
# Bitboard constants
# =========================
FULL = (1 << 64) - 1

A_FILE = 0x0101010101010101
H_FILE = 0x8080808080808080
NOT_A = FULL ^ A_FILE
NOT_H = FULL ^ H_FILE

ROW_1 = 0x00000000000000FF
ROW_8 = 0xFF00000000000000
EDGES = ROW_1 | ROW_8 | A_FILE | H_FILE

CORNERS = (1 << 0) | (1 << 7) | (1 << 56) | (1 << 63)

A1_ADJ = (1 << 1) | (1 << 8) | (1 << 9)
H1_ADJ = (1 << 6) | (1 << 14) | (1 << 15)
A8_ADJ = (1 << 48) | (1 << 49) | (1 << 57)
H8_ADJ = (1 << 54) | (1 << 55) | (1 << 62)

INF = 10**9
EXACT, LOWER, UPPER = 0, 1, 2

# =========================
# Positional weights
# =========================
PSQ = (
    120, -20,  20,   5,   5,  20, -20, 120,
    -20, -40,  -5,  -5,  -5,  -5, -40, -20,
     20,  -5,  15,   3,   3,  15,  -5,  20,
      5,  -5,   3,   3,   3,   3,  -5,   5,
      5,  -5,   3,   3,   3,   3,  -5,   5,
     20,  -5,  15,   3,   3,  15,  -5,  20,
    -20, -40,  -5,  -5,  -5,  -5, -40, -20,
    120, -20,  20,   5,   5,  20, -20, 120,
)

ORDER_SQ = tuple(w * 4 for w in PSQ)

# Adjacent-to-corner metadata for move ordering
ADJ_CORNER = [0] * 64  # which corner this square is tied to, else 0
ADJ_TYPE = [0] * 64    # 2 = X-square, 1 = C-square, 0 = other

# a1
ADJ_CORNER[1] = 1 << 0;  ADJ_TYPE[1] = 1
ADJ_CORNER[8] = 1 << 0;  ADJ_TYPE[8] = 1
ADJ_CORNER[9] = 1 << 0;  ADJ_TYPE[9] = 2
# h1
ADJ_CORNER[6] = 1 << 7;  ADJ_TYPE[6] = 1
ADJ_CORNER[15] = 1 << 7; ADJ_TYPE[15] = 1
ADJ_CORNER[14] = 1 << 7; ADJ_TYPE[14] = 2
# a8
ADJ_CORNER[48] = 1 << 56; ADJ_TYPE[48] = 1
ADJ_CORNER[57] = 1 << 56; ADJ_TYPE[57] = 1
ADJ_CORNER[49] = 1 << 56; ADJ_TYPE[49] = 2
# h8
ADJ_CORNER[55] = 1 << 63; ADJ_TYPE[55] = 1
ADJ_CORNER[62] = 1 << 63; ADJ_TYPE[62] = 1
ADJ_CORNER[54] = 1 << 63; ADJ_TYPE[54] = 2

# =========================
# Search state
# =========================
TT = {}              # (p, o, passed) -> (depth, value, flag, best_move)
HISTORY = [0] * 64   # simple history heuristic
DEADLINE = 0.0
NODE_COUNT = 0


class SearchTimeout(Exception):
    pass


# =========================
# Precompute PSQ chunk tables
# =========================
def _build_psq_tables():
    tables = []
    for chunk in range(4):
        base = chunk * 16
        tbl = [0] * 65536
        for mask in range(1, 65536):
            lsb = mask & -mask
            idx = lsb.bit_length() - 1
            tbl[mask] = tbl[mask ^ lsb] + PSQ[base + idx]
        tables.append(tbl)
    return tuple(tables)


PSQ_TABLES = _build_psq_tables()


# =========================
# Bit operations
# =========================
def sh_e(x):
    return (x & NOT_H) << 1


def sh_w(x):
    return (x & NOT_A) >> 1


def sh_n(x):
    return x >> 8


def sh_s(x):
    return (x << 8) & FULL


def sh_ne(x):
    return (x & NOT_H) >> 7


def sh_nw(x):
    return (x & NOT_A) >> 9


def sh_se(x):
    return ((x & NOT_H) << 9) & FULL


def sh_sw(x):
    return ((x & NOT_A) << 7) & FULL


SHIFT_FUNCS = (sh_n, sh_s, sh_e, sh_w, sh_ne, sh_nw, sh_se, sh_sw)


def neighbors(bits):
    return (
        sh_n(bits) | sh_s(bits) | sh_e(bits) | sh_w(bits) |
        sh_ne(bits) | sh_nw(bits) | sh_se(bits) | sh_sw(bits)
    )


def legal_moves(p, o):
    empty = FULL ^ (p | o)
    moves = 0

    x = sh_e(p) & o
    x |= sh_e(x) & o
    x |= sh_e(x) & o
    x |= sh_e(x) & o
    x |= sh_e(x) & o
    x |= sh_e(x) & o
    moves |= sh_e(x) & empty

    x = sh_w(p) & o
    x |= sh_w(x) & o
    x |= sh_w(x) & o
    x |= sh_w(x) & o
    x |= sh_w(x) & o
    x |= sh_w(x) & o
    moves |= sh_w(x) & empty

    x = sh_n(p) & o
    x |= sh_n(x) & o
    x |= sh_n(x) & o
    x |= sh_n(x) & o
    x |= sh_n(x) & o
    x |= sh_n(x) & o
    moves |= sh_n(x) & empty

    x = sh_s(p) & o
    x |= sh_s(x) & o
    x |= sh_s(x) & o
    x |= sh_s(x) & o
    x |= sh_s(x) & o
    x |= sh_s(x) & o
    moves |= sh_s(x) & empty

    x = sh_ne(p) & o
    x |= sh_ne(x) & o
    x |= sh_ne(x) & o
    x |= sh_ne(x) & o
    x |= sh_ne(x) & o
    x |= sh_ne(x) & o
    moves |= sh_ne(x) & empty

    x = sh_nw(p) & o
    x |= sh_nw(x) & o
    x |= sh_nw(x) & o
    x |= sh_nw(x) & o
    x |= sh_nw(x) & o
    x |= sh_nw(x) & o
    moves |= sh_nw(x) & empty

    x = sh_se(p) & o
    x |= sh_se(x) & o
    x |= sh_se(x) & o
    x |= sh_se(x) & o
    x |= sh_se(x) & o
    x |= sh_se(x) & o
    moves |= sh_se(x) & empty

    x = sh_sw(p) & o
    x |= sh_sw(x) & o
    x |= sh_sw(x) & o
    x |= sh_sw(x) & o
    x |= sh_sw(x) & o
    x |= sh_sw(x) & o
    moves |= sh_sw(x) & empty

    return moves


def flips_for_move(p, o, move):
    flips = 0
    for sh in SHIFT_FUNCS:
        x = sh(move)
        captured = 0
        while x and (x & o):
            captured |= x
            x = sh(x)
        if x & p:
            flips |= captured
    return flips


def apply_move(p, o, move):
    flips = flips_for_move(p, o, move)
    new_p = p | move | flips
    new_o = o & ~flips
    return new_p, new_o


# =========================
# Evaluation
# =========================
def psq_sum(bits):
    return (
        PSQ_TABLES[0][bits & 0xFFFF] +
        PSQ_TABLES[1][(bits >> 16) & 0xFFFF] +
        PSQ_TABLES[2][(bits >> 32) & 0xFFFF] +
        PSQ_TABLES[3][(bits >> 48) & 0xFFFF]
    )


def ratio_score(a, b, scale):
    s = a + b
    if s == 0:
        return 0
    return scale * (a - b) // s


def stable_edge_mask(player):
    mask = 0

    # a1
    if player & (1 << 0):
        i = 0
        while i < 8 and ((player >> i) & 1):
            mask |= 1 << i
            i += 1
        i = 0
        while i < 64 and ((player >> i) & 1):
            mask |= 1 << i
            i += 8

    # h1
    if player & (1 << 7):
        i = 7
        while i >= 0 and ((player >> i) & 1):
            mask |= 1 << i
            i -= 1
        i = 7
        while i < 64 and ((player >> i) & 1):
            mask |= 1 << i
            i += 8

    # a8
    if player & (1 << 56):
        i = 56
        while i < 64 and ((player >> i) & 1):
            mask |= 1 << i
            i += 1
        i = 56
        while i >= 0 and ((player >> i) & 1):
            mask |= 1 << i
            i -= 8

    # h8
    if player & (1 << 63):
        i = 63
        while i >= 56 and ((player >> i) & 1):
            mask |= 1 << i
            i -= 1
        i = 63
        while i >= 0 and ((player >> i) & 1):
            mask |= 1 << i
            i -= 8

    return mask


def terminal_score(p, o):
    diff = p.bit_count() - o.bit_count()
    if diff > 0:
        return 100000 + diff
    if diff < 0:
        return -100000 + diff
    return 0


def evaluate(p, o, my_moves=None):
    occupied = p | o
    empties = 64 - occupied.bit_count()

    pm = my_moves if my_moves is not None else legal_moves(p, o)
    om = legal_moves(o, p)

    if pm == 0 and om == 0:
        return terminal_score(p, o)

    if empties > 40:
        mob_scale, pot_scale, front_scale, stable_w, pos_w = 200, 70, 100, 35, 4
    elif empties > 20:
        mob_scale, pot_scale, front_scale, stable_w, pos_w = 170, 55, 80, 45, 3
    else:
        mob_scale, pot_scale, front_scale, stable_w, pos_w = 120, 35, 50, 60, 2

    score = 0

    # Corner occupancy
    corner_diff = (p & CORNERS).bit_count() - (o & CORNERS).bit_count()
    score += 180 * corner_diff

    # Legal corner moves
    corner_move_diff = (pm & CORNERS).bit_count() - (om & CORNERS).bit_count()
    score += 100 * corner_move_diff

    # Corner closeness (adjacent to empty corner is bad)
    close = 0
    empty_corners = (~occupied) & CORNERS
    if empty_corners & (1 << 0):
        close += (o & A1_ADJ).bit_count() - (p & A1_ADJ).bit_count()
    if empty_corners & (1 << 7):
        close += (o & H1_ADJ).bit_count() - (p & H1_ADJ).bit_count()
    if empty_corners & (1 << 56):
        close += (o & A8_ADJ).bit_count() - (p & A8_ADJ).bit_count()
    if empty_corners & (1 << 63):
        close += (o & H8_ADJ).bit_count() - (p & H8_ADJ).bit_count()
    score += 35 * close

    # Positional weights
    score += pos_w * (psq_sum(p) - psq_sum(o))

    # Mobility
    score += ratio_score(pm.bit_count(), om.bit_count(), mob_scale)

    # Potential mobility
    empty = FULL ^ occupied
    pot_p = (empty & neighbors(o)).bit_count()
    pot_o = (empty & neighbors(p)).bit_count()
    score += ratio_score(pot_p, pot_o, pot_scale)

    # Frontier discs (fewer is better)
    frontier_zone = neighbors(empty)
    pf = (p & frontier_zone).bit_count()
    of = (o & frontier_zone).bit_count()
    score += ratio_score(of, pf, front_scale)

    # Approximate edge stability
    if occupied & CORNERS:
        stable_diff = stable_edge_mask(p).bit_count() - stable_edge_mask(o).bit_count()
        score += stable_w * stable_diff

    # Disc count matters more later
    disc_diff = p.bit_count() - o.bit_count()
    if empties <= 20:
        score += 10 * disc_diff
    if empties <= 14:
        score += 10 * disc_diff

    # Small parity nudge late
    if empties <= 15:
        score += 8 if (empties & 1) else -8

    return score


# =========================
# Move ordering
# =========================
def order_moves(moves, p, o, tt_move=0):
    occupied = p | o
    empty_corners = (~occupied) & CORNERS
    own_corners = p & CORNERS

    scored = []
    m = moves
    while m:
        move = m & -m
        m ^= move
        idx = move.bit_length() - 1

        score = ORDER_SQ[idx] + min(HISTORY[idx], 5000)

        if move == tt_move:
            score += 20000

        if move & CORNERS:
            score += 10000

        if move & EDGES:
            score += 150

        corner_bit = ADJ_CORNER[idx]
        if corner_bit:
            if empty_corners & corner_bit:
                if ADJ_TYPE[idx] == 2:
                    score -= 2500  # X-square
                else:
                    score -= 900   # C-square
            elif own_corners & corner_bit:
                if ADJ_TYPE[idx] == 2:
                    score += 250
                else:
                    score += 120

        scored.append((score, move))

    scored.sort(reverse=True)
    return [mv for _, mv in scored]


# =========================
# Search
# =========================
def search(p, o, depth, alpha, beta, passed):
    global NODE_COUNT, DEADLINE, TT

    NODE_COUNT += 1
    if (NODE_COUNT & 255) == 0 and time.perf_counter() >= DEADLINE:
        raise SearchTimeout

    if depth == 0:
        moves = legal_moves(p, o)
        return evaluate(p, o, moves)

    alpha_orig = alpha
    beta_orig = beta
    key = (p, o, passed)

    entry = TT.get(key)
    tt_move = 0
    if entry is not None:
        entry_depth, entry_value, entry_flag, entry_best = entry
        tt_move = entry_best
        if entry_depth >= depth:
            if entry_flag == EXACT:
                return entry_value
            if entry_flag == LOWER:
                if entry_value > alpha:
                    alpha = entry_value
            else:  # UPPER
                if entry_value < beta:
                    beta = entry_value
            if alpha >= beta:
                return entry_value

    moves = legal_moves(p, o)

    if moves == 0:
        opp_moves = legal_moves(o, p)
        if passed or opp_moves == 0:
            value = terminal_score(p, o)
        else:
            value = -search(o, p, depth, -beta, -alpha, True)
        TT[key] = (depth, value, EXACT, 0)
        return value

    ordered = order_moves(moves, p, o, tt_move)
    best_value = -INF
    best_move = ordered[0]

    first = True
    for move in ordered:
        new_p, new_o = apply_move(p, o, move)

        if first:
            value = -search(new_o, new_p, depth - 1, -beta, -alpha, False)
            first = False
        else:
            # PVS / null-window search
            value = -search(new_o, new_p, depth - 1, -alpha - 1, -alpha, False)
            if alpha < value < beta:
                value = -search(new_o, new_p, depth - 1, -beta, -alpha, False)

        if value > best_value:
            best_value = value
            best_move = move

        if value > alpha:
            alpha = value

        if alpha >= beta:
            idx = move.bit_length() - 1
            HISTORY[idx] += depth * depth
            break

    if best_value <= alpha_orig:
        flag = UPPER
    elif best_value >= beta_orig:
        flag = LOWER
    else:
        flag = EXACT

    TT[key] = (depth, best_value, flag, best_move)
    return best_value


def root_search(p, o, depth, pv_move=0):
    global NODE_COUNT, DEADLINE, TT

    if time.perf_counter() >= DEADLINE:
        raise SearchTimeout

    alpha = -INF
    beta = INF

    moves = legal_moves(p, o)
    entry = TT.get((p, o, False))
    tt_move = pv_move if pv_move else (entry[3] if entry is not None else 0)
    ordered = order_moves(moves, p, o, tt_move)

    best_move = ordered[0]
    best_value = -INF

    for move in ordered:
        NODE_COUNT += 1
        if (NODE_COUNT & 255) == 0 and time.perf_counter() >= DEADLINE:
            raise SearchTimeout

        new_p, new_o = apply_move(p, o, move)
        value = -search(new_o, new_p, depth - 1, -beta, -alpha, False)

        if value > best_value:
            best_value = value
            best_move = move

        if value > alpha:
            alpha = value

    TT[(p, o, False)] = (depth, best_value, EXACT, best_move)
    return best_move, best_value


# =========================
# I/O helpers
# =========================
def board_to_bits(board):
    bits = 0
    for r in range(8):
        base = r * 8
        row = board[r]
        for c in range(8):
            if row[c]:
                bits |= 1 << (base + c)
    return bits


def move_to_str(move):
    idx = move.bit_length() - 1
    r, c = divmod(idx, 8)
    return chr(ord('a') + c) + str(r + 1)


# =========================
# Required policy API
# =========================
def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    global DEADLINE, NODE_COUNT, TT, HISTORY

    try:
        # Keep transposition table bounded
        if len(TT) > 300000:
            TT.clear()

        # Light decay so history stays useful but not stale
        for i in range(64):
            HISTORY[i] >>= 1

        p = board_to_bits(you)
        o = board_to_bits(opponent)

        moves = legal_moves(p, o)
        if moves == 0:
            return "pass"

        # Only one legal move
        if (moves & (moves - 1)) == 0:
            return move_to_str(moves)

        occupied = p | o
        empties = 64 - occupied.bit_count()

        # Safe time budget
        DEADLINE = time.perf_counter() + 0.93
        NODE_COUNT = 0

        entry = TT.get((p, o, False))
        pv_move = entry[3] if entry is not None else 0
        ordered = order_moves(moves, p, o, pv_move)
        best_move = ordered[0]

        # Search depth schedule
        if empties <= 12:
            hard_cap = empties   # full endgame search
        elif empties <= 18:
            hard_cap = 9
        elif empties <= 24:
            hard_cap = 8
        elif empties <= 36:
            hard_cap = 7
        elif empties <= 48:
            hard_cap = 6
        else:
            hard_cap = 5

        depth = 1
        while depth <= hard_cap:
            if time.perf_counter() >= DEADLINE:
                break
            try:
                move, _score = root_search(p, o, depth, best_move)
                best_move = move
                depth += 1
            except SearchTimeout:
                break

        return move_to_str(best_move)

    except Exception:
        # Guaranteed-legal fallback
        p = board_to_bits(you)
        o = board_to_bits(opponent)
        moves = legal_moves(p, o)
        if moves == 0:
            return "pass"
        return move_to_str(moves & -moves)

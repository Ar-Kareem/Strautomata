
from __future__ import annotations

import time

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

INF = 10**9
WIN = 10**7

MAN_VALUE = 100
KING_VALUE = 175

TIME_BUDGET = 0.84
QUIESCE_DEPTH = 4

OPP = {"b": "w", "w": "b"}

BITS = [1 << i for i in range(64)]
IDX_TO_RC = [(i // 8, i % 8) for i in range(64)]
ROW = [i // 8 for i in range(64)]
COL = [i % 8 for i in range(64)]

# Search globals, reset on every call.
ROOT_SIDE = "b"
DEADLINE = 0.0
NODES = 0
TT = {}

# Small memory for engines that call again during a forced multi-jump.
_LAST_PREDICTED_STATE = None
_LAST_TO_IDX = None
_LAST_COLOR = None


# ---------------------------------------------------------------------------
# Move tables
# ---------------------------------------------------------------------------

def _inside(r: int, c: int) -> bool:
    return 0 <= r < 8 and 0 <= c < 8


MAN_STEPS_B = [[] for _ in range(64)]
MAN_STEPS_W = [[] for _ in range(64)]
KING_STEPS = [[] for _ in range(64)]

MAN_CAPS_B = [[] for _ in range(64)]
MAN_CAPS_W = [[] for _ in range(64)]
KING_CAPS = [[] for _ in range(64)]

for idx in range(64):
    r, c = IDX_TO_RC[idx]

    for dr, dc in [(-1, -1), (-1, 1)]:
        nr, nc = r + dr, c + dc
        if _inside(nr, nc):
            MAN_STEPS_B[idx].append(nr * 8 + nc)
        mr, mc = r + dr, c + dc
        lr, lc = r + 2 * dr, c + 2 * dc
        if _inside(mr, mc) and _inside(lr, lc):
            MAN_CAPS_B[idx].append((mr * 8 + mc, lr * 8 + lc))

    for dr, dc in [(1, -1), (1, 1)]:
        nr, nc = r + dr, c + dc
        if _inside(nr, nc):
            MAN_STEPS_W[idx].append(nr * 8 + nc)
        mr, mc = r + dr, c + dc
        lr, lc = r + 2 * dr, c + 2 * dc
        if _inside(mr, mc) and _inside(lr, lc):
            MAN_CAPS_W[idx].append((mr * 8 + mc, lr * 8 + lc))

    for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        nr, nc = r + dr, c + dc
        if _inside(nr, nc):
            KING_STEPS[idx].append(nr * 8 + nc)
        mr, mc = r + dr, c + dc
        lr, lc = r + 2 * dr, c + 2 * dc
        if _inside(mr, mc) and _inside(lr, lc):
            KING_CAPS[idx].append((mr * 8 + mc, lr * 8 + lc))


# ---------------------------------------------------------------------------
# Piece-square tables
# ---------------------------------------------------------------------------

COL_CENTER = [0, 2, 4, 5, 5, 4, 2, 0]
ROW_CENTER = [0, 2, 4, 5, 5, 4, 2, 0]

BLACK_MAN_TABLE = [0] * 64
WHITE_MAN_TABLE = [0] * 64
KING_TABLE = [0] * 64

for idx in range(64):
    r, c = IDX_TO_RC[idx]

    edge_bonus = 2 if c in (0, 7) else 0
    col_bonus = COL_CENTER[c] * 2
    midrow_bonus = 2 if 2 <= r <= 5 else 0

    # Black moves toward row 0.
    b_advance = (7 - r) * 7
    b_promo = 10 if r == 1 else (5 if r == 2 else 0)
    b_back_guard = 6 if r == 7 else 0
    BLACK_MAN_TABLE[idx] = b_advance + b_promo + b_back_guard + col_bonus + midrow_bonus + edge_bonus

    # White moves toward row 7.
    w_advance = r * 7
    w_promo = 10 if r == 6 else (5 if r == 5 else 0)
    w_back_guard = 6 if r == 0 else 0
    WHITE_MAN_TABLE[idx] = w_advance + w_promo + w_back_guard + col_bonus + midrow_bonus + edge_bonus

    # Kings prefer central mobility.
    KING_TABLE[idx] = (COL_CENTER[c] + ROW_CENTER[r]) * 4


# ---------------------------------------------------------------------------
# Bitboard helpers
# ---------------------------------------------------------------------------

def _bits_from(coords) -> int:
    mask = 0
    for p in coords:
        r = int(p[0])
        c = int(p[1])
        if 0 <= r < 8 and 0 <= c < 8:
            mask |= BITS[r * 8 + c]
    return mask


def _root_score(black_score: int) -> int:
    return black_score if ROOT_SIDE == "b" else -black_score


# ---------------------------------------------------------------------------
# Move generation
# Move tuple: (source_idx, dest_idx, captured_idx or -1, is_king 0/1)
# ---------------------------------------------------------------------------

def _captures(state, side: str):
    bm, bk, wm, wk = state
    occ = bm | bk | wm | wk

    if side == "b":
        own_m, own_k = bm, bk
        opp = wm | wk
        man_caps = MAN_CAPS_B
    else:
        own_m, own_k = wm, wk
        opp = bm | bk
        man_caps = MAN_CAPS_W

    moves = []
    bits = own_m
    while bits:
        lsb = bits & -bits
        src = lsb.bit_length() - 1
        bits ^= lsb
        for mid, dst in man_caps[src]:
            if (opp & BITS[mid]) and not (occ & BITS[dst]):
                moves.append((src, dst, mid, 0))

    bits = own_k
    while bits:
        lsb = bits & -bits
        src = lsb.bit_length() - 1
        bits ^= lsb
        for mid, dst in KING_CAPS[src]:
            if (opp & BITS[mid]) and not (occ & BITS[dst]):
                moves.append((src, dst, mid, 1))

    return moves


def _quiets(state, side: str):
    bm, bk, wm, wk = state
    occ = bm | bk | wm | wk

    if side == "b":
        own_m, own_k = bm, bk
        man_steps = MAN_STEPS_B
    else:
        own_m, own_k = wm, wk
        man_steps = MAN_STEPS_W

    moves = []
    bits = own_m
    while bits:
        lsb = bits & -bits
        src = lsb.bit_length() - 1
        bits ^= lsb
        for dst in man_steps[src]:
            if not (occ & BITS[dst]):
                moves.append((src, dst, -1, 0))

    bits = own_k
    while bits:
        lsb = bits & -bits
        src = lsb.bit_length() - 1
        bits ^= lsb
        for dst in KING_STEPS[src]:
            if not (occ & BITS[dst]):
                moves.append((src, dst, -1, 1))

    return moves


def _moves(state, side: str):
    caps = _captures(state, side)
    if caps:
        return caps
    return _quiets(state, side)


def _make(state, side: str, mv):
    bm, bk, wm, wk = state
    src, dst, cap, is_king = mv
    sb = BITS[src]
    db = BITS[dst]

    if side == "b":
        if is_king:
            bk = (bk & ~sb) | db
        else:
            bm &= ~sb
            if ROW[dst] == 0:
                bk |= db
            else:
                bm |= db

        if cap >= 0:
            cb = BITS[cap]
            if wm & cb:
                wm &= ~cb
            else:
                wk &= ~cb

    else:
        if is_king:
            wk = (wk & ~sb) | db
        else:
            wm &= ~sb
            if ROW[dst] == 7:
                wk |= db
            else:
                wm |= db

        if cap >= 0:
            cb = BITS[cap]
            if bm & cb:
                bm &= ~cb
            else:
                bk &= ~cb

    return bm, bk, wm, wk


# ---------------------------------------------------------------------------
# Evaluation and ordering
# ---------------------------------------------------------------------------

def _captured_value(state, side: str, cap_idx: int) -> int:
    if cap_idx < 0:
        return 0
    bit = BITS[cap_idx]
    bm, bk, wm, wk = state
    if side == "b":
        return KING_VALUE if (wk & bit) else MAN_VALUE
    return KING_VALUE if (bk & bit) else MAN_VALUE


def _promotes(side: str, mv) -> bool:
    src, dst, cap, is_king = mv
    if is_king:
        return False
    return (side == "b" and ROW[dst] == 0) or (side == "w" and ROW[dst] == 7)


def _move_order_score(state, side: str, mv, tt_mv=None) -> int:
    src, dst, cap, is_king = mv
    score = 0

    if tt_mv is not None and mv == tt_mv:
        score += 10_000_000

    if cap >= 0:
        score += 100_000 + 20 * _captured_value(state, side, cap)

    if _promotes(side, mv):
        score += 5_000

    if is_king:
        score += KING_TABLE[dst] - KING_TABLE[src]
    else:
        table = BLACK_MAN_TABLE if side == "b" else WHITE_MAN_TABLE
        score += table[dst] - table[src]

    return score


def _ordered(moves, state, side: str, tt_mv=None):
    return sorted(moves, key=lambda m: _move_order_score(state, side, m, tt_mv), reverse=True)


def _evaluate(state, side_to_move: str) -> int:
    bm, bk, wm, wk = state

    black_pieces = bm | bk
    white_pieces = wm | wk

    if not black_pieces:
        return _root_score(-WIN)
    if not white_pieces:
        return _root_score(WIN)

    bm_n = bm.bit_count()
    bk_n = bk.bit_count()
    wm_n = wm.bit_count()
    wk_n = wk.bit_count()

    score = (bm_n - wm_n) * MAN_VALUE + (bk_n - wk_n) * KING_VALUE

    bits = bm
    while bits:
        lsb = bits & -bits
        idx = lsb.bit_length() - 1
        bits ^= lsb
        score += BLACK_MAN_TABLE[idx]

    bits = wm
    while bits:
        lsb = bits & -bits
        idx = lsb.bit_length() - 1
        bits ^= lsb
        score -= WHITE_MAN_TABLE[idx]

    bits = bk
    while bits:
        lsb = bits & -bits
        idx = lsb.bit_length() - 1
        bits ^= lsb
        score += KING_TABLE[idx]

    bits = wk
    while bits:
        lsb = bits & -bits
        idx = lsb.bit_length() - 1
        bits ^= lsb
        score -= KING_TABLE[idx]

    total_pieces = bm_n + bk_n + wm_n + wk_n
    unit_delta = (bm_n + 2 * bk_n) - (wm_n + 2 * wk_n)
    score += unit_delta * (24 - total_pieces)

    b_moves = _moves(state, "b")
    w_moves = _moves(state, "w")

    if not b_moves:
        score -= WIN // 2
    if not w_moves:
        score += WIN // 2

    score += 4 * (len(b_moves) - len(w_moves))

    for mv in b_moves:
        if mv[2] >= 0:
            score += 18 + _captured_value(state, "b", mv[2]) // 8

    for mv in w_moves:
        if mv[2] >= 0:
            score -= 18 + _captured_value(state, "w", mv[2]) // 8

    # Tiny tempo preference.
    score += 3 if side_to_move == "b" else -3

    return _root_score(score)


# ---------------------------------------------------------------------------
# Alpha-beta search
# ---------------------------------------------------------------------------

EXACT = 0
LOWER = 1
UPPER = 2


def _loss_score(side: str, depth: int) -> int:
    if side == ROOT_SIDE:
        return -WIN - depth
    return WIN + depth


def _store_tt(key, depth, qdepth, flag, value, best_move):
    old = TT.get(key)
    if old is None or depth > old[0] or (depth == old[0] and qdepth >= old[1]):
        TT[key] = (depth, qdepth, flag, value, best_move)


def _alphabeta(state, side: str, depth: int, alpha: int, beta: int, qdepth: int) -> int:
    global NODES

    NODES += 1
    if (NODES & 511) == 0 and time.perf_counter() >= DEADLINE:
        raise TimeoutError

    alpha_orig = alpha
    beta_orig = beta

    key = (state[0], state[1], state[2], state[3], side)
    entry = TT.get(key)
    tt_move = None

    if entry is not None:
        edepth, eqdepth, flag, val, emove = entry
        tt_move = emove
        if edepth > depth or (edepth == depth and eqdepth >= qdepth):
            if flag == EXACT:
                return val
            if flag == LOWER:
                alpha = max(alpha, val)
            elif flag == UPPER:
                beta = min(beta, val)
            if alpha >= beta:
                return val

    if depth <= 0:
        if qdepth > 0:
            moves = _captures(state, side)
            if not moves:
                return _evaluate(state, side)
            next_depth = 0
            next_qdepth = qdepth - 1
        else:
            return _evaluate(state, side)
    else:
        moves = _moves(state, side)
        if not moves:
            return _loss_score(side, depth)
        next_depth = depth - 1
        next_qdepth = qdepth

    moves = _ordered(moves, state, side, tt_move)
    best_move = moves[0]

    if side == ROOT_SIDE:
        value = -INF
        other = OPP[side]
        for mv in moves:
            child = _make(state, side, mv)
            sc = _alphabeta(child, other, next_depth, alpha, beta, next_qdepth)
            if sc > value:
                value = sc
                best_move = mv
            alpha = max(alpha, value)
            if alpha >= beta:
                break
    else:
        value = INF
        other = OPP[side]
        for mv in moves:
            child = _make(state, side, mv)
            sc = _alphabeta(child, other, next_depth, alpha, beta, next_qdepth)
            if sc < value:
                value = sc
                best_move = mv
            beta = min(beta, value)
            if alpha >= beta:
                break

    if value <= alpha_orig:
        flag = UPPER
    elif value >= beta_orig:
        flag = LOWER
    else:
        flag = EXACT

    _store_tt(key, depth, qdepth, flag, value, best_move)
    return value


def _root_search(state, side: str, depth: int, root_moves, preferred):
    alpha = -INF
    beta = INF

    tt_move = preferred
    entry = TT.get((state[0], state[1], state[2], state[3], side))
    if tt_move is None and entry is not None:
        tt_move = entry[4]

    moves = _ordered(list(root_moves), state, side, tt_move)
    best_move = moves[0]
    best_score = -INF
    other = OPP[side]

    for mv in moves:
        if time.perf_counter() >= DEADLINE:
            raise TimeoutError

        child = _make(state, side, mv)
        sc = _alphabeta(child, other, depth - 1, alpha, beta, QUIESCE_DEPTH)

        if sc > best_score:
            best_score = sc
            best_move = mv

        alpha = max(alpha, best_score)

    return best_score, best_move


def _fallback_choice(state, side: str, moves):
    ordered = _ordered(list(moves), state, side, None)
    best = ordered[0]
    best_val = -INF
    other = OPP[side]

    for mv in ordered:
        child = _make(state, side, mv)
        val = _evaluate(child, other)
        if val > best_val:
            best_val = val
            best = mv

    return best


def _depth_cap(state, root_moves) -> int:
    bm, bk, wm, wk = state
    pieces = (bm | bk | wm | wk).bit_count()

    if pieces <= 4:
        cap = 15
    elif pieces <= 8:
        cap = 12
    elif pieces <= 12:
        cap = 10
    elif pieces <= 18:
        cap = 8
    else:
        cap = 7

    if len(root_moves) <= 2:
        cap += 2
    if any(mv[2] >= 0 for mv in root_moves):
        cap += 2

    return cap


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _build_state(my_men, my_kings, opp_men, opp_kings, color: str):
    side = "b" if color == "b" else "w"

    my_m = _bits_from(my_men)
    my_k = _bits_from(my_kings)
    op_m = _bits_from(opp_men)
    op_k = _bits_from(opp_kings)

    if side == "b":
        return side, (my_m, my_k, op_m, op_k)
    return side, (op_m, op_k, my_m, my_k)


def _emergency(my_men, my_kings, opp_men, opp_kings, color):
    try:
        side, state = _build_state(my_men, my_kings, opp_men, opp_kings, color)
        moves = _moves(state, side)
        if moves:
            mv = moves[0]
            return IDX_TO_RC[mv[0]], IDX_TO_RC[mv[1]]
    except Exception:
        pass

    # Terminal positions should not be queried. This is only a syntactic fallback.
    pieces = list(my_men) + list(my_kings)
    if pieces:
        r = int(pieces[0][0])
        c = int(pieces[0][1])
        dirs = [(-1, -1), (-1, 1)] if color == "b" else [(1, -1), (1, 1)]
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                return (r, c), (nr, nc)

    return (0, 0), (1, 1)


def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    global ROOT_SIDE, DEADLINE, NODES, TT
    global _LAST_PREDICTED_STATE, _LAST_TO_IDX, _LAST_COLOR

    try:
        ROOT_SIDE, state = _build_state(my_men, my_kings, opp_men, opp_kings, color)
        DEADLINE = time.perf_counter() + TIME_BUDGET
        NODES = 0
        TT = {}

        legal = _moves(state, ROOT_SIDE)
        if not legal:
            return _emergency(my_men, my_kings, opp_men, opp_kings, color)

        # If the engine is asking for the next leg of a multi-jump, only the
        # previously moved piece may continue.
        if (
            _LAST_COLOR == ROOT_SIDE
            and _LAST_PREDICTED_STATE == state
            and _LAST_TO_IDX is not None
        ):
            caps = _captures(state, ROOT_SIDE)
            continuation = [mv for mv in caps if mv[0] == _LAST_TO_IDX]
            if continuation:
                legal = continuation

        best_move = _fallback_choice(state, ROOT_SIDE, legal)

        if len(legal) > 1:
            preferred = best_move
            max_depth = _depth_cap(state, legal)

            for depth in range(1, max_depth + 1):
                if time.perf_counter() >= DEADLINE:
                    break
                try:
                    _, mv = _root_search(state, ROOT_SIDE, depth, legal, preferred)
                    best_move = mv
                    preferred = mv
                except TimeoutError:
                    break

        predicted = _make(state, ROOT_SIDE, best_move)
        _LAST_PREDICTED_STATE = predicted
        _LAST_TO_IDX = best_move[1]
        _LAST_COLOR = ROOT_SIDE

        return IDX_TO_RC[best_move[0]], IDX_TO_RC[best_move[1]]

    except Exception:
        return _emergency(my_men, my_kings, opp_men, opp_kings, color)

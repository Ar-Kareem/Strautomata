
import time

# ---------------------------------------------------------------------------
# Board geometry and bitboard precomputation
# ---------------------------------------------------------------------------

FULL = (1 << 64) - 1
FILE_A = sum(1 << (r * 8) for r in range(8))
FILE_H = sum(1 << (r * 8 + 7) for r in range(8))
NOT_A = FULL ^ FILE_A
NOT_H = FULL ^ FILE_H

MATE = 1_000_000
INF = 2_000_000

# Direction entries are (row_delta, column_delta, line_axis).
# Axes: 0=row, 1=column, 2=main diagonal, 3=anti-diagonal.
DIRECTIONS = (
    (0, 1, 0),
    (0, -1, 0),
    (1, 0, 1),
    (-1, 0, 1),
    (1, 1, 2),
    (-1, -1, 2),
    (1, -1, 3),
    (-1, 1, 3),
)

LINE_MASKS = [[0] * 64 for _ in range(4)]
NEIGHBORS = [0] * 64
BETWEEN = [[0] * 64 for _ in range(64)]
CENTER_VALUE = [0] * 64

for r in range(8):
    for c in range(8):
        sq = r * 8 + c

        row_mask = 0
        col_mask = 0
        diag_mask = 0
        anti_mask = 0

        for rr in range(8):
            for cc in range(8):
                bit = 1 << (rr * 8 + cc)
                if rr == r:
                    row_mask |= bit
                if cc == c:
                    col_mask |= bit
                if rr - cc == r - c:
                    diag_mask |= bit
                if rr + cc == r + c:
                    anti_mask |= bit

                if max(abs(rr - r), abs(cc - c)) == 1:
                    NEIGHBORS[sq] |= bit

        LINE_MASKS[0][sq] = row_mask
        LINE_MASKS[1][sq] = col_mask
        LINE_MASKS[2][sq] = diag_mask
        LINE_MASKS[3][sq] = anti_mask

        CENTER_VALUE[sq] = min(r, 7 - r) + min(c, 7 - c)

for f in range(64):
    fr, fc = divmod(f, 8)
    for t in range(64):
        if f == t:
            continue

        tr, tc = divmod(t, 8)
        dr_raw = tr - fr
        dc_raw = tc - fc

        if not (
            dr_raw == 0
            or dc_raw == 0
            or abs(dr_raw) == abs(dc_raw)
        ):
            continue

        dr = 0 if dr_raw == 0 else (1 if dr_raw > 0 else -1)
        dc = 0 if dc_raw == 0 else (1 if dc_raw > 0 else -1)

        rr = fr + dr
        cc = fc + dc
        mask = 0

        while (rr, cc) != (tr, tc):
            mask |= 1 << (rr * 8 + cc)
            rr += dr
            cc += dc

        BETWEEN[f][t] = mask


# ---------------------------------------------------------------------------
# Search state
# ---------------------------------------------------------------------------

_DEADLINE = 0.0
_NODES = 0
_TT = {}
_HISTORY = [[0] * 4096 for _ in range(2)]
_KILLERS = [[-1, -1] for _ in range(32)]


class _SearchTimeout(Exception):
    pass


# ---------------------------------------------------------------------------
# Bitboard utilities
# ---------------------------------------------------------------------------

def _neighbor_union(bits):
    return (
        ((bits << 1) & NOT_A)
        | ((bits >> 1) & NOT_H)
        | ((bits << 8) & FULL)
        | (bits >> 8)
        | ((bits << 9) & NOT_A)
        | ((bits << 7) & NOT_H)
        | ((bits >> 7) & NOT_A)
        | ((bits >> 9) & NOT_H)
    ) & FULL


def _connected(bits):
    if bits == 0:
        return False
    if bits & (bits - 1) == 0:
        return True

    reached = bits & -bits
    while True:
        expanded = reached | (_neighbor_union(reached) & bits)
        if expanded == reached:
            return reached == bits
        reached = expanded


def _component_sizes(bits):
    sizes = []
    remaining = bits

    while remaining:
        group = remaining & -remaining

        while True:
            expanded = group | (_neighbor_union(group) & bits)
            if expanded == group:
                break
            group = expanded

        sizes.append(group.bit_count())
        remaining &= ~group

    return sizes


# ---------------------------------------------------------------------------
# Legal move generation
# A move is encoded as from_square * 64 + to_square.
# ---------------------------------------------------------------------------

def _generate_moves(p1, p2, side):
    occupied = p1 | p2
    friendly = p1 if side == 1 else p2
    enemy = p2 if side == 1 else p1
    pieces = friendly
    moves = []

    while pieces:
        lsb = pieces & -pieces
        f = lsb.bit_length() - 1
        pieces ^= lsb

        fr = f >> 3
        fc = f & 7

        for dr, dc, axis in DIRECTIONS:
            distance = (occupied & LINE_MASKS[axis][f]).bit_count()
            tr = fr + dr * distance
            tc = fc + dc * distance

            if tr < 0 or tr > 7 or tc < 0 or tc > 7:
                continue

            t = tr * 8 + tc
            target_bit = 1 << t

            if friendly & target_bit:
                continue

            if BETWEEN[f][t] & enemy:
                continue

            moves.append((f << 6) | t)

    return moves


def _apply_move(p1, p2, side, move):
    f = move >> 6
    t = move & 63
    from_bit = 1 << f
    to_bit = 1 << t

    if side == 1:
        captured = bool(p2 & to_bit)
        p1 = (p1 & ~from_bit) | to_bit
        p2 &= ~to_bit
    else:
        captured = bool(p1 & to_bit)
        p2 = (p2 & ~from_bit) | to_bit
        p1 &= ~to_bit

    return p1, p2, captured


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def _quality(bits):
    count = bits.bit_count()
    if count == 0:
        return -50_000, 99

    sizes = _component_sizes(bits)
    components = len(sizes)
    largest = max(sizes)
    sum_squares = sum(size * size for size in sizes)
    isolated = sum(1 for size in sizes if size == 1)

    temp = bits
    row_sum = 0
    col_sum = 0
    min_r = 7
    max_r = 0
    min_c = 7
    max_c = 0
    adjacency_sum = 0
    linked = 0
    center_score = 0
    squares = []

    while temp:
        lsb = temp & -temp
        sq = lsb.bit_length() - 1
        temp ^= lsb

        r = sq >> 3
        c = sq & 7
        squares.append((r, c))

        row_sum += r
        col_sum += c
        min_r = min(min_r, r)
        max_r = max(max_r, r)
        min_c = min(min_c, c)
        max_c = max(max_c, c)

        adjacent = (NEIGHBORS[sq] & bits).bit_count()
        adjacency_sum += adjacent
        if adjacent:
            linked += 1

        center_score += CENTER_VALUE[sq]

    adjacency_pairs = adjacency_sum // 2

    # Integer Manhattan dispersion around the center of mass.
    dispersion_scaled = 0
    for r, c in squares:
        dispersion_scaled += abs(count * r - row_sum)
        dispersion_scaled += abs(count * c - col_sum)
    dispersion = dispersion_scaled // count

    span = (max_r - min_r) + (max_c - min_c)

    score = 0
    score -= 275 * (components - 1)
    score += 24 * largest
    score += 5 * sum_squares
    score += 10 * adjacency_pairs
    score += 8 * linked
    score -= 18 * isolated
    score -= 5 * dispersion
    score -= 7 * span
    score += 3 * center_score
    score += 4 * count

    return score, components


def _evaluate_details(p1, p2, side):
    q1, components1 = _quality(p1)
    q2, components2 = _quality(p2)
    score = q1 - q2

    if side == -1:
        score = -score

    return score, components1, components2


def _has_immediate_win(p1, p2, side):
    own = p1 if side == 1 else p2

    for move in _generate_moves(p1, p2, side):
        f = move >> 6
        t = move & 63
        new_own = (own & ~(1 << f)) | (1 << t)
        if _connected(new_own):
            return True

    return False


# ---------------------------------------------------------------------------
# Move ordering
# ---------------------------------------------------------------------------

def _move_order_score(move, p1, p2, side, tt_move, ply):
    if move == tt_move:
        return 20_000_000

    score = 0
    history_index = 0 if side == 1 else 1
    score += _HISTORY[history_index][move]

    if ply < len(_KILLERS):
        if move == _KILLERS[ply][0]:
            score += 800_000
        elif move == _KILLERS[ply][1]:
            score += 500_000

    f = move >> 6
    t = move & 63
    from_bit = 1 << f
    to_bit = 1 << t

    friendly = p1 if side == 1 else p2
    enemy = p2 if side == 1 else p1

    friendly_after = (friendly & ~from_bit) | to_bit
    source_neighbors = (NEIGHBORS[f] & friendly).bit_count()
    target_neighbors = (NEIGHBORS[t] & friendly_after).bit_count()

    score += 90 * (target_neighbors - source_neighbors)
    score += 12 * (CENTER_VALUE[t] - CENTER_VALUE[f])

    if enemy & to_bit:
        score += 35

    return score


def _order_moves(moves, p1, p2, side, tt_move, ply):
    moves.sort(
        key=lambda move: _move_order_score(
            move, p1, p2, side, tt_move, ply
        ),
        reverse=True,
    )


# ---------------------------------------------------------------------------
# Alpha-beta negamax
# ---------------------------------------------------------------------------

def _negamax(p1, p2, side, depth, alpha, beta, ply):
    global _NODES

    _NODES += 1
    if (_NODES & 127) == 0 and time.perf_counter() >= _DEADLINE:
        raise _SearchTimeout

    if depth == 0:
        value, components1, components2 = _evaluate_details(p1, p2, side)
        current_components = components1 if side == 1 else components2

        # A one-ply tactical check reduces horizon blunders near a win.
        if current_components == 2 and _has_immediate_win(p1, p2, side):
            return MATE - ply - 1

        return value

    key = (p1, p2, side)
    alpha_original = alpha
    beta_original = beta
    tt_move = -1

    entry = _TT.get(key)
    if entry is not None:
        stored_depth, stored_value, flag, tt_move = entry

        if stored_depth >= depth:
            if flag == 0:
                return stored_value
            if flag == 1:
                alpha = max(alpha, stored_value)
            else:
                beta = min(beta, stored_value)

            if alpha >= beta:
                return stored_value

    moves = _generate_moves(p1, p2, side)
    if not moves:
        return -MATE + ply

    _order_moves(moves, p1, p2, side, tt_move, ply)

    best_value = -INF
    best_move = moves[0]

    for move in moves:
        new_p1, new_p2, captured = _apply_move(p1, p2, side, move)
        moved_bits = new_p1 if side == 1 else new_p2
        opponent_bits = new_p2 if side == 1 else new_p1

        # If both become connected, the moving player wins.
        if _connected(moved_bits):
            value = MATE - ply
        elif captured and _connected(opponent_bits):
            value = -MATE + ply
        else:
            value = -_negamax(
                new_p1,
                new_p2,
                -side,
                depth - 1,
                -beta,
                -alpha,
                ply + 1,
            )

        if value > best_value:
            best_value = value
            best_move = move

        if value > alpha:
            alpha = value

        if alpha >= beta:
            history_index = 0 if side == 1 else 1
            _HISTORY[history_index][move] += depth * depth

            if ply < len(_KILLERS):
                if move != _KILLERS[ply][0]:
                    _KILLERS[ply][1] = _KILLERS[ply][0]
                    _KILLERS[ply][0] = move
            break

    if best_value <= alpha_original:
        flag = 2  # Upper bound
    elif best_value >= beta_original:
        flag = 1  # Lower bound
    else:
        flag = 0  # Exact

    _TT[key] = (depth, best_value, flag, best_move)
    return best_value


# ---------------------------------------------------------------------------
# Required API
# ---------------------------------------------------------------------------

def policy(board) -> str:
    global _DEADLINE, _NODES, _TT, _HISTORY, _KILLERS

    start = time.perf_counter()
    _DEADLINE = start + 0.94
    _NODES = 0
    _TT = {}
    _HISTORY = [[0] * 4096 for _ in range(2)]
    _KILLERS = [[-1, -1] for _ in range(32)]

    p1 = 0
    p2 = 0

    for r in range(8):
        for c in range(8):
            value = int(board[r][c])
            bit = 1 << (r * 8 + c)
            if value == 1:
                p1 |= bit
            elif value == -1:
                p2 |= bit

    legal_moves = _generate_moves(p1, p2, 1)

    # A legal move cannot be produced if the supplied position itself has
    # no legal moves. Arena positions are expected to be playable.
    if not legal_moves:
        return "0,0:0,0"

    best_move = legal_moves[0]
    best_static = -INF

    # Establish a tactically safe fallback and immediately take a win.
    for move in legal_moves:
        new_p1, new_p2, captured = _apply_move(p1, p2, 1, move)

        if _connected(new_p1):
            f = move >> 6
            t = move & 63
            return f"{f // 8},{f % 8}:{t // 8},{t % 8}"

        if captured and _connected(new_p2):
            value = -MATE
        else:
            value, _, _ = _evaluate_details(new_p1, new_p2, 1)

        if value > best_static:
            best_static = value
            best_move = move

    # Iterative deepening always retains the best result from the last
    # completely searched depth.
    for depth in range(1, 10):
        if time.perf_counter() >= _DEADLINE:
            break

        try:
            value = _negamax(p1, p2, 1, depth, -INF, INF, 0)
        except _SearchTimeout:
            break

        root_entry = _TT.get((p1, p2, 1))
        if root_entry is not None and root_entry[3] in legal_moves:
            best_move = root_entry[3]

        # A positive mate score is a fully proven forced win.
        if value > MATE // 2:
            break

    f = best_move >> 6
    t = best_move & 63
    return f"{f // 8},{f % 8}:{t // 8},{t % 8}"

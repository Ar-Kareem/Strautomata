
import time

# ---------- Precomputation ----------

def _idx(i: int, j: int, k: int) -> int:
    return i * 9 + j * 3 + k


def _coord(idx: int) -> tuple[int, int, int]:
    return (idx // 9, (idx % 9) // 3, idx % 3)


def _generate_line_masks() -> tuple[int, ...]:
    seen = set()
    masks = []

    def add_line(cells):
        mask = 0
        for c in cells:
            mask |= 1 << c
        if mask not in seen:
            seen.add(mask)
            masks.append(mask)

    # Axis-aligned lines
    for j in range(3):
        for k in range(3):
            add_line([_idx(i, j, k) for i in range(3)])
    for i in range(3):
        for k in range(3):
            add_line([_idx(i, j, k) for j in range(3)])
    for i in range(3):
        for j in range(3):
            add_line([_idx(i, j, k) for k in range(3)])

    # Plane diagonals: xy planes
    for k in range(3):
        add_line([_idx(d, d, k) for d in range(3)])
        add_line([_idx(d, 2 - d, k) for d in range(3)])

    # Plane diagonals: xz planes
    for j in range(3):
        add_line([_idx(d, j, d) for d in range(3)])
        add_line([_idx(d, j, 2 - d) for d in range(3)])

    # Plane diagonals: yz planes
    for i in range(3):
        add_line([_idx(i, d, d) for d in range(3)])
        add_line([_idx(i, d, 2 - d) for d in range(3)])

    # Space diagonals
    add_line([_idx(d, d, d) for d in range(3)])
    add_line([_idx(d, d, 2 - d) for d in range(3)])
    add_line([_idx(d, 2 - d, d) for d in range(3)])
    add_line([_idx(d, 2 - d, 2 - d) for d in range(3)])

    return tuple(masks)


LINE_MASKS = _generate_line_masks()
assert len(LINE_MASKS) == 49

CELL_TO_LINE_MASKS = [[] for _ in range(27)]
for mask in LINE_MASKS:
    m = mask
    while m:
        bit = m & -m
        idx = bit.bit_length() - 1
        CELL_TO_LINE_MASKS[idx].append(mask)
        m ^= bit
CELL_TO_LINE_MASKS = tuple(tuple(x) for x in CELL_TO_LINE_MASKS)

CELL_WEIGHTS = tuple(len(CELL_TO_LINE_MASKS[i]) for i in range(27))
FULL_MASK = (1 << 27) - 1
CENTER_IDX = _idx(1, 1, 1)
CORNERS = (0, 2, 6, 8, 18, 20, 24, 26)

LINE_SCORES = (0, 4, 80, 0)
MATE = 1_000_000
INF = 10_000_000

# Transposition table persists across calls; capped to avoid unbounded growth.
_TT: dict[tuple[int, int, int], tuple[int, int, int | None]] = {}
_deadline = 0.0
_nodes = 0


# ---------- Bitboard helpers ----------

def _best_bit(bits: int, preferred: int | None = None) -> int:
    if preferred is not None and ((bits >> preferred) & 1):
        return preferred
    best_idx = 0
    best_score = -1
    b = bits
    while b:
        bit = b & -b
        idx = bit.bit_length() - 1
        score = CELL_WEIGHTS[idx]
        if score > best_score:
            best_score = score
            best_idx = idx
        b ^= bit
    return best_idx


def _immediate_win_bits(cur_bits: int, other_bits: int) -> int:
    occ = cur_bits | other_bits
    wins = 0
    for mask in LINE_MASKS:
        if other_bits & mask:
            continue
        if (cur_bits & mask).bit_count() == 2:
            wins |= mask & ~occ
    return wins & FULL_MASK


def _evaluate(my_bits: int, opp_bits: int, player: int) -> int:
    occ = my_bits | opp_bits
    score = 0
    my_threat_bits = 0
    opp_threat_bits = 0

    for mask in LINE_MASKS:
        my_on = my_bits & mask
        opp_on = opp_bits & mask
        if my_on and opp_on:
            continue
        if my_on:
            c = my_on.bit_count()
            score += LINE_SCORES[c]
            if c == 2:
                my_threat_bits |= mask & ~occ
        elif opp_on:
            c = opp_on.bit_count()
            score -= LINE_SCORES[c]
            if c == 2:
                opp_threat_bits |= mask & ~occ

    my_threats = my_threat_bits.bit_count()
    opp_threats = opp_threat_bits.bit_count()

    # Base threat difference
    score += 1200 * (my_threats - opp_threats)

    # Side-to-move urgency
    if player == 1:
        score += 2400 * my_threats
        score -= 600 * opp_threats
    else:
        score += 600 * my_threats
        score -= 2400 * opp_threats

    # Fork-like bonus/penalty
    if my_threats >= 2:
        score += 1800
    if opp_threats >= 2:
        score -= 1800

    return score


def _ordered_moves(my_bits: int, opp_bits: int, player: int, depth: int, tt_move: int | None = None) -> list[int]:
    occupied = my_bits | opp_bits
    empties_bits = FULL_MASK ^ occupied

    if player == 1:
        own_bits, other_bits = my_bits, opp_bits
    else:
        own_bits, other_bits = opp_bits, my_bits

    own_win_bits = _immediate_win_bits(own_bits, other_bits) & empties_bits
    if own_win_bits:
        return [_best_bit(own_win_bits, tt_move)]

    opp_win_bits = _immediate_win_bits(other_bits, own_bits) & empties_bits
    candidate_bits = opp_win_bits if opp_win_bits else empties_bits

    scored = []
    b = candidate_bits
    while b:
        bit = b & -b
        idx = bit.bit_length() - 1
        s = CELL_WEIGHTS[idx] * 2

        if tt_move == idx:
            s += 1_000_000
        if bit & opp_win_bits:
            s += 300_000

        for mask in CELL_TO_LINE_MASKS[idx]:
            own_count = (own_bits & mask).bit_count()
            opp_count = (other_bits & mask).bit_count()

            if opp_count == 0:
                if own_count == 2:
                    s += 100_000
                elif own_count == 1:
                    s += 140
                else:
                    s += 8
            elif own_count == 0:
                if opp_count == 2:
                    s += 20_000
                elif opp_count == 1:
                    s += 50

        scored.append((s, idx))
        b ^= bit

    scored.sort(reverse=True)
    return [idx for _, idx in scored]


# ---------- Search ----------

def _alphabeta(my_bits: int, opp_bits: int, player: int, depth: int, alpha: int, beta: int, last_idx: int) -> int:
    global _nodes, _deadline, _TT

    _nodes += 1
    if (_nodes & 1023) == 0 and time.perf_counter() >= _deadline:
        raise TimeoutError

    # Check whether the previous move ended the game.
    if last_idx != -1:
        if player == -1:
            for mask in CELL_TO_LINE_MASKS[last_idx]:
                if (my_bits & mask) == mask:
                    return MATE + depth
        else:
            for mask in CELL_TO_LINE_MASKS[last_idx]:
                if (opp_bits & mask) == mask:
                    return -MATE - depth

    occupied = my_bits | opp_bits
    empties = 27 - occupied.bit_count()
    if empties == 0:
        return 0

    key = (my_bits, opp_bits, player)
    entry = _TT.get(key)
    tt_move = None
    if entry is not None:
        stored_depth, stored_value, stored_move = entry
        tt_move = stored_move
        if stored_depth >= depth:
            return stored_value

    if depth == 0:
        value = _evaluate(my_bits, opp_bits, player)
        if entry is None or entry[0] <= depth:
            _TT[key] = (depth, value, tt_move)
        return value

    moves = _ordered_moves(my_bits, opp_bits, player, depth, tt_move)
    if not moves:
        return 0

    best_move = moves[0]

    if player == 1:
        best = -INF
        for idx in moves:
            bit = 1 << idx
            new_my = my_bits | bit

            won = False
            for mask in CELL_TO_LINE_MASKS[idx]:
                if (new_my & mask) == mask:
                    score = MATE + depth
                    won = True
                    break
            if not won:
                score = _alphabeta(new_my, opp_bits, -1, depth - 1, alpha, beta, idx)

            if score > best:
                best = score
                best_move = idx
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

    else:
        best = INF
        for idx in moves:
            bit = 1 << idx
            new_opp = opp_bits | bit

            won = False
            for mask in CELL_TO_LINE_MASKS[idx]:
                if (new_opp & mask) == mask:
                    score = -MATE - depth
                    won = True
                    break
            if not won:
                score = _alphabeta(my_bits, new_opp, 1, depth - 1, alpha, beta, idx)

            if score < best:
                best = score
                best_move = idx
            if best < beta:
                beta = best
            if alpha >= beta:
                break

    if entry is None or entry[0] <= depth:
        _TT[key] = (depth, best, best_move)
    return best


def _search_root(my_bits: int, opp_bits: int, depth: int, hint_move: int | None = None) -> tuple[int, int | None]:
    key = (my_bits, opp_bits, 1)
    entry = _TT.get(key)
    if entry is not None and entry[0] >= depth:
        return entry[1], entry[2]

    tt_move = hint_move if hint_move is not None else (entry[2] if entry is not None else None)
    moves = _ordered_moves(my_bits, opp_bits, 1, depth, tt_move)
    if not moves:
        return 0, None

    alpha = -INF
    beta = INF
    best = -INF
    best_move = moves[0]

    for idx in moves:
        bit = 1 << idx
        new_my = my_bits | bit

        won = False
        for mask in CELL_TO_LINE_MASKS[idx]:
            if (new_my & mask) == mask:
                score = MATE + depth
                won = True
                break
        if not won:
            score = _alphabeta(new_my, opp_bits, -1, depth - 1, alpha, beta, idx)

        if score > best:
            best = score
            best_move = idx
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    _TT[key] = (depth, best, best_move)
    return best, best_move


# ---------- Public policy ----------

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    global _deadline, _nodes, _TT

    if len(_TT) > 300000:
        _TT.clear()

    my_bits = 0
    opp_bits = 0
    first_empty = None
    occupied = 0

    for i in range(3):
        for j in range(3):
            for k in range(3):
                idx = _idx(i, j, k)
                v = board[i][j][k]
                if v == 1:
                    my_bits |= 1 << idx
                    occupied += 1
                elif v == -1:
                    opp_bits |= 1 << idx
                    occupied += 1
                else:
                    if first_empty is None:
                        first_empty = idx

    if first_empty is None:
        return (0, 0, 0)

    occupied_bits = my_bits | opp_bits
    empties = 27 - occupied

    # Opening rules
    if occupied == 0 and ((occupied_bits >> CENTER_IDX) & 1) == 0:
        return (1, 1, 1)

    if my_bits == 0 and occupied == 1:
        if ((occupied_bits >> CENTER_IDX) & 1) == 0:
            return (1, 1, 1)
        for idx in CORNERS:
            if ((occupied_bits >> idx) & 1) == 0:
                return _coord(idx)

    # Immediate win
    wins = _immediate_win_bits(my_bits, opp_bits) & (FULL_MASK ^ occupied_bits)
    if wins:
        return _coord(_best_bit(wins))

    # Single forced block
    blocks = _immediate_win_bits(opp_bits, my_bits) & (FULL_MASK ^ occupied_bits)
    if blocks and blocks.bit_count() == 1:
        return _coord((blocks & -blocks).bit_length() - 1)

    # Safe fallback
    fallback_moves = _ordered_moves(my_bits, opp_bits, 1, 1, None)
    best_move = fallback_moves[0] if fallback_moves else first_empty

    # Iterative deepening
    _deadline = time.perf_counter() + 0.90
    _nodes = 0

    if empties <= 8:
        max_depth = empties
    elif empties <= 12:
        max_depth = 10
    else:
        max_depth = 8

    hint = best_move
    for depth in range(1, max_depth + 1):
        try:
            value, move = _search_root(my_bits, opp_bits, depth, hint)
            if move is not None:
                best_move = move
                hint = move
            if abs(value) >= MATE:
                break
        except TimeoutError:
            break

    # Final legality guard
    if ((occupied_bits >> best_move) & 1) != 0:
        best_move = first_empty

    return _coord(best_move)

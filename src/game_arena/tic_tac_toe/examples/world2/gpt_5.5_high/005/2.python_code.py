
import time
from array import array

# 4x4 Tic Tac Toe: rows, columns, and the two length-4 diagonals.
N = 4
SIZE = 1 << 16
FULL_MASK = SIZE - 1

WIN_SCORE = 1_000_000
INF = 10_000_000

TIME_LIMIT = 0.88  # keep a safety margin under the 1 second limit
TT_LIMIT = 500_000
WM_LIMIT = 800_000

_EXACT, _LOWER, _UPPER = 0, 1, 2

_TT = {}
_WM_CACHE = {}

_DEADLINE = 0.0
_NODES = 0


def _make_win_masks():
    masks = []

    # Rows
    for r in range(4):
        m = 0
        for c in range(4):
            m |= 1 << (4 * r + c)
        masks.append(m)

    # Columns
    for c in range(4):
        m = 0
        for r in range(4):
            m |= 1 << (4 * r + c)
        masks.append(m)

    # Main diagonal
    m = 0
    for i in range(4):
        m |= 1 << (4 * i + i)
    masks.append(m)

    # Anti-diagonal
    m = 0
    for i in range(4):
        m |= 1 << (4 * i + (3 - i))
    masks.append(m)

    return tuple(masks)


_WIN_MASKS = _make_win_masks()

# Positional values: cells on diagonals are more valuable; central diagonal cells
# get a small extra preference.
_POS = (
    7, 3, 3, 7,
    3, 8, 8, 3,
    3, 8, 8, 3,
    7, 3, 3, 7,
)

_LINE_VALUE = (0, 5, 40, 700, WIN_SCORE)
_ORDER_LINE = (0, 8, 90, 2500, 0)
_BLOCK_LINE = (0, 7, 80, 2200, 0)

_tmp_lines = [[] for _ in range(16)]
for _m in _WIN_MASKS:
    for _i in range(16):
        if _m & (1 << _i):
            _tmp_lines[_i].append(_m)
_LINES_BY_CELL = tuple(tuple(x) for x in _tmp_lines)


def _build_has_win():
    table = bytearray(SIZE)
    for bits in range(SIZE):
        for mask in _WIN_MASKS:
            if bits & mask == mask:
                table[bits] = 1
                break
    return table


def _build_pos_sum():
    arr = array("h", [0]) * SIZE
    for bits in range(1, SIZE):
        lsb = bits & -bits
        idx = lsb.bit_length() - 1
        arr[bits] = arr[bits ^ lsb] + _POS[idx]
    return arr


def _build_transforms():
    funcs = (
        lambda r, c: (r, c),
        lambda r, c: (c, 3 - r),
        lambda r, c: (3 - r, 3 - c),
        lambda r, c: (3 - c, r),
        lambda r, c: (r, 3 - c),
        lambda r, c: (3 - r, c),
        lambda r, c: (c, r),
        lambda r, c: (3 - c, 3 - r),
    )

    transforms = []
    seen = set()

    for f in funcs:
        mapping = [0] * 16
        for r in range(4):
            for c in range(4):
                nr, nc = f(r, c)
                mapping[4 * r + c] = 4 * nr + nc

        t = tuple(mapping)
        if t in seen:
            continue
        seen.add(t)

        mapped_bits = [1 << mapping[i] for i in range(16)]
        arr = array("H", [0]) * SIZE
        for bits in range(1, SIZE):
            lsb = bits & -bits
            idx = lsb.bit_length() - 1
            arr[bits] = arr[bits ^ lsb] | mapped_bits[idx]
        transforms.append(arr)

    return tuple(transforms)


_HAS_WIN = _build_has_win()
_POS_SUM = _build_pos_sum()
_TRANSFORMS = _build_transforms()


def _has_win(bits: int) -> bool:
    return bool(_HAS_WIN[bits])


def _canonical(player: int, other: int) -> tuple[int, int]:
    best_p, best_o = player, other
    for arr in _TRANSFORMS[1:]:
        p = arr[player]
        o = arr[other]
        if (p, o) < (best_p, best_o):
            best_p, best_o = p, o
    return best_p, best_o


def _winning_moves(player: int, other: int, empties: int) -> int:
    """Empty cells where 'player' can complete a line immediately."""
    key = (player << 16) | other
    cached = _WM_CACHE.get(key)
    if cached is not None:
        return cached

    result = 0
    for mask in _WIN_MASKS:
        if mask & other:
            continue
        missing = mask & empties
        if missing and (missing & (missing - 1)) == 0:
            if (player & mask).bit_count() == 3:
                result |= missing

    if len(_WM_CACHE) < WM_LIMIT:
        _WM_CACHE[key] = result
    return result


def _static_eval(player: int, other: int, empties: int) -> int:
    """Heuristic from the perspective of 'player'."""
    score = int(_POS_SUM[player]) - int(_POS_SUM[other])

    p_twos = 0
    o_twos = 0

    for mask in _WIN_MASKS:
        p = (player & mask).bit_count()
        o = (other & mask).bit_count()

        if o == 0:
            score += _LINE_VALUE[p]
            if p == 2:
                p_twos += 1
        elif p == 0:
            score -= _LINE_VALUE[o]
            if o == 2:
                o_twos += 1

    # Multiple open 2-lines are often precursors to forks.
    score += 12 * p_twos * p_twos
    score -= 12 * o_twos * o_twos

    return score


def _fork_moves(player: int, other: int, empties: int) -> int:
    """Moves that create at least two distinct immediate winning threats."""
    result = 0
    mm = empties
    while mm:
        bit = mm & -mm
        new_player = player | bit
        rem = empties ^ bit
        if not _has_win(new_player):
            if _winning_moves(new_player, other, rem).bit_count() >= 2:
                result |= bit
        mm ^= bit
    return result


def _move_order_score(player: int, other: int, idx: int, empties: int) -> int:
    bit = 1 << idx
    new_player = player | bit
    rem = empties ^ bit

    score = _POS[idx] * 20

    own_threats = _winning_moves(new_player, other, rem).bit_count()
    opp_threats = _winning_moves(other, new_player, rem).bit_count()

    if own_threats >= 2:
        score += 50_000 + 5_000 * own_threats
    elif own_threats == 1:
        score += 3_000

    score -= 4_000 * opp_threats

    for mask in _LINES_BY_CELL[idx]:
        p_before = (player & mask).bit_count()
        o = (other & mask).bit_count()

        if o == 0:
            score += _ORDER_LINE[p_before + 1]
        elif p_before == 0:
            # This move blocks a pure opponent line.
            score += _BLOCK_LINE[o]

    return score


def _ordered_moves(player: int, other: int, moves_mask: int, empties: int) -> list[int]:
    if moves_mask and (moves_mask & (moves_mask - 1)) == 0:
        return [moves_mask.bit_length() - 1]

    scored = []
    mm = moves_mask
    while mm:
        bit = mm & -mm
        idx = bit.bit_length() - 1
        scored.append((_move_order_score(player, other, idx, empties), -idx, idx))
        mm ^= bit

    scored.sort(reverse=True)
    return [idx for _, __, idx in scored]


def _best_heuristic_bit(my: int, opp: int, empties: int, forced_mask: int | None = None) -> int:
    mask = empties if forced_mask is None else (empties & forced_mask)
    if mask == 0:
        mask = empties

    best_bit = mask & -mask
    best_score = -INF

    opponent_forks_now = _fork_moves(opp, my, empties)

    mm = mask
    while mm:
        bit = mm & -mm
        idx = bit.bit_length() - 1
        new_my = my | bit
        rem = empties ^ bit

        if _has_win(new_my):
            return bit

        score = _static_eval(new_my, opp, rem)
        score += _move_order_score(my, opp, idx, empties)

        own_threats = _winning_moves(new_my, opp, rem).bit_count()
        opp_threats = _winning_moves(opp, new_my, rem).bit_count()

        if own_threats >= 2:
            score += 60_000
        elif own_threats == 1:
            score += 4_000

        score -= 50_000 * opp_threats

        # Occupying an opponent fork square is usually urgent.
        if bit & opponent_forks_now:
            score += 25_000

        # Penalize allowing opponent fork replies.
        opp_forks_after = _fork_moves(opp, new_my, rem).bit_count()
        score -= 18_000 * opp_forks_after

        if score > best_score:
            best_score = score
            best_bit = bit

        mm ^= bit

    return best_bit


def _check_time():
    if time.perf_counter() > _DEADLINE:
        raise TimeoutError


def _search(player: int, other: int, empties: int, depth: int, alpha: int, beta: int) -> int:
    """Negamax search from the perspective of 'player' to move."""
    global _NODES

    _NODES += 1
    if (_NODES & 1023) == 0:
        _check_time()

    ecount = empties.bit_count()

    if _has_win(other):
        return -WIN_SCORE - ecount
    if _has_win(player):
        return WIN_SCORE + ecount
    if empties == 0:
        return 0

    # Tactical cutoffs/extensions.
    wins = _winning_moves(player, other, empties)
    if wins:
        return WIN_SCORE + ecount

    opp_wins = _winning_moves(other, player, empties)
    if opp_wins:
        # Multiple distinct opponent winning cells cannot all be blocked.
        if opp_wins & (opp_wins - 1):
            return -WIN_SCORE - ecount
        moves_mask = opp_wins  # forced block
    else:
        if depth <= 0:
            return _static_eval(player, other, empties)
        moves_mask = empties

    depth_key = depth if depth > 0 else 0
    cp, co = _canonical(player, other)
    key = (depth_key << 32) | (cp << 16) | co

    alpha_start = alpha
    beta_start = beta

    entry = _TT.get(key)
    if entry is not None:
        val, flag = entry
        if flag == _EXACT:
            return val
        if flag == _LOWER:
            alpha = max(alpha, val)
        elif flag == _UPPER:
            beta = min(beta, val)
        if alpha >= beta:
            return val

    best = -INF

    for idx in _ordered_moves(player, other, moves_mask, empties):
        bit = 1 << idx
        val = -_search(other, player | bit, empties ^ bit, depth - 1, -beta, -alpha)

        if val > best:
            best = val
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

    if best <= alpha_start:
        flag = _UPPER
    elif best >= beta_start:
        flag = _LOWER
    else:
        flag = _EXACT

    if len(_TT) < TT_LIMIT:
        _TT[key] = (best, flag)

    return best


def _search_best_bit(my: int, opp: int, empties: int, fallback_bit: int) -> int:
    best_bit = fallback_bit
    candidates = _ordered_moves(my, opp, empties, empties)

    fallback_idx = fallback_bit.bit_length() - 1
    if fallback_idx in candidates:
        candidates.remove(fallback_idx)
        candidates.insert(0, fallback_idx)

    last_scores = {}
    max_depth = empties.bit_count()

    for depth in range(1, max_depth + 1):
        if time.perf_counter() > _DEADLINE:
            break

        if last_scores:
            candidates.sort(key=lambda i: last_scores.get(i, -INF), reverse=True)

        best_idx = best_bit.bit_length() - 1
        if best_idx in candidates:
            candidates.remove(best_idx)
            candidates.insert(0, best_idx)

        scores = {}
        alpha = -INF
        beta = INF

        depth_best_bit = best_bit
        depth_best_score = -INF

        try:
            for idx in candidates:
                if time.perf_counter() > _DEADLINE:
                    raise TimeoutError

                bit = 1 << idx
                val = -_search(opp, my | bit, empties ^ bit, depth - 1, -beta, -alpha)
                scores[idx] = val

                if val > depth_best_score:
                    depth_best_score = val
                    depth_best_bit = bit

                if val > alpha:
                    alpha = val

            best_bit = depth_best_bit
            last_scores = scores

            # A forced win has been found.
            if depth_best_score >= WIN_SCORE:
                break

        except TimeoutError:
            break

    return best_bit


def _bit_to_move(bit: int) -> tuple[int, int]:
    idx = bit.bit_length() - 1
    return idx // 4, idx % 4


def policy(board: list[list[int]]) -> tuple[int, int]:
    global _DEADLINE, _NODES

    _DEADLINE = time.perf_counter() + TIME_LIMIT
    _NODES = 0

    if len(_TT) > TT_LIMIT:
        _TT.clear()
    if len(_WM_CACHE) > WM_LIMIT:
        _WM_CACHE.clear()

    my = 0
    opp = 0

    for r in range(4):
        for c in range(4):
            bit = 1 << (4 * r + c)
            v = board[r][c]
            if v == 1:
                my |= bit
            elif v == -1:
                opp |= bit

    empties = FULL_MASK & ~(my | opp)

    # No legal move exists; this should not happen in a live game.
    if empties == 0:
        return (0, 0)

    # 1. Win immediately if possible.
    my_wins = _winning_moves(my, opp, empties)
    if my_wins:
        bit = _best_heuristic_bit(my, opp, empties, my_wins)
        if bit & empties:
            return _bit_to_move(bit)

    # 2. Block opponent's immediate win.
    opp_wins = _winning_moves(opp, my, empties)
    if opp_wins:
        if opp_wins & (opp_wins - 1) == 0:
            return _bit_to_move(opp_wins)
        # Multiple threats means the position is probably lost, but still return
        # the best legal block.
        bit = _best_heuristic_bit(my, opp, empties, opp_wins)
        if bit & empties:
            return _bit_to_move(bit)

    # 3. If we can create an unavoidable fork, do it.
    forks = _fork_moves(my, opp, empties)
    if forks:
        bit = _best_heuristic_bit(my, opp, empties, forks)
        if bit & empties:
            return _bit_to_move(bit)

    # 4. Heuristic fallback, then improve it with iterative-deepening search.
    fallback = _best_heuristic_bit(my, opp, empties)

    try:
        bit = _search_best_bit(my, opp, empties, fallback)
    except Exception:
        bit = fallback

    # Final legality guard.
    if not (bit & empties):
        bit = empties & -empties

    return _bit_to_move(bit)

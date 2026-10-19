
import time

# 4x4 board bit numbering:
#  0  1  2  3
#  4  5  6  7
#  8  9 10 11
# 12 13 14 15

FULL_MASK = (1 << 16) - 1
WIN_SCORE = 10_000_000
INF_SCORE = 100_000_000

# Winning lines: 4 rows, 4 columns, 2 diagonals.
_win_masks = []

for r in range(4):
    m = 0
    for c in range(4):
        m |= 1 << (4 * r + c)
    _win_masks.append(m)

for c in range(4):
    m = 0
    for r in range(4):
        m |= 1 << (4 * r + c)
    _win_masks.append(m)

_win_masks.append((1 << 0) | (1 << 5) | (1 << 10) | (1 << 15))
_win_masks.append((1 << 3) | (1 << 6) | (1 << 9) | (1 << 12))

WIN_MASKS = tuple(_win_masks)

# Precompute whether any 16-bit mask already contains a winning line.
WIN_TABLE = bytearray(1 << 16)
for _mask in range(1 << 16):
    for _w in WIN_MASKS:
        if (_mask & _w) == _w:
            WIN_TABLE[_mask] = 1
            break

# Lines touching each cell, used for move ordering.
_cell_lines = [[] for _ in range(16)]
for i in range(16):
    b = 1 << i
    for w in WIN_MASKS:
        if w & b:
            _cell_lines[i].append(w)
CELL_LINES = tuple(tuple(x) for x in _cell_lines)

# Small positional preference. Diagonal cells are already favored by line count.
POSITION_BONUS = (
    3, 2, 2, 3,
    2, 5, 5, 2,
    2, 5, 5, 2,
    3, 2, 2, 3,
)
CELL_WEIGHTS = tuple(len(CELL_LINES[i]) * 100 + POSITION_BONUS[i] for i in range(16))

LINE_VALUE = (0, 10, 250, 20_000, WIN_SCORE)
ATTACK_VALUE = (0, 20, 300, 15_000, 1_000_000)
BLOCK_VALUE = (0, 15, 500, 20_000, 0)

EXACT, LOWER, UPPER = 0, 1, 2

# Persistent transposition table across calls.
_TT = {}


class _Timeout(Exception):
    pass


def _tuple_from_bit(bit: int) -> tuple[int, int]:
    i = bit.bit_length() - 1
    return (i // 4, i % 4)


def _winning_squares(player: int, blocker: int) -> int:
    """Empty squares where 'player' can move and immediately complete a line."""
    empty = FULL_MASK & ~(player | blocker)
    res = 0
    for w in WIN_MASKS:
        if (w & blocker) == 0 and (player & w).bit_count() == 3:
            res |= w & empty
    return res


def _static_eval(x: int, o: int, side: int) -> int:
    """Evaluation from the perspective of side-to-move."""
    sx = 0
    so = 0

    for w in WIN_MASKS:
        cx = (x & w).bit_count()
        co = (o & w).bit_count()

        if co == 0:
            sx += LINE_VALUE[cx]
        if cx == 0:
            so += LINE_VALUE[co]

    tx = _winning_squares(x, o).bit_count()
    to = _winning_squares(o, x).bit_count()

    if tx:
        sx += tx * 25_000
        if tx >= 2:
            sx += 250_000

    if to:
        so += to * 25_000
        if to >= 2:
            so += 250_000

    raw = sx - so
    return raw if side == 1 else -raw


def _move_score(x: int, o: int, side: int, bit: int) -> int:
    """Heuristic ordering score for a move."""
    idx = bit.bit_length() - 1

    if side == 1:
        my = x
        opp = o
        my2 = x | bit
    else:
        my = o
        opp = x
        my2 = o | bit

    score = CELL_WEIGHTS[idx]

    if WIN_TABLE[my2]:
        return 100_000_000 + score

    # Prefer blocking immediate opponent wins.
    opp_now = _winning_squares(opp, my)
    if bit & opp_now:
        score += 5_000_000

    # Prefer creating immediate threats, especially forks.
    my_threats = _winning_squares(my2, opp).bit_count()
    score += my_threats * 120_000
    if my_threats >= 2:
        score += 3_000_000

    # Avoid leaving opponent tactical chances.
    opp_after = _winning_squares(opp, my2).bit_count()
    score -= opp_after * 100_000
    if opp_after >= 2:
        score -= 3_000_000

    # Local line-building and line-blocking value.
    for w in CELL_LINES[idx]:
        cm = (my & w).bit_count()
        co = (opp & w).bit_count()

        if co == 0:
            score += ATTACK_VALUE[cm + 1]
        if cm == 0:
            score += BLOCK_VALUE[co]

    return score


def _ordered_moves(
    x: int,
    o: int,
    side: int,
    mask: int | None = None,
    preferred: int = 0,
) -> list[int]:
    legal = FULL_MASK & ~(x | o)
    if mask is not None:
        legal &= mask

    scored = []
    mm = legal
    while mm:
        bit = mm & -mm
        mm ^= bit

        s = _move_score(x, o, side, bit)
        if bit == preferred:
            s += 1_000_000_000

        scored.append((s, bit))

    scored.sort(reverse=True)
    return [b for _, b in scored]


def _store_tt(key, depth: int, value: int, flag: int, best_bit: int) -> None:
    old = _TT.get(key)
    if old is None or depth >= old[0]:
        _TT[key] = (depth, value, flag, best_bit)


def _search(
    x: int,
    o: int,
    side: int,
    depth: int,
    alpha: int,
    beta: int,
    deadline: float,
    nodes: list[int],
) -> int:
    nodes[0] += 1
    if (nodes[0] & 2047) == 0 and time.perf_counter() > deadline:
        raise _Timeout()

    if WIN_TABLE[x]:
        return WIN_SCORE if side == 1 else -WIN_SCORE
    if WIN_TABLE[o]:
        return WIN_SCORE if side == -1 else -WIN_SCORE

    legal = FULL_MASK & ~(x | o)
    if legal == 0:
        return 0

    if side == 1:
        my = x
        opp = o
    else:
        my = o
        opp = x

    # If side-to-move can win immediately, this node is won.
    my_wins = _winning_squares(my, opp)
    if my_wins:
        return WIN_SCORE

    # If opponent has two distinct immediate wins, side-to-move cannot stop both.
    opp_wins = _winning_squares(opp, my)
    if opp_wins.bit_count() >= 2:
        return -WIN_SCORE

    if depth <= 0:
        return _static_eval(x, o, side)

    key = (x, o, side)
    entry = _TT.get(key)
    preferred = entry[3] if entry else 0

    alpha_orig = alpha
    beta_orig = beta

    if entry is not None and entry[0] >= depth:
        tt_depth, tt_value, tt_flag, tt_best = entry
        preferred = tt_best

        if tt_flag == EXACT:
            return tt_value
        if tt_flag == LOWER:
            alpha = max(alpha, tt_value)
        elif tt_flag == UPPER:
            beta = min(beta, tt_value)

        if alpha >= beta:
            return tt_value

    # If opponent has exactly one immediate win, the reply is forced.
    move_mask = opp_wins if opp_wins else legal

    # Tactical shortcut: creating two distinct immediate winning squares is forced.
    mm = move_mask
    while mm:
        bit = mm & -mm
        mm ^= bit

        my2 = my | bit
        if _winning_squares(my2, opp).bit_count() >= 2:
            value = WIN_SCORE - 1
            _store_tt(key, depth, value, EXACT, bit)
            return value

    best = -INF_SCORE
    best_bit = 0

    for bit in _ordered_moves(x, o, side, move_mask, preferred):
        if side == 1:
            nx = x | bit
            no = o
        else:
            nx = x
            no = o | bit

        value = -_search(nx, no, -side, depth - 1, -beta, -alpha, deadline, nodes)

        if value > best:
            best = value
            best_bit = bit

        if value > alpha:
            alpha = value

        if alpha >= beta:
            break

    if best <= alpha_orig:
        flag = UPPER
    elif best >= beta_orig:
        flag = LOWER
    else:
        flag = EXACT

    _store_tt(key, depth, best, flag, best_bit)
    return best


def _search_root(x: int, o: int, deadline: float) -> int:
    legal = FULL_MASK & ~(x | o)
    moves = _ordered_moves(x, o, 1, legal)

    if not moves:
        return 0

    best_bit = moves[0]
    nodes = [0]
    max_depth = legal.bit_count()

    for depth in range(1, max_depth + 1):
        if time.perf_counter() > deadline:
            break

        try:
            alpha = -INF_SCORE
            beta = INF_SCORE
            depth_best = best_bit
            depth_best_value = -INF_SCORE

            root_moves = _ordered_moves(x, o, 1, legal, best_bit)

            for bit in root_moves:
                if time.perf_counter() > deadline:
                    raise _Timeout()

                value = -_search(x | bit, o, -1, depth - 1, -beta, -alpha, deadline, nodes)

                if value > depth_best_value:
                    depth_best_value = value
                    depth_best = bit

                if value > alpha:
                    alpha = value

            best_bit = depth_best

            if depth_best_value >= WIN_SCORE - 10:
                break

        except _Timeout:
            break

    return best_bit


def _fallback_move(board) -> tuple[int, int]:
    try:
        for r in range(4):
            for c in range(4):
                if board[r][c] == 0:
                    return (r, c)
    except Exception:
        pass
    return (0, 0)


def policy(board: list[list[int]]) -> tuple[int, int]:
    try:
        x = 0
        o = 0

        for r in range(4):
            for c in range(4):
                bit = 1 << (4 * r + c)
                v = board[r][c]

                if v == 1:
                    x |= bit
                elif v == -1:
                    o |= bit

        legal = FULL_MASK & ~(x | o)
        if legal == 0:
            return (0, 0)

        # Keep memory bounded across many games.
        if len(_TT) > 200_000:
            _TT.clear()

        # If somehow called after a finished game, still return a legal move.
        if WIN_TABLE[x] or WIN_TABLE[o]:
            return _tuple_from_bit(legal & -legal)

        # Strong opening: choose a diagonal central cell.
        if legal == FULL_MASK:
            return (1, 1)

        ordered = _ordered_moves(x, o, 1, legal)

        # 1. Win immediately if possible.
        for bit in ordered:
            if WIN_TABLE[x | bit]:
                return _tuple_from_bit(bit)

        # 2. Block opponent's immediate win.
        opp_wins = _winning_squares(o, x) & legal
        if opp_wins:
            block_moves = _ordered_moves(x, o, 1, opp_wins)
            return _tuple_from_bit(block_moves[0])

        # 3. Play an immediate fork if available.
        for bit in ordered:
            if _winning_squares(x | bit, o).bit_count() >= 2:
                return _tuple_from_bit(bit)

        if legal.bit_count() == 1:
            return _tuple_from_bit(legal & -legal)

        # 4. Otherwise search.
        deadline = time.perf_counter() + 0.88
        best_bit = _search_root(x, o, deadline)

        if not (best_bit & legal):
            best_bit = legal & -legal

        return _tuple_from_bit(best_bit)

    except Exception:
        return _fallback_move(board)

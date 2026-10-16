
from __future__ import annotations

from time import perf_counter


def _idx(i: int, j: int, k: int) -> int:
    return i * 9 + j * 3 + k


# Precompute the 49 winning lines in 3x3x3 tic tac toe.
_LINES: list[tuple[int, int, int]] = []

# Axis-aligned lines
for j in range(3):
    for k in range(3):
        _LINES.append((_idx(0, j, k), _idx(1, j, k), _idx(2, j, k)))  # i-axis
for i in range(3):
    for k in range(3):
        _LINES.append((_idx(i, 0, k), _idx(i, 1, k), _idx(i, 2, k)))  # j-axis
for i in range(3):
    for j in range(3):
        _LINES.append((_idx(i, j, 0), _idx(i, j, 1), _idx(i, j, 2)))  # k-axis

# Plane diagonals
for k in range(3):  # ij planes
    _LINES.append((_idx(0, 0, k), _idx(1, 1, k), _idx(2, 2, k)))
    _LINES.append((_idx(0, 2, k), _idx(1, 1, k), _idx(2, 0, k)))

for j in range(3):  # ik planes
    _LINES.append((_idx(0, j, 0), _idx(1, j, 1), _idx(2, j, 2)))
    _LINES.append((_idx(0, j, 2), _idx(1, j, 1), _idx(2, j, 0)))

for i in range(3):  # jk planes
    _LINES.append((_idx(i, 0, 0), _idx(i, 1, 1), _idx(i, 2, 2)))
    _LINES.append((_idx(i, 0, 2), _idx(i, 1, 1), _idx(i, 2, 0)))

# Space diagonals
_LINES.append((_idx(0, 0, 0), _idx(1, 1, 1), _idx(2, 2, 2)))
_LINES.append((_idx(0, 0, 2), _idx(1, 1, 1), _idx(2, 2, 0)))
_LINES.append((_idx(0, 2, 0), _idx(1, 1, 1), _idx(2, 0, 2)))
_LINES.append((_idx(0, 2, 2), _idx(1, 1, 1), _idx(2, 0, 0)))

assert len(_LINES) == 49

LINE_MASKS: tuple[int, ...] = tuple(
    (1 << a) | (1 << b) | (1 << c) for (a, b, c) in _LINES
)

_cell_to_masks: list[list[int]] = [[] for _ in range(27)]
for mask, line in zip(LINE_MASKS, _LINES):
    for sq in line:
        _cell_to_masks[sq].append(mask)

CELL_TO_MASKS: tuple[tuple[int, ...], ...] = tuple(tuple(v) for v in _cell_to_masks)
CELL_WEIGHTS: tuple[int, ...] = tuple(len(v) for v in CELL_TO_MASKS)

FULL_MASK = (1 << 27) - 1
CENTER_INDEX = _idx(1, 1, 1)
CORNER_INDICES = (
    _idx(0, 0, 0), _idx(0, 0, 2), _idx(0, 2, 0), _idx(0, 2, 2),
    _idx(2, 0, 0), _idx(2, 0, 2), _idx(2, 2, 0), _idx(2, 2, 2),
)

WIN_SCORE = 10_000_000
INF = 10**18
TIME_LIMIT = 0.88

EXACT = 0
LOWER = 1
UPPER = 2

# Heuristic line values: open 1-in-line and 2-in-line.
LINE_VALUES = (0, 2, 24, 5000)


def _iter_bits(mask: int):
    while mask:
        b = mask & -mask
        yield b.bit_length() - 1
        mask ^= b


def _single_index(mask: int) -> int:
    return (mask & -mask).bit_length() - 1


def _coord(move: int) -> tuple[int, int, int]:
    return move // 9, (move % 9) // 3, move % 3


def _move_wins(player_bits: int, move: int) -> bool:
    bit = 1 << move
    if not (player_bits & bit):
        return False
    for mask in CELL_TO_MASKS[move]:
        if (player_bits & mask) == mask:
            return True
    return False


def _winning_moves(me_bits: int, opp_bits: int) -> int:
    empty = FULL_MASK ^ (me_bits | opp_bits)
    wins = 0
    for mask in LINE_MASKS:
        if mask & opp_bits:
            continue
        if (me_bits & mask).bit_count() == 2:
            wins |= (mask & empty)
    return wins


def _static_eval(x_bits: int, o_bits: int) -> int:
    empty = FULL_MASK ^ (x_bits | o_bits)
    score = 0
    x_win_cells = 0
    o_win_cells = 0

    for mask in LINE_MASKS:
        xm = x_bits & mask
        om = o_bits & mask
        if xm and om:
            continue
        if xm:
            c = xm.bit_count()
            score += LINE_VALUES[c]
            if c == 2:
                x_win_cells |= (mask & empty)
        elif om:
            c = om.bit_count()
            score -= LINE_VALUES[c]
            if c == 2:
                o_win_cells |= (mask & empty)

    xw = x_win_cells.bit_count()
    ow = o_win_cells.bit_count()

    # Distinct next-move winning cells matter a lot.
    score += 120 * xw + 180 * max(0, xw - 1)
    score -= 140 * ow + 200 * max(0, ow - 1)

    return score


def _move_order_score(move: int, x_bits: int, o_bits: int, player: int, opp_win_cells: int) -> int:
    me_bits, them_bits = (x_bits, o_bits) if player == 1 else (o_bits, x_bits)
    bit = 1 << move

    score = CELL_WEIGHTS[move] * 4

    if bit & opp_win_cells:
        score += 500  # blocking urgency

    if _move_wins(me_bits | bit, move):
        score += 100_000

    for mask in CELL_TO_MASKS[move]:
        others = mask ^ bit
        me = (others & me_bits).bit_count()
        them = (others & them_bits).bit_count()

        if them == 0:
            score += (0, 6, 35)[me]
        elif me == 0:
            score += (0, 3, 24)[them]

    return score


def _ordered_moves(x_bits: int, o_bits: int, player: int, tt_move: int = -1) -> list[int]:
    occupied = x_bits | o_bits
    empty = FULL_MASK ^ occupied
    me_bits, them_bits = (x_bits, o_bits) if player == 1 else (o_bits, x_bits)
    opp_win_cells = _winning_moves(them_bits, me_bits)

    scored: list[tuple[int, int]] = []

    if tt_move >= 0 and (empty & (1 << tt_move)):
        scored.append((10**15, tt_move))
        empty ^= (1 << tt_move)

    while empty:
        b = empty & -empty
        m = b.bit_length() - 1
        scored.append((_move_order_score(m, x_bits, o_bits, player, opp_win_cells), m))
        empty ^= b

    scored.sort(reverse=True)
    return [m for _, m in scored]


def _best_from_mask(mask: int, x_bits: int, o_bits: int, player: int) -> int:
    if mask == 0:
        mask = FULL_MASK ^ (x_bits | o_bits)
    if mask & (mask - 1) == 0:
        return _single_index(mask)

    me_bits, them_bits = (x_bits, o_bits) if player == 1 else (o_bits, x_bits)
    opp_win_cells = _winning_moves(them_bits, me_bits)

    best_move = _single_index(mask)
    best_score = -INF
    for m in _iter_bits(mask):
        s = _move_order_score(m, x_bits, o_bits, player, opp_win_cells)
        if s > best_score:
            best_score = s
            best_move = m
    return best_move


def _first_legal(board) -> tuple[int, int, int]:
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    return (i, j, k)
    return (0, 0, 0)


def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    try:
        x_bits = 0
        o_bits = 0

        for i in range(3):
            for j in range(3):
                row = board[i][j]
                for k in range(3):
                    v = row[k]
                    sq = _idx(i, j, k)
                    if v == 1:
                        x_bits |= (1 << sq)
                    elif v == -1:
                        o_bits |= (1 << sq)

        legal_mask = FULL_MASK ^ (x_bits | o_bits)
        if legal_mask == 0:
            return _first_legal(board)
        if legal_mask & (legal_mask - 1) == 0:
            return _coord(_single_index(legal_mask))

        marks_played = 27 - legal_mask.bit_count()

        # Opening book: center first; if opponent took center, take a corner.
        if marks_played == 0 and (legal_mask & (1 << CENTER_INDEX)):
            return _coord(CENTER_INDEX)
        if marks_played == 1:
            if legal_mask & (1 << CENTER_INDEX):
                return _coord(CENTER_INDEX)
            for c in CORNER_INDICES:
                if legal_mask & (1 << c):
                    return _coord(c)

        # 1) Immediate win
        our_wins = _winning_moves(x_bits, o_bits)
        if our_wins:
            return _coord(_best_from_mask(our_wins, x_bits, o_bits, 1))

        # 2) Immediate block if needed
        opp_wins = _winning_moves(o_bits, x_bits)
        allowed_mask = legal_mask
        if opp_wins:
            if opp_wins & (opp_wins - 1) == 0:
                return _coord(_single_index(opp_wins))
            allowed_mask = opp_wins

        # 3) Safe fork: create 2+ distinct winning cells next turn,
        #    while not allowing an immediate opponent win now.
        if not opp_wins:
            best_fork_move = -1
            best_fork_key = None
            for m in _iter_bits(legal_mask):
                b = 1 << m
                nx = x_bits | b
                if _winning_moves(o_bits, nx):
                    continue
                our_next_wins = _winning_moves(nx, o_bits).bit_count()
                if our_next_wins >= 2:
                    key = (our_next_wins, _move_order_score(m, x_bits, o_bits, 1, 0))
                    if best_fork_key is None or key > best_fork_key:
                        best_fork_key = key
                        best_fork_move = m
            if best_fork_move != -1:
                return _coord(best_fork_move)

        # 4) Notice a unique dangerous opponent fork square and use it as fallback.
        danger_move = -1
        if not opp_wins:
            danger_cells = 0
            for m in _iter_bits(legal_mask):
                b = 1 << m
                no = o_bits | b
                # If we can immediately win after that, the fork is less urgent.
                if _winning_moves(x_bits, no):
                    continue
                if _winning_moves(no, x_bits).bit_count() >= 2:
                    danger_cells |= b
            if danger_cells and not (danger_cells & (danger_cells - 1)):
                danger_move = _single_index(danger_cells)

        fallback_move = danger_move if danger_move != -1 else _best_from_mask(allowed_mask, x_bits, o_bits, 1)

        end_time = perf_counter() + TIME_LIMIT
        tt: dict[tuple[int, int, int], tuple[int, int, int, int]] = {}
        nodes = 0

        class _SearchTimeout(Exception):
            pass

        def alphabeta(xb: int, ob: int, player: int, depth: int,
                      alpha: int, beta: int, last_move: int, ply: int) -> int:
            nonlocal nodes
            nodes += 1
            if (nodes & 1023) == 0 and perf_counter() >= end_time:
                raise _SearchTimeout

            # Last move was by -player. If it won, current player has lost.
            if last_move != -1:
                last_bits = xb if player == -1 else ob
                if _move_wins(last_bits, last_move):
                    return -WIN_SCORE + ply

            empty = FULL_MASK ^ (xb | ob)
            if empty == 0:
                return 0

            if depth <= 0:
                base = _static_eval(xb, ob)
                return base if player == 1 else -base

            alpha0, beta0 = alpha, beta
            key = (xb, ob, player)
            entry = tt.get(key)
            tt_move = -1

            if entry is not None:
                entry_depth, flag, entry_score, entry_best = entry
                tt_move = entry_best
                if entry_depth >= depth:
                    if flag == EXACT:
                        return entry_score
                    if flag == LOWER:
                        if entry_score > alpha:
                            alpha = entry_score
                    else:
                        if entry_score < beta:
                            beta = entry_score
                    if alpha >= beta:
                        return entry_score

            moves = _ordered_moves(xb, ob, player, tt_move)
            best_move = moves[0]
            value = -INF

            for m in moves:
                b = 1 << m
                if player == 1:
                    score = -alphabeta(xb | b, ob, -1, depth - 1, -beta, -alpha, m, ply + 1)
                else:
                    score = -alphabeta(xb, ob | b, 1, depth - 1, -beta, -alpha, m, ply + 1)

                if score > value:
                    value = score
                    best_move = m
                if value > alpha:
                    alpha = value
                if alpha >= beta:
                    break

            if value <= alpha0:
                flag = UPPER
            elif value >= beta0:
                flag = LOWER
            else:
                flag = EXACT
            tt[key] = (depth, flag, value, best_move)
            return value

        def root_search(depth: int, root_allowed_mask: int, first_hint: int) -> tuple[int, int]:
            moves = _ordered_moves(x_bits, o_bits, 1, first_hint)
            if root_allowed_mask != legal_mask:
                moves = [m for m in moves if root_allowed_mask & (1 << m)]
            if not moves:
                moves = list(_iter_bits(root_allowed_mask if root_allowed_mask else legal_mask))

            alpha = -INF
            beta = INF
            best_move = moves[0]
            best_score = -INF

            for m in moves:
                if perf_counter() >= end_time:
                    raise _SearchTimeout
                score = -alphabeta(x_bits | (1 << m), o_bits, -1, depth - 1, -beta, -alpha, m, 1)

                if score > best_score:
                    best_score = score
                    best_move = m
                if score > alpha:
                    alpha = score
                if alpha >= beta:
                    break

            return best_move, best_score

        best_move = fallback_move
        best_score = -INF

        # Iterative deepening until time runs out.
        max_depth = legal_mask.bit_count()
        for depth in range(1, max_depth + 1):
            if perf_counter() >= end_time:
                break
            try:
                mv, sc = root_search(depth, allowed_mask, best_move)
                best_move, best_score = mv, sc
                if abs(best_score) >= WIN_SCORE - 100:
                    break
            except _SearchTimeout:
                break

        return _coord(best_move)

    except Exception:
        return _first_legal(board)

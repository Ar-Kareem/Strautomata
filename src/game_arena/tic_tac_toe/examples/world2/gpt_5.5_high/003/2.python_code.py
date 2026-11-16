
from time import perf_counter

# 4x4 board bit index: bit = 1 << (row * 4 + col)
_FULL = 0xFFFF

# Winning lines: 4 rows, 4 columns, 2 long diagonals.
_WIN_MASKS = (
    0x000F, 0x00F0, 0x0F00, 0xF000,  # rows
    0x1111, 0x2222, 0x4444, 0x8888,  # columns
    0x8421, 0x1248,                  # diagonals
)

_MATE = 1_000_000
_INF = 10_000_000
_TIME_LIMIT = 0.82

_EXACT, _LOWER, _UPPER = 0, 1, 2

# Positional value: cells on a diagonal participate in 3 winning lines,
# other cells participate in 2.
_POS = (
    6, 4, 4, 6,
    4, 6, 6, 4,
    4, 6, 6, 4,
    6, 4, 4, 6,
)

_LINE_MY = (0, 8, 80, 1000, 0)
_LINE_OP = (0, 9, 90, 1100, 0)
_EXTEND_VAL = (0, 30, 300, 3000)
_BLOCK_VAL = (0, 35, 350, 3500)

# Fast win table.
_WIN_TABLE = [False] * (1 << 16)
for _bits in range(1 << 16):
    for _mask in _WIN_MASKS:
        if (_bits & _mask) == _mask:
            _WIN_TABLE[_bits] = True
            break

# Lines containing each cell, used for move ordering.
_CELL_LINES = [[] for _ in range(16)]
for _mask in _WIN_MASKS:
    for _i in range(16):
        if _mask & (1 << _i):
            _CELL_LINES[_i].append(_mask)
_CELL_LINES = tuple(tuple(x) for x in _CELL_LINES)

_TT = {}
_DEADLINE = 0.0
_NODES = 0


class _Timeout(Exception):
    pass


def _check_time():
    global _NODES
    _NODES += 1
    if (_NODES & 1023) == 0 and perf_counter() > _DEADLINE:
        raise _Timeout()


def _to_bits(board):
    mine = 0
    opp = 0
    for r in range(4):
        row = board[r]
        for c in range(4):
            v = row[c]
            bit = 1 << (r * 4 + c)
            if v == 1:
                mine |= bit
            elif v == -1:
                opp |= bit
    return mine, opp


def _bit_to_move(bit):
    i = bit.bit_length() - 1
    return (i // 4, i % 4)


def _first_empty(board):
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                return (r, c)
    return (0, 0)


def _winning_moves(mine, opp):
    """Empty cells where mine can complete a 4-in-a-row immediately."""
    res = 0
    for mask in _WIN_MASKS:
        if (mask & opp) == 0:
            missing = mask & ~mine
            if missing and (missing & (missing - 1)) == 0:
                res |= missing
    return res & ~mine & ~opp & _FULL


def _fork_moves(mine, opp, candidates=None):
    """
    Moves that create at least two distinct immediate winning moves,
    while not allowing the opponent to win immediately.
    """
    legal = _FULL & ~(mine | opp)
    moves = legal if candidates is None else (candidates & legal)
    res = 0

    while moves:
        bit = moves & -moves
        moves ^= bit
        nmine = mine | bit

        # Immediate wins are handled separately.
        if _WIN_TABLE[nmine]:
            continue

        # Do not make a fork if the opponent can win immediately.
        if _winning_moves(opp, nmine):
            continue

        if _winning_moves(nmine, opp).bit_count() >= 2:
            res |= bit

    return res


def _evaluate(mine, opp):
    """Static evaluation from the side-to-move perspective."""
    if _WIN_TABLE[mine]:
        return _MATE
    if _WIN_TABLE[opp]:
        return -_MATE

    score = 0

    m = mine
    while m:
        b = m & -m
        score += 4 * _POS[b.bit_length() - 1]
        m ^= b

    o = opp
    while o:
        b = o & -o
        score -= 4 * _POS[b.bit_length() - 1]
        o ^= b

    for mask in _WIN_MASKS:
        mc = (mine & mask).bit_count()
        oc = (opp & mask).bit_count()
        if oc == 0:
            score += _LINE_MY[mc]
        elif mc == 0:
            score -= _LINE_OP[oc]

    score += 250 * _winning_moves(mine, opp).bit_count()
    score -= 300 * _winning_moves(opp, mine).bit_count()

    return score


def _move_order_score(mine, opp, bit, opp_now):
    idx = bit.bit_length() - 1
    nmine = mine | bit

    if _WIN_TABLE[nmine]:
        return 10_000_000

    score = 10 * _POS[idx]

    # Blocking an immediate opponent win is urgent.
    if bit & opp_now:
        score += 1_000_000

    opp_after = _winning_moves(opp, nmine).bit_count()
    my_after = _winning_moves(nmine, opp).bit_count()

    # Avoid moves allowing immediate opponent wins.
    score -= 600_000 * opp_after

    # Prefer creating immediate threats, especially double threats.
    score += 500_000 * my_after
    if my_after >= 2 and opp_after == 0:
        score += 2_000_000

    # Prefer extending our open lines and blocking opponent open lines.
    for mask in _CELL_LINES[idx]:
        if (mask & opp) == 0:
            c = (mine & mask).bit_count()
            score += _EXTEND_VAL[c]
        if (mask & mine) == 0:
            c = (opp & mask).bit_count()
            score += _BLOCK_VAL[c]

    return score


def _ordered_moves(mine, opp, candidates, tt_move=0):
    legal = _FULL & ~(mine | opp)
    candidates &= legal
    if not candidates:
        return []

    opp_now = _winning_moves(opp, mine)
    items = []

    m = candidates
    while m:
        bit = m & -m
        m ^= bit
        sc = _move_order_score(mine, opp, bit, opp_now)
        if bit == tt_move:
            sc += 5_000_000
        items.append((sc, bit))

    items.sort(reverse=True)
    return [bit for _, bit in items]


def _best_heuristic_move(mine, opp, candidates=None):
    legal = _FULL & ~(mine | opp)
    if not legal:
        return 0
    if candidates is None:
        candidates = legal
    moves = _ordered_moves(mine, opp, candidates)
    if moves:
        return moves[0]
    return legal & -legal


def _negamax(mine, opp, depth, alpha, beta):
    _check_time()

    legal = _FULL & ~(mine | opp)
    empties = legal.bit_count()

    # The opponent is the player who just moved.
    if _WIN_TABLE[opp]:
        return -_MATE - empties
    if _WIN_TABLE[mine]:
        return _MATE + empties
    if legal == 0:
        return 0

    # Win immediately if possible.
    my_wins = _winning_moves(mine, opp)
    if my_wins:
        return _MATE + (empties - 1)

    # If opponent has immediate threats, we must block. Multiple distinct
    # threats are an unavoidable loss unless we already had a win.
    opp_wins = _winning_moves(opp, mine)
    forced = False
    if opp_wins:
        if opp_wins.bit_count() > 1:
            return -_MATE - max(0, empties - 2)
        moves_mask = opp_wins
        forced = True
    else:
        moves_mask = legal

    alpha_orig = alpha
    beta_orig = beta
    tt_move = 0

    if depth > 0:
        ent = _TT.get((mine, opp))
        if ent is not None:
            ent_depth, flag, val, mv = ent
            tt_move = mv
            if ent_depth >= depth:
                if flag == _EXACT:
                    return val
                if flag == _LOWER:
                    alpha = max(alpha, val)
                elif flag == _UPPER:
                    beta = min(beta, val)
                if alpha >= beta:
                    return val

    # Threat extension: a safe double-threat move is a forced win in 3 plies.
    if mine.bit_count() >= 3:
        forks = _fork_moves(mine, opp, moves_mask)
        if forks:
            score = _MATE + max(0, empties - 3)
            if depth > 0:
                _TT[(mine, opp)] = (depth, _EXACT, score, forks & -forks)
            return score

    # Quiescence: if there is a single immediate opponent threat, search
    # the forced block even beyond nominal depth.
    if depth <= 0 and not forced:
        return _evaluate(mine, opp)

    ordered = _ordered_moves(mine, opp, moves_mask, tt_move)
    if not ordered:
        return _evaluate(mine, opp)

    best_score = -_INF
    best_move = ordered[0]

    for bit in ordered:
        val = -_negamax(opp, mine | bit, depth - 1, -beta, -alpha)
        if val > best_score:
            best_score = val
            best_move = bit
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

    if depth > 0:
        if best_score <= alpha_orig:
            flag = _UPPER
        elif best_score >= beta_orig:
            flag = _LOWER
        else:
            flag = _EXACT
        _TT[(mine, opp)] = (depth, flag, best_score, best_move)

    return best_score


def _root_search(mine, opp, depth, fallback):
    _check_time()

    legal = _FULL & ~(mine | opp)
    if not legal:
        return fallback, 0

    opp_wins = _winning_moves(opp, mine)
    if opp_wins:
        moves_mask = opp_wins & legal
        if not moves_mask:
            moves_mask = legal
    else:
        moves_mask = legal

    tt_move = 0
    ent = _TT.get((mine, opp))
    if ent is not None:
        tt_move = ent[3]

    ordered = _ordered_moves(mine, opp, moves_mask, tt_move)
    if not ordered:
        return fallback, _evaluate(mine, opp)

    alpha = -_INF
    beta = _INF
    best_score = -_INF
    best_move = ordered[0]

    for bit in ordered:
        val = -_negamax(opp, mine | bit, depth - 1, -beta, -alpha)
        if val > best_score:
            best_score = val
            best_move = bit
        if val > alpha:
            alpha = val

    if depth > 0:
        _TT[(mine, opp)] = (depth, _EXACT, best_score, best_move)

    return best_move, best_score


def policy(board: list[list[int]]) -> tuple[int, int]:
    global _DEADLINE, _NODES

    try:
        mine, opp = _to_bits(board)
        legal = _FULL & ~(mine | opp)

        if not legal:
            return _first_empty(board)

        # Strong, symmetric opening: choose a high-participation diagonal cell.
        if mine == 0 and opp == 0:
            return (1, 1)

        # 1. Win immediately.
        my_wins = _winning_moves(mine, opp)
        if my_wins:
            bit = _best_heuristic_move(mine, opp, my_wins)
            move = _bit_to_move(bit)
            if board[move[0]][move[1]] == 0:
                return move

        # 2. Block immediate opponent win(s).
        opp_wins = _winning_moves(opp, mine)
        if opp_wins:
            bit = _best_heuristic_move(mine, opp, opp_wins)
            move = _bit_to_move(bit)
            if board[move[0]][move[1]] == 0:
                return move

        # 3. Take a safe forced fork if available.
        forks = _fork_moves(mine, opp)
        if forks:
            bit = _best_heuristic_move(mine, opp, forks)
            move = _bit_to_move(bit)
            if board[move[0]][move[1]] == 0:
                return move

        fallback = _best_heuristic_move(mine, opp, legal)
        if not fallback:
            return _first_empty(board)

        # Keep memory bounded across many games.
        if len(_TT) > 600_000:
            _TT.clear()

        _DEADLINE = perf_counter() + _TIME_LIMIT
        _NODES = 0

        best = fallback
        empties = legal.bit_count()

        # Iterative deepening: always retain the last completed legal move.
        for depth in range(1, empties + 1):
            try:
                bit, score = _root_search(mine, opp, depth, best)
                if bit & legal:
                    best = bit

                # Proven forced win, or exact full-depth result.
                if score > _MATE // 2 or depth >= empties:
                    break
            except _Timeout:
                break

        if not (best & legal):
            best = fallback
        if not (best & legal):
            best = legal & -legal

        move = _bit_to_move(best)
        if board[move[0]][move[1]] == 0:
            return move

        return _first_empty(board)

    except Exception:
        # Absolute safety fallback: never intentionally return an occupied cell.
        return _first_empty(board)

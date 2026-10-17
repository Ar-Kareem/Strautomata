
import time

# Board constants for a 6x7 Connect 4 board.
_WIDTH = 7
_HEIGHT = 6
_STRIDE = _HEIGHT + 1  # one sentinel bit per column

_ORDER = (3, 2, 4, 1, 5, 0, 6)  # center-first move order
_BIAS = (0, 1, 2, 3, 2, 1, 0)
_COL_WEIGHTS = (3, 4, 5, 7, 5, 4, 3)

_BOTTOM_MASKS = tuple(1 << (_STRIDE * c) for c in range(_WIDTH))
_TOP_MASKS = tuple(1 << (_STRIDE * c + _HEIGHT - 1) for c in range(_WIDTH))
_COLUMN_MASKS = tuple(((1 << _HEIGHT) - 1) << (_STRIDE * c) for c in range(_WIDTH))
_BOTTOM_ALL = sum(_BOTTOM_MASKS)
_BOARD_MASK = sum(_COLUMN_MASKS)

_INF = 10**9
_WIN_SCORE = 1_000_000

_EXACT = 0
_LOWER = 1
_UPPER = 2

_MY_WEIGHTS = (0, 2, 12, 80, 100000)
_OP_WEIGHTS = (0, 2, 14, 95, 100000)

_WIN_MASKS_LIST = []

# Horizontal windows.
for r in range(_HEIGHT):
    for c in range(_WIDTH - 3):
        m = 0
        for i in range(4):
            m |= 1 << ((_STRIDE * (c + i)) + r)
        _WIN_MASKS_LIST.append(m)

# Vertical windows.
for c in range(_WIDTH):
    for r in range(_HEIGHT - 3):
        m = 0
        for i in range(4):
            m |= 1 << ((_STRIDE * c) + r + i)
        _WIN_MASKS_LIST.append(m)

# Diagonal up-right windows.
for c in range(_WIDTH - 3):
    for r in range(_HEIGHT - 3):
        m = 0
        for i in range(4):
            m |= 1 << ((_STRIDE * (c + i)) + r + i)
        _WIN_MASKS_LIST.append(m)

# Diagonal down-right windows.
for c in range(_WIDTH - 3):
    for r in range(3, _HEIGHT):
        m = 0
        for i in range(4):
            m |= 1 << ((_STRIDE * (c + i)) + r - i)
        _WIN_MASKS_LIST.append(m)

_WIN_MASKS = tuple(_WIN_MASKS_LIST)

_DEADLINE = 0.0
_NODES = 0
_TT = {}


class _Timeout(Exception):
    pass


def _to_bitboards(board):
    """Convert 6x7 board into root-player and opponent bitboards."""
    p1 = 0
    p2 = 0
    for r in range(_HEIGHT):
        row = board[r]
        bit_row = _HEIGHT - 1 - r
        for c in range(_WIDTH):
            v = row[c]
            if v:
                bit = 1 << (_STRIDE * c + bit_row)
                if v > 0:
                    p1 |= bit
                else:
                    p2 |= bit
    return p1, p2, p1 | p2


def _has_won(pos):
    """Return True if bitboard pos contains four connected discs."""
    m = pos & (pos >> 1)
    if m & (m >> 2):
        return True

    m = pos & (pos >> _STRIDE)
    if m & (m >> (2 * _STRIDE)):
        return True

    m = pos & (pos >> (_HEIGHT))
    if m & (m >> (2 * _HEIGHT)):
        return True

    m = pos & (pos >> (_HEIGHT + 2))
    if m & (m >> (2 * (_HEIGHT + 2))):
        return True

    return False


def _play_bit(mask, col):
    """Bit where a disc lands in col."""
    return (mask + _BOTTOM_MASKS[col]) & _COLUMN_MASKS[col]


def _possible_moves(mask):
    """Bitboard of all currently playable landing cells."""
    return (mask + _BOTTOM_ALL) & _BOARD_MASK


def _compute_winning_position(position, mask):
    """
    Return empty cells that would complete a connect-four for position.
    Based on standard sentinel-column bitboard Connect 4 formulas.
    """
    # Vertical.
    r = (position << 1) & (position << 2) & (position << 3)

    # Horizontal.
    p = (position << _STRIDE) & (position << (2 * _STRIDE))
    r |= p & (position << (3 * _STRIDE))
    r |= p & (position >> _STRIDE)

    p = (position >> _STRIDE) & (position >> (2 * _STRIDE))
    r |= p & (position << _STRIDE)
    r |= p & (position >> (3 * _STRIDE))

    # Diagonal: shift 6.
    p = (position << _HEIGHT) & (position << (2 * _HEIGHT))
    r |= p & (position << (3 * _HEIGHT))
    r |= p & (position >> _HEIGHT)

    p = (position >> _HEIGHT) & (position >> (2 * _HEIGHT))
    r |= p & (position << _HEIGHT)
    r |= p & (position >> (3 * _HEIGHT))

    # Diagonal: shift 8.
    diag = _HEIGHT + 2
    p = (position << diag) & (position << (2 * diag))
    r |= p & (position << (3 * diag))
    r |= p & (position >> diag)

    p = (position >> diag) & (position >> (2 * diag))
    r |= p & (position << diag)
    r |= p & (position >> (3 * diag))

    return r & (_BOARD_MASK ^ mask)


def _winning_move_bits(position, mask):
    """Playable cells that win immediately for position."""
    return _compute_winning_position(position, mask) & _possible_moves(mask)


def _col_from_bits(bits):
    """Choose a center-preferred column from a nonzero move bitboard."""
    for c in _ORDER:
        if bits & _COLUMN_MASKS[c]:
            return c
    return -1


def _legal_moves(mask, first=-1):
    moves = []
    if 0 <= first < _WIDTH and not (mask & _TOP_MASKS[first]):
        moves.append(first)
    for c in _ORDER:
        if c != first and not (mask & _TOP_MASKS[c]):
            moves.append(c)
    return moves


def _evaluate(p1, p2, mask):
    """Static evaluation from the root/current player's perspective."""
    score = 0

    # Column/center control.
    for c in range(_WIDTH):
        cm = _COLUMN_MASKS[c]
        score += ((p1 & cm).bit_count() - (p2 & cm).bit_count()) * _COL_WEIGHTS[c] * 4

    # Immediate playable threats.
    w1 = _winning_move_bits(p1, mask)
    w2 = _winning_move_bits(p2, mask)
    n1 = w1.bit_count()
    n2 = w2.bit_count()

    if n1:
        score += 420 * n1
        if n1 > 1:
            score += 2600
    if n2:
        score -= 480 * n2
        if n2 > 1:
            score -= 3200

    # Potential four-cell windows.
    for m in _WIN_MASKS:
        a = (p1 & m).bit_count()
        b = (p2 & m).bit_count()

        if a and b:
            continue
        if a:
            score += _MY_WEIGHTS[a]
        elif b:
            score -= _OP_WEIGHTS[b]

    return score


def _fallback_move(p1, p2, mask):
    """Fast legal move if search times out or something unexpected happens."""
    legal = _legal_moves(mask)
    if not legal:
        return 0

    wins = _winning_move_bits(p1, mask)
    if wins:
        col = _col_from_bits(wins)
        if col in legal:
            return col

    opp_wins = _winning_move_bits(p2, mask)
    if opp_wins.bit_count() == 1:
        col = _col_from_bits(opp_wins)
        if col in legal:
            return col

    best = legal[0]
    best_score = -_INF

    for c in legal:
        bit = _play_bit(mask, c)
        if not bit:
            continue

        np1 = p1 | bit
        nmask = mask | bit

        if _has_won(np1):
            return c

        sc = _evaluate(np1, p2, nmask)

        # Strongly avoid moves that allow an immediate opponent win.
        reply = _winning_move_bits(p2, nmask)
        if reply:
            sc -= 200000 + 10000 * reply.bit_count()

        my_threats = _winning_move_bits(np1, nmask).bit_count()
        if my_threats > 1:
            sc += 5000

        sc += _BIAS[c]

        if sc > best_score:
            best_score = sc
            best = c

    return best


def _alphabeta(p1, p2, mask, turn, depth, alpha, beta, ply):
    """
    Minimax alpha-beta search.
    turn == 1 means root player to move.
    turn == -1 means opponent to move.
    """
    global _NODES

    _NODES += 1
    if (_NODES & 511) == 0 and time.perf_counter() > _DEADLINE:
        raise _Timeout()

    if mask == _BOARD_MASK:
        return 0

    key = (p1, p2, turn)
    entry = _TT.get(key)
    if entry is not None and entry[0] >= depth:
        val, flag = entry[1], entry[2]
        if flag == _EXACT:
            return val
        if flag == _LOWER:
            if val > alpha:
                alpha = val
        elif flag == _UPPER:
            if val < beta:
                beta = val
        if alpha >= beta:
            return val

    alpha0 = alpha
    beta0 = beta

    if turn == 1:
        # If current side can win now, take it.
        cur_wins = _winning_move_bits(p1, mask)
        if cur_wins:
            return _WIN_SCORE - (ply + 1)

        # If opponent has multiple immediate wins, current side cannot block all.
        opp_wins = _winning_move_bits(p2, mask)
        opp_count = opp_wins.bit_count()
        if opp_count > 1:
            return -_WIN_SCORE + (ply + 2)

        if depth <= 0:
            return _evaluate(p1, p2, mask)

        forced_col = _col_from_bits(opp_wins) if opp_count == 1 else -1
        moves = (forced_col,) if forced_col >= 0 else _ORDER

        value = -_INF

        for c in moves:
            if c < 0 or c >= _WIDTH or (mask & _TOP_MASKS[c]):
                continue

            bit = _play_bit(mask, c)
            if not bit:
                continue

            np1 = p1 | bit
            nmask = mask | bit

            if _has_won(np1):
                score = _WIN_SCORE - (ply + 1)
            else:
                score = _alphabeta(np1, p2, nmask, -1, depth - 1, alpha, beta, ply + 1)

            if score > value:
                value = score
            if value > alpha:
                alpha = value
            if alpha >= beta:
                break

        if value == -_INF:
            value = 0

    else:
        # Opponent can win now.
        cur_wins = _winning_move_bits(p2, mask)
        if cur_wins:
            return -_WIN_SCORE + (ply + 1)

        # Root player has multiple immediate wins; opponent cannot block all.
        opp_wins = _winning_move_bits(p1, mask)
        opp_count = opp_wins.bit_count()
        if opp_count > 1:
            return _WIN_SCORE - (ply + 2)

        if depth <= 0:
            return _evaluate(p1, p2, mask)

        forced_col = _col_from_bits(opp_wins) if opp_count == 1 else -1
        moves = (forced_col,) if forced_col >= 0 else _ORDER

        value = _INF

        for c in moves:
            if c < 0 or c >= _WIDTH or (mask & _TOP_MASKS[c]):
                continue

            bit = _play_bit(mask, c)
            if not bit:
                continue

            np2 = p2 | bit
            nmask = mask | bit

            if _has_won(np2):
                score = -_WIN_SCORE + (ply + 1)
            else:
                score = _alphabeta(p1, np2, nmask, 1, depth - 1, alpha, beta, ply + 1)

            if score < value:
                value = score
            if value < beta:
                beta = value
            if alpha >= beta:
                break

        if value == _INF:
            value = 0

    if value <= alpha0:
        flag = _UPPER
    elif value >= beta0:
        flag = _LOWER
    else:
        flag = _EXACT

    if len(_TT) < 300000:
        _TT[key] = (depth, value, flag)

    return value


def _root_search(p1, p2, mask, depth, hint):
    alpha = -_INF
    best_score = -_INF
    best_move = -1

    for c in _legal_moves(mask, hint):
        if time.perf_counter() > _DEADLINE:
            raise _Timeout()

        bit = _play_bit(mask, c)
        if not bit:
            continue

        np1 = p1 | bit
        nmask = mask | bit

        if _has_won(np1):
            score = _WIN_SCORE - 1
        else:
            score = _alphabeta(np1, p2, nmask, -1, depth - 1, alpha, _INF, 1)

        if best_move < 0 or score > best_score or (
            score == best_score and _BIAS[c] > _BIAS[best_move]
        ):
            best_score = score
            best_move = c

        if score > alpha:
            alpha = score

    if best_move < 0:
        moves = _legal_moves(mask)
        best_move = moves[0] if moves else 0
        best_score = 0

    return best_score, best_move


def _ensure_legal(move, board):
    """Final safety guard: always return a non-full column if one exists."""
    try:
        m = int(move)
        if 0 <= m < _WIDTH and board[0][m] == 0:
            return m
    except Exception:
        pass

    try:
        top = board[0]
        for c in _ORDER:
            if top[c] == 0:
                return c
    except Exception:
        pass

    return 0


def policy(board: list[list[int]]) -> int:
    """
    Return a legal column index for the current player.
    The board uses 1 for our discs, -1 for opponent discs, and 0 for empty.
    """
    global _DEADLINE, _NODES, _TT

    start = time.perf_counter()

    try:
        p1, p2, mask = _to_bitboards(board)
        legal = _legal_moves(mask)

        if not legal:
            return 0

        # Strong opening.
        if mask == 0 and not (mask & _TOP_MASKS[3]):
            return 3

        # Immediate tactical necessities.
        wins = _winning_move_bits(p1, mask)
        if wins:
            return _ensure_legal(_col_from_bits(wins), board)

        opp_wins = _winning_move_bits(p2, mask)
        if opp_wins.bit_count() == 1:
            return _ensure_legal(_col_from_bits(opp_wins), board)

        fallback = _fallback_move(p1, p2, mask)
        best = fallback
        hint = fallback

        # Conservative time budget under a 1 second limit.
        _DEADLINE = start + 0.92
        _NODES = 0
        _TT = {}

        remaining = 42 - mask.bit_count()
        max_depth = remaining if remaining <= 18 else 14

        try:
            for depth in range(1, max_depth + 1):
                if time.perf_counter() > _DEADLINE - 0.015:
                    break

                score, move = _root_search(p1, p2, mask, depth, hint)

                if move in legal:
                    best = move
                    hint = move

                # A proven near-term win is enough.
                if score >= _WIN_SCORE - 30:
                    break

        except _Timeout:
            pass

        return _ensure_legal(best, board)

    except Exception:
        return _ensure_legal(3, board)

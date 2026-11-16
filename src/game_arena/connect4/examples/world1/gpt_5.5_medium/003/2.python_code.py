
import time

# Bitboard layout:
# Each column uses 7 bits: 6 playable cells plus one unused sentinel bit.
# Bit index = col * 7 + row_from_bottom, where row_from_bottom is 0..5.

WIDTH = 7
HEIGHT = 6

ORDER = [3, 2, 4, 1, 5, 0, 6]
INF = 10**9
WIN_SCORE = 1_000_000

BOTTOM_MASKS = [1 << (c * 7) for c in range(WIDTH)]
TOP_MASKS = [1 << (c * 7 + HEIGHT - 1) for c in range(WIDTH)]
COL_MASKS = [((1 << HEIGHT) - 1) << (c * 7) for c in range(WIDTH)]
ALL_CELLS = 0
for _m in COL_MASKS:
    ALL_CELLS |= _m

COL_WEIGHTS = [3, 4, 5, 7, 5, 4, 3]

# Precompute all 4-cell winning windows.
WINDOWS = []

# Vertical windows
for c in range(WIDTH):
    for y in range(HEIGHT - 3):
        m = 0
        for i in range(4):
            m |= 1 << (c * 7 + y + i)
        WINDOWS.append(m)

# Horizontal windows
for c in range(WIDTH - 3):
    for y in range(HEIGHT):
        m = 0
        for i in range(4):
            m |= 1 << ((c + i) * 7 + y)
        WINDOWS.append(m)

# Diagonal up-right windows
for c in range(WIDTH - 3):
    for y in range(HEIGHT - 3):
        m = 0
        for i in range(4):
            m |= 1 << ((c + i) * 7 + y + i)
        WINDOWS.append(m)

# Diagonal down-right windows
for c in range(WIDTH - 3):
    for y in range(3, HEIGHT):
        m = 0
        for i in range(4):
            m |= 1 << ((c + i) * 7 + y - i)
        WINDOWS.append(m)

_TT = {}
_deadline = 0.0
_nodes = 0


def _won(pos: int) -> bool:
    """Return True if bitboard pos contains a connect four."""
    m = pos & (pos >> 1)       # vertical
    if m & (m >> 2):
        return True
    m = pos & (pos >> 7)       # horizontal
    if m & (m >> 14):
        return True
    m = pos & (pos >> 6)       # diagonal
    if m & (m >> 12):
        return True
    m = pos & (pos >> 8)       # other diagonal
    if m & (m >> 16):
        return True
    return False


def _move_bit(mask: int, col: int) -> int:
    """Bit corresponding to dropping a disc into col. Assumes col is legal."""
    return (mask + BOTTOM_MASKS[col]) & COL_MASKS[col]


def _legal_cols(mask: int):
    return [c for c in ORDER if not (mask & TOP_MASKS[c])]


def _winning_cols(cur: int, opp: int):
    mask = cur | opp
    wins = []
    for c in ORDER:
        if not (mask & TOP_MASKS[c]):
            mb = _move_bit(mask, c)
            if _won(cur | mb):
                wins.append(c)
    return wins


def _count_winning_moves(cur: int, opp: int) -> int:
    mask = cur | opp
    cnt = 0
    for c in ORDER:
        if not (mask & TOP_MASKS[c]):
            if _won(cur | _move_bit(mask, c)):
                cnt += 1
    return cnt


def _check_time():
    global _nodes
    _nodes += 1
    if (_nodes & 2047) == 0 and time.perf_counter() > _deadline:
        raise TimeoutError


def _evaluate(cur: int, opp: int) -> int:
    """Heuristic evaluation from the side-to-move perspective."""
    score = 0

    # Positional / center control.
    for c, w in enumerate(COL_WEIGHTS):
        score += w * ((cur & COL_MASKS[c]).bit_count() - (opp & COL_MASKS[c]).bit_count())

    # Open 4-cell windows.
    my_weights = [0, 3, 25, 160, 100000]
    op_weights = [0, 3, 28, 190, 100000]

    for wmask in WINDOWS:
        a = (cur & wmask).bit_count()
        b = (opp & wmask).bit_count()
        if a and b:
            continue
        if a:
            score += my_weights[a]
        elif b:
            score -= op_weights[b]

    # Horizon threat awareness.
    my_wins = _count_winning_moves(cur, opp)
    op_wins = _count_winning_moves(opp, cur)
    if my_wins:
        score += 5000 * my_wins
    if op_wins:
        score -= 5500 * op_wins

    return score


def _negamax(cur: int, opp: int, depth: int, alpha: int, beta: int) -> int:
    """Negamax alpha-beta. cur is the player to move."""
    _check_time()

    if _won(opp):
        return -WIN_SCORE - depth

    mask = cur | opp
    if mask == ALL_CELLS:
        return 0

    if depth <= 0:
        return _evaluate(cur, opp)

    key = (cur, opp)
    entry = _TT.get(key)
    if entry is not None:
        stored_depth, flag, val = entry
        if stored_depth >= depth:
            if flag == 0:
                return val
            if flag == 1:
                alpha = max(alpha, val)
            else:
                beta = min(beta, val)
            if alpha >= beta:
                return val

    # If the player to move can win immediately, no need to search.
    if _count_winning_moves(cur, opp) > 0:
        return WIN_SCORE + depth

    alpha_orig = alpha
    beta_orig = beta
    best = -INF

    for c in ORDER:
        if mask & TOP_MASKS[c]:
            continue

        mb = _move_bit(mask, c)
        val = -_negamax(opp, cur | mb, depth - 1, -beta, -alpha)

        if val > best:
            best = val
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

    if best == -INF:
        best = 0

    if best <= alpha_orig:
        flag = 2   # upper bound
    elif best >= beta_orig:
        flag = 1   # lower bound
    else:
        flag = 0   # exact

    _TT[key] = (depth, flag, best)
    return best


def _root_search(cur: int, opp: int, depth: int):
    mask = cur | opp
    best_col = None
    best_val = -INF
    alpha = -INF
    beta = INF

    for c in ORDER:
        if mask & TOP_MASKS[c]:
            continue

        mb = _move_bit(mask, c)
        if _won(cur | mb):
            val = WIN_SCORE + depth
        else:
            val = -_negamax(opp, cur | mb, depth - 1, -beta, -alpha)

        if val > best_val:
            best_val = val
            best_col = c
        if val > alpha:
            alpha = val

    return best_val, best_col


def _safe_fallback(cur: int, opp: int) -> int:
    """Prefer a legal move that does not allow an immediate opponent win."""
    mask = cur | opp
    first_legal = None

    for c in ORDER:
        if mask & TOP_MASKS[c]:
            continue
        if first_legal is None:
            first_legal = c

        mb = _move_bit(mask, c)
        # If this move wins, it is certainly safe.
        if _won(cur | mb):
            return c
        # Avoid giving the opponent an immediate win when possible.
        if _count_winning_moves(opp, cur | mb) == 0:
            return c

    return first_legal if first_legal is not None else 0


def policy(board: list[list[int]]) -> int:
    global _TT, _deadline, _nodes

    cur = 0
    opp = 0

    # Convert board to bitboards.
    for r in range(HEIGHT):
        row = board[r]
        y = HEIGHT - 1 - r
        for c in range(WIDTH):
            v = row[c]
            if v:
                bit = 1 << (c * 7 + y)
                if v == 1:
                    cur |= bit
                elif v == -1:
                    opp |= bit

    mask = cur | opp
    legal = _legal_cols(mask)
    if not legal:
        return 0
    if len(legal) == 1:
        return legal[0]

    # Immediate win.
    my_wins = _winning_cols(cur, opp)
    if my_wins:
        return my_wins[0]

    # Forced immediate block.
    opp_wins = _winning_cols(opp, cur)
    if len(opp_wins) == 1:
        return opp_wins[0]

    # Reliable fallback before starting timed search.
    best_col = _safe_fallback(cur, opp)

    # Time-limited iterative deepening.
    _TT = {}
    _nodes = 0
    _deadline = time.perf_counter() + 0.86

    stones = mask.bit_count()
    remaining = WIDTH * HEIGHT - stones

    if remaining <= 10:
        max_depth = remaining
    elif remaining <= 16:
        max_depth = 12
    elif remaining <= 24:
        max_depth = 10
    else:
        max_depth = 8

    try:
        for depth in range(1, max_depth + 1):
            if time.perf_counter() > _deadline:
                break
            val, col = _root_search(cur, opp, depth)
            if col is not None and col in legal:
                best_col = col
            if abs(val) >= WIN_SCORE:
                break
    except TimeoutError:
        pass
    except Exception:
        # Never risk returning an illegal move because of an unexpected issue.
        pass

    # Final legality / safety check.
    if best_col not in legal:
        best_col = legal[0]

    return int(best_col)

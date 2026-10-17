
import time
from itertools import product

# ---------- Board geometry ----------

ALL_MASK = (1 << 27) - 1
CENTER_BIT = 1 << 13
WIN_SCORE = 1_000_000
INF = 10**9

# Transposition table flags
EXACT, LOWER, UPPER = 0, 1, 2

_TT = {}
_TT_MAX = 400_000
_DEADLINE = 0.0
_NODES = 0


class _Timeout(Exception):
    pass


def _idx(i: int, j: int, k: int) -> int:
    return i * 9 + j * 3 + k


def _bit_to_cell(bit: int) -> tuple[int, int, int]:
    idx = bit.bit_length() - 1
    return (idx // 9, (idx // 3) % 3, idx % 3)


def _first_bit(mask: int) -> int:
    return mask & -mask


def _iter_bits(mask: int):
    while mask:
        b = mask & -mask
        yield b
        mask ^= b


def _make_win_masks():
    masks = set()

    dirs = []
    for dx, dy, dz in product((-1, 0, 1), repeat=3):
        if dx == dy == dz == 0:
            continue
        # Keep one orientation of each opposite pair.
        for v in (dx, dy, dz):
            if v != 0:
                if v > 0:
                    dirs.append((dx, dy, dz))
                break

    for dx, dy, dz in dirs:
        for i, j, k in product(range(3), repeat=3):
            pi, pj, pk = i - dx, j - dy, k - dz
            ei, ej, ek = i + 2 * dx, j + 2 * dy, k + 2 * dz

            # Start must be the first cell of the line, and end must be inside.
            if 0 <= pi < 3 and 0 <= pj < 3 and 0 <= pk < 3:
                continue
            if not (0 <= ei < 3 and 0 <= ej < 3 and 0 <= ek < 3):
                continue

            m = 0
            for t in range(3):
                m |= 1 << _idx(i + t * dx, j + t * dy, k + t * dz)
            masks.add(m)

    return tuple(sorted(masks))


WIN_MASKS = _make_win_masks()

CELL_LINES = [[] for _ in range(27)]
for _m in WIN_MASKS:
    _x = _m
    while _x:
        _b = _x & -_x
        CELL_LINES[_b.bit_length() - 1].append(_m)
        _x ^= _b

# Positional value: cells participating in more winning lines are better.
POS_WEIGHTS = [len(CELL_LINES[i]) * 8 for i in range(27)]
POS_WEIGHTS[13] += 40

CORNER_BITS = tuple(
    1 << _idx(i, j, k)
    for i in (0, 2)
    for j in (0, 2)
    for k in (0, 2)
)


# ---------- Core line/threat logic ----------

def _has_win(bb: int) -> bool:
    for m in WIN_MASKS:
        if (bb & m) == m:
            return True
    return False


def _winning_moves(p: int, o: int) -> int:
    """Empty cells where player p can move now to complete a line."""
    empty = ALL_MASK ^ (p | o)
    wins = 0
    for m in WIN_MASKS:
        if (m & o) == 0 and (m & p).bit_count() == 2:
            e = m & empty
            if e:
                wins |= e
    return wins


def _pos_sum(bb: int) -> int:
    s = 0
    while bb:
        b = bb & -bb
        s += POS_WEIGHTS[b.bit_length() - 1]
        bb ^= b
    return s


def _evaluate(p: int, o: int) -> int:
    """Static score from the point of view of the side to move p."""
    score = 0

    # Open-line potential.
    for m in WIN_MASKS:
        pc = (p & m).bit_count()
        oc = (o & m).bit_count()
        if pc and oc:
            continue
        if oc == 0:
            if pc == 1:
                score += 8
            elif pc == 2:
                score += 160
        elif pc == 0:
            if oc == 1:
                score -= 10
            elif oc == 2:
                score -= 190

    score += 2 * (_pos_sum(p) - _pos_sum(o))

    # Horizon safety: having to answer an immediate threat is bad.
    my_threats = _winning_moves(p, o).bit_count()
    opp_threats = _winning_moves(o, p).bit_count()
    score += 260 * my_threats
    score -= 340 * opp_threats

    return score


def _move_sort_score(bit: int, p: int, o: int, tt_move: int = 0) -> int:
    idx = bit.bit_length() - 1
    score = POS_WEIGHTS[idx]

    if bit == tt_move:
        score += 2_000_000

    # Local line impact for move ordering.
    for m in CELL_LINES[idx]:
        pc = (p & m).bit_count()
        oc = (o & m).bit_count()

        if oc == 0:
            if pc == 2:
                score += 200_000  # immediate win
            elif pc == 1:
                score += 5_000    # creates a threat
            else:
                score += 35

        if pc == 0:
            if oc == 2:
                score += 150_000  # block immediate loss
            elif oc == 1:
                score += 1_200    # prevents opponent threat growth

    return score


def _ordered_moves(p: int, o: int, tt_move: int = 0):
    empty = ALL_MASK ^ (p | o)
    scored = []
    for b in _iter_bits(empty):
        scored.append((_move_sort_score(b, p, o, tt_move), b))
    scored.sort(reverse=True)
    return [b for _, b in scored]


# ---------- Search ----------

def _check_time():
    global _NODES
    _NODES += 1
    if (_NODES & 1023) == 0 and time.perf_counter() > _DEADLINE:
        raise _Timeout()


def _negamax(p: int, o: int, depth: int, alpha: int, beta: int) -> int:
    _check_time()

    empty = ALL_MASK ^ (p | o)
    empties = empty.bit_count()

    # Previous move already won.
    if _has_win(o):
        return -WIN_SCORE - empties

    if empty == 0:
        return 0

    # If side to move can win immediately, no need to search deeper.
    my_wins = _winning_moves(p, o)
    if my_wins:
        return WIN_SCORE + empties

    # If opponent has two distinct immediate wins, side to move cannot parry both.
    opp_wins = _winning_moves(o, p)
    opp_win_count = opp_wins.bit_count()
    if opp_win_count > 1:
        return -WIN_SCORE - max(0, empties - 1)

    if depth <= 0:
        return _evaluate(p, o)

    key = (p, o)
    entry = _TT.get(key)
    tt_move = 0

    if entry is not None:
        e_depth, e_flag, e_val, e_best = entry
        tt_move = e_best
        if e_depth >= depth:
            if e_flag == EXACT:
                return e_val
            if e_flag == LOWER:
                alpha = max(alpha, e_val)
            elif e_flag == UPPER:
                beta = min(beta, e_val)
            if alpha >= beta:
                return e_val

    alpha_orig = alpha
    beta_orig = beta

    # A single opponent immediate win is a forced block.
    if opp_win_count == 1:
        moves = [opp_wins]
    else:
        moves = _ordered_moves(p, o, tt_move)

    best_val = -INF
    best_move = 0

    for b in moves:
        val = -_negamax(o, p | b, depth - 1, -beta, -alpha)

        if val > best_val:
            best_val = val
            best_move = b

        if val > alpha:
            alpha = val

        if alpha >= beta:
            break

    if best_val <= alpha_orig:
        flag = UPPER
    elif best_val >= beta_orig:
        flag = LOWER
    else:
        flag = EXACT

    if len(_TT) < _TT_MAX:
        _TT[key] = (depth, flag, best_val, best_move)

    return best_val


def _root_search(p: int, o: int, depth: int) -> tuple[int, int]:
    if time.perf_counter() > _DEADLINE:
        raise _Timeout()

    entry = _TT.get((p, o))
    tt_move = entry[3] if entry else 0

    moves = _ordered_moves(p, o, tt_move)

    alpha = -INF
    beta = INF
    best_val = -INF
    best_move = moves[0] if moves else 0

    for b in moves:
        if time.perf_counter() > _DEADLINE:
            raise _Timeout()

        val = -_negamax(o, p | b, depth - 1, -beta, -alpha)

        if val > best_val:
            best_val = val
            best_move = b

        if val > alpha:
            alpha = val

    return best_val, best_move


# ---------- Tactical helpers / fallback ----------

def _best_bit_from_mask(mask: int, p: int, o: int) -> int:
    best = 0
    best_score = -INF
    for b in _iter_bits(mask):
        s = _move_sort_score(b, p, o)
        if s > best_score:
            best_score = s
            best = b
    return best or _first_bit(mask)


def _find_own_fork(p: int, o: int) -> int:
    """Find a move creating two or more distinct immediate winning moves."""
    empty = ALL_MASK ^ (p | o)
    best = 0
    best_score = -INF

    for b in _iter_bits(empty):
        np = p | b
        threats = _winning_moves(np, o).bit_count()
        if threats >= 2:
            s = _move_sort_score(b, p, o) + 50_000 * threats
            if s > best_score:
                best_score = s
                best = b

    return best


def _opponent_fork_moves(p: int, o: int) -> int:
    """Cells where opponent o would create a decisive fork if allowed to move."""
    empty = ALL_MASK ^ (p | o)
    forks = 0

    for b in _iter_bits(empty):
        no = o | b
        if _winning_moves(no, p).bit_count() >= 2:
            forks |= b

    return forks


def _heuristic_move(p: int, o: int) -> int:
    empty = ALL_MASK ^ (p | o)
    if not empty:
        return 0

    my_wins = _winning_moves(p, o)
    if my_wins:
        return _best_bit_from_mask(my_wins, p, o)

    opp_wins = _winning_moves(o, p)
    if opp_wins.bit_count() == 1:
        return opp_wins

    best = 0
    best_score = -10**18

    for b in _iter_bits(empty):
        np = p | b

        my_next_threats = _winning_moves(np, o).bit_count()
        opp_next_wins = _winning_moves(o, np).bit_count()

        score = _move_sort_score(b, p, o)
        score += 25_000 * my_next_threats
        score -= 80_000 * opp_next_wins

        # Resulting static position from our perspective:
        # after our move, opponent is side to move, so negate their evaluation.
        score -= _evaluate(o, np) // 2

        if my_next_threats >= 2:
            score += 300_000

        if score > best_score:
            best_score = score
            best = b

    return best or _first_bit(empty)


def _search_best(p: int, o: int, fallback: int) -> int:
    global _DEADLINE, _NODES

    _DEADLINE = time.perf_counter() + 0.78
    _NODES = 0

    empty = ALL_MASK ^ (p | o)
    empties = empty.bit_count()
    best = fallback

    # Iterative deepening keeps a legal completed-depth move at all times.
    for depth in range(1, empties + 1):
        if time.perf_counter() > _DEADLINE:
            break

        try:
            val, move = _root_search(p, o, depth)
            if move and (move & empty):
                best = move

            # A proven forced win within the searched tree is enough.
            if val >= WIN_SCORE:
                break

        except _Timeout:
            break

    return best


def _parse_board(board: list[list[list[int]]]) -> tuple[int, int]:
    p = 0
    o = 0
    for i in range(3):
        for j in range(3):
            for k in range(3):
                bit = 1 << _idx(i, j, k)
                v = board[i][j][k]
                if v == 1:
                    p |= bit
                elif v == -1:
                    o |= bit
    return p, o


def _fallback_from_board(board) -> tuple[int, int, int]:
    try:
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    if board[i][j][k] == 0:
                        return (i, j, k)
    except Exception:
        pass
    return (0, 0, 0)


# ---------- Required API ----------

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    try:
        global _TT

        if len(_TT) > _TT_MAX:
            _TT = {}

        p, o = _parse_board(board)
        occupied = p | o
        empty = ALL_MASK ^ occupied

        if not empty:
            return _fallback_from_board(board)

        total_moves = occupied.bit_count()

        # 1. Immediate tactical necessities.
        my_wins = _winning_moves(p, o)
        if my_wins:
            chosen = _best_bit_from_mask(my_wins, p, o)
            return _bit_to_cell(chosen)

        opp_wins = _winning_moves(o, p)
        if opp_wins.bit_count() == 1:
            return _bit_to_cell(opp_wins)

        # 2. Opening principles.
        if total_moves == 0 and (empty & CENTER_BIT):
            return (1, 1, 1)

        if total_moves == 1:
            # If opponent did not take center, take it. If they did, take a corner.
            if empty & CENTER_BIT:
                return (1, 1, 1)
            for c in CORNER_BITS:
                if empty & c:
                    return _bit_to_cell(c)

        # 3. Decisive forks.
        if opp_wins == 0:
            fork = _find_own_fork(p, o)
            if fork and (fork & empty):
                return _bit_to_cell(fork)

            opp_forks = _opponent_fork_moves(p, o)
            if opp_forks.bit_count() == 1:
                return _bit_to_cell(opp_forks)

        # 4. Search with safe heuristic fallback.
        fallback = _heuristic_move(p, o)
        chosen = _search_best(p, o, fallback)

        if not chosen or not (chosen & empty):
            chosen = fallback

        if not chosen or not (chosen & empty):
            chosen = _first_bit(empty)

        return _bit_to_cell(chosen)

    except Exception:
        # Absolute safety: return the first legal empty cell from the raw board.
        return _fallback_from_board(board)

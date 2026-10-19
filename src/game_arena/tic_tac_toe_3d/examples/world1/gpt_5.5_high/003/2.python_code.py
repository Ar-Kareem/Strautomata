
import time
from functools import lru_cache
from itertools import product

# 3x3x3 Tic Tac Toe policy.
# Board values:  1 = us, -1 = opponent, 0 = empty.

NUM_CELLS = 27
FULL_MASK = (1 << NUM_CELLS) - 1
CENTER_IDX = 13
CENTER_BIT = 1 << CENTER_IDX

WIN = 1_000_000
INF = 1_000_000_000

EXACT, LOWER, UPPER = 0, 1, 2

DEADLINE = 0.0
NODES = 0
TT = {}


def _idx(i: int, j: int, k: int) -> int:
    return i * 9 + j * 3 + k


COORDS = [(i, j, k) for i in range(3) for j in range(3) for k in range(3)]
CORNERS = tuple(_idx(i, j, k) for i in (0, 2) for j in (0, 2) for k in (0, 2))


# Generate the 49 standard winning lines in 3D tic tac toe.
_DIRS = []
for dx, dy, dz in product((-1, 0, 1), repeat=3):
    if dx == dy == dz == 0:
        continue
    for v in (dx, dy, dz):
        if v != 0:
            if v > 0:
                _DIRS.append((dx, dy, dz))
            break

_line_set = set()
for i, j, k in product(range(3), repeat=3):
    for dx, dy, dz in _DIRS:
        cells = []
        ok = True
        for t in range(3):
            x, y, z = i + t * dx, j + t * dy, k + t * dz
            if not (0 <= x < 3 and 0 <= y < 3 and 0 <= z < 3):
                ok = False
                break
            cells.append(_idx(x, y, z))
        if ok:
            mask = 0
            for c in cells:
                mask |= 1 << c
            _line_set.add(mask)

WIN_MASKS = tuple(sorted(_line_set))

CELL_LINES = [[] for _ in range(NUM_CELLS)]
for line in WIN_MASKS:
    for n in range(NUM_CELLS):
        if line & (1 << n):
            CELL_LINES[n].append(line)

# Positional values: center is strongest, corners are also valuable.
POS = []
for n, (i, j, k) in enumerate(COORDS):
    p = 10 * len(CELL_LINES[n])
    if n == CENTER_IDX:
        p += 40
    if i in (0, 2) and j in (0, 2) and k in (0, 2):
        p += 12
    POS.append(p)


class SearchTimeout(Exception):
    pass


def _iter_bits(mask: int):
    while mask:
        b = mask & -mask
        yield b
        mask ^= b


def _bit_to_coord(bit: int) -> tuple[int, int, int]:
    return COORDS[bit.bit_length() - 1]


def _safe_first_empty(board) -> tuple[int, int, int]:
    try:
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    if board[i][j][k] == 0:
                        return (i, j, k)
    except Exception:
        pass
    return (0, 0, 0)


def _board_to_bits(board) -> tuple[int, int]:
    own = 0
    opp = 0
    for i in range(3):
        for j in range(3):
            for k in range(3):
                v = board[i][j][k]
                bit = 1 << _idx(i, j, k)
                if v == 1:
                    own |= bit
                elif v == -1:
                    opp |= bit
    return own, opp


@lru_cache(maxsize=120_000)
def _has_win(bits: int) -> bool:
    for line in WIN_MASKS:
        if bits & line == line:
            return True
    return False


@lru_cache(maxsize=180_000)
def _threat_mask(side: int, occ: int) -> int:
    """Empty cells where 'side' can win immediately."""
    threats = 0
    for line in WIN_MASKS:
        if (line & side).bit_count() == 2 and (line & occ).bit_count() == 2:
            threats |= line & ~occ
    return threats


@lru_cache(maxsize=120_000)
def _pos_sum(bits: int) -> int:
    s = 0
    m = bits
    while m:
        b = m & -m
        s += POS[b.bit_length() - 1]
        m ^= b
    return s


def _created_threat_mask(side: int, other: int, move_bit: int, occ: int | None = None) -> int:
    """
    Threat cells created if 'side' plays move_bit.
    Counts distinct future winning cells.
    """
    if occ is None:
        occ = side | other
    idx = move_bit.bit_length() - 1
    occ2 = occ | move_bit
    threats = 0

    for line in CELL_LINES[idx]:
        if line & other:
            continue
        # Before the move, exactly one friendly stone in this line;
        # after the move, the line has two friendly stones and one empty.
        if (line & side).bit_count() == 1:
            empty = line & ~occ2
            if empty:
                threats |= empty

    return threats


@lru_cache(maxsize=120_000)
def _fork_moves_mask(side: int, other: int) -> int:
    """
    Legal moves for 'side' that create at least two distinct immediate
    winning threats. Such a move is a forced win if the opponent has no
    immediate win already.
    """
    occ = side | other
    empty = FULL_MASK & ~occ
    result = 0
    for b in _iter_bits(empty):
        if _created_threat_mask(side, other, b, occ).bit_count() >= 2:
            result |= b
    return result


def _check_time():
    global NODES, DEADLINE
    NODES += 1
    if (NODES & 511) == 0 and time.perf_counter() > DEADLINE:
        raise SearchTimeout()


def _move_score(own: int, opp: int, bit: int, preferred: int = 0) -> int:
    idx = bit.bit_length() - 1
    occ = own | opp

    score = POS[idx] * 10
    if bit == preferred:
        score += 10_000_000

    # Line-local tactical value.
    for line in CELL_LINES[idx]:
        oc = (line & own).bit_count()
        pc = (line & opp).bit_count()

        if pc == 0:
            if oc == 2:
                score += 2_000_000       # winning move
            elif oc == 1:
                score += 500
            else:
                score += 20

        if oc == 0:
            if pc == 2:
                score += 1_500_000       # block immediate loss
            elif pc == 1:
                score += 420

    # Create our threats/forks.
    c = _created_threat_mask(own, opp, bit, occ).bit_count()
    if c >= 2:
        score += 1_200_000 + c * 100_000
    elif c == 1:
        score += 80_000

    # Occupy cells the opponent would like for threats/forks.
    oc = _created_threat_mask(opp, own, bit, occ).bit_count()
    if oc >= 2:
        score += 900_000 + oc * 80_000
    elif oc == 1:
        score += 20_000

    return score


def _ordered_moves(own: int, opp: int, moves_mask: int, preferred: int = 0) -> list[int]:
    scored = []
    for b in _iter_bits(moves_mask):
        scored.append((_move_score(own, opp, b, preferred), b))
    scored.sort(reverse=True)
    return [b for _, b in scored]


def _choose_move(own: int, opp: int, moves_mask: int, preferred: int = 0) -> int:
    ordered = _ordered_moves(own, opp, moves_mask, preferred)
    if ordered:
        return ordered[0]
    legal = FULL_MASK & ~(own | opp)
    return legal & -legal


def _evaluate(own: int, opp: int) -> int:
    occ = own | opp
    score = _pos_sum(own) - _pos_sum(opp)

    # Open-line potential.
    for line in WIN_MASKS:
        oc = (line & own).bit_count()
        pc = (line & opp).bit_count()

        if oc and pc:
            continue
        if oc:
            if oc == 1:
                score += 15
            elif oc == 2:
                score += 260
        elif pc:
            if pc == 1:
                score -= 16
            elif pc == 2:
                score -= 280

    # One-move threat/fork potential.
    empty = FULL_MASK & ~occ
    own_single = opp_single = 0
    own_forks = opp_forks = 0

    for b in _iter_bits(empty):
        c = _created_threat_mask(own, opp, b, occ).bit_count()
        if c >= 2:
            own_forks += 1
            score += 8_000 + c * 1_000
        elif c == 1:
            own_single += 1

        d = _created_threat_mask(opp, own, b, occ).bit_count()
        if d >= 2:
            opp_forks += 1
            score -= 8_500 + d * 1_100
        elif d == 1:
            opp_single += 1

    score += 140 * own_single
    score -= 155 * opp_single
    score += 900 * own_forks
    score -= 1_000 * opp_forks

    if score >= WIN:
        return WIN - 1
    if score <= -WIN:
        return -WIN + 1
    return score


def _negamax(own: int, opp: int, depth: int, alpha: int, beta: int) -> int:
    _check_time()

    # If the previous player has already completed a line, current side lost.
    if _has_win(opp):
        return -WIN
    if _has_win(own):
        return WIN

    occ = own | opp
    if occ == FULL_MASK:
        return 0

    # Immediate win.
    my_wins = _threat_mask(own, occ)
    if my_wins:
        return WIN

    # Forced defense against opponent immediate win(s).
    opp_wins = _threat_mask(opp, occ)
    forced = 0
    if opp_wins:
        # Two distinct immediate winning cells cannot both be blocked.
        if opp_wins & (opp_wins - 1):
            return -WIN
        forced = opp_wins
    else:
        # Exact tactical rule: a move creating two distinct winning threats
        # wins by force.
        if _fork_moves_mask(own, opp):
            return WIN

    if depth <= 0 and not forced:
        return _evaluate(own, opp)

    alpha_orig = alpha
    beta_orig = beta
    key = (own, opp)
    tt_move = 0

    entry = TT.get(key)
    if entry is not None:
        tt_depth, tt_val, tt_flag, tt_move = entry
        if tt_depth >= depth:
            if tt_flag == EXACT:
                return tt_val
            if tt_flag == LOWER:
                alpha = max(alpha, tt_val)
            elif tt_flag == UPPER:
                beta = min(beta, tt_val)
            if alpha >= beta:
                return tt_val

    if forced:
        moves = [forced]
        next_depth = depth - 1 if depth > 0 else 0  # quiescent forced extension
    else:
        moves = _ordered_moves(own, opp, FULL_MASK & ~occ, tt_move)
        next_depth = depth - 1

    best = -INF
    best_move = 0

    for b in moves:
        val = -_negamax(opp, own | b, next_depth, -beta, -alpha)

        if val > best:
            best = val
            best_move = b

        if val > alpha:
            alpha = val

        if alpha >= beta:
            break

    if best == -INF:
        best = 0

    if best <= alpha_orig:
        flag = UPPER
    elif best >= beta_orig:
        flag = LOWER
    else:
        flag = EXACT

    old = TT.get(key)
    if old is None or depth >= old[0]:
        TT[key] = (depth, best, flag, best_move)

    return best


def _root_search(own: int, opp: int, depth: int, preferred: int = 0) -> tuple[int, int]:
    occ = own | opp
    legal = FULL_MASK & ~occ
    moves = _ordered_moves(own, opp, legal, preferred)

    best_val = -INF
    best_move = moves[0] if moves else 0
    alpha = -INF
    beta = INF

    for b in moves:
        val = -_negamax(opp, own | b, depth - 1, -beta, -alpha)

        if val > best_val:
            best_val = val
            best_move = b

        if val > alpha:
            alpha = val

        if best_val >= WIN:
            break

    return best_val, best_move


def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    global DEADLINE, NODES, TT

    try:
        own, opp = _board_to_bits(board)
        occ = own | opp
        legal = FULL_MASK & ~occ

        if legal == 0:
            return (0, 0, 0)

        # Keep memory bounded across repeated games.
        if len(TT) > 160_000:
            TT.clear()

        DEADLINE = time.perf_counter() + 0.86
        NODES = 0

        # 1. Win immediately if possible.
        own_wins = _threat_mask(own, occ) & legal
        if own_wins:
            return _bit_to_coord(_choose_move(own, opp, own_wins))

        # 2. Block immediate opponent win(s).
        opp_wins = _threat_mask(opp, occ) & legal
        if opp_wins:
            # If multiple distinct threats exist, the position is probably lost,
            # but blocking one is still the best legal practical move.
            return _bit_to_coord(_choose_move(own, opp, opp_wins))

        own_count = own.bit_count()
        opp_count = opp.bit_count()
        total = own_count + opp_count

        # 3. Strong opening principles.
        if total == 0 and (legal & CENTER_BIT):
            return (1, 1, 1)

        # If we are moving second and center is free, take it.
        if own_count == 0:
            if legal & CENTER_BIT:
                return (1, 1, 1)
            # If opponent took center, take a corner.
            for c in CORNERS:
                b = 1 << c
                if legal & b:
                    return COORDS[c]

        # 4. If we can create an immediate double-threat fork, do it.
        forks = _fork_moves_mask(own, opp) & legal
        if forks:
            return _bit_to_coord(_choose_move(own, opp, forks))

        # 5. Legal heuristic fallback before search.
        fallback = _choose_move(own, opp, legal)
        best_move = fallback
        preferred = fallback

        empties = legal.bit_count()
        if empties <= 8:
            max_depth = empties
        elif empties <= 12:
            max_depth = 10
        elif empties <= 17:
            max_depth = 8
        else:
            max_depth = 6

        # 6. Iterative-deepening tactical alpha-beta search.
        for depth in range(1, max_depth + 1):
            if time.perf_counter() > DEADLINE:
                break
            try:
                val, move = _root_search(own, opp, depth, preferred)
                if move & legal:
                    best_move = move
                    preferred = move
                if val >= WIN:
                    break
            except SearchTimeout:
                break

        if best_move & legal:
            return _bit_to_coord(best_move)

        return _bit_to_coord(fallback)

    except Exception:
        # Absolute safety fallback: always try to return a legal empty cell.
        return _safe_first_empty(board)

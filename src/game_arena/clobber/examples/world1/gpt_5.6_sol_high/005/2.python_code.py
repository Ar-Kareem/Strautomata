
from time import perf_counter

ROWS = 5
COLS = 6
CELLS = ROWS * COLS
FULL_MASK = (1 << CELLS) - 1

WIN = 30000
INF = 40000

EXACT = 0
LOWER = 1
UPPER = 2

# Cells which are not on the corresponding horizontal boundary.
NOT_LEFT = 0
NOT_RIGHT = 0
for _r in range(ROWS):
    for _c in range(COLS):
        _b = 1 << (_r * COLS + _c)
        if _c != 0:
            NOT_LEFT |= _b
        if _c != COLS - 1:
            NOT_RIGHT |= _b

# Legal destinations and printable forms for every possible move.
DESTS = [[] for _ in range(CELLS)]
MOVE_TEXT = {}

for r in range(ROWS):
    for c in range(COLS):
        s = r * COLS + c
        if r > 0:
            d = s - COLS
            DESTS[s].append(d)
            MOVE_TEXT[s * CELLS + d] = f"{r},{c},U"
        if c < COLS - 1:
            d = s + 1
            DESTS[s].append(d)
            MOVE_TEXT[s * CELLS + d] = f"{r},{c},R"
        if r < ROWS - 1:
            d = s + COLS
            DESTS[s].append(d)
            MOVE_TEXT[s * CELLS + d] = f"{r},{c},D"
        if c > 0:
            d = s - 1
            DESTS[s].append(d)
            MOVE_TEXT[s * CELLS + d] = f"{r},{c},L"


# Rectangle-preserving symmetries:
# 0 = identity, 1 = horizontal reflection,
# 2 = vertical reflection, 3 = rotation by 180 degrees.
SYM_MAP = [[0] * CELLS for _ in range(4)]
for r in range(ROWS):
    for c in range(COLS):
        s = r * COLS + c
        SYM_MAP[0][s] = s
        SYM_MAP[1][s] = r * COLS + (COLS - 1 - c)
        SYM_MAP[2][s] = (ROWS - 1 - r) * COLS + c
        SYM_MAP[3][s] = (ROWS - 1 - r) * COLS + (COLS - 1 - c)

# Small chunk tables make bitboard transformations inexpensive.
_TRANS_TABLES = []
for t in range(1, 4):
    chunks = []
    for chunk in range(3):
        table = [0] * 1024
        base = chunk * 10
        for value in range(1, 1024):
            low = value & -value
            i = low.bit_length() - 1
            table[value] = table[value ^ low] | (1 << SYM_MAP[t][base + i])
        chunks.append(table)
    _TRANS_TABLES.append(chunks)


def _transform(board, symmetry):
    if symmetry == 0:
        return board
    tab = _TRANS_TABLES[symmetry - 1]
    return (
        tab[0][board & 1023]
        | tab[1][(board >> 10) & 1023]
        | tab[2][(board >> 20) & 1023]
    )


def _canonical(p, q):
    """Return a canonical packed key and the symmetry used."""
    best_key = p | (q << CELLS)
    best_t = 0

    for t in (1, 2, 3):
        tp = _transform(p, t)
        tq = _transform(q, t)
        key = tp | (tq << CELLS)
        if key < best_key:
            best_key = key
            best_t = t

    return best_key, best_t


def _map_move(move, symmetry):
    if move < 0:
        return -1
    s, d = divmod(move, CELLS)
    return SYM_MAP[symmetry][s] * CELLS + SYM_MAP[symmetry][d]


def _adjacent(bits):
    return (
        ((bits & NOT_RIGHT) << 1)
        | ((bits & NOT_LEFT) >> 1)
        | ((bits << COLS) & FULL_MASK)
        | (bits >> COLS)
    )


def _cross_edges(p, q):
    """Number of legal captures, equivalently bichromatic board edges."""
    return (
        (((p & NOT_RIGHT) << 1) & q).bit_count()
        + (((p & NOT_LEFT) >> 1) & q).bit_count()
        + (((p << COLS) & FULL_MASK) & q).bit_count()
        + ((p >> COLS) & q).bit_count()
    )


def _moves(p, q):
    result = []
    bits = p
    while bits:
        low = bits & -bits
        s = low.bit_length() - 1
        for d in DESTS[s]:
            if q & (1 << d):
                result.append(s * CELLS + d)
        bits ^= low
    return result


def _apply(p, q, move):
    s, d = divmod(move, CELLS)
    source = 1 << s
    destination = 1 << d
    new_p = (p ^ source) | destination
    new_q = q ^ destination
    return new_p, new_q


def _to_bitboard(array):
    """Accept nested Python lists, flat lists, or NumPy-style arrays."""
    board = 0
    try:
        for r in range(ROWS):
            row = array[r]
            for c in range(COLS):
                if int(row[c]):
                    board |= 1 << (r * COLS + c)
        return board
    except (TypeError, IndexError):
        board = 0
        for i in range(CELLS):
            if int(array[i]):
                board |= 1 << i
        return board


# Persistent transposition table. Entries are:
# key -> (decision_depth, score, bound_type, canonical_best_move)
_TT = {}

_deadline = 0.0
_nodes = 0
_history = [0] * (CELLS * CELLS)
_killers = [[-1, -1] for _ in range(CELLS + 2)]


class _SearchTimeout(Exception):
    pass


def _check_time():
    global _nodes
    _nodes += 1
    if (_nodes & 127) == 0 and perf_counter() >= _deadline:
        raise _SearchTimeout


def _store_tt(key, symmetry, depth, score, flag, best_move):
    old = _TT.get(key)
    if old is not None:
        old_depth, old_score, old_flag, old_move = old
        if old_depth > depth and abs(score) != WIN:
            return

    canonical_move = _map_move(best_move, symmetry)
    _TT[key] = (depth, score, flag, canonical_move)


def _static_eval(p, q, moves, current_edges):
    """
    Tactical frontier evaluator.

    It values moves which sharply reduce the opponent's available captures,
    force the opponent to use few pieces, and expose several distinct targets.
    An immediately terminal child is a mathematically proven win.
    """
    best_quality = -100000
    best_count = 0

    for move in moves:
        new_p, new_q = _apply(p, q, move)

        # The recursive child has new_q as its side to move.
        reply_edges = _cross_edges(new_q, new_p)
        if reply_edges == 0:
            return WIN

        reply_movers = (new_q & _adjacent(new_p)).bit_count()
        reduction = current_edges - reply_edges

        quality = 28 * reduction - 11 * reply_edges - 5 * reply_movers
        if reply_edges == 1:
            quality += 45
        elif reply_edges == 2:
            quality += 18

        if quality > best_quality:
            best_quality = quality
            best_count = 1
        elif quality == best_quality:
            best_count += 1

    own_movers = (p & _adjacent(q)).bit_count()
    distinct_targets = (q & _adjacent(p)).bit_count()

    score = (
        best_quality
        + 7 * (distinct_targets - own_movers)
        + min(best_count, 6) * 3
    )

    if score > 2500:
        return 2500
    if score < -2500:
        return -2500
    return score


def _ordered_children(p, q, moves, tt_move, ply):
    scored = []
    killer0, killer1 = _killers[ply]

    for move in moves:
        new_p, new_q = _apply(p, q, move)
        reply_edges = _cross_edges(new_q, new_p)
        reply_movers = (new_q & _adjacent(new_p)).bit_count()

        score = -80 * reply_edges - 10 * reply_movers + _history[move]

        if reply_edges == 0:
            score += 100000000
        if move == killer0:
            score += 400000
        elif move == killer1:
            score += 200000
        if move == tt_move:
            score += 1000000000

        scored.append((score, move, new_p, new_q))

    scored.sort(reverse=True)
    return scored


def _search(p, q, depth, alpha, beta, ply):
    _check_time()

    alpha_initial = alpha
    beta_initial = beta

    key, symmetry = _canonical(p, q)
    entry = _TT.get(key)
    tt_move = -1

    if entry is not None:
        entry_depth, entry_score, entry_flag, canonical_move = entry
        tt_move = _map_move(canonical_move, symmetry)

        if entry_depth >= depth:
            if entry_flag == EXACT:
                return entry_score
            if entry_flag == LOWER and entry_score > alpha:
                alpha = entry_score
            elif entry_flag == UPPER and entry_score < beta:
                beta = entry_score

            if alpha >= beta:
                return entry_score

    moves = _moves(p, q)

    if not moves:
        _store_tt(key, symmetry, 99, -WIN, EXACT, -1)
        return -WIN

    # Continue through forced sequences without consuming decision depth.
    if depth <= 0 and len(moves) > 1:
        value = _static_eval(p, q, moves, _cross_edges(p, q))
        if value == WIN:
            _store_tt(key, symmetry, 99, WIN, EXACT, moves[0])
        return value

    next_depth = depth if len(moves) == 1 else depth - 1
    children = _ordered_children(p, q, moves, tt_move, ply)

    best_score = -INF
    best_move = children[0][1]
    first = True

    for _, move, new_p, new_q in children:
        # Swap roles: new_q belongs to the next player.
        if first:
            score = -_search(new_q, new_p, next_depth, -beta, -alpha, ply + 1)
            first = False
        else:
            # Principal variation search.
            score = -_search(
                new_q, new_p, next_depth, -alpha - 1, -alpha, ply + 1
            )
            if alpha < score < beta:
                score = -_search(
                    new_q, new_p, next_depth, -beta, -alpha, ply + 1
                )

        if score > best_score:
            best_score = score
            best_move = move

        if score > alpha:
            alpha = score

        if alpha >= beta:
            k0, k1 = _killers[ply]
            if move != k0:
                _killers[ply][1] = k0
                _killers[ply][0] = move

            bonus = depth * depth + 1
            _history[move] = min(_history[move] + bonus, 100000)
            break

    if best_score <= alpha_initial:
        flag = UPPER
    elif best_score >= beta_initial:
        flag = LOWER
    else:
        flag = EXACT

    if depth > 0 or abs(best_score) == WIN:
        store_depth = 99 if abs(best_score) == WIN and flag == EXACT else depth
        _store_tt(key, symmetry, store_depth, best_score, flag, best_move)

    return best_score


def _tt_best_move(p, q):
    key, symmetry = _canonical(p, q)
    entry = _TT.get(key)
    if entry is None:
        return -1
    return _map_move(entry[3], symmetry)


def policy(you: list[int], opponent: list[int]) -> str:
    global _deadline, _nodes, _history, _killers, _TT

    p = _to_bitboard(you)
    q = _to_bitboard(opponent)

    legal = _moves(p, q)

    # A policy is normally never called on a terminal state. This preserves
    # the required string format if the surrounding engine nevertheless does.
    if not legal:
        return "0,0,U"

    # The first legal move is retained throughout as a timeout-safe fallback.
    best_move = legal[0]
    if len(legal) == 1:
        return MOVE_TEXT[best_move]

    # Bound memory across long-running arena processes.
    if len(_TT) > 260000:
        _TT.clear()

    _history = [0] * (CELLS * CELLS)
    _killers = [[-1, -1] for _ in range(CELLS + 2)]
    _nodes = 0
    _deadline = perf_counter() + 0.92

    previous_score = 0
    maximum_depth = max(1, (p | q).bit_count())

    try:
        for depth in range(1, maximum_depth + 1):
            if perf_counter() >= _deadline:
                break

            # Aspiration windows improve pruning after the first iterations.
            if depth >= 3 and abs(previous_score) < WIN:
                low = max(-INF, previous_score - 350)
                high = min(INF, previous_score + 350)
                score = _search(p, q, depth, low, high, 0)

                if score <= low or score >= high:
                    score = _search(p, q, depth, -INF, INF, 0)
            else:
                score = _search(p, q, depth, -INF, INF, 0)

            candidate = _tt_best_move(p, q)
            if candidate in legal:
                best_move = candidate

            previous_score = score

            # A full-window root result of either sign is a solved outcome.
            if abs(score) == WIN:
                break

    except _SearchTimeout:
        pass
    except Exception:
        # The legal fallback is preferable to forfeiting because of any
        # unexpected environment-specific issue.
        pass

    return MOVE_TEXT[best_move]

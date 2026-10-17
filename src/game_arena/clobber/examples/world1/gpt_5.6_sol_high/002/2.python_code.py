
import time


# Board and bitboard constants
_ROWS = 5
_COLS = 6
_CELLS = 30
_FULL = (1 << _CELLS) - 1

_NOT_LEFT = 0
_NOT_RIGHT = 0
for _r in range(_ROWS):
    for _c in range(_COLS):
        _bit = 1 << (_r * _COLS + _c)
        if _c != 0:
            _NOT_LEFT |= _bit
        if _c != _COLS - 1:
            _NOT_RIGHT |= _bit

_NEIGHBORS = []
for _i in range(_CELLS):
    _r, _c = divmod(_i, _COLS)
    _m = 0
    if _r:
        _m |= 1 << (_i - _COLS)
    if _r + 1 < _ROWS:
        _m |= 1 << (_i + _COLS)
    if _c:
        _m |= 1 << (_i - 1)
    if _c + 1 < _COLS:
        _m |= 1 << (_i + 1)
    _NEIGHBORS.append(_m)
_NEIGHBORS = tuple(_NEIGHBORS)

# Six-bit row reversal, used for geometric symmetry canonicalization.
_REV6 = []
for _x in range(64):
    _y = 0
    for _j in range(6):
        if (_x >> _j) & 1:
            _y |= 1 << (5 - _j)
    _REV6.append(_y)
_REV6 = tuple(_REV6)

# Transform 0: identity, 1: horizontal reflection,
# 2: vertical reflection, 3: both reflections.
_TMAP = []
for _t in range(4):
    _mapping = []
    for _i in range(_CELLS):
        _r, _c = divmod(_i, _COLS)
        if _t & 1:
            _c = 5 - _c
        if _t & 2:
            _r = 4 - _r
        _mapping.append(_r * _COLS + _c)
    _TMAP.append(tuple(_mapping))
_TMAP = tuple(_TMAP)

_MATE = 30000
_EXACT = 0
_LOWER = 1
_UPPER = 2

# Persistent data can be reused on later calls in the same game.
_TT = {}
_HISTORY = [0] * 1024

_deadline = 0.0
_nodes = 0
_killers = None
_clock = time.perf_counter


class _SearchTimeout(Exception):
    pass


def _adjacent(mask):
    return (
        ((mask << 6) & _FULL)
        | (mask >> 6)
        | ((mask & _NOT_RIGHT) << 1)
        | ((mask & _NOT_LEFT) >> 1)
    )


def _edge_count(me, opponent):
    """Number of bichromatic orthogonal edges."""
    return (
        (((me << 6) & _FULL) & opponent).bit_count()
        + ((me >> 6) & opponent).bit_count()
        + (((me & _NOT_RIGHT) << 1) & opponent).bit_count()
        + (((me & _NOT_LEFT) >> 1) & opponent).bit_count()
    )


def _profile(owner, target):
    """
    Return:
      number of distinct owner pieces adjacent to target pieces,
      sum of squared target-degrees of those owner pieces.
    """
    a = ((target << 6) & _FULL) & owner
    b = (target >> 6) & owner
    c = ((target & _NOT_RIGHT) << 1) & owner
    d = ((target & _NOT_LEFT) >> 1) & owner

    movable = (a | b | c | d).bit_count()

    edges = a.bit_count() + b.bit_count() + c.bit_count() + d.bit_count()
    pairs = (
        (a & b).bit_count()
        + (a & c).bit_count()
        + (a & d).bit_count()
        + (b & c).bit_count()
        + (b & d).bit_count()
        + (c & d).bit_count()
    )
    degree_squared = edges + 2 * pairs
    return movable, degree_squared


def _evaluate(me, opponent):
    """
    Static score from the perspective of the side to move.

    Concentrating many boundary edges on a small number of friendly pieces is
    often useful in Clobber: moving such a piece can erase several threats at
    once. Material is included with a lower weight.
    """
    my_movable, my_sq = _profile(me, opponent)
    opp_movable, opp_sq = _profile(opponent, me)

    material = me.bit_count() - opponent.bit_count()

    return (
        14 * (opp_movable - my_movable)
        + 4 * (my_sq - opp_sq)
        + 3 * material
    )


def _generate_moves(me, opponent):
    # A move is packed as source*32 + destination.
    result = []
    pieces = me
    while pieces:
        source_bit = pieces & -pieces
        source = source_bit.bit_length() - 1
        targets = _NEIGHBORS[source] & opponent
        while targets:
            destination_bit = targets & -targets
            destination = destination_bit.bit_length() - 1
            result.append((source << 5) | destination)
            targets ^= destination_bit
        pieces ^= source_bit
    return result


def _apply(me, opponent, move):
    source = move >> 5
    destination = move & 31
    source_bit = 1 << source
    destination_bit = 1 << destination

    # At the child, the old opponent is the side to move.
    child_me = opponent ^ destination_bit
    child_opponent = (me ^ source_bit) | destination_bit
    return child_me, child_opponent


def _mask_transforms(mask):
    r0 = mask & 63
    r1 = (mask >> 6) & 63
    r2 = (mask >> 12) & 63
    r3 = (mask >> 18) & 63
    r4 = (mask >> 24) & 63

    horizontal = (
        _REV6[r0]
        | (_REV6[r1] << 6)
        | (_REV6[r2] << 12)
        | (_REV6[r3] << 18)
        | (_REV6[r4] << 24)
    )
    vertical = r4 | (r3 << 6) | (r2 << 12) | (r1 << 18) | (r0 << 24)
    both = (
        _REV6[r4]
        | (_REV6[r3] << 6)
        | (_REV6[r2] << 12)
        | (_REV6[r1] << 18)
        | (_REV6[r0] << 24)
    )
    return mask, horizontal, vertical, both


def _canonical(me, opponent):
    my_forms = _mask_transforms(me)
    opp_forms = _mask_transforms(opponent)

    best_t = 0
    best_key = my_forms[0] | (opp_forms[0] << 30)
    for t in (1, 2, 3):
        key = my_forms[t] | (opp_forms[t] << 30)
        if key < best_key:
            best_key = key
            best_t = t
    return best_key, best_t


def _transform_move(move, transform):
    if move < 0:
        return -1
    source = move >> 5
    destination = move & 31
    mapping = _TMAP[transform]
    return (mapping[source] << 5) | mapping[destination]


def _ordered_moves(me, opponent, moves, tt_move, ply):
    scored = []
    killer0, killer1 = _killers[ply] if ply < len(_killers) else (-1, -1)

    for move in moves:
        child_me, child_opponent = _apply(me, opponent, move)
        replies = _edge_count(child_me, child_opponent)

        if replies == 0:
            score = 2_000_000
        else:
            # Negate the child's evaluation because it is from the
            # opponent's perspective.
            score = -32 * _evaluate(child_me, child_opponent)
            score -= 3 * replies

        if move == tt_move:
            score += 1_000_000
        if move == killer0:
            score += 500_000
        elif move == killer1:
            score += 400_000

        score += _HISTORY[move]
        scored.append((score, move))

    scored.sort(reverse=True)
    return [move for _, move in scored]


def _store_tt(key, depth, value, flag, canonical_move):
    old = _TT.get(key)
    if old is None or depth >= old[0] or flag == _EXACT:
        _TT[key] = (depth, value, flag, canonical_move)


def _search(me, opponent, depth, alpha, beta, ply):
    global _nodes

    _nodes += 1
    if (_nodes & 255) == 0 and _clock() >= _deadline:
        raise _SearchTimeout

    # Avoid symmetry and dictionary overhead on the large leaf layer.
    if depth <= 0:
        if not (me & _adjacent(opponent)):
            return -_MATE
        return _evaluate(me, opponent)

    original_alpha = alpha
    original_beta = beta

    key, transform = _canonical(me, opponent)
    entry = _TT.get(key)
    tt_move = -1

    if entry is not None:
        entry_depth, entry_value, entry_flag, stored_move = entry
        if stored_move >= 0:
            # All four transforms are their own inverses.
            tt_move = _transform_move(stored_move, transform)

        if entry_depth >= depth:
            if entry_flag == _EXACT:
                return entry_value
            if entry_flag == _LOWER:
                if entry_value > alpha:
                    alpha = entry_value
            else:
                if entry_value < beta:
                    beta = entry_value
            if alpha >= beta:
                return entry_value

    moves = _generate_moves(me, opponent)
    if not moves:
        _store_tt(key, 60, -_MATE, _EXACT, -1)
        return -_MATE

    ordered = _ordered_moves(me, opponent, moves, tt_move, ply)

    best_value = -_MATE
    best_move = ordered[0]
    first = True

    for move in ordered:
        child_me, child_opponent = _apply(me, opponent, move)

        if first:
            value = -_search(
                child_me, child_opponent, depth - 1, -beta, -alpha, ply + 1
            )
            first = False
        else:
            # Principal-variation search: try a null window first.
            value = -_search(
                child_me, child_opponent, depth - 1, -alpha - 1, -alpha, ply + 1
            )
            if alpha < value < beta:
                value = -_search(
                    child_me, child_opponent, depth - 1, -beta, -alpha, ply + 1
                )

        if value > best_value:
            best_value = value
            best_move = move

        if value > alpha:
            alpha = value

        if alpha >= beta:
            if ply < len(_killers):
                if move != _killers[ply][0]:
                    _killers[ply][1] = _killers[ply][0]
                    _killers[ply][0] = move
            _HISTORY[move] = min(
                100_000, _HISTORY[move] + depth * depth
            )
            break

    if best_value <= original_alpha:
        flag = _UPPER
    elif best_value >= original_beta:
        flag = _LOWER
    else:
        flag = _EXACT

    stored_depth = 60 if flag == _EXACT and abs(best_value) == _MATE else depth
    canonical_move = _transform_move(best_move, transform)
    _store_tt(key, stored_depth, best_value, flag, canonical_move)
    return best_value


def _tt_best_move(me, opponent):
    key, transform = _canonical(me, opponent)
    entry = _TT.get(key)
    if entry is None or entry[3] < 0:
        return -1
    return _transform_move(entry[3], transform)


def _to_mask(board):
    mask = 0

    nested = False
    try:
        if len(board) == 5:
            first = board[0]
            nested = hasattr(first, "__len__")
    except Exception:
        nested = False

    if nested:
        for r in range(5):
            row = board[r]
            for c in range(6):
                if row[c]:
                    mask |= 1 << (r * 6 + c)
    else:
        values = list(board)
        for i in range(min(30, len(values))):
            if values[i]:
                mask |= 1 << i

    return mask


def _move_string(move):
    source = move >> 5
    destination = move & 31
    row, col = divmod(source, 6)

    if destination == source - 6:
        direction = "U"
    elif destination == source + 1:
        direction = "R"
    elif destination == source + 6:
        direction = "D"
    else:
        direction = "L"

    return f"{row},{col},{direction}"


def policy(you: list[int], opponent: list[int]) -> str:
    global _deadline, _nodes, _killers

    start = _clock()
    _deadline = start + 0.94
    _nodes = 0
    _killers = [[-1, -1] for _ in range(34)]

    # Bound persistent memory use.
    if len(_TT) > 400_000:
        _TT.clear()

    me = _to_mask(you)
    them = _to_mask(opponent)

    legal_moves = _generate_moves(me, them)

    # A policy is normally never called in a terminal position.
    if not legal_moves:
        return "0,0,U"

    if len(legal_moves) == 1:
        return _move_string(legal_moves[0])

    # Always take an immediate game-winning capture.
    for move in legal_moves:
        child_me, child_opponent = _apply(me, them, move)
        if not (child_me & _adjacent(child_opponent)):
            return _move_string(move)

    previous_tt_move = _tt_best_move(me, them)
    ordered_fallback = _ordered_moves(
        me, them, legal_moves, previous_tt_move, 0
    )
    best_move = ordered_fallback[0]

    total_pieces = (me | them).bit_count()
    maximum_depth = max(1, total_pieces - 1)

    # Iterative deepening ensures the last fully completed search is usable.
    for depth in range(1, maximum_depth + 1):
        if _clock() >= _deadline:
            break
        try:
            value = _search(me, them, depth, -_MATE, _MATE, 0)
            candidate = _tt_best_move(me, them)
            if candidate in legal_moves:
                best_move = candidate

            # With uniform mate scores, either sign is a proven game result.
            if abs(value) == _MATE:
                break
        except _SearchTimeout:
            break

    return _move_string(best_move)

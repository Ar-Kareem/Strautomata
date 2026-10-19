
import time

# ---------------------------------------------------------------------------
# Board geometry and bitboard tables
# ---------------------------------------------------------------------------

SIZE = 6
NSQUARES = 36
FULL_MASK = (1 << NSQUARES) - 1
MATE = 1000000
INF = 99

DIRECTIONS = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),            (0, 1),
    (1, -1),  (1, 0),   (1, 1),
)

RAYS = []
NEIGHBORS = []
CENTER = []

for sq in range(NSQUARES):
    r, c = divmod(sq, SIZE)

    square_rays = []
    neighbor_mask = 0

    for dr, dc in DIRECTIONS:
        ray = []
        nr, nc = r + dr, c + dc
        if 0 <= nr < SIZE and 0 <= nc < SIZE:
            neighbor_mask |= 1 << (nr * SIZE + nc)

        while 0 <= nr < SIZE and 0 <= nc < SIZE:
            ray.append(nr * SIZE + nc)
            nr += dr
            nc += dc

        square_rays.append(tuple(ray))

    RAYS.append(tuple(square_rays))
    NEIGHBORS.append(neighbor_mask)

    # Mild preference for flexible central landing squares.
    CENTER.append(min(r, SIZE - 1 - r) + min(c, SIZE - 1 - c))

RAYS = tuple(RAYS)
NEIGHBORS = tuple(NEIGHBORS)
CENTER = tuple(CENTER)

_deadline = 0.0
_history = {}
_pv_moves = {}


class _SearchTimeout(Exception):
    pass


# ---------------------------------------------------------------------------
# Bitboard and move utilities
# A move is packed as: from | (to << 6) | (arrow << 12)
# ---------------------------------------------------------------------------

def _pack_move(fr, to, arrow):
    return fr | (to << 6) | (arrow << 12)


def _unpack_move(move):
    return move & 63, (move >> 6) & 63, (move >> 12) & 63


def _apply_move(me, arrows, move):
    fr, to, arrow = _unpack_move(move)
    new_me = (me ^ (1 << fr)) | (1 << to)
    new_arrows = arrows | (1 << arrow)
    return new_me, new_arrows


def _first_legal_move(me, opp, arrows):
    """Finds a legal move very quickly for the timeout-safe fallback."""
    occupied = me | opp | arrows
    pieces = me

    while pieces:
        low = pieces & -pieces
        fr = low.bit_length() - 1
        pieces ^= low

        for ray in RAYS[fr]:
            for to in ray:
                if occupied & (1 << to):
                    break

                # Shooting back to the vacated origin is always legal because
                # the just-traversed path was clear.
                return _pack_move(fr, to, fr)

    return None


# ---------------------------------------------------------------------------
# Mobility and evaluation
# ---------------------------------------------------------------------------

def _reachable_count(square, occupied):
    count = 0
    for ray in RAYS[square]:
        for target in ray:
            if occupied & (1 << target):
                break
            count += 1
    return count


def _mobility_profile(pieces, occupied):
    total = 0
    trapped = 0
    count = 0

    while pieces:
        low = pieces & -pieces
        square = low.bit_length() - 1
        pieces ^= low

        liberty = _reachable_count(square, occupied)
        total += liberty
        count += 1
        if liberty == 0:
            trapped += 1

    return total, trapped, count


def _queen_distances(starts, occupied):
    dist = [INF] * NSQUARES
    queue = []
    pieces = starts

    while pieces:
        low = pieces & -pieces
        square = low.bit_length() - 1
        pieces ^= low
        dist[square] = 0
        queue.append(square)

    head = 0
    while head < len(queue):
        square = queue[head]
        head += 1
        next_distance = dist[square] + 1

        for ray in RAYS[square]:
            for target in ray:
                bit = 1 << target
                if occupied & bit:
                    break
                if dist[target] == INF:
                    dist[target] = next_distance
                    queue.append(target)

    return dist


def _king_distances(starts, occupied):
    dist = [INF] * NSQUARES
    queue = []
    pieces = starts

    while pieces:
        low = pieces & -pieces
        square = low.bit_length() - 1
        pieces ^= low
        dist[square] = 0
        queue.append(square)

    head = 0
    while head < len(queue):
        square = queue[head]
        head += 1
        next_distance = dist[square] + 1
        candidates = NEIGHBORS[square] & ~occupied & FULL_MASK

        while candidates:
            low = candidates & -candidates
            target = low.bit_length() - 1
            candidates ^= low

            if dist[target] == INF:
                dist[target] = next_distance
                queue.append(target)

    return dist


def _evaluate(me, opp, arrows):
    occupied = me | opp | arrows

    my_mobility, my_trapped, _ = _mobility_profile(me, occupied)
    if my_mobility == 0:
        # "me" is the player whose turn it is.
        return -MATE

    opp_mobility, opp_trapped, _ = _mobility_profile(opp, occupied)

    my_q = _queen_distances(me, occupied)
    op_q = _queen_distances(opp, occupied)
    my_k = _king_distances(me, occupied)
    op_k = _king_distances(opp, occupied)

    empty = FULL_MASK & ~occupied
    territory = 0

    while empty:
        low = empty & -empty
        square = low.bit_length() - 1
        empty ^= low

        mq = my_q[square]
        oq = op_q[square]

        if mq == INF and oq == INF:
            continue
        elif oq == INF:
            territory += 18
        elif mq == INF:
            territory -= 18
        elif mq < oq:
            territory += 5
        elif oq < mq:
            territory -= 5
        else:
            # King-distance acts as a tie-breaker for equally close queen
            # territory and rewards locally secure regions.
            mk = my_k[square]
            ok = op_k[square]

            if mk == INF and ok != INF:
                territory -= 4
            elif ok == INF and mk != INF:
                territory += 4
            elif mk < ok:
                territory += 2
            elif ok < mk:
                territory -= 2

    score = territory
    score += 2 * (my_mobility - opp_mobility)
    score += 32 * (opp_trapped - my_trapped)

    # If every opposing amazon is currently immobilized, the position is
    # usually nearly won, though moving can occasionally open a route.
    if opp_mobility == 0:
        score += 220

    return score


# ---------------------------------------------------------------------------
# Move generation and ordering
# ---------------------------------------------------------------------------

def _quick_move_score(new_me, opp, arrows, to, arrow):
    occupied = new_me | opp | arrows

    my_mobility, my_trapped, _ = _mobility_profile(new_me, occupied)
    op_mobility, op_trapped, _ = _mobility_profile(opp, occupied)

    adjacent_opponents = (NEIGHBORS[arrow] & opp).bit_count()
    adjacent_friends = (NEIGHBORS[arrow] & new_me).bit_count()

    score = 6 * (my_mobility - op_mobility)
    score += 70 * (op_trapped - my_trapped)
    score += 2 * CENTER[to]
    score += 12 * adjacent_opponents
    score -= 5 * adjacent_friends
    return score


def _generate_ordered_moves(me, opp, arrows, limit=None, preferred=None):
    occupied = me | opp | arrows
    scored = []
    pieces = me
    generated = 0

    while pieces:
        low = pieces & -pieces
        fr = low.bit_length() - 1
        pieces ^= low
        from_bit = 1 << fr

        for move_ray in RAYS[fr]:
            for to in move_ray:
                to_bit = 1 << to
                if occupied & to_bit:
                    break

                moved_me = (me ^ from_bit) | to_bit
                moved_occupied = (occupied ^ from_bit) | to_bit

                for arrow_ray in RAYS[to]:
                    for arrow in arrow_ray:
                        arrow_bit = 1 << arrow
                        if moved_occupied & arrow_bit:
                            break

                        move = _pack_move(fr, to, arrow)
                        new_arrows = arrows | arrow_bit
                        score = _quick_move_score(
                            moved_me, opp, new_arrows, to, arrow
                        )

                        score += _history.get(move, 0)
                        if move == preferred:
                            score += 10000000

                        scored.append((score, move))
                        generated += 1

                        if (generated & 255) == 0:
                            if time.perf_counter() >= _deadline:
                                raise _SearchTimeout

    scored.sort(reverse=True)

    if limit is not None and len(scored) > limit:
        scored = scored[:limit]

    return [item[1] for item in scored]


# ---------------------------------------------------------------------------
# Selective negamax search
# ---------------------------------------------------------------------------

def _node_limit(depth, empty_count):
    # With few empty cells, every move consumes one of them, so an unrestricted
    # search can often solve the complete remaining game.
    if empty_count <= 8:
        return None

    if depth <= 1:
        return 26
    if depth == 2:
        return 30
    if depth == 3:
        return 25
    return 21


def _negamax(me, opp, arrows, depth, alpha, beta):
    if time.perf_counter() >= _deadline:
        raise _SearchTimeout

    if depth == 0:
        return _evaluate(me, opp, arrows)

    occupied = me | opp | arrows
    empty_count = (FULL_MASK & ~occupied).bit_count()
    state_key = (me, opp, arrows)
    preferred = _pv_moves.get(state_key)

    moves = _generate_ordered_moves(
        me,
        opp,
        arrows,
        limit=_node_limit(depth, empty_count),
        preferred=preferred,
    )

    if not moves:
        return -MATE

    best_value = -MATE
    best_move = moves[0]

    for move in moves:
        new_me, new_arrows = _apply_move(me, arrows, move)

        value = -_negamax(
            opp,
            new_me,
            new_arrows,
            depth - 1,
            -beta,
            -alpha,
        )

        if value > best_value:
            best_value = value
            best_move = move

        if value > alpha:
            alpha = value

        if alpha >= beta:
            _history[move] = min(
                5000,
                _history.get(move, 0) + depth * depth + 2
            )
            break

    _pv_moves[state_key] = best_move
    return best_value


# ---------------------------------------------------------------------------
# Public policy API
# ---------------------------------------------------------------------------

def policy(board) -> str:
    global _deadline, _history, _pv_moves

    start_time = time.perf_counter()
    _deadline = start_time + 0.88
    _history = {}
    _pv_moves = {}

    me = 0
    opp = 0
    arrows = 0

    for r in range(SIZE):
        for c in range(SIZE):
            value = int(board[r][c])
            bit = 1 << (r * SIZE + c)

            if value == 1:
                me |= bit
            elif value == 2:
                opp |= bit
            elif value == -1:
                arrows |= bit

    fallback = _first_legal_move(me, opp, arrows)

    # The environment promises not to call policy in terminal positions.
    if fallback is None:
        return ""

    best_move = fallback

    try:
        root_moves = _generate_ordered_moves(
            me, opp, arrows, limit=None, preferred=None
        )
    except _SearchTimeout:
        root_moves = []

    if not root_moves:
        fr, to, arrow = _unpack_move(best_move)
        return (
            f"{fr // SIZE},{fr % SIZE}:"
            f"{to // SIZE},{to % SIZE}:"
            f"{arrow // SIZE},{arrow % SIZE}"
        )

    # The first ordered move is already a strong mobility-based fallback.
    best_move = root_moves[0]

    occupied = me | opp | arrows
    empty_count = (FULL_MASK & ~occupied).bit_count()

    if empty_count <= 8:
        max_depth = empty_count
    else:
        max_depth = 5

    root_limits = {
        1: 200,
        2: 72,
        3: 42,
        4: 28,
        5: 20,
    }

    for depth in range(1, max_depth + 1):
        if time.perf_counter() >= _deadline - 0.012:
            break

        if empty_count <= 8:
            selected = root_moves
        else:
            limit = root_limits.get(depth, 18)
            selected = root_moves[:limit]

        iteration_values = []
        iteration_best = None
        iteration_best_value = -MATE
        alpha = -MATE

        try:
            for move in selected:
                if time.perf_counter() >= _deadline:
                    raise _SearchTimeout

                new_me, new_arrows = _apply_move(me, arrows, move)
                value = -_negamax(
                    opp,
                    new_me,
                    new_arrows,
                    depth - 1,
                    -MATE,
                    -alpha,
                )

                iteration_values.append((value, move))

                if value > iteration_best_value:
                    iteration_best_value = value
                    iteration_best = move

                if value > alpha:
                    alpha = value

        except _SearchTimeout:
            break

        if iteration_best is not None:
            best_move = iteration_best

            # Preserve deeper-search ordering for the next iteration while
            # retaining all unsearched legal root moves.
            iteration_values.sort(reverse=True)
            searched_set = {move for _, move in iteration_values}
            root_moves = (
                [move for _, move in iteration_values]
                + [move for move in root_moves if move not in searched_set]
            )

            if iteration_best_value >= MATE:
                break

    fr, to, arrow = _unpack_move(best_move)
    return (
        f"{fr // SIZE},{fr % SIZE}:"
        f"{to // SIZE},{to % SIZE}:"
        f"{arrow // SIZE},{arrow % SIZE}"
    )

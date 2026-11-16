
import time

BOARD_SIZE = 6
NUM_SQUARES = 36
FULL_MASK = (1 << NUM_SQUARES) - 1
INF = 99
WIN_SCORE = 100000

DIRECTIONS = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
)

RAYS = []
NEIGHBORS = []
OPEN_DEGREE = []

for sq in range(NUM_SQUARES):
    r, c = divmod(sq, BOARD_SIZE)
    square_rays = []
    open_degree = 0

    for dr, dc in DIRECTIONS:
        ray = []
        nr, nc = r + dr, c + dc
        while 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
            ray.append(nr * BOARD_SIZE + nc)
            nr += dr
            nc += dc
        square_rays.append(tuple(ray))
        open_degree += len(ray)

    RAYS.append(tuple(square_rays))
    OPEN_DEGREE.append(open_degree)

    adjacent = []
    for dr, dc in DIRECTIONS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
            adjacent.append(nr * BOARD_SIZE + nc)
    NEIGHBORS.append(tuple(adjacent))

RAYS = tuple(RAYS)
NEIGHBORS = tuple(NEIGHBORS)
OPEN_DEGREE = tuple(OPEN_DEGREE)

BETWEEN = [[-1] * NUM_SQUARES for _ in range(NUM_SQUARES)]
LINE_DISTANCE = [[0] * NUM_SQUARES for _ in range(NUM_SQUARES)]

for a in range(NUM_SQUARES):
    ar, ac = divmod(a, BOARD_SIZE)
    for b in range(NUM_SQUARES):
        if a == b:
            continue

        br, bc = divmod(b, BOARD_SIZE)
        rr = br - ar
        cc = bc - ac

        if rr == 0:
            dr, dc = 0, 1 if cc > 0 else -1
        elif cc == 0:
            dr, dc = 1 if rr > 0 else -1, 0
        elif abs(rr) == abs(cc):
            dr = 1 if rr > 0 else -1
            dc = 1 if cc > 0 else -1
        else:
            continue

        mask = 0
        r, c = ar + dr, ac + dc
        distance = 0

        while (r, c) != (br, bc):
            mask |= 1 << (r * BOARD_SIZE + c)
            r += dr
            c += dc
            distance += 1

        BETWEEN[a][b] = mask
        LINE_DISTANCE[a][b] = distance + 1

BETWEEN = tuple(tuple(row) for row in BETWEEN)
LINE_DISTANCE = tuple(tuple(row) for row in LINE_DISTANCE)

_EVAL_CACHE = {}
_DEADLINE = 0.0
_ITERATION_DEPTH = 1
_EMPTY_COUNT = 0


class _SearchTimeout(Exception):
    pass


def _check_time():
    if time.perf_counter() >= _DEADLINE:
        raise _SearchTimeout


def _apply_move(me, them, arrows, move):
    src, dst, arrow = move
    new_me = (me ^ (1 << src)) | (1 << dst)
    new_arrows = arrows | (1 << arrow)
    return them, new_me, new_arrows


def _mobility(mask, occupancy):
    total = 0
    maximum = 0

    pieces = mask
    while pieces:
        low = pieces & -pieces
        sq = low.bit_length() - 1
        pieces ^= low

        degree = 0
        for ray in RAYS[sq]:
            for target in ray:
                bit = 1 << target
                if occupancy & bit:
                    break
                degree += 1

        total += degree
        if degree > maximum:
            maximum = degree

    return total, maximum


def _queen_distances(starts, occupancy):
    distances = [INF] * NUM_SQUARES
    frontier = []
    pieces = starts

    while pieces:
        low = pieces & -pieces
        sq = low.bit_length() - 1
        pieces ^= low
        distances[sq] = 0
        frontier.append(sq)

    level = 0
    while frontier:
        level += 1
        next_frontier = []

        for sq in frontier:
            for ray in RAYS[sq]:
                for target in ray:
                    bit = 1 << target
                    if occupancy & bit:
                        break
                    if distances[target] == INF:
                        distances[target] = level
                        next_frontier.append(target)

        frontier = next_frontier

    return distances


def _king_distances(starts, occupancy):
    distances = [INF] * NUM_SQUARES
    frontier = []
    pieces = starts

    while pieces:
        low = pieces & -pieces
        sq = low.bit_length() - 1
        pieces ^= low
        distances[sq] = 0
        frontier.append(sq)

    level = 0
    while frontier:
        level += 1
        next_frontier = []

        for sq in frontier:
            for target in NEIGHBORS[sq]:
                bit = 1 << target
                if occupancy & bit:
                    continue
                if distances[target] == INF:
                    distances[target] = level
                    next_frontier.append(target)

        frontier = next_frontier

    return distances


def _evaluate(me, them, arrows):
    key = (me, them, arrows)
    cached = _EVAL_CACHE.get(key)
    if cached is not None:
        return cached

    occupancy = me | them | arrows
    empty = FULL_MASK ^ occupancy

    my_mobility, my_max = _mobility(me, occupancy)
    if my_mobility == 0:
        _EVAL_CACHE[key] = -WIN_SCORE
        return -WIN_SCORE

    opp_mobility, opp_max = _mobility(them, occupancy)

    my_q = _queen_distances(me, occupancy)
    opp_q = _queen_distances(them, occupancy)

    need_king = False
    cells = empty
    while cells:
        low = cells & -cells
        sq = low.bit_length() - 1
        cells ^= low
        if my_q[sq] != INF and my_q[sq] == opp_q[sq]:
            need_king = True
            break

    if need_king:
        my_k = _king_distances(me, occupancy)
        opp_k = _king_distances(them, occupancy)
    else:
        my_k = None
        opp_k = None

    score = 0
    cells = empty

    while cells:
        low = cells & -cells
        sq = low.bit_length() - 1
        cells ^= low

        dm = my_q[sq]
        do = opp_q[sq]

        if dm == INF:
            if do != INF:
                score -= 110
            continue

        if do == INF:
            score += 110
            continue

        if dm < do:
            score += 28
        elif do < dm:
            score -= 28
        elif my_k is not None:
            km = my_k[sq]
            ko = opp_k[sq]
            if km < ko:
                score += 9
            elif ko < km:
                score -= 9

        score += 14 // (dm + 1)
        score -= 14 // (do + 1)

    score += 2 * (my_mobility - opp_mobility)
    score += 3 * (my_max - opp_max)

    if opp_mobility == 0:
        score += 350

    _EVAL_CACHE[key] = score
    return score


def _generate_scored_moves(me, them, arrows, check_deadline=True):
    occupancy = me | them | arrows
    result = []
    pieces = me
    work_counter = 0

    while pieces:
        low = pieces & -pieces
        src = low.bit_length() - 1
        pieces ^= low
        src_bit = 1 << src

        for move_ray in RAYS[src]:
            for dst in move_ray:
                dst_bit = 1 << dst
                if occupancy & dst_bit:
                    break

                after_move = (occupancy ^ src_bit) | dst_bit
                arrow_rays = []
                base_degree = 0

                for arrow_ray in RAYS[dst]:
                    available = []
                    for arrow in arrow_ray:
                        arrow_bit = 1 << arrow
                        if after_move & arrow_bit:
                            break
                        available.append(arrow)
                    arrow_rays.append(available)
                    base_degree += len(available)

                for available in arrow_rays:
                    ray_length = len(available)
                    for index, arrow in enumerate(available):
                        remaining_degree = base_degree - (ray_length - index)
                        impact = 0

                        opponents = them
                        while opponents:
                            opp_low = opponents & -opponents
                            opp_sq = opp_low.bit_length() - 1
                            opponents ^= opp_low

                            between = BETWEEN[opp_sq][arrow]
                            if between >= 0 and (between & after_move) == 0:
                                distance = LINE_DISTANCE[opp_sq][arrow]
                                impact += 14 + 3 * (6 - distance)
                                if distance == 1:
                                    impact += 10

                        quick_score = (
                            5 * remaining_degree
                            + 2 * OPEN_DEGREE[dst]
                            + OPEN_DEGREE[arrow]
                            + impact
                        )
                        result.append((quick_score, (src, dst, arrow)))

                work_counter += 1
                if check_deadline and (work_counter & 31) == 0:
                    _check_time()

    return result


def _ranked_moves(me, them, arrows, limit):
    generated = _generate_scored_moves(me, them, arrows, True)
    if not generated:
        return []

    generated.sort(key=lambda item: item[0], reverse=True)

    pool_size = min(
        len(generated),
        max(limit * 2, limit + 12)
    )
    pool = generated[:pool_size]

    ranked = []
    for index, (quick, move) in enumerate(pool):
        child = _apply_move(me, them, arrows, move)
        static_value = -_evaluate(*child)
        ranked.append((static_value, quick, move))

        if (index & 7) == 0:
            _check_time()

    ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [item[2] for item in ranked[:limit]]


def _beam_limit(depth):
    if _EMPTY_COUNT <= 10:
        if depth == 1:
            return 54
        if depth == 2:
            return 38
        return 28

    if _ITERATION_DEPTH == 2:
        return 34

    if depth == 1:
        return 18
    if depth == 2:
        return 22
    return 16


def _negamax(me, them, arrows, depth, alpha, beta, ply):
    _check_time()

    if depth <= 0:
        return _evaluate(me, them, arrows)

    moves = _ranked_moves(me, them, arrows, _beam_limit(depth))
    if not moves:
        return -WIN_SCORE + ply

    best = -WIN_SCORE * 2

    for move in moves:
        child = _apply_move(me, them, arrows, move)
        value = -_negamax(
            child[0], child[1], child[2],
            depth - 1, -beta, -alpha, ply + 1
        )

        if value > best:
            best = value
        if value > alpha:
            alpha = value
        if alpha >= beta:
            break

    return best


def _root_search(me, them, arrows, moves, depth):
    best_value = -WIN_SCORE * 2
    best_move = moves[0]
    alpha = -WIN_SCORE * 2
    beta = WIN_SCORE * 2
    values = []

    for move in moves:
        _check_time()
        child = _apply_move(me, them, arrows, move)
        value = -_negamax(
            child[0], child[1], child[2],
            depth - 1, -beta, -alpha, 1
        )
        values.append((value, move))

        if value > best_value:
            best_value = value
            best_move = move
        if value > alpha:
            alpha = value

    values.sort(key=lambda item: item[0], reverse=True)
    return best_move, best_value, [item[1] for item in values]


def _format_move(move):
    src, dst, arrow = move
    sr, sc = divmod(src, BOARD_SIZE)
    dr, dc = divmod(dst, BOARD_SIZE)
    ar, ac = divmod(arrow, BOARD_SIZE)
    return f"{sr},{sc}:{dr},{dc}:{ar},{ac}"


def policy(board) -> str:
    global _EVAL_CACHE
    global _DEADLINE
    global _ITERATION_DEPTH
    global _EMPTY_COUNT

    start_time = time.perf_counter()
    _DEADLINE = start_time + 0.92
    _EVAL_CACHE = {}

    me = 0
    them = 0
    arrows = 0

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            value = int(board[r][c])
            bit = 1 << (r * BOARD_SIZE + c)
            if value == 1:
                me |= bit
            elif value == 2:
                them |= bit
            elif value == -1:
                arrows |= bit

    occupancy = me | them | arrows
    _EMPTY_COUNT = NUM_SQUARES - occupancy.bit_count()

    generated = _generate_scored_moves(me, them, arrows, False)
    if not generated:
        return ""

    generated.sort(key=lambda item: item[0], reverse=True)
    fallback = generated[0][1]
    best_move = fallback

    if len(generated) <= 300 or _EMPTY_COUNT <= 16:
        root_pool = generated
    else:
        root_pool = generated[:280]

    root_ranked = []

    try:
        for index, (quick, move) in enumerate(root_pool):
            child = _apply_move(me, them, arrows, move)
            value = -_evaluate(*child)
            root_ranked.append((value, quick, move))

            if value > root_ranked[0][0]:
                best_move = move

            if (index & 7) == 0:
                _check_time()

        root_ranked.sort(
            key=lambda item: (item[0], item[1]),
            reverse=True
        )
        best_move = root_ranked[0][2]
        ordered = [item[2] for item in root_ranked]

        max_depth = 8 if _EMPTY_COUNT <= 9 else 5

        for depth in range(2, max_depth + 1):
            _ITERATION_DEPTH = depth

            if depth == 2:
                cap = 120 if _EMPTY_COUNT <= 14 else 72
            elif depth == 3:
                cap = 64 if _EMPTY_COUNT <= 12 else 42
            elif depth == 4:
                cap = 42 if _EMPTY_COUNT <= 10 else 28
            else:
                cap = 30

            candidates = ordered[:min(cap, len(ordered))]
            iteration_move, _, iteration_order = _root_search(
                me, them, arrows, candidates, depth
            )

            best_move = iteration_move
            ordered = iteration_order

    except _SearchTimeout:
        pass

    return _format_move(best_move)

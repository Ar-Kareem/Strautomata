
import time

_ALL = (1 << 36) - 1
_MATE = 1_000_000
_INF = 10_000_000

# Every length-five winning segment.
_LINES = []
for _dr, _dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
    for _r in range(6):
        for _c in range(6):
            _er = _r + 4 * _dr
            _ec = _c + 4 * _dc
            if 0 <= _er < 6 and 0 <= _ec < 6:
                _LINES.append(sum(
                    1 << ((_r + k * _dr) * 6 + _c + k * _dc)
                    for k in range(5)
                ))
_LINES = tuple(_LINES)

# Rotation IDs are 2 * quadrant + direction, with L=0 and R=1.
_ROT_DATA = []
_MAPS = []
_QCELLS = []
_QOFFSETS = []

for _qr, _qc in ((0, 0), (0, 3), (3, 0), (3, 3)):
    _off = _qr * 6 + _qc
    _QOFFSETS.append(_off)
    _cells = tuple((_qr + j // 3) * 6 + _qc + j % 3
                   for j in range(9))
    _QCELLS.append(_cells)
    _mask = sum(1 << i for i in _cells)

    for _direction in range(2):
        _mapping = list(range(36))
        _dest = []
        for _j, _src in enumerate(_cells):
            _u, _v = divmod(_j, 3)
            if _direction == 0:
                _nu, _nv = 2 - _v, _u
            else:
                _nu, _nv = _v, 2 - _u
            _dst = (_qr + _nu) * 6 + _qc + _nv
            _mapping[_src] = _dst
            _dest.append(1 << _dst)

        _table = [0] * 512
        for _p in range(1, 512):
            _bit = _p & -_p
            _table[_p] = (
                _table[_p ^ _bit] | _dest[_bit.bit_length() - 1]
            )
        _ROT_DATA.append((_off, _ALL ^ _mask, tuple(_table)))
        _MAPS.append(tuple(_mapping))

_ROT_DATA = tuple(_ROT_DATA)
_MAPS = tuple(_MAPS)
_QCELLS = tuple(_QCELLS)
_QOFFSETS = tuple(_QOFFSETS)

_CENTERS = sum(1 << i for i in (7, 10, 25, 28))
_WEIGHTS = (0, 2, 12, 72, 420, 30000)

# These local features are unchanged by rotating a quadrant.
_LOCAL_LINES = (7, 56, 448, 73, 146, 292, 273, 84)
_LOCAL_VALUE = tuple(
    sum((0, 0, 3, 18)[(p & m).bit_count()] for m in _LOCAL_LINES)
    for p in range(512)
)


class _Timeout(Exception):
    pass


def _rotate(board, rotation):
    shift, keep, table = _ROT_DATA[rotation]
    x = board >> shift
    pattern = (x & 7) | ((x >> 3) & 56) | ((x >> 6) & 448)
    return (board & keep) | table[pattern]


def _format_action(action):
    square, rotation = divmod(action, 8)
    row, col = divmod(square, 6)
    return f"{row + 1},{col + 1},{rotation // 2},{'LR'[rotation & 1]}"


def policy(you, opponent) -> str:
    deadline = time.perf_counter() + 0.90

    a = 0
    b = 0
    for r in range(6):
        for c in range(6):
            bit = 1 << (6 * r + c)
            if you[r][c]:
                a |= bit
            elif opponent[r][c]:
                b |= bit

    empty = _ALL ^ (a | b)
    first = (empty & -empty).bit_length() - 1
    best_action = first * 8
    empty_count = empty.bit_count()

    rotation_cache = {}
    shape_cache = {}
    node_cache = {}
    transpositions = {}
    preferred = {}

    late = empty_count <= 12
    stored_width = 28 if late else 20

    def check_time():
        if time.perf_counter() >= deadline:
            raise _Timeout

    def rotations(board):
        result = rotation_cache.get(board)
        if result is not None:
            return result
        out = []
        for shift, keep, table in _ROT_DATA:
            x = board >> shift
            p = (x & 7) | ((x >> 3) & 56) | ((x >> 6) & 448)
            out.append((board & keep) | table[p])
        result = tuple(out)
        rotation_cache[board] = result
        return result

    def shape(board):
        """Return (already has five, all single-cell completions)."""
        result = shape_cache.get(board)
        if result is not None:
            return result

        if board.bit_count() < 4:
            result = (False, 0)
        else:
            holes = 0
            for mask in _LINES:
                part = board & mask
                if part == mask:
                    result = (True, 0)
                    shape_cache[board] = result
                    return result
                if part.bit_count() == 4:
                    holes |= mask ^ part
            result = (False, holes)

        shape_cache[board] = result
        return result

    def invariant_features(x, y):
        base = 4 * (
            (x & _CENTERS).bit_count() - (y & _CENTERS).bit_count()
        )
        gains = [0] * 36
        for q, off in enumerate(_QOFFSETS):
            xx = x >> off
            yy = y >> off
            px = (xx & 7) | ((xx >> 3) & 56) | ((xx >> 6) & 448)
            py = (yy & 7) | ((yy >> 3) & 56) | ((yy >> 6) & 448)
            old = _LOCAL_VALUE[px]
            base += old - _LOCAL_VALUE[py]
            for j, square in enumerate(_QCELLS[q]):
                gains[square] = (
                    _LOCAL_VALUE[px | (1 << j)] - old
                    + (4 if j == 4 else 0)
                )
        return base, gains

    def placement_scores(x, y, allowed, rotation, invariant, gains):
        """Evaluate all allowed placements incrementally."""
        base = invariant
        inc = [gains[i] for i in _MAPS[rotation ^ 1]]
        weights = _WEIGHTS

        for mask in _LINES:
            nx = (x & mask).bit_count()
            ny = (y & mask).bit_count()
            if ny == 0:
                base += weights[nx]
                delta = weights[nx + 1] - weights[nx] if nx < 5 else 0
            elif nx == 0:
                base -= weights[ny]
                delta = weights[ny]
            else:
                continue

            cells = mask & allowed
            while cells:
                bit = cells & -cells
                cells ^= bit
                inc[bit.bit_length() - 1] += delta
        return base, inc

    def build(x, y, root=False):
        """
        Node: (kind, terminal_action, ordered_moves, draw_action).
        kind=1: immediate win; kind=-1: no non-losing move.
        A move is (heuristic, resulting_x, resulting_y, action).
        """
        key = (x, y)
        cached = node_cache.get(key)
        if cached is not None:
            return cached
        check_time()

        rx = rotations(x)
        ry = rotations(y)
        seen_bases = set()
        bases = []
        draw_action = None
        nempty = 36 - (x | y).bit_count()

        # Placement followed by rotation is equivalent to rotation followed
        # by placement at the correspondingly mapped square.
        for t in range(8):
            xx, yy = rx[t], ry[t]
            pair = (xx, yy)
            if pair in seen_bases:
                continue
            seen_bases.add(pair)

            vacancies = _ALL ^ (xx | yy)
            wx, hx = shape(xx)
            wy, _ = shape(yy)
            winning = vacancies if wx else hx & vacancies

            if winning:
                p = (winning & -winning).bit_length() - 1
                action = _MAPS[t ^ 1][p] * 8 + t
                if not wy:
                    result = (1, action, (), None)
                    node_cache[key] = result
                    return result
                if draw_action is None:
                    draw_action = action

            if wy:
                continue

            if nempty == 1:
                p = (vacancies & -vacancies).bit_length() - 1
                draw_action = _MAPS[t ^ 1][p] * 8 + t
            else:
                bases.append((t, xx, yy, vacancies))

        invariant, gains = invariant_features(x, y)
        can_enemy_win = y.bit_count() >= 4
        unique_moves = {}

        for t, xx, yy, vacancies in bases:
            check_time()
            safe = vacancies

            if can_enemy_win:
                # Check all possible rotations on the enemy's next turn.
                # The enemy's board is independent of our placement.
                next_x = rotations(xx)
                next_y = rotations(yy)

                for s in range(8):
                    sx, sy = next_x[s], next_y[s]
                    enemy_five, enemy_holes = shape(sy)
                    free = _ALL ^ (sx | sy)
                    threats = enemy_holes & free

                    if not enemy_five and not threats:
                        continue

                    own_five, own_holes = shape(sx)
                    if own_five:
                        # This enemy rotation cannot produce an enemy-only win.
                        continue

                    allowed = own_holes & free
                    if (not enemy_five and threats
                            and not (threats & (threats - 1))):
                        # A single winning square can also be occupied.
                        allowed |= threats

                    if not allowed:
                        safe = 0
                        break

                    safe &= _rotate(allowed, s ^ 1)
                    if not safe:
                        break

            if not safe:
                continue

            base, inc = placement_scores(
                xx, yy, safe, t, invariant, gains
            )
            cells = safe
            while cells:
                bit = cells & -cells
                cells ^= bit
                p = bit.bit_length() - 1
                child_x = xx | bit
                child_key = (child_x, yy)
                if child_key not in unique_moves:
                    action = _MAPS[t ^ 1][p] * 8 + t
                    unique_moves[child_key] = (
                        base + inc[p], child_x, yy, action
                    )

        moves = sorted(
            unique_moves.values(), key=lambda move: move[0], reverse=True
        )
        if not root:
            moves = moves[:stored_width]

        if not moves and draw_action is None:
            result = (-1, None, (), None)
        else:
            result = (0, None, tuple(moves), draw_action)
        node_cache[key] = result
        return result

    def search(x, y, depth, alpha, beta, ply):
        check_time()
        original_alpha, original_beta = alpha, beta
        tt_key = (x, y, depth)

        if depth > 1:
            hit = transpositions.get(tt_key)
            if hit is not None:
                value, bound = hit
                if bound == 0:
                    return value
                if bound > 0:
                    alpha = max(alpha, value)
                else:
                    beta = min(beta, value)
                if alpha >= beta:
                    return value

        kind, action, moves, draw_action = build(x, y)
        if kind == 1:
            return _MATE - ply
        if kind == -1:
            return -_MATE + ply + 2

        best = 0 if draw_action is not None else -_INF
        if depth <= 1:
            if moves:
                best = max(best, moves[0][0])
            return best

        if not moves:
            return 0

        alpha = max(alpha, best)
        if alpha >= beta:
            return best

        if depth == 2:
            width = 24 if late else 14
        else:
            width = 16 if late else 10

        pv = preferred.get((x, y))
        selected = list(moves[:width])
        if pv is not None:
            pv_move = next((m for m in moves if m[3] == pv), None)
            if pv_move is not None:
                selected = [pv_move] + [
                    m for m in selected if m[3] != pv
                ]
                selected = selected[:width]

        best_move = draw_action
        for _, child_x, child_y, move_action in selected:
            value = -search(
                child_y, child_x, depth - 1, -beta, -alpha, ply + 1
            )
            if value > best:
                best = value
                best_move = move_action
            if value > alpha:
                alpha = value
            if alpha >= beta:
                break

        if best_move is not None:
            preferred[(x, y)] = best_move

        if best <= original_alpha:
            bound = -1
        elif best >= original_beta:
            bound = 1
        else:
            bound = 0
        transpositions[tt_key] = (best, bound)
        return best

    try:
        kind, action, root_moves, draw_action = build(a, b, root=True)

        if kind == 1:
            return _format_action(action)

        if kind == -1:
            # Under perfect play the position is lost. Prefer moves giving
            # the opponent the fewest immediate winning replies.
            best_key = None
            invariant, gains = invariant_features(a, b)
            seen = set()

            for t, (xx, yy) in enumerate(zip(rotations(a), rotations(b))):
                check_time()
                if (xx, yy) in seen:
                    continue
                seen.add((xx, yy))

                if shape(yy)[0]:
                    continue

                vacancies = _ALL ^ (xx | yy)
                base, inc = placement_scores(
                    xx, yy, vacancies, t, invariant, gains
                )
                cells = vacancies
                while cells:
                    check_time()
                    bit = cells & -cells
                    cells ^= bit
                    p = bit.bit_length() - 1
                    after = xx | bit
                    winning_replies = 0

                    for enemy, own in zip(rotations(yy), rotations(after)):
                        own_five, _ = shape(own)
                        if own_five:
                            continue
                        enemy_five, holes = shape(enemy)
                        free = _ALL ^ (enemy | own)
                        winning_replies += (
                            free.bit_count() if enemy_five
                            else (holes & free).bit_count()
                        )

                    candidate_key = (-winning_replies, base + inc[p])
                    if best_key is None or candidate_key > best_key:
                        best_key = candidate_key
                        best_action = _MAPS[t ^ 1][p] * 8 + t

            return _format_action(best_action)

        if not root_moves:
            return _format_action(draw_action)

        ordered = list(root_moves)
        best_action = ordered[0][3]
        if draw_action is not None and ordered[0][0] <= 0:
            best_action = draw_action

        # The first iteration examines every safe root move. In particular,
        # it detects forced wins where every enemy response loses next turn.
        for depth in range(2, min(8, empty_count) + 1):
            check_time()
            if depth == 2:
                pool = ordered
            elif depth == 3:
                pool = ordered[:48 if late else 36]
            elif depth == 4:
                pool = ordered[:28 if late else 24]
            else:
                pool = ordered[:20 if late else 16]

            iteration_best = draw_action
            alpha = 0 if draw_action is not None else -_INF
            scored = []

            for move in pool:
                check_time()
                _, child_x, child_y, move_action = move
                value = -search(
                    child_y, child_x, depth - 1, -_INF, -alpha, 1
                )
                scored.append((value, move))

                if value > alpha:
                    alpha = value
                    iteration_best = move_action

                if iteration_best is not None:
                    best_action = iteration_best

                if depth == 2 and value >= _MATE - 4:
                    return _format_action(move_action)

            scored.sort(key=lambda item: (item[0], item[1][0]), reverse=True)
            ordered = [move for _, move in scored]

    except _Timeout:
        pass

    return _format_action(best_action)

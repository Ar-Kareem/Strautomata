
import time


def _idx(x: int, y: int, z: int) -> int:
    return x * 9 + y * 3 + z


COORDS = [(i // 9, (i // 3) % 3, i % 3) for i in range(27)]
CENTER = _idx(1, 1, 1)


def _generate_lines():
    dirs = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx == 0 and dy == 0 and dz == 0:
                    continue
                # Canonical half of directions to avoid duplicates.
                if dx > 0 or (dx == 0 and dy > 0) or (dx == 0 and dy == 0 and dz > 0):
                    dirs.append((dx, dy, dz))

    lines = []
    for x in range(3):
        for y in range(3):
            for z in range(3):
                for dx, dy, dz in dirs:
                    x2, y2, z2 = x + 2 * dx, y + 2 * dy, z + 2 * dz
                    if not (0 <= x2 < 3 and 0 <= y2 < 3 and 0 <= z2 < 3):
                        continue
                    px, py, pz = x - dx, y - dy, z - dz
                    # Start must be the minimal point on the line.
                    if 0 <= px < 3 and 0 <= py < 3 and 0 <= pz < 3:
                        continue
                    lines.append((
                        _idx(x, y, z),
                        _idx(x + dx, y + dy, z + dz),
                        _idx(x2, y2, z2),
                    ))
    return lines


LINES = _generate_lines()
CELL_TO_LINES = [[] for _ in range(27)]
for li, line in enumerate(LINES):
    for c in line:
        CELL_TO_LINES[c].append(li)

CELL_WEIGHT = [len(CELL_TO_LINES[i]) for i in range(27)]

POW3 = [1] * 27
for i in range(1, 27):
    POW3[i] = POW3[i - 1] * 3
HASH_ADD_1 = POW3[:]
HASH_ADD_N1 = [2 * p for p in POW3]

INF = 10**9
MATE = 10**6
MATE_THREAT = 10**5


class _Timeout(Exception):
    pass


def _is_win(arr, last_move: int, player: int) -> bool:
    for li in CELL_TO_LINES[last_move]:
        a, b, c = LINES[li]
        if arr[a] == player and arr[b] == player and arr[c] == player:
            return True
    return False


def _immediate_wins(arr, player: int):
    opp = -player
    wins = set()
    for a, b, c in LINES:
        cp = 0
        co = 0
        empty = -1

        va = arr[a]
        if va == player:
            cp += 1
        elif va == opp:
            co += 1
        else:
            empty = a

        vb = arr[b]
        if vb == player:
            cp += 1
        elif vb == opp:
            co += 1
        else:
            empty = b

        vc = arr[c]
        if vc == player:
            cp += 1
        elif vc == opp:
            co += 1
        else:
            empty = c

        if cp == 2 and co == 0:
            wins.add(empty)
    return wins


def _quick_move_score(arr, m: int, player: int, block_cells=None) -> int:
    opp = -player
    score = CELL_WEIGHT[m] * 10
    if m == CENTER:
        score += 8
    if block_cells is not None and m in block_cells:
        score += 800

    for li in CELL_TO_LINES[m]:
        a, b, c = LINES[li]
        my_count = 1  # after placing at m
        opp_count = 0

        for t in (a, b, c):
            if t == m:
                continue
            v = arr[t]
            if v == player:
                my_count += 1
            elif v == opp:
                opp_count += 1

        if opp_count == 0:
            if my_count == 1:
                score += 4
            elif my_count == 2:
                score += 30
            else:
                score += 5000
        elif my_count == 1:
            if opp_count == 1:
                score += 8
            elif opp_count == 2:
                score += 140

    return score


def _best_from_cells(arr, cells, player: int, block_cells=None):
    best = None
    best_score = -INF
    for m in cells:
        s = _quick_move_score(arr, m, player, block_cells)
        if best is None or s > best_score or (s == best_score and CELL_WEIGHT[m] > CELL_WEIGHT[best]):
            best = m
            best_score = s
    return best


def _fork_moves(arr, player: int, legal):
    forks = []
    for m in legal:
        arr[m] = player
        wins = _immediate_wins(arr, player)
        arr[m] = 0
        if len(wins) >= 2:
            forks.append(m)
    return forks


def _order_moves(arr, legal, player: int, depth: int, hint_move=None, root=False):
    mywins = _immediate_wins(arr, player)
    if mywins:
        ordered = list(mywins)
        ordered.sort(key=lambda m: (_quick_move_score(arr, m, player), CELL_WEIGHT[m]), reverse=True)
        return ordered

    oppwins = _immediate_wins(arr, -player)
    if oppwins:
        ordered = list(oppwins)
        ordered.sort(key=lambda m: (_quick_move_score(arr, m, player, oppwins), CELL_WEIGHT[m]), reverse=True)
        return ordered

    scored = []
    for m in legal:
        s = _quick_move_score(arr, m, player)
        if hint_move == m:
            s += 2000
        scored.append((s, m))

    scored.sort(reverse=True)
    moves = [m for _, m in scored]
    n = len(moves)
    limit = n

    # Mild beam pruning only in wide positions / deeper search.
    if root:
        if depth >= 5 and n > 18:
            limit = 14
        elif depth >= 4 and n > 22:
            limit = 16
    else:
        if depth >= 4 and n > 18:
            limit = 10
        elif depth >= 3 and n > 15:
            limit = 12
        elif depth >= 2 and n > 22:
            limit = 14

    return moves[:limit]


def _static_eval(arr, player: int) -> int:
    opp = -player
    score = 0

    # Positional: central / high-intersection cells are better.
    for i, v in enumerate(arr):
        if v == player:
            score += 3 * CELL_WEIGHT[i]
        elif v == opp:
            score -= 3 * CELL_WEIGHT[i]

    my_win_cells = set()
    opp_win_cells = set()

    for a, b, c in LINES:
        cp = 0
        co = 0
        empty = -1

        va = arr[a]
        if va == player:
            cp += 1
        elif va == opp:
            co += 1
        else:
            empty = a

        vb = arr[b]
        if vb == player:
            cp += 1
        elif vb == opp:
            co += 1
        else:
            empty = b

        vc = arr[c]
        if vc == player:
            cp += 1
        elif vc == opp:
            co += 1
        else:
            empty = c

        if co == 0:
            if cp == 1:
                score += 5
            elif cp == 2:
                score += 60
                my_win_cells.add(empty)
        elif cp == 0:
            if co == 1:
                score -= 6
            elif co == 2:
                score -= 72
                opp_win_cells.add(empty)

    mw = len(my_win_cells)
    ow = len(opp_win_cells)
    score += 140 * mw
    score -= 160 * ow

    if mw >= 2:
        score += 250 + 35 * mw
    if ow >= 2:
        score -= 290 + 40 * ow

    return score


def _quiescence(arr, h: int, player: int, alpha: int, beta: int, last_move: int,
                ply: int, deadline: float, qdepth: int = 4) -> int:
    if time.perf_counter() >= deadline:
        raise _Timeout

    if last_move != -1 and _is_win(arr, last_move, -player):
        return -MATE + ply

    mywins = _immediate_wins(arr, player)
    if mywins:
        return MATE_THREAT - ply + 10 * len(mywins)

    oppwins = _immediate_wins(arr, -player)
    if qdepth > 0 and oppwins:
        # If there are multiple distinct opponent winning cells, we cannot block all.
        if len(oppwins) > 1:
            return -MATE_THREAT + ply - 10 * len(oppwins)

        m = next(iter(oppwins))
        arr[m] = player
        nh = h + (HASH_ADD_1[m] if player == 1 else HASH_ADD_N1[m])
        score = -_quiescence(arr, nh, -player, -beta, -alpha, m, ply + 1, deadline, qdepth - 1)
        arr[m] = 0
        return score

    return _static_eval(arr, player)


def _negamax(arr, h: int, player: int, depth: int, alpha: int, beta: int, last_move: int,
             ply: int, deadline: float, move_cache) -> int:
    if time.perf_counter() >= deadline:
        raise _Timeout

    if last_move != -1 and _is_win(arr, last_move, -player):
        return -MATE + ply

    legal = [i for i in range(27) if arr[i] == 0]
    if not legal:
        return 0

    if depth == 0:
        return _quiescence(arr, h, player, alpha, beta, last_move, ply, deadline)

    hint = move_cache.get((h, player))
    moves = _order_moves(arr, legal, player, depth, hint_move=hint, root=False)

    best = -INF
    best_move = moves[0]

    for m in moves:
        arr[m] = player
        nh = h + (HASH_ADD_1[m] if player == 1 else HASH_ADD_N1[m])
        score = -_negamax(arr, nh, -player, depth - 1, -beta, -alpha, m, ply + 1, deadline, move_cache)
        arr[m] = 0

        if score > best:
            best = score
            best_move = m
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break

    move_cache[(h, player)] = best_move
    return best


def _search_root(arr, h: int, depth: int, deadline: float, move_cache):
    if time.perf_counter() >= deadline:
        raise _Timeout

    legal = [i for i in range(27) if arr[i] == 0]
    hint = move_cache.get((h, 1))
    moves = _order_moves(arr, legal, 1, depth, hint_move=hint, root=True)

    alpha = -INF
    beta = INF
    best_score = -INF
    best_move = moves[0]

    for m in moves:
        if time.perf_counter() >= deadline:
            raise _Timeout

        arr[m] = 1
        nh = h + HASH_ADD_1[m]
        score = -_negamax(arr, nh, -1, depth - 1, -beta, -alpha, m, 1, deadline, move_cache)
        arr[m] = 0

        if score > best_score:
            best_score = score
            best_move = m
        if score > alpha:
            alpha = score

    move_cache[(h, 1)] = best_move
    return best_score, best_move


def _root_tactical_move(arr, legal):
    # Win now.
    mywins = _immediate_wins(arr, 1)
    if mywins:
        return _best_from_cells(arr, mywins, 1)

    # Must block opponent win now (if several, position is likely lost, but block one legally).
    oppwins = _immediate_wins(arr, -1)
    if oppwins:
        return _best_from_cells(arr, oppwins, 1, oppwins)

    # Create a fork.
    myforks = _fork_moves(arr, 1, legal)
    if myforks:
        return _best_from_cells(arr, myforks, 1)

    # Block a unique opponent fork if possible.
    oppforks = _fork_moves(arr, -1, legal)
    if len(oppforks) == 1:
        return oppforks[0]

    # Strong opening bias: take center early.
    if CENTER in legal and len(legal) >= 23:
        return CENTER

    return None


def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    arr = [0] * 27
    for x in range(3):
        for y in range(3):
            base = x * 9 + y * 3
            row = board[x][y]
            arr[base] = row[0]
            arr[base + 1] = row[1]
            arr[base + 2] = row[2]

    legal = [i for i in range(27) if arr[i] == 0]
    if not legal:
        return (0, 0, 0)

    if len(legal) == 1:
        return COORDS[legal[0]]

    if len(legal) == 27:
        return COORDS[CENTER]

    tactical = _root_tactical_move(arr, legal)
    if tactical is not None and arr[tactical] == 0:
        return COORDS[tactical]

    # Fallback move is always legal.
    best_move = max(legal, key=lambda m: _quick_move_score(arr, m, 1))

    # Exact board hash in base-3 encoding: 0->0, 1->1, -1->2
    h = 0
    for i, v in enumerate(arr):
        if v == 1:
            h += HASH_ADD_1[i]
        elif v == -1:
            h += HASH_ADD_N1[i]

    deadline = time.perf_counter() + 0.94
    move_cache = {}

    n = len(legal)
    if n > 20:
        max_depth = 5
    elif n > 14:
        max_depth = 6
    elif n > 10:
        max_depth = 7
    else:
        max_depth = min(9, n + 1)

    try:
        for depth in range(1, max_depth + 1):
            score, move = _search_root(arr, h, depth, deadline, move_cache)
            if arr[move] == 0:
                best_move = move
            if abs(score) >= MATE - 1000:
                break
    except _Timeout:
        pass

    if arr[best_move] != 0:
        best_move = legal[0]

    return COORDS[best_move]

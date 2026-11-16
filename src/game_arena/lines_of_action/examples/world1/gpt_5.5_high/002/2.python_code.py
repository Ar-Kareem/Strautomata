
import time

# ---------- Constants and precomputation ----------

_INF = 10 ** 9
_WIN = 1_000_000
_MASK = (1 << 64) - 1

_DIRS = [
    (-1, 0), (1, 0),      # vertical
    (0, -1), (0, 1),      # horizontal
    (-1, -1), (1, 1),     # main diagonal
    (-1, 1), (1, -1),     # anti diagonal
]

# 0 = column, 1 = row, 2 = r-c diagonal, 3 = r+c diagonal
_KIND = [0, 0, 1, 1, 2, 2, 3, 3]

_NEIGH = []
_CENTER = []

for r in range(8):
    for c in range(8):
        ns = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                rr, cc = r + dr, c + dc
                if 0 <= rr < 8 and 0 <= cc < 8:
                    ns.append(rr * 8 + cc)
        _NEIGH.append(tuple(ns))

        # High near center, low near corners.
        dist2 = (2 * r - 7) ** 2 + (2 * c - 7) ** 2
        _CENTER.append(50 - dist2)

_DEST = []
_PATH = []

for d, (dr, dc) in enumerate(_DIRS):
    ddest = []
    dpath = []
    for i in range(64):
        r, c = divmod(i, 8)
        dests = [-1] * 9
        paths = [()] * 9
        for n in range(1, 9):
            rr, cc = r + dr * n, c + dc * n
            if 0 <= rr < 8 and 0 <= cc < 8:
                dests[n] = rr * 8 + cc
                paths[n] = tuple((r + dr * k) * 8 + (c + dc * k) for k in range(1, n))
        ddest.append(dests)
        dpath.append(paths)
    _DEST.append(ddest)
    _PATH.append(dpath)


def _splitmix64(x):
    x = (x + 0x9E3779B97F4A7C15) & _MASK
    z = x
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & _MASK
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & _MASK
    return (z ^ (z >> 31)) & _MASK


_Z = [[_splitmix64(1234567 + i * 2 + j) for j in range(2)] for i in range(64)]
_SIDE = _splitmix64(987654321)

_TT = {}
_DEADLINE = 0.0
_NODES = 0


# ---------- Move generation ----------

def _line_counts(board):
    rows = [0] * 8
    cols = [0] * 8
    d1 = [0] * 15
    d2 = [0] * 15

    for i, v in enumerate(board):
        if v:
            r, c = divmod(i, 8)
            rows[r] += 1
            cols[c] += 1
            d1[r - c + 7] += 1
            d2[r + c] += 1

    return rows, cols, d1, d2


def _generate_moves(board, color):
    rows, cols, d1, d2 = _line_counts(board)
    enemy = -color
    moves = []

    for src, v in enumerate(board):
        if v != color:
            continue

        r, c = divmod(src, 8)

        for d in range(8):
            kind = _KIND[d]
            if kind == 0:
                n = cols[c]
            elif kind == 1:
                n = rows[r]
            elif kind == 2:
                n = d1[r - c + 7]
            else:
                n = d2[r + c]

            dst = _DEST[d][src][n]
            if dst < 0 or board[dst] == color:
                continue

            blocked = False
            for p in _PATH[d][src][n]:
                if board[p] == enemy:
                    blocked = True
                    break

            if not blocked:
                moves.append((src, dst))

    return moves


def _move_to_str(move):
    src, dst = move
    sr, sc = divmod(src, 8)
    tr, tc = divmod(dst, 8)
    return f"{sr},{sc}:{tr},{tc}"


# ---------- Board utilities ----------

def _hash_board(board):
    h = 0
    for i, v in enumerate(board):
        if v == 1:
            h ^= _Z[i][0]
        elif v == -1:
            h ^= _Z[i][1]
    return h


def _make(board, move, color, key):
    src, dst = move
    cap = board[dst]

    idx = 0 if color == 1 else 1
    key ^= _Z[src][idx]

    if cap == 1:
        key ^= _Z[dst][0]
    elif cap == -1:
        key ^= _Z[dst][1]

    key ^= _Z[dst][idx]

    board[src] = 0
    board[dst] = color
    return cap, key


def _undo(board, move, color, cap):
    src, dst = move
    board[src] = color
    board[dst] = cap


def _is_connected(board, color):
    first = -1
    total = 0

    for i, v in enumerate(board):
        if v == color:
            total += 1
            if first < 0:
                first = i

    if total == 0:
        return False
    if total == 1:
        return True

    seen = [False] * 64
    stack = [first]
    seen[first] = True
    reached = 0

    while stack:
        x = stack.pop()
        reached += 1
        for nb in _NEIGH[x]:
            if not seen[nb] and board[nb] == color:
                seen[nb] = True
                stack.append(nb)

    return reached == total


# ---------- Evaluation ----------

def _side_score(board, color):
    pieces = []
    central = 0
    minr, minc = 8, 8
    maxr, maxc = -1, -1

    for i, v in enumerate(board):
        if v == color:
            pieces.append(i)
            central += _CENTER[i]
            r, c = divmod(i, 8)
            if r < minr:
                minr = r
            if r > maxr:
                maxr = r
            if c < minc:
                minc = c
            if c > maxc:
                maxc = c

    n = len(pieces)
    if n == 0:
        return -50000
    if n == 1:
        return 50000 + central

    visited = [False] * 64
    comps = 0
    largest = 0
    sumsq = 0

    for st in pieces:
        if visited[st]:
            continue

        comps += 1
        cnt = 0
        visited[st] = True
        stack = [st]

        while stack:
            x = stack.pop()
            cnt += 1
            for nb in _NEIGH[x]:
                if not visited[nb] and board[nb] == color:
                    visited[nb] = True
                    stack.append(nb)

        if cnt > largest:
            largest = cnt
        sumsq += cnt * cnt

    adj_pairs = 0
    for i in pieces:
        for nb in _NEIGH[i]:
            if nb > i and board[nb] == color:
                adj_pairs += 1

    pairdist = 0
    pairs = 0
    for a in range(n):
        r1, c1 = divmod(pieces[a], 8)
        for b in range(a + 1, n):
            r2, c2 = divmod(pieces[b], 8)
            pairdist += max(abs(r1 - r2), abs(c1 - c2))
            pairs += 1

    area = (maxr - minr + 1) * (maxc - minc + 1)

    score = 0
    score -= 1400 * (comps - 1)
    score += (800 * largest) // n
    score += (80 * sumsq) // n
    score += 45 * adj_pairs
    if pairs:
        score -= (35 * pairdist) // pairs
    score -= 6 * area
    score += 2 * central
    score += 6 * n

    return score


def _evaluate(board, color):
    return _side_score(board, color) - _side_score(board, -color)


# ---------- Search ----------

def _ordered_moves(board, moves, color, tt_best=None):
    if len(moves) <= 1:
        return moves

    enemy = -color
    scored = []

    for m in moves:
        src, dst = m
        s = 0

        if tt_best is not None and m == tt_best:
            s += 100000

        if board[dst] == enemy:
            s += 70

        s += 2 * (_CENTER[dst] - _CENTER[src])

        for nb in _NEIGH[dst]:
            if nb == src:
                continue
            if board[nb] == color:
                s += 30
            elif board[nb] == enemy:
                s += 3

        for nb in _NEIGH[src]:
            if nb != dst and board[nb] == color:
                s -= 8

        scored.append((s, m))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scored]


def _negamax(board, color, depth, alpha, beta, ply, key):
    global _NODES

    _NODES += 1
    if (_NODES & 255) == 0 and time.perf_counter() > _DEADLINE:
        raise TimeoutError

    # Previous mover is -color. If previous mover connected, current side lost.
    if _is_connected(board, -color):
        return -_WIN + ply

    # If current side is already connected because of the previous move, it wins.
    if _is_connected(board, color):
        return _WIN - ply

    if depth <= 0:
        return _evaluate(board, color)

    tt_key = key if color == 1 else (key ^ _SIDE)
    alpha_orig = alpha

    entry = _TT.get(tt_key)
    tt_best = None
    if entry is not None:
        e_depth, e_flag, e_val, e_best = entry
        tt_best = e_best
        if e_depth >= depth:
            if e_flag == 0:
                return e_val
            elif e_flag == 1:
                if e_val > alpha:
                    alpha = e_val
            else:
                if e_val < beta:
                    beta = e_val
            if alpha >= beta:
                return e_val

    moves = _generate_moves(board, color)
    if not moves:
        return _evaluate(board, color)

    moves = _ordered_moves(board, moves, color, tt_best)

    best_val = -_INF
    best_move = moves[0]

    for m in moves:
        cap, new_key = _make(board, m, color, key)
        val = -_negamax(board, -color, depth - 1, -beta, -alpha, ply + 1, new_key)
        _undo(board, m, color, cap)

        if val > best_val:
            best_val = val
            best_move = m

        if val > alpha:
            alpha = val

        if alpha >= beta:
            break

    if best_val <= alpha_orig:
        flag = -1   # upper bound
    elif best_val >= beta:
        flag = 1    # lower bound
    else:
        flag = 0    # exact

    if len(_TT) < 200000:
        _TT[tt_key] = (depth, flag, best_val, best_move)

    return best_val


# ---------- Required API ----------

def policy(board) -> str:
    global _TT, _DEADLINE, _NODES

    start = time.perf_counter()
    _DEADLINE = start + 0.88
    _NODES = 0
    _TT = {}

    # Convert possible list/numpy board into a flat Python list.
    b = []
    for r in range(8):
        for c in range(8):
            v = board[r][c]
            if v > 0:
                b.append(1)
            elif v < 0:
                b.append(-1)
            else:
                b.append(0)

    moves = _generate_moves(b, 1)

    # If the position has no legal move, no legal string exists; this is a last resort.
    if not moves:
        for i, v in enumerate(b):
            if v == 1:
                r, c = divmod(i, 8)
                return f"{r},{c}:{r},{c}"
        return "0,0:0,0"

    moves = _ordered_moves(b, moves, 1)
    best = moves[0]
    key0 = _hash_board(b)

    # Immediate win check.
    for m in moves:
        cap, k1 = _make(b, m, 1, key0)
        win = _is_connected(b, 1)
        _undo(b, m, 1, cap)
        if win:
            return _move_to_str(m)

    lm = len(moves)
    if lm <= 10:
        max_depth = 7
    elif lm <= 22:
        max_depth = 6
    elif lm <= 40:
        max_depth = 5
    else:
        max_depth = 4

    completed_best = best

    for depth in range(1, max_depth + 1):
        try:
            if time.perf_counter() > _DEADLINE:
                break

            ordered = _ordered_moves(b, moves, 1, completed_best)
            local_best = completed_best
            local_score = -_INF
            alpha = -_INF
            beta = _INF

            for m in ordered:
                if time.perf_counter() > _DEADLINE:
                    raise TimeoutError

                cap, new_key = _make(b, m, 1, key0)
                val = -_negamax(b, -1, depth - 1, -beta, -alpha, 1, new_key)
                _undo(b, m, 1, cap)

                if val > local_score:
                    local_score = val
                    local_best = m

                if val > alpha:
                    alpha = val

            completed_best = local_best
            best = completed_best

            if local_score > _WIN // 2:
                break

        except TimeoutError:
            break

    return _move_to_str(best)

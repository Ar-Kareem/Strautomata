
import time

DIRECTIONS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
]

INF = 10 ** 12
WIN = 10 ** 9


def policy(board) -> str:
    """
    Return a legal Lines of Action move in the format:
    "from_row,from_col:to_row,to_col"
    """
    try:
        b = [list(row) for row in board]
        moves = _gen_moves(b, 1)

        if not moves:
            return "0,0:0,0"

        deadline = time.perf_counter() + 0.90
        nodes = 0

        moves = _order_moves(b, moves, 1)
        best_move = moves[0]
        best_value = -INF

        # Greedy one-ply fallback, including immediate win detection.
        for m in moves:
            _make(b, m, 1)
            try:
                tv = _terminal_value(b, -1)
                if tv is not None:
                    val = tv
                else:
                    val = _evaluate(b)

                if val > WIN // 2:
                    return _fmt(m)

                if val > best_value:
                    best_value = val
                    best_move = m
            finally:
                _undo(b, m, 1)

        def alphabeta(depth, alpha, beta, side):
            nonlocal nodes
            nodes += 1

            if (nodes & 255) == 0 and time.perf_counter() > deadline:
                raise TimeoutError

            tv = _terminal_value(b, side)
            if tv is not None:
                if tv > 0:
                    return tv + depth
                return tv - depth

            if depth <= 0:
                return _evaluate(b)

            legal = _gen_moves(b, side)
            if not legal:
                # No legal move is very bad for the side to move.
                return -WIN // 2 if side == 1 else WIN // 2

            legal = _order_moves(b, legal, side)

            if side == 1:
                value = -INF
                for mv in legal:
                    _make(b, mv, side)
                    try:
                        score = alphabeta(depth - 1, alpha, beta, -side)
                    finally:
                        _undo(b, mv, side)

                    if score > value:
                        value = score
                    if value > alpha:
                        alpha = value
                    if alpha >= beta:
                        break
                return value
            else:
                value = INF
                for mv in legal:
                    _make(b, mv, side)
                    try:
                        score = alphabeta(depth - 1, alpha, beta, -side)
                    finally:
                        _undo(b, mv, side)

                    if score < value:
                        value = score
                    if value < beta:
                        beta = value
                    if alpha >= beta:
                        break
                return value

        # Iterative deepening. Keep the best fully completed depth.
        depth = 2
        while depth <= 8 and time.perf_counter() < deadline:
            try:
                current_best = best_move
                current_value = -INF

                # Try previous best first.
                root_moves = [best_move] + [m for m in moves if m != best_move]

                for mv in root_moves:
                    if time.perf_counter() > deadline:
                        raise TimeoutError

                    _make(b, mv, 1)
                    try:
                        score = alphabeta(depth - 1, -INF, INF, -1)
                    finally:
                        _undo(b, mv, 1)

                    if score > current_value:
                        current_value = score
                        current_best = mv

                best_move = current_best
                best_value = current_value
                moves = [best_move] + [m for m in moves if m != best_move]
                depth += 1

            except TimeoutError:
                break

        return _fmt(best_move)

    except Exception:
        # Last-resort legal fallback.
        try:
            b = [list(row) for row in board]
            moves = _gen_moves(b, 1)
            if moves:
                return _fmt(moves[0])
        except Exception:
            pass
        return "0,0:0,0"


def _fmt(m):
    return f"{m[0]},{m[1]}:{m[2]},{m[3]}"


def _inside(r, c):
    return 0 <= r < 8 and 0 <= c < 8


def _line_count(b, r, c, dr, dc):
    if dr == 0:
        return sum(1 for x in range(8) if b[r][x] != 0)

    if dc == 0:
        return sum(1 for x in range(8) if b[x][c] != 0)

    count = 0

    rr, cc = r, c
    while _inside(rr - dr, cc - dc):
        rr -= dr
        cc -= dc

    while _inside(rr, cc):
        if b[rr][cc] != 0:
            count += 1
        rr += dr
        cc += dc

    return count


def _gen_moves(b, side):
    moves = []
    enemy = -side

    for r in range(8):
        row = b[r]
        for c in range(8):
            if row[c] != side:
                continue

            for dr, dc in DIRECTIONS:
                dist = _line_count(b, r, c, dr, dc)
                tr = r + dr * dist
                tc = c + dc * dist

                if not _inside(tr, tc):
                    continue

                if b[tr][tc] == side:
                    continue

                blocked = False
                for step in range(1, dist):
                    rr = r + dr * step
                    cc = c + dc * step
                    if b[rr][cc] == enemy:
                        blocked = True
                        break

                if not blocked:
                    moves.append((r, c, tr, tc, b[tr][tc]))

    return moves


def _make(b, m, side):
    fr, fc, tr, tc, captured = m
    b[fr][fc] = 0
    b[tr][tc] = side


def _undo(b, m, side):
    fr, fc, tr, tc, captured = m
    b[fr][fc] = side
    b[tr][tc] = captured


def _pieces(b, side):
    ps = []
    for r in range(8):
        for c in range(8):
            if b[r][c] == side:
                ps.append((r, c))
    return ps


def _connected(b, side):
    ps = _pieces(b, side)

    if len(ps) == 0:
        return False
    if len(ps) == 1:
        return True

    start = ps[0]
    stack = [start]
    seen = {start}

    while stack:
        r, c = stack.pop()
        for dr, dc in DIRECTIONS:
            nr = r + dr
            nc = c + dc
            if _inside(nr, nc) and b[nr][nc] == side and (nr, nc) not in seen:
                seen.add((nr, nc))
                stack.append((nr, nc))

    return len(seen) == len(ps)


def _terminal_value(b, side_to_move):
    us = _connected(b, 1)
    them = _connected(b, -1)

    if us and them:
        # If both are connected after a move, favor the player who just moved.
        previous_mover = -side_to_move
        return WIN if previous_mover == 1 else -WIN

    if us:
        return WIN

    if them:
        return -WIN

    return None


def _component_stats(b, side):
    ps = _pieces(b, side)
    n = len(ps)

    if n == 0:
        return {
            "n": 0,
            "components": 99,
            "largest": 0,
            "adj": 0,
            "bbox": 64,
            "nearest": 100,
            "center": 0.0,
        }

    visited = set()
    components = 0
    largest = 0

    for p in ps:
        if p in visited:
            continue

        components += 1
        size = 0
        stack = [p]
        visited.add(p)

        while stack:
            r, c = stack.pop()
            size += 1
            for dr, dc in DIRECTIONS:
                nr = r + dr
                nc = c + dc
                np = (nr, nc)
                if _inside(nr, nc) and b[nr][nc] == side and np not in visited:
                    visited.add(np)
                    stack.append(np)

        if size > largest:
            largest = size

    adj = 0
    for r, c in ps:
        for dr, dc in ((0, 1), (1, -1), (1, 0), (1, 1)):
            nr = r + dr
            nc = c + dc
            if _inside(nr, nc) and b[nr][nc] == side:
                adj += 1

    rows = [p[0] for p in ps]
    cols = [p[1] for p in ps]
    bbox = (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)

    nearest = 0
    if n > 1:
        for i, (r, c) in enumerate(ps):
            best = 99
            for j, (rr, cc) in enumerate(ps):
                if i == j:
                    continue
                d = max(abs(r - rr), abs(c - cc))
                if d < best:
                    best = d
            nearest += best

    center = 0.0
    for r, c in ps:
        center += 3.5 - max(abs(r - 3.5), abs(c - 3.5))

    return {
        "n": n,
        "components": components,
        "largest": largest,
        "adj": adj,
        "bbox": bbox,
        "nearest": nearest,
        "center": center,
    }


def _side_score(b, side):
    s = _component_stats(b, side)
    n = s["n"]

    if n == 0:
        return -100000.0

    largest_ratio = s["largest"] / float(n)

    score = 0.0
    score -= 1000.0 * (s["components"] - 1)
    score += 700.0 * largest_ratio
    score += 45.0 * s["adj"]
    score -= 25.0 * s["nearest"]
    score -= 6.0 * s["bbox"]
    score += 8.0 * s["center"]

    return score


def _evaluate(b):
    tv = _terminal_value(b, 1)
    if tv is not None:
        return tv

    return _side_score(b, 1) - _side_score(b, -1)


def _order_moves(b, moves, side):
    ps = _pieces(b, side)

    if ps:
        cr = sum(p[0] for p in ps) / float(len(ps))
        cc = sum(p[1] for p in ps) / float(len(ps))
    else:
        cr = cc = 3.5

    scored = []

    for m in moves:
        fr, fc, tr, tc, captured = m

        score = 0.0

        if captured == -side:
            score += 500.0

        # Prefer central, compact, adjacency-building moves.
        old_dist = max(abs(fr - cr), abs(fc - cc))
        new_dist = max(abs(tr - cr), abs(tc - cc))
        score += 20.0 * (old_dist - new_dist)

        score += 8.0 * (3.5 - max(abs(tr - 3.5), abs(tc - 3.5)))

        adjacent_friends = 0
        for dr, dc in DIRECTIONS:
            nr = tr + dr
            nc = tc + dc
            if _inside(nr, nc) and not (nr == fr and nc == fc) and b[nr][nc] == side:
                adjacent_friends += 1

        score += 70.0 * adjacent_friends

        # Slightly prefer leaving edge/corner squares.
        if fr in (0, 7) or fc in (0, 7):
            score += 10.0
        if tr in (0, 7) or tc in (0, 7):
            score -= 5.0

        scored.append((score, m))

    scored.sort(reverse=True, key=lambda x: x[0])
    return [m for _, m in scored]

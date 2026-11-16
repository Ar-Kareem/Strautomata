
import time
import math

BOARD_SIZE = 8
DIRS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1)
]


def policy(board) -> str:
    """
    Return a legal Lines of Action move for the current player.
    The current player's pieces are encoded as 1, opponent as -1.
    """
    b = tuple(tuple(int(board[r][c]) for c in range(BOARD_SIZE)) for r in range(BOARD_SIZE))
    moves = generate_moves(b, 1)

    if not moves:
        # Extremely defensive fallback. In a valid LOA state this should not happen.
        return "0,0:0,0"

    # Immediate winning move check.
    for mv in moves:
        nb = apply_move(b, mv)
        if is_connected(nb, 1):
            return move_to_str(mv)

    start = time.time()
    limit = 0.86

    best_move = moves[0]
    best_score = -10**18

    # Good initial ordering improves alpha-beta pruning.
    moves = order_moves(b, moves, 1)

    # Iterative deepening keeps us safe under the time limit.
    max_depth = 4
    if len(moves) > 38:
        max_depth = 3
    if len(moves) > 60:
        max_depth = 2

    trans = {}

    try:
        for depth in range(1, max_depth + 1):
            if time.time() - start > limit:
                break

            current_best = best_move
            current_score = -10**18
            alpha = -10**18
            beta = 10**18

            for mv in moves:
                if time.time() - start > limit:
                    raise TimeoutError

                nb = apply_move(b, mv)
                score = minimax(
                    nb,
                    depth - 1,
                    -1,
                    alpha,
                    beta,
                    start,
                    limit,
                    trans
                )

                if score > current_score:
                    current_score = score
                    current_best = mv

                if score > alpha:
                    alpha = score

            best_move = current_best
            best_score = current_score

            # If we found a forced/immediate decisive line, stop.
            if best_score > 900000:
                break

            moves = order_moves(b, moves, 1)

    except TimeoutError:
        pass
    except Exception:
        # Never risk returning an illegal or malformed move.
        pass

    return move_to_str(best_move)


def minimax(b, depth, side, alpha, beta, start, limit, trans):
    if time.time() - start > limit:
        raise TimeoutError

    # Terminal checks.
    if is_connected(b, 1):
        return 1000000 + depth
    if is_connected(b, -1):
        return -1000000 - depth

    if depth <= 0:
        return evaluate(b)

    key = (b, side, depth)
    if key in trans:
        return trans[key]

    moves = generate_moves(b, side)
    if not moves:
        val = evaluate(b)
        trans[key] = val
        return val

    moves = order_moves(b, moves, side)

    if side == 1:
        value = -10**18
        for mv in moves:
            nb = apply_move(b, mv)
            value = max(value, minimax(nb, depth - 1, -side, alpha, beta, start, limit, trans))
            alpha = max(alpha, value)
            if alpha >= beta:
                break
    else:
        value = 10**18
        for mv in moves:
            nb = apply_move(b, mv)
            value = min(value, minimax(nb, depth - 1, -side, alpha, beta, start, limit, trans))
            beta = min(beta, value)
            if alpha >= beta:
                break

    trans[key] = value
    return value


def generate_moves(b, side):
    moves = []

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if b[r][c] != side:
                continue

            for dr, dc in DIRS:
                count = line_count(b, r, c, dr, dc)
                tr = r + dr * count
                tc = c + dc * count

                if not in_bounds(tr, tc):
                    continue

                # Cannot land on own piece.
                if b[tr][tc] == side:
                    continue

                # May jump over friendly pieces, but not enemy pieces.
                blocked = False
                cr = r + dr
                cc = c + dc
                while (cr, cc) != (tr, tc):
                    if b[cr][cc] == -side:
                        blocked = True
                        break
                    cr += dr
                    cc += dc

                if not blocked:
                    moves.append((r, c, tr, tc))

    return moves


def line_count(b, r, c, dr, dc):
    """
    Count all pieces, friendly and enemy, on the complete movement line.
    """
    count = 0

    # Move backward to the start of the line.
    sr, sc = r, c
    while in_bounds(sr - dr, sc - dc):
        sr -= dr
        sc -= dc

    # Traverse forward.
    while in_bounds(sr, sc):
        if b[sr][sc] != 0:
            count += 1
        sr += dr
        sc += dc

    return count


def apply_move(b, mv):
    r, c, tr, tc = mv
    side = b[r][c]

    rows = [list(row) for row in b]
    rows[r][c] = 0
    rows[tr][tc] = side

    return tuple(tuple(row) for row in rows)


def is_connected(b, side):
    pieces = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if b[r][c] == side:
                pieces.append((r, c))

    if len(pieces) <= 1:
        return True

    seen = set()
    stack = [pieces[0]]
    seen.add(pieces[0])

    while stack:
        r, c = stack.pop()
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc) and b[nr][nc] == side and (nr, nc) not in seen:
                seen.add((nr, nc))
                stack.append((nr, nc))

    return len(seen) == len(pieces)


def component_info(b, side):
    pieces = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if b[r][c] == side:
                pieces.append((r, c))

    n = len(pieces)
    if n == 0:
        return {
            "pieces": 0,
            "components": 0,
            "largest": 0,
            "area": 0,
            "dist": 0,
            "center": 0
        }

    piece_set = set(pieces)
    seen = set()
    components = 0
    largest = 0

    for p in pieces:
        if p in seen:
            continue

        components += 1
        size = 0
        stack = [p]
        seen.add(p)

        while stack:
            r, c = stack.pop()
            size += 1
            for dr, dc in DIRS:
                q = (r + dr, c + dc)
                if q in piece_set and q not in seen:
                    seen.add(q)
                    stack.append(q)

        largest = max(largest, size)

    min_r = min(r for r, c in pieces)
    max_r = max(r for r, c in pieces)
    min_c = min(c for r, c in pieces)
    max_c = max(c for r, c in pieces)
    area = (max_r - min_r + 1) * (max_c - min_c + 1)

    avg_r = sum(r for r, c in pieces) / float(n)
    avg_c = sum(c for r, c in pieces) / float(n)

    # Compactness: sum of Chebyshev distances to centroid.
    dist = 0.0
    for r, c in pieces:
        dist += max(abs(r - avg_r), abs(c - avg_c))

    # Centralization bonus.
    center = 0.0
    for r, c in pieces:
        center -= abs(r - 3.5) + abs(c - 3.5)

    return {
        "pieces": n,
        "components": components,
        "largest": largest,
        "area": area,
        "dist": dist,
        "center": center
    }


def evaluate(b):
    if is_connected(b, 1):
        return 1000000
    if is_connected(b, -1):
        return -1000000

    me = component_info(b, 1)
    op = component_info(b, -1)

    my_moves = len(generate_moves(b, 1))
    op_moves = len(generate_moves(b, -1))

    score = 0.0

    # Primary objective: reduce own components and prevent opponent connection.
    score += (op["components"] - me["components"]) * 1450.0

    # Grow the largest connected cluster.
    score += (me["largest"] - op["largest"]) * 135.0

    # Compact formations connect faster.
    score += (op["area"] - me["area"]) * 38.0
    score += (op["dist"] - me["dist"]) * 42.0

    # Mobility matters, but less than connectivity.
    score += (my_moves - op_moves) * 4.0

    # Slight centralization preference.
    score += (me["center"] - op["center"]) * 4.0

    # Capturing can help, but having more pieces connected is usually valuable.
    score += (me["pieces"] - op["pieces"]) * 15.0

    return int(score)


def order_moves(b, moves, side):
    scored = []

    before = component_info(b, side)
    opp = -side

    for mv in moves:
        r, c, tr, tc = mv
        capture = 1 if b[tr][tc] == opp else 0
        nb = apply_move(b, mv)

        if is_connected(nb, side):
            s = 10**9
        else:
            after = component_info(nb, side)
            s = 0
            s += (before["components"] - after["components"]) * 10000
            s += (after["largest"] - before["largest"]) * 1000
            s += (before["area"] - after["area"]) * 80
            s += capture * 500
            # Prefer moves toward board center.
            s -= int((abs(tr - 3.5) + abs(tc - 3.5)) * 10)

        scored.append((s, mv))

    reverse = True
    scored.sort(reverse=reverse, key=lambda x: x[0])
    return [mv for s, mv in scored]


def in_bounds(r, c):
    return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE


def move_to_str(mv):
    r, c, tr, tc = mv
    return f"{r},{c}:{tr},{tc}"

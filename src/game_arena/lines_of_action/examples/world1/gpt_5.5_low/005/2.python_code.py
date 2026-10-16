
import time
import math

BOARD_SIZE = 8
DIRS8 = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
MOVE_DIRS = [(1,0),(0,1),(1,1),(1,-1)]
INF = 10**9

_deadline = 0.0


def policy(board) -> str:
    """
    Return a legal Lines of Action move in the format:
    "from_row,from_col:to_row,to_col"
    """
    global _deadline
    _deadline = time.time() + 0.90

    b = tuple(tuple(int(board[r][c]) for c in range(BOARD_SIZE)) for r in range(BOARD_SIZE))
    moves = generate_moves(b)

    if not moves:
        # This should almost never happen in a valid LOA position.
        # Required to return a string.
        return "0,0:0,0"

    # If any move wins immediately, play it.
    for mv in moves:
        nb = make_move_no_flip(b, mv)
        if connected(nb, 1):
            return move_to_str(mv)

    # Move ordering for stronger alpha-beta.
    moves = order_moves(b, moves)

    best_move = moves[0]
    best_score = -INF

    # Iterative deepening. Depth 3 is usually feasible; depth 4 if position is quiet.
    max_depth = 4 if len(moves) <= 18 else 3

    try:
        for depth in range(1, max_depth + 1):
            if time.time() > _deadline:
                break

            current_best = best_move
            current_score = -INF
            alpha = -INF
            beta = INF

            for mv in moves:
                if time.time() > _deadline:
                    raise TimeoutError

                child = make_move_and_flip(b, mv)
                score = -negamax(child, depth - 1, -beta, -alpha)

                if score > current_score:
                    current_score = score
                    current_best = mv

                if score > alpha:
                    alpha = score

            best_move = current_best
            best_score = current_score

    except TimeoutError:
        pass
    except Exception:
        # Absolute safety: never fail to return a legal move.
        best_move = moves[0]

    return move_to_str(best_move)


def move_to_str(mv):
    return f"{mv[0]},{mv[1]}:{mv[2]},{mv[3]}"


def in_bounds(r, c):
    return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE


def generate_moves(b):
    moves = []

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if b[r][c] != 1:
                continue

            for dr, dc in MOVE_DIRS:
                dist = count_line_pieces(b, r, c, dr, dc)

                for sgn in (1, -1):
                    nr = r + sgn * dr * dist
                    nc = c + sgn * dc * dist

                    if not in_bounds(nr, nc):
                        continue

                    if b[nr][nc] == 1:
                        continue

                    step_r = sgn * dr
                    step_c = sgn * dc

                    blocked = False
                    cr = r + step_r
                    cc = c + step_c

                    while (cr, cc) != (nr, nc):
                        if b[cr][cc] == -1:
                            blocked = True
                            break
                        cr += step_r
                        cc += step_c

                    if not blocked:
                        moves.append((r, c, nr, nc))

    return moves


def count_line_pieces(b, r, c, dr, dc):
    count = 1

    rr = r + dr
    cc = c + dc
    while in_bounds(rr, cc):
        if b[rr][cc] != 0:
            count += 1
        rr += dr
        cc += dc

    rr = r - dr
    cc = c - dc
    while in_bounds(rr, cc):
        if b[rr][cc] != 0:
            count += 1
        rr -= dr
        cc -= dc

    return count


def make_move_no_flip(b, mv):
    r1, c1, r2, c2 = mv
    rows = [list(row) for row in b]
    rows[r1][c1] = 0
    rows[r2][c2] = 1
    return tuple(tuple(row) for row in rows)


def make_move_and_flip(b, mv):
    r1, c1, r2, c2 = mv
    rows = [list(row) for row in b]
    rows[r1][c1] = 0
    rows[r2][c2] = 1

    # Flip perspective: next player to move is always represented as 1.
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            rows[r][c] = -rows[r][c]

    return tuple(tuple(row) for row in rows)


def connected(b, side):
    pieces = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if b[r][c] == side:
                pieces.append((r, c))

    if len(pieces) <= 1:
        return True

    start = pieces[0]
    seen = {start}
    stack = [start]

    while stack:
        r, c = stack.pop()
        for dr, dc in DIRS8:
            nr = r + dr
            nc = c + dc
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

    if not pieces:
        return 0, 0, []

    unseen = set(pieces)
    comps = []
    largest = 0

    while unseen:
        start = unseen.pop()
        stack = [start]
        size = 1

        while stack:
            r, c = stack.pop()
            for dr, dc in DIRS8:
                nr = r + dr
                nc = c + dc
                if (nr, nc) in unseen:
                    unseen.remove((nr, nc))
                    stack.append((nr, nc))
                    size += 1

        comps.append(size)
        if size > largest:
            largest = size

    return len(comps), largest, pieces


def compactness_score(pieces):
    n = len(pieces)
    if n <= 1:
        return 0.0

    cr = sum(r for r, c in pieces) / n
    cc = sum(c for r, c in pieces) / n

    dist = 0.0
    center = 0.0

    for r, c in pieces:
        dist += abs(r - cr) + abs(c - cc)
        center += abs(r - 3.5) + abs(c - 3.5)

    return -dist * 4.0 - center * 1.2


def bounding_box_score(pieces):
    if not pieces:
        return 0.0

    rs = [r for r, c in pieces]
    cs = [c for r, c in pieces]

    height = max(rs) - min(rs) + 1
    width = max(cs) - min(cs) + 1

    return -(height + width) * 5.0


def mobility_count_limited(b, limit=40):
    count = 0

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if b[r][c] != 1:
                continue

            for dr, dc in MOVE_DIRS:
                dist = count_line_pieces(b, r, c, dr, dc)

                for sgn in (1, -1):
                    nr = r + sgn * dr * dist
                    nc = c + sgn * dc * dist

                    if not in_bounds(nr, nc) or b[nr][nc] == 1:
                        continue

                    step_r = sgn * dr
                    step_c = sgn * dc

                    blocked = False
                    cr = r + step_r
                    cc = c + step_c

                    while (cr, cc) != (nr, nc):
                        if b[cr][cc] == -1:
                            blocked = True
                            break
                        cr += step_r
                        cc += step_c

                    if not blocked:
                        count += 1
                        if count >= limit:
                            return count

    return count


def evaluate(b):
    # In the search representation, side 1 is always the player to move.
    # If opponent is already connected, the previous move won.
    if connected(b, -1):
        return -INF + 1000

    if connected(b, 1):
        return INF - 1000

    my_comps, my_largest, my_pieces = component_info(b, 1)
    op_comps, op_largest, op_pieces = component_info(b, -1)

    my_n = len(my_pieces)
    op_n = len(op_pieces)

    score = 0.0

    # Primary LOA goal: reduce own components and grow largest connected group.
    score += (op_comps - my_comps) * 650.0
    score += my_largest * 95.0
    score -= op_largest * 90.0

    if my_n:
        score += (my_largest / my_n) * 500.0
    if op_n:
        score -= (op_largest / op_n) * 520.0

    # Compactness and bounding box strongly correlate with connecting.
    score += compactness_score(my_pieces)
    score -= compactness_score(op_pieces) * 0.85

    score += bounding_box_score(my_pieces)
    score -= bounding_box_score(op_pieces) * 0.85

    # Capturing opponent pieces can help by reducing their material/connectivity.
    score += (my_n - op_n) * 35.0

    # Mobility matters, but not as much as connection.
    try:
        my_mob = mobility_count_limited(b)
        fb = flip_board(b)
        op_mob = mobility_count_limited(fb)
        score += (my_mob - op_mob) * 3.0
    except Exception:
        pass

    return int(score)


def flip_board(b):
    return tuple(tuple(-b[r][c] for c in range(BOARD_SIZE)) for r in range(BOARD_SIZE))


def negamax(b, depth, alpha, beta):
    if time.time() > _deadline:
        raise TimeoutError

    if connected(b, -1):
        return -INF + depth

    if connected(b, 1):
        return INF - depth

    if depth <= 0:
        return evaluate(b)

    moves = generate_moves(b)

    if not moves:
        return evaluate(b)

    moves = order_moves(b, moves)

    best = -INF

    for mv in moves:
        child = make_move_and_flip(b, mv)
        score = -negamax(child, depth - 1, -beta, -alpha)

        if score > best:
            best = score

        if score > alpha:
            alpha = score

        if alpha >= beta:
            break

    return best


def order_moves(b, moves):
    scored = []

    my_comps_before, my_largest_before, _ = component_info(b, 1)

    for mv in moves:
        r1, c1, r2, c2 = mv
        s = 0

        # Captures are often useful.
        if b[r2][c2] == -1:
            s += 80

        nb = make_move_no_flip(b, mv)

        if connected(nb, 1):
            s += 100000

        comps, largest, _ = component_info(nb, 1)
        s += (my_comps_before - comps) * 600
        s += (largest - my_largest_before) * 90

        # Prefer central destinations.
        s -= int((abs(r2 - 3.5) + abs(c2 - 3.5)) * 5)

        scored.append((s, mv))

    scored.sort(reverse=True, key=lambda x: x[0])
    return [mv for s, mv in scored]

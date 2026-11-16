
import time
import math

BOARD_SIZE = 8
INF = 10**9
WIN = 10**7

DIRECTIONS = [
    (-1, 0), (1, 0), (0, -1), (0, 1),
    (-1, -1), (1, 1), (-1, 1), (1, -1)
]

NEIGHBORS = DIRECTIONS[:]

# Precompute all full lines through each square in each movement direction.
LINE_CELLS = {}
for r in range(BOARD_SIZE):
    for c in range(BOARD_SIZE):
        for dr, dc in DIRECTIONS:
            sr, sc = r, c
            while 0 <= sr - dr < BOARD_SIZE and 0 <= sc - dc < BOARD_SIZE:
                sr -= dr
                sc -= dc
            cells = []
            rr, cc = sr, sc
            while 0 <= rr < BOARD_SIZE and 0 <= cc < BOARD_SIZE:
                cells.append((rr, cc))
                rr += dr
                cc += dc
            LINE_CELLS[(r, c, dr, dc)] = cells


def policy(board) -> str:
    """
    Return a legal Lines of Action move in the format:
    "from_row,from_col:to_row,to_col"
    """
    b = [[int(board[r][c]) for c in range(BOARD_SIZE)] for r in range(BOARD_SIZE)]
    start_time = time.perf_counter()
    deadline = start_time + 0.88

    def in_bounds(r, c):
        return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE

    def move_to_str(m):
        fr, fc, tr, tc = m
        return f"{fr},{fc}:{tr},{tc}"

    def board_key(side, depth):
        return (side, depth, tuple(x for row in b for x in row))

    def legal_moves(side):
        moves = []
        enemy = -side

        for r in range(BOARD_SIZE):
            row = b[r]
            for c in range(BOARD_SIZE):
                if row[c] != side:
                    continue

                for dr, dc in DIRECTIONS:
                    line = LINE_CELLS[(r, c, dr, dc)]
                    dist = 0
                    for lr, lc in line:
                        if b[lr][lc] != 0:
                            dist += 1

                    tr = r + dr * dist
                    tc = c + dc * dist
                    if not in_bounds(tr, tc):
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
                        moves.append((r, c, tr, tc))

        return moves

    def apply_move(m, side):
        fr, fc, tr, tc = m
        captured = b[tr][tc]
        b[fr][fc] = 0
        b[tr][tc] = side
        return captured

    def undo_move(m, side, captured):
        fr, fc, tr, tc = m
        b[tr][tc] = captured
        b[fr][fc] = side

    def positions(side):
        return [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) if b[r][c] == side]

    def component_info(side):
        ps = positions(side)
        n = len(ps)
        if n == 0:
            return 99, 0, ps

        pset = set(ps)
        seen = set()
        comps = 0
        largest = 0

        for p in ps:
            if p in seen:
                continue

            comps += 1
            size = 0
            stack = [p]
            seen.add(p)

            while stack:
                r, c = stack.pop()
                size += 1
                for dr, dc in NEIGHBORS:
                    nr, nc = r + dr, c + dc
                    q = (nr, nc)
                    if q in pset and q not in seen:
                        seen.add(q)
                        stack.append(q)

            if size > largest:
                largest = size

        return comps, largest, ps

    def is_connected(side):
        comps, largest, ps = component_info(side)
        return len(ps) == 1 or (len(ps) > 1 and comps == 1)

    def static_feature(side):
        comps, largest, ps = component_info(side)
        n = len(ps)
        if n == 0:
            return -100000.0
        if n == 1:
            return 100000.0

        rs = [p[0] for p in ps]
        cs = [p[1] for p in ps]

        cr = sum(rs) / n
        cc = sum(cs) / n

        avg_cluster_dist = 0.0
        avg_center_dist = 0.0
        for r, c in ps:
            avg_cluster_dist += max(abs(r - cr), abs(c - cc))
            avg_center_dist += max(abs(r - 3.5), abs(c - 3.5))
        avg_cluster_dist /= n
        avg_center_dist /= n

        bbox_area = (max(rs) - min(rs) + 1) * (max(cs) - min(cs) + 1)

        # Average pairwise Chebyshev distance encourages compact connection shapes.
        pair_dist = 0.0
        pair_count = 0
        for i in range(n):
            r1, c1 = ps[i]
            for j in range(i + 1, n):
                r2, c2 = ps[j]
                pair_dist += max(abs(r1 - r2), abs(c1 - c2))
                pair_count += 1
        if pair_count:
            pair_dist /= pair_count

        # Mobility is useful, but not as important as connectivity.
        mob = len(legal_moves(side))

        return (
            -950.0 * (comps - 1)
            + 380.0 * (largest / n)
            - 42.0 * avg_cluster_dist
            - 22.0 * pair_dist
            - 5.0 * bbox_area
            - 7.0 * avg_center_dist
            + 2.0 * mob
        )

    def evaluate():
        if is_connected(1):
            return WIN
        if is_connected(-1):
            return -WIN

        own_count = len(positions(1))
        opp_count = len(positions(-1))

        return (
            static_feature(1)
            - static_feature(-1)
            + 6.0 * (own_count - opp_count)
        )

    def order_moves(moves, side):
        scored = []
        enemy = -side

        for m in moves:
            if time.perf_counter() > deadline:
                raise TimeoutError

            fr, fc, tr, tc = m
            captured_before = b[tr][tc]
            captured = apply_move(m, side)

            if is_connected(side):
                s = 1000000.0
            elif is_connected(enemy):
                s = -1000000.0
            else:
                comps, largest, ps = component_info(side)
                n = max(1, len(ps))
                s = (
                    -600.0 * comps
                    + 180.0 * (largest / n)
                    - 5.0 * max(abs(tr - 3.5), abs(tc - 3.5))
                )
                if captured_before == enemy:
                    s += 70.0

                # Prefer moves that increase adjacency to friendly pieces.
                adj = 0
                for dr, dc in NEIGHBORS:
                    nr, nc = tr + dr, tc + dc
                    if in_bounds(nr, nc) and b[nr][nc] == side:
                        adj += 1
                s += 25.0 * adj

            undo_move(m, side, captured)
            scored.append((s, m))

        scored.sort(reverse=True, key=lambda x: x[0])
        return [m for _, m in scored]

    transposition = {}

    def alphabeta(depth, side, alpha, beta):
        if time.perf_counter() > deadline:
            raise TimeoutError

        if is_connected(1):
            return WIN + depth
        if is_connected(-1):
            return -WIN - depth

        if depth <= 0:
            return evaluate()

        key = board_key(side, depth)
        entry = transposition.get(key)
        if entry is not None:
            val, flag, stored_depth = entry
            if stored_depth >= depth:
                if flag == "E":
                    return val
                elif flag == "L":
                    alpha = max(alpha, val)
                elif flag == "U":
                    beta = min(beta, val)
                if alpha >= beta:
                    return val

        orig_alpha = alpha
        orig_beta = beta

        moves = legal_moves(side)
        if not moves:
            return evaluate()

        moves = order_moves(moves, side)

        if side == 1:
            value = -INF
            for m in moves:
                captured = apply_move(m, side)

                if is_connected(side):
                    val = WIN + depth
                else:
                    val = alphabeta(depth - 1, -side, alpha, beta)

                undo_move(m, side, captured)

                if val > value:
                    value = val
                if value > alpha:
                    alpha = value
                if alpha >= beta:
                    break
        else:
            value = INF
            for m in moves:
                captured = apply_move(m, side)

                if is_connected(side):
                    val = -WIN - depth
                else:
                    val = alphabeta(depth - 1, -side, alpha, beta)

                undo_move(m, side, captured)

                if val < value:
                    value = val
                if value < beta:
                    beta = value
                if alpha >= beta:
                    break

        if value <= orig_alpha:
            flag = "U"
        elif value >= orig_beta:
            flag = "L"
        else:
            flag = "E"
        transposition[key] = (value, flag, depth)

        return value

    root_moves = legal_moves(1)

    # In a normal LOA state there should always be at least one move. This is
    # only a final safety fallback for malformed terminal inputs.
    if not root_moves:
        return "0,0:0,0"

    best_move = root_moves[0]

    # Never miss an immediate winning move.
    for m in root_moves:
        captured = apply_move(m, 1)
        won = is_connected(1)
        undo_move(m, 1, captured)
        if won:
            return move_to_str(m)

    try:
        root_moves = order_moves(root_moves, 1)
    except TimeoutError:
        return move_to_str(best_move)

    # Dynamic depth target. Iterative deepening guarantees a legal move even
    # if the final deeper search is interrupted.
    if len(root_moves) <= 12:
        max_depth = 5
    elif len(root_moves) <= 28:
        max_depth = 4
    else:
        max_depth = 4

    for depth in range(1, max_depth + 1):
        if time.perf_counter() > deadline:
            break

        local_best = best_move
        local_value = -INF
        alpha = -INF
        beta = INF
        completed = True

        try:
            # Put previous best first for better pruning.
            ordered = [best_move] + [m for m in root_moves if m != best_move]

            for m in ordered:
                if time.perf_counter() > deadline:
                    raise TimeoutError

                captured = apply_move(m, 1)

                if is_connected(1):
                    val = WIN + depth
                else:
                    val = alphabeta(depth - 1, -1, alpha, beta)

                undo_move(m, 1, captured)

                if val > local_value:
                    local_value = val
                    local_best = m

                if val > alpha:
                    alpha = val

            best_move = local_best

            # A forced win was found.
            if local_value >= WIN // 2:
                break

        except TimeoutError:
            completed = False

        if not completed:
            break

    return move_to_str(best_move)

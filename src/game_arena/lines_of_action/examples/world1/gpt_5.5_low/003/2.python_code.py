
import time
import math

BOARD_SIZE = 8
DIRS = [
    (-1, 0), (1, 0), (0, -1), (0, 1),
    (-1, -1), (-1, 1), (1, -1), (1, 1)
]

SEARCH_LIMIT = 0.92


def policy(board) -> str:
    start_time = time.time()

    b = [list(row) for row in board]

    legal = generate_moves(b, 1)
    if not legal:
        return "0,0:0,0"

    # If any move wins immediately, play it.
    for mv in legal:
        nb = make_move(b, mv)
        if is_connected(nb, 1):
            return move_to_str(mv)

    # Safe fallback.
    best_move = legal[0]
    best_score = -10**18

    # Prefer a decent static move immediately in case time is tight.
    ordered = order_moves(b, legal, 1)
    if ordered:
        best_move = ordered[0]

    depth = 1
    while depth <= 4:
        if time.time() - start_time > SEARCH_LIMIT:
            break

        current_best = best_move
        current_score = -10**18
        alpha = -10**18
        beta = 10**18

        try:
            for mv in ordered:
                if time.time() - start_time > SEARCH_LIMIT:
                    raise TimeoutError

                nb = make_move(b, mv)
                score = alphabeta(
                    nb,
                    depth - 1,
                    -1,
                    alpha,
                    beta,
                    start_time
                )

                if score > current_score:
                    current_score = score
                    current_best = mv

                alpha = max(alpha, current_score)

            best_move = current_best
            best_score = current_score
            depth += 1

            # Reorder next iteration around best move.
            ordered = [best_move] + [m for m in ordered if m != best_move]

        except TimeoutError:
            break

    return move_to_str(best_move)


def alphabeta(b, depth, side, alpha, beta, start_time):
    if time.time() - start_time > SEARCH_LIMIT:
        raise TimeoutError

    if is_connected(b, 1):
        return 10000000 + depth
    if is_connected(b, -1):
        return -10000000 - depth

    if depth == 0:
        return evaluate(b)

    moves = generate_moves(b, side)
    if not moves:
        return evaluate(b)

    moves = order_moves(b, moves, side)

    if side == 1:
        value = -10**18
        for mv in moves:
            if time.time() - start_time > SEARCH_LIMIT:
                raise TimeoutError

            nb = make_move(b, mv)
            value = max(value, alphabeta(nb, depth - 1, -1, alpha, beta, start_time))
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value
    else:
        value = 10**18
        for mv in moves:
            if time.time() - start_time > SEARCH_LIMIT:
                raise TimeoutError

            nb = make_move(b, mv)
            value = min(value, alphabeta(nb, depth - 1, 1, alpha, beta, start_time))
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value


def generate_moves(b, side):
    moves = []

    row_counts = [0] * BOARD_SIZE
    col_counts = [0] * BOARD_SIZE
    diag1_counts = [0] * (2 * BOARD_SIZE - 1)  # r - c + 7
    diag2_counts = [0] * (2 * BOARD_SIZE - 1)  # r + c

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if b[r][c] != 0:
                row_counts[r] += 1
                col_counts[c] += 1
                diag1_counts[r - c + 7] += 1
                diag2_counts[r + c] += 1

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if b[r][c] != side:
                continue

            for dr, dc in DIRS:
                if dr == 0:
                    dist = row_counts[r]
                elif dc == 0:
                    dist = col_counts[c]
                elif dr == dc:
                    dist = diag1_counts[r - c + 7]
                else:
                    dist = diag2_counts[r + c]

                tr = r + dr * dist
                tc = c + dc * dist

                if not inside(tr, tc):
                    continue

                if b[tr][tc] == side:
                    continue

                # May jump over own pieces, but not enemy pieces.
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


def make_move(b, mv):
    r, c, tr, tc = mv
    nb = [row[:] for row in b]
    nb[tr][tc] = nb[r][c]
    nb[r][c] = 0
    return nb


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
            nr = r + dr
            nc = c + dc
            if inside(nr, nc) and b[nr][nc] == side and (nr, nc) not in seen:
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
        return 0, 0, 0.0, 0.0

    seen = set()
    comps = 0
    largest = 0

    for p in pieces:
        if p in seen:
            continue

        comps += 1
        stack = [p]
        seen.add(p)
        size = 0

        while stack:
            r, c = stack.pop()
            size += 1
            for dr, dc in DIRS:
                nr = r + dr
                nc = c + dc
                if inside(nr, nc) and b[nr][nc] == side and (nr, nc) not in seen:
                    seen.add((nr, nc))
                    stack.append((nr, nc))

        largest = max(largest, size)

    cr = sum(p[0] for p in pieces) / len(pieces)
    cc = sum(p[1] for p in pieces) / len(pieces)

    spread = 0.0
    center_penalty = 0.0

    for r, c in pieces:
        spread += max(abs(r - cr), abs(c - cc))
        center_penalty += abs(r - 3.5) + abs(c - 3.5)

    return comps, largest, spread, center_penalty


def evaluate(b):
    if is_connected(b, 1):
        return 10000000
    if is_connected(b, -1):
        return -10000000

    my_count = count_pieces(b, 1)
    op_count = count_pieces(b, -1)

    my_comps, my_largest, my_spread, my_center = component_info(b, 1)
    op_comps, op_largest, op_spread, op_center = component_info(b, -1)

    my_mob = len(generate_moves(b, 1))
    op_mob = len(generate_moves(b, -1))

    score = 0.0

    # Connectivity is by far the most important strategic feature.
    score += (op_comps - my_comps) * 1200.0
    score += (my_largest - op_largest) * 220.0

    # Compactness helps pieces connect.
    score += (op_spread - my_spread) * 95.0

    # Captures can be good because fewer pieces are easier to connect,
    # but avoid overvaluing material.
    score += (op_count - my_count) * 35.0

    # Centralization and mobility are secondary.
    score += (op_center - my_center) * 8.0
    score += (my_mob - op_mob) * 4.0

    # Reward near-adjacencies.
    score += adjacency_score(b, 1) * 18.0
    score -= adjacency_score(b, -1) * 18.0

    return score


def adjacency_score(b, side):
    total = 0
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if b[r][c] != side:
                continue
            for dr, dc in DIRS:
                nr = r + dr
                nc = c + dc
                if inside(nr, nc) and b[nr][nc] == side:
                    total += 1
    return total // 2


def order_moves(b, moves, side):
    scored = []

    for mv in moves:
        r, c, tr, tc = mv
        capture = 1 if b[tr][tc] == -side else 0
        nb = make_move(b, mv)

        if is_connected(nb, side):
            win_bonus = 1000000
        else:
            win_bonus = 0

        comps, largest, spread, center = component_info(nb, side)

        # For side 1 higher is better; for side -1 lower root eval is better.
        local = (
            win_bonus
            - comps * 1000
            + largest * 150
            - spread * 50
            - center * 3
            + capture * 80
        )

        if side == 1:
            scored.append((local, mv))
        else:
            scored.append((-local, mv))

    scored.sort(reverse=True, key=lambda x: x[0])
    return [mv for _, mv in scored]


def count_pieces(b, side):
    n = 0
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if b[r][c] == side:
                n += 1
    return n


def inside(r, c):
    return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE


def move_to_str(mv):
    r, c, tr, tc = mv
    return f"{r},{c}:{tr},{tc}"

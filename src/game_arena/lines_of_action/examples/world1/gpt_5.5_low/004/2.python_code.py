
import time
import math
from collections import deque

BOARD_SIZE = 8
DIRS = [
    (-1, 0), (1, 0), (0, -1), (0, 1),
    (-1, -1), (-1, 1), (1, -1), (1, 1)
]

TIME_LIMIT = 0.90


def policy(board) -> str:
    start = time.time()

    # Convert to plain list-of-lists in case board is numpy-like.
    b = [[int(board[r][c]) for c in range(BOARD_SIZE)] for r in range(BOARD_SIZE)]

    moves = generate_moves(b)
    if not moves:
        # Should not normally happen, but return syntactically valid fallback.
        return "0,0:0,0"

    # Immediate win.
    for mv in moves:
        nb = make_move_no_flip(b, mv)
        if is_connected(nb, 1):
            return move_to_str(mv)

    # Safe fallback: ordered first move.
    ordered = order_moves(b, moves)
    best_move = ordered[0]

    # Iterative deepening.
    try:
        depth = 1
        while True:
            if time.time() - start > TIME_LIMIT:
                break

            alpha = -10**12
            beta = 10**12
            current_best = best_move
            current_best_score = -10**12

            for mv in ordered:
                if time.time() - start > TIME_LIMIT:
                    raise TimeoutError

                child = make_move_flip(b, mv)

                # If the move connects us, it is winning.
                nb_no_flip = make_move_no_flip(b, mv)
                if is_connected(nb_no_flip, 1):
                    score = 10**9
                else:
                    score = -negamax(child, depth - 1, -beta, -alpha, start)

                if score > current_best_score:
                    current_best_score = score
                    current_best = mv

                if score > alpha:
                    alpha = score

            best_move = current_best
            depth += 1

            # In practice depth 4+ can be risky in Python within 1 second.
            if depth > 4:
                break

    except TimeoutError:
        pass
    except Exception:
        # Never fail to return a legal move.
        pass

    return move_to_str(best_move)


def negamax(b, depth, alpha, beta, start):
    if time.time() - start > TIME_LIMIT:
        raise TimeoutError

    # From current side's perspective.
    if is_connected(b, 1):
        return 10**8
    if is_connected(b, -1):
        return -10**8

    if depth <= 0:
        return evaluate(b)

    moves = generate_moves(b)
    if not moves:
        return -10**7

    moves = order_moves(b, moves)

    best = -10**12

    for mv in moves:
        if time.time() - start > TIME_LIMIT:
            raise TimeoutError

        nb_no_flip = make_move_no_flip(b, mv)
        if is_connected(nb_no_flip, 1):
            score = 10**8 + depth
        else:
            child = flip_board(nb_no_flip)
            score = -negamax(child, depth - 1, -beta, -alpha, start)

        if score > best:
            best = score
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break

    return best


def generate_moves(b):
    moves = []

    # Precompute line counts.
    row_count = [0] * BOARD_SIZE
    col_count = [0] * BOARD_SIZE
    diag1_count = {}  # r - c
    diag2_count = {}  # r + c

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if b[r][c] != 0:
                row_count[r] += 1
                col_count[c] += 1
                diag1_count[r - c] = diag1_count.get(r - c, 0) + 1
                diag2_count[r + c] = diag2_count.get(r + c, 0) + 1

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if b[r][c] != 1:
                continue

            for dr, dc in DIRS:
                if dr == 0:
                    dist = row_count[r]
                elif dc == 0:
                    dist = col_count[c]
                elif dr == dc:
                    dist = diag1_count.get(r - c, 0)
                else:
                    dist = diag2_count.get(r + c, 0)

                tr = r + dr * dist
                tc = c + dc * dist

                if not in_bounds(tr, tc):
                    continue
                if b[tr][tc] == 1:
                    continue

                blocked = False
                cr = r + dr
                cc = c + dc
                while (cr, cc) != (tr, tc):
                    if b[cr][cc] == -1:
                        blocked = True
                        break
                    cr += dr
                    cc += dc

                if not blocked:
                    moves.append((r, c, tr, tc))

    return moves


def order_moves(b, moves):
    scored = []
    for mv in moves:
        r, c, tr, tc = mv
        score = 0

        # Captures are often strong in LOA.
        if b[tr][tc] == -1:
            score += 500

        # Prefer moving toward center.
        old_center_dist = abs(r - 3.5) + abs(c - 3.5)
        new_center_dist = abs(tr - 3.5) + abs(tc - 3.5)
        score += int((old_center_dist - new_center_dist) * 20)

        # Prefer destination adjacent to own pieces.
        adj = 0
        for dr, dc in DIRS:
            nr, nc = tr + dr, tc + dc
            if in_bounds(nr, nc) and b[nr][nc] == 1:
                adj += 1
        score += adj * 60

        # Penalize moving away from friendly cluster.
        own = get_pieces(b, 1)
        if own:
            cx = sum(x for x, y in own) / len(own)
            cy = sum(y for x, y in own) / len(own)
            old_d = max(abs(r - cx), abs(c - cy))
            new_d = max(abs(tr - cx), abs(tc - cy))
            score += int((old_d - new_d) * 30)

        scored.append((score, mv))

    scored.sort(reverse=True, key=lambda x: x[0])
    return [mv for _, mv in scored]


def make_move_no_flip(b, mv):
    r, c, tr, tc = mv
    nb = [row[:] for row in b]
    nb[r][c] = 0
    nb[tr][tc] = 1
    return nb


def make_move_flip(b, mv):
    return flip_board(make_move_no_flip(b, mv))


def flip_board(b):
    return [[-b[r][c] for c in range(BOARD_SIZE)] for r in range(BOARD_SIZE)]


def evaluate(b):
    # Current side is 1.
    if is_connected(b, 1):
        return 10**8
    if is_connected(b, -1):
        return -10**8

    my_pieces = get_pieces(b, 1)
    op_pieces = get_pieces(b, -1)

    if not my_pieces:
        return -10**8
    if not op_pieces:
        return 10**8

    my_components, my_largest = component_info(b, 1)
    op_components, op_largest = component_info(b, -1)

    score = 0

    # Connecting is the main objective.
    score += (op_components - my_components) * 3500
    score += (my_largest - op_largest) * 700

    # Having fewer pieces can sometimes help connectivity, but material still matters.
    score += (len(my_pieces) - len(op_pieces)) * 120

    # Compactness.
    score -= compactness(my_pieces) * 45
    score += compactness(op_pieces) * 45

    # Center control.
    score += center_score(my_pieces) * 18
    score -= center_score(op_pieces) * 18

    # Local adjacency.
    score += adjacency_score(b, 1) * 90
    score -= adjacency_score(b, -1) * 90

    # Mobility, lightly weighted.
    my_mob = len(generate_moves(b))
    fb = flip_board(b)
    op_mob = len(generate_moves(fb))
    score += (my_mob - op_mob) * 8

    return score


def component_info(b, side):
    pieces = get_pieces(b, side)
    if not pieces:
        return 99, 0

    unvisited = set(pieces)
    components = 0
    largest = 0

    while unvisited:
        components += 1
        start = next(iter(unvisited))
        q = deque([start])
        unvisited.remove(start)
        size = 0

        while q:
            r, c = q.popleft()
            size += 1

            for dr, dc in DIRS:
                nr, nc = r + dr, c + dc
                if (nr, nc) in unvisited and b[nr][nc] == side:
                    unvisited.remove((nr, nc))
                    q.append((nr, nc))

        if size > largest:
            largest = size

    return components, largest


def is_connected(b, side):
    pieces = get_pieces(b, side)
    n = len(pieces)
    if n <= 1:
        return True

    start = pieces[0]
    seen = {start}
    q = deque([start])

    while q:
        r, c = q.popleft()
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc) and b[nr][nc] == side and (nr, nc) not in seen:
                seen.add((nr, nc))
                q.append((nr, nc))

    return len(seen) == n


def compactness(pieces):
    if len(pieces) <= 1:
        return 0

    cx = sum(r for r, c in pieces) / len(pieces)
    cy = sum(c for r, c in pieces) / len(pieces)

    total = 0
    for r, c in pieces:
        total += max(abs(r - cx), abs(c - cy))
    return total


def center_score(pieces):
    score = 0
    for r, c in pieces:
        score -= abs(r - 3.5) + abs(c - 3.5)
    return score


def adjacency_score(b, side):
    score = 0
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if b[r][c] != side:
                continue
            for dr, dc in DIRS:
                nr, nc = r + dr, c + dc
                if in_bounds(nr, nc) and b[nr][nc] == side:
                    score += 1
    return score // 2


def get_pieces(b, side):
    pieces = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if b[r][c] == side:
                pieces.append((r, c))
    return pieces


def in_bounds(r, c):
    return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE


def move_to_str(mv):
    r, c, tr, tc = mv
    return f"{r},{c}:{tr},{tc}"

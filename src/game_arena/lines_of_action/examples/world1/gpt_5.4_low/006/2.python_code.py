
import time
from collections import deque

WIN_SCORE = 10**9
DIRS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
]

def policy(board) -> str:
    start = time.time()
    time_limit = 0.92

    # Ensure mutable plain Python list structure
    board = [list(row) for row in board]

    moves = generate_moves(board)
    if not moves:
        # Should not normally happen, but must always return a legal string.
        # If arena never supplies no-move states, this path is irrelevant.
        # Still, return a syntactically valid placeholder.
        return "0,0:0,0"

    # Immediate winning move if available
    for mv in moves:
        nb = apply_move(board, mv)
        if is_connected(nb, 1):
            return move_to_str(mv)

    # Order root moves
    ordered = order_moves(board, moves)

    best_move = ordered[0]
    best_score = -10**18

    # Iterative deepening
    depth = 1
    while True:
        if time.time() - start > time_limit:
            break
        current_best_move = best_move
        current_best_score = -10**18
        alpha = -10**18
        beta = 10**18

        completed = True
        for mv in ordered:
            if time.time() - start > time_limit:
                completed = False
                break

            nb = apply_move(board, mv)
            child = flip_board(nb)
            score = -negamax(child, depth - 1, -beta, -alpha, start, time_limit)

            if score > current_best_score:
                current_best_score = score
                current_best_move = mv
            if score > alpha:
                alpha = score

        if completed:
            best_move = current_best_move
            best_score = current_best_score
            # Reorder root by principal variation preference
            ordered = [best_move] + [m for m in ordered if m != best_move]
            depth += 1
            if depth > 4:
                break
        else:
            break

    return move_to_str(best_move)


def move_to_str(mv):
    r1, c1, r2, c2 = mv
    return f"{r1},{c1}:{r2},{c2}"


def flip_board(board):
    return [[-x for x in row] for row in board]


def apply_move(board, mv):
    r1, c1, r2, c2 = mv
    nb = [row[:] for row in board]
    nb[r2][c2] = nb[r1][c1]
    nb[r1][c1] = 0
    return nb


def in_bounds(r, c):
    return 0 <= r < 8 and 0 <= c < 8


def line_counts(board):
    rowc = [0] * 8
    colc = [0] * 8
    diagc = [0] * 15      # r-c+7
    antidiagc = [0] * 15  # r+c
    for r in range(8):
        for c in range(8):
            if board[r][c] != 0:
                rowc[r] += 1
                colc[c] += 1
                diagc[r - c + 7] += 1
                antidiagc[r + c] += 1
    return rowc, colc, diagc, antidiagc


def move_distance(rowc, colc, diagc, antidiagc, r, c, dr, dc):
    if dr == 0:
        return rowc[r]
    if dc == 0:
        return colc[c]
    if dr == dc:
        return diagc[r - c + 7]
    return antidiagc[r + c]


def generate_moves(board):
    rowc, colc, diagc, antidiagc = line_counts(board)
    moves = []

    for r in range(8):
        for c in range(8):
            if board[r][c] != 1:
                continue

            for dr, dc in DIRS:
                dist = move_distance(rowc, colc, diagc, antidiagc, r, c, dr, dc)
                tr = r + dr * dist
                tc = c + dc * dist

                if not in_bounds(tr, tc):
                    continue
                if board[tr][tc] == 1:
                    continue

                legal = True
                # Cannot jump over enemy pieces
                for step in range(1, dist):
                    rr = r + dr * step
                    cc = c + dc * step
                    if board[rr][cc] == -1:
                        legal = False
                        break

                if legal:
                    moves.append((r, c, tr, tc))

    return moves


def order_moves(board, moves):
    scored = []
    for mv in moves:
        r1, c1, r2, c2 = mv
        score = 0

        # Captures are good
        if board[r2][c2] == -1:
            score += 80

        # Prefer centralization
        score -= abs(r2 - 3.5) + abs(c2 - 3.5)
        score += 0.25 * (abs(r1 - 3.5) + abs(c1 - 3.5))

        # Small preference for moves that reduce spread / create contact
        nb = apply_move(board, mv)
        if is_connected(nb, 1):
            score += 1000000
        else:
            comps, largest, area, adj = component_metrics(nb, 1)
            score += 20 * (10 - comps)
            score += 2 * largest
            score += 0.5 * adj
            score -= 0.2 * area

        scored.append((score, mv))

    scored.sort(reverse=True, key=lambda x: x[0])
    return [mv for _, mv in scored]


def negamax(board, depth, alpha, beta, start, time_limit):
    if time.time() - start > time_limit:
        return evaluate(board)

    # If opponent is already connected, previous move won for them.
    if is_connected(board, -1):
        return -WIN_SCORE
    # Rare/degenerate safeguard
    if is_connected(board, 1):
        return WIN_SCORE

    if depth <= 0:
        return evaluate(board)

    moves = generate_moves(board)
    if not moves:
        return evaluate(board)

    moves = order_moves(board, moves)

    best = -10**18
    for mv in moves:
        if time.time() - start > time_limit:
            break

        nb = apply_move(board, mv)
        child = flip_board(nb)
        score = -negamax(child, depth - 1, -beta, -alpha, start, time_limit)

        if score > best:
            best = score
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    if best == -10**18:
        return evaluate(board)
    return best


def is_connected(board, player):
    positions = []
    for r in range(8):
        for c in range(8):
            if board[r][c] == player:
                positions.append((r, c))

    if len(positions) <= 1:
        return True

    start = positions[0]
    seen = {start}
    dq = deque([start])

    while dq:
        r, c = dq.popleft()
        for dr, dc in DIRS:
            rr, cc = r + dr, c + dc
            if in_bounds(rr, cc) and board[rr][cc] == player and (rr, cc) not in seen:
                seen.add((rr, cc))
                dq.append((rr, cc))

    return len(seen) == len(positions)


def component_metrics(board, player):
    seen = [[False] * 8 for _ in range(8)]
    comps = 0
    largest = 0
    positions = []
    adjacency = 0

    for r in range(8):
        for c in range(8):
            if board[r][c] == player:
                positions.append((r, c))
                # Count local friendly adjacency edges (rough compactness)
                for dr, dc in DIRS:
                    rr, cc = r + dr, c + dc
                    if in_bounds(rr, cc) and board[rr][cc] == player:
                        adjacency += 1

    adjacency //= 2

    for r, c in positions:
        if seen[r][c]:
            continue
        comps += 1
        q = deque([(r, c)])
        seen[r][c] = True
        size = 0
        while q:
            x, y = q.popleft()
            size += 1
            for dr, dc in DIRS:
                xx, yy = x + dr, y + dc
                if in_bounds(xx, yy) and not seen[xx][yy] and board[xx][yy] == player:
                    seen[xx][yy] = True
                    q.append((xx, yy))
        if size > largest:
            largest = size

    if positions:
        rs = [r for r, _ in positions]
        cs = [c for _, c in positions]
        area = (max(rs) - min(rs) + 1) * (max(cs) - min(cs) + 1)
    else:
        area = 0

    return comps, largest, area, adjacency


def evaluate(board):
    # Terminal checks
    if is_connected(board, -1):
        return -WIN_SCORE
    if is_connected(board, 1):
        return WIN_SCORE

    my_count = 0
    opp_count = 0
    for r in range(8):
        for c in range(8):
            if board[r][c] == 1:
                my_count += 1
            elif board[r][c] == -1:
                opp_count += 1

    my_comp, my_largest, my_area, my_adj = component_metrics(board, 1)
    op_comp, op_largest, op_area, op_adj = component_metrics(board, -1)

    score = 0
    score += 600 * (op_comp - my_comp)
    score += 80 * (my_largest - op_largest)
    score += 12 * (op_area - my_area)
    score += 15 * (my_adj - op_adj)
    score += 40 * (my_count - opp_count)

    # Mild centralization bonus
    my_central = 0.0
    op_central = 0.0
    for r in range(8):
        for c in range(8):
            if board[r][c] == 1:
                my_central -= abs(r - 3.5) + abs(c - 3.5)
            elif board[r][c] == -1:
                op_central -= abs(r - 3.5) + abs(c - 3.5)
    score += int(my_central - op_central)

    return score

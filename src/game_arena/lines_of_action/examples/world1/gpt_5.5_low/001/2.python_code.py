
import time
import math
from collections import deque

BOARD_SIZE = 8
DIRS = [
    (-1, 0), (1, 0), (0, -1), (0, 1),
    (-1, -1), (-1, 1), (1, -1), (1, 1)
]

TIME_LIMIT = 0.92


def policy(board) -> str:
    """
    Return a legal Lines of Action move in the format:
    "from_row,from_col:to_row,to_col"

    The board is always from the current player's perspective:
      1  = our piece
     -1  = opponent piece
      0  = empty
    """
    start_time = time.time()

    # Convert to a lightweight mutable list-of-lists if needed.
    b = [list(row) for row in board]

    legal = generate_moves(b, 1)
    if not legal:
        # This should almost never happen in a normal LOA position.
        # Return syntactically valid fallback.
        return "0,0:0,0"

    # If any move immediately connects us, play it.
    for mv in legal:
        nb = make_move(b, mv)
        if is_connected(nb, 1):
            return move_to_str(mv)

    # Strong fallback in case search times out.
    best_move = legal[0]
    best_score = -10**18

    # Good initial ordering.
    legal = order_moves(b, legal, 1)

    # Iterative deepening. Usually reaches depth 3-4 comfortably.
    max_depth = 4
    piece_count = count_pieces(b, 1) + count_pieces(b, -1)
    if piece_count <= 12:
        max_depth = 5

    try:
        for depth in range(1, max_depth + 1):
            if time.time() - start_time > TIME_LIMIT:
                break

            current_best = best_move
            current_score = -10**18

            alpha = -10**18
            beta = 10**18

            for mv in legal:
                if time.time() - start_time > TIME_LIMIT:
                    raise TimeoutError

                nb = make_move(b, mv)

                if is_connected(nb, 1):
                    score = 10**12
                else:
                    score = alphabeta(
                        nb,
                        depth - 1,
                        alpha,
                        beta,
                        -1,
                        start_time
                    )

                if score > current_score:
                    current_score = score
                    current_best = mv

                alpha = max(alpha, current_score)

            best_move = current_best
            best_score = current_score

            # Reorder root moves around the best move for next iteration.
            legal = [best_move] + [m for m in legal if m != best_move]

            if best_score >= 10**11:
                break

    except TimeoutError:
        pass
    except Exception:
        # Safety: never fail to return a legal move.
        pass

    return move_to_str(best_move)


def alphabeta(board, depth, alpha, beta, side, start_time):
    """
    Alpha-beta search.
    side == 1  : maximizing player to move
    side == -1 : minimizing opponent to move

    Evaluation is always from side 1's perspective.
    """
    if time.time() - start_time > TIME_LIMIT:
        raise TimeoutError

    if is_connected(board, 1):
        return 10**12 + depth
    if is_connected(board, -1):
        return -10**12 - depth

    if depth <= 0:
        return evaluate(board)

    moves = generate_moves(board, side)
    if not moves:
        return evaluate(board)

    moves = order_moves(board, moves, side)

    if side == 1:
        value = -10**18
        for mv in moves:
            nb = make_move(board, mv)
            score = alphabeta(nb, depth - 1, alpha, beta, -1, start_time)
            if score > value:
                value = score
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value
    else:
        value = 10**18
        for mv in moves:
            nb = make_move(board, mv)
            score = alphabeta(nb, depth - 1, alpha, beta, 1, start_time)
            if score < value:
                value = score
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value


def generate_moves(board, side):
    moves = []

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != side:
                continue

            for dr, dc in DIRS:
                line_count = count_line_pieces(board, r, c, dr, dc)
                tr = r + dr * line_count
                tc = c + dc * line_count

                if not in_bounds(tr, tc):
                    continue

                # Cannot land on own piece.
                if board[tr][tc] == side:
                    continue

                # Cannot jump over enemy pieces.
                blocked = False
                cr, cc = r + dr, c + dc
                while (cr, cc) != (tr, tc):
                    if board[cr][cc] == -side:
                        blocked = True
                        break
                    cr += dr
                    cc += dc

                if blocked:
                    continue

                moves.append((r, c, tr, tc))

    return moves


def count_line_pieces(board, r, c, dr, dc):
    """
    Count all pieces, friendly and enemy, on the full line determined by direction.
    """
    count = 0

    # Walk backward to start of line.
    sr, sc = r, c
    while in_bounds(sr - dr, sc - dc):
        sr -= dr
        sc -= dc

    # Walk forward along line.
    while in_bounds(sr, sc):
        if board[sr][sc] != 0:
            count += 1
        sr += dr
        sc += dc

    return count


def make_move(board, mv):
    r, c, tr, tc = mv
    nb = [row[:] for row in board]
    side = nb[r][c]
    nb[r][c] = 0
    nb[tr][tc] = side
    return nb


def is_connected(board, side):
    pieces = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == side:
                pieces.append((r, c))

    if len(pieces) <= 1:
        return True

    start = pieces[0]
    seen = {start}
    q = deque([start])

    while q:
        r, c = q.popleft()
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc) and board[nr][nc] == side and (nr, nc) not in seen:
                seen.add((nr, nc))
                q.append((nr, nc))

    return len(seen) == len(pieces)


def component_info(board, side):
    pieces = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == side:
                pieces.append((r, c))

    if not pieces:
        return 0, 0, []

    unseen = set(pieces)
    components = []
    largest = 0

    while unseen:
        start = next(iter(unseen))
        unseen.remove(start)
        q = deque([start])
        comp = [start]

        while q:
            r, c = q.popleft()
            for dr, dc in DIRS:
                nr, nc = r + dr, c + dc
                if (nr, nc) in unseen:
                    unseen.remove((nr, nc))
                    q.append((nr, nc))
                    comp.append((nr, nc))

        components.append(comp)
        if len(comp) > largest:
            largest = len(comp)

    return len(components), largest, pieces


def evaluate(board):
    """
    Static evaluation from our perspective.
    Main goals in LOA:
    - become connected
    - reduce number of components
    - keep pieces compact
    - avoid letting opponent connect
    - maintain useful mobility
    """
    if is_connected(board, 1):
        return 10**12
    if is_connected(board, -1):
        return -10**12

    my_components, my_largest, my_pieces = component_info(board, 1)
    op_components, op_largest, op_pieces = component_info(board, -1)

    my_n = len(my_pieces)
    op_n = len(op_pieces)

    if my_n == 0:
        return -10**12
    if op_n == 0:
        return 10**12

    score = 0.0

    # Fewer components is usually the strongest non-terminal indicator.
    score += 1400.0 * (op_components - my_components)

    # Larger connected mass.
    score += 220.0 * (my_largest - op_largest)

    # Captures are useful because fewer pieces are easier to connect.
    score += 120.0 * (op_n - my_n)

    # Compactness around centroid.
    score += 45.0 * (compactness(op_pieces) - compactness(my_pieces))

    # Pairwise closeness.
    score += 12.0 * (pair_distance(op_pieces) - pair_distance(my_pieces))

    # Centralization helps pieces meet.
    score += 8.0 * (centrality(my_pieces) - centrality(op_pieces))

    # Mobility, but not too heavily.
    try:
        my_mob = len(generate_moves(board, 1))
        op_mob = len(generate_moves(board, -1))
        score += 3.0 * (my_mob - op_mob)
    except Exception:
        pass

    return score


def compactness(pieces):
    if not pieces:
        return 99.0

    cr = sum(r for r, c in pieces) / float(len(pieces))
    cc = sum(c for r, c in pieces) / float(len(pieces))

    total = 0.0
    for r, c in pieces:
        total += max(abs(r - cr), abs(c - cc))
    return total / float(len(pieces))


def pair_distance(pieces):
    n = len(pieces)
    if n <= 1:
        return 0.0

    total = 0.0
    count = 0
    for i in range(n):
        r1, c1 = pieces[i]
        for j in range(i + 1, n):
            r2, c2 = pieces[j]
            total += max(abs(r1 - r2), abs(c1 - c2))
            count += 1

    return total / float(count)


def centrality(pieces):
    total = 0.0
    for r, c in pieces:
        total -= abs(r - 3.5) + abs(c - 3.5)
    return total


def order_moves(board, moves, side):
    """
    Move ordering:
    - immediate wins first
    - captures
    - moves toward center / compactness
    """
    scored = []

    for mv in moves:
        r, c, tr, tc = mv
        capture = 1 if board[tr][tc] == -side else 0

        center_before = abs(r - 3.5) + abs(c - 3.5)
        center_after = abs(tr - 3.5) + abs(tc - 3.5)
        center_gain = center_before - center_after

        nb = make_move(board, mv)
        win = 1 if is_connected(nb, side) else 0

        if side == 1:
            h = 1000000 * win + 5000 * capture + 20 * center_gain + evaluate_light(nb, side)
        else:
            h = 1000000 * win + 5000 * capture + 20 * center_gain + evaluate_light(nb, side)

        scored.append((h, mv))

    scored.sort(reverse=True, key=lambda x: x[0])
    return [mv for _, mv in scored]


def evaluate_light(board, side):
    comps, largest, pieces = component_info(board, side)
    return 100 * largest - 300 * comps - 10 * compactness(pieces)


def count_pieces(board, side):
    n = 0
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == side:
                n += 1
    return n


def in_bounds(r, c):
    return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE


def move_to_str(mv):
    r, c, tr, tc = mv
    return f"{r},{c}:{tr},{tc}"

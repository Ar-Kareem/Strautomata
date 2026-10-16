
import time
from collections import deque
import numpy as np

SIZE = 6
DIRS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
]


def slide_squares(board, r, c):
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        while 0 <= nr < SIZE and 0 <= nc < SIZE and board[nr, nc] == 0:
            yield nr, nc
            nr += dr
            nc += dc


def format_move(m):
    return f"{int(m[0])},{int(m[1])}:{int(m[2])},{int(m[3])}:{int(m[4])},{int(m[5])}"


def apply_move(board, move, player):
    fr, fc, tr, tc, ar, ac = move
    board[fr, fc] = 0
    board[tr, tc] = player
    board[ar, ac] = -1


def undo_move(board, move, player):
    fr, fc, tr, tc, ar, ac = move
    board[ar, ac] = 0
    board[tr, tc] = 0
    board[fr, fc] = player


def generate_moves(board, player):
    moves = []
    positions = np.argwhere(board == player)
    for fr, fc in positions:
        fr = int(fr)
        fc = int(fc)
        board[fr, fc] = 0
        for tr, tc in slide_squares(board, fr, fc):
            board[tr, tc] = player
            for ar, ac in slide_squares(board, tr, tc):
                moves.append((fr, fc, tr, tc, ar, ac))
            board[tr, tc] = 0
        board[fr, fc] = player
    return moves


def count_reach(board, player):
    total = 0
    positions = np.argwhere(board == player)
    for r, c in positions:
        r = int(r)
        c = int(c)
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while 0 <= nr < SIZE and 0 <= nc < SIZE and board[nr, nc] == 0:
                total += 1
                nr += dr
                nc += dc
    return total


def queen_distance_map(board, player):
    dist = np.full((SIZE, SIZE), 99, dtype=np.int8)
    q = deque()
    positions = np.argwhere(board == player)
    for r, c in positions:
        r = int(r)
        c = int(c)
        dist[r, c] = 0
        q.append((r, c))

    while q:
        r, c = q.popleft()
        nd = int(dist[r, c]) + 1
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while 0 <= nr < SIZE and 0 <= nc < SIZE and board[nr, nc] == 0:
                if dist[nr, nc] > nd:
                    dist[nr, nc] = nd
                    q.append((nr, nc))
                nr += dr
                nc += dc
    return dist


def evaluate(board, player):
    opp = 3 - player

    my_reach = count_reach(board, player)
    opp_reach = count_reach(board, opp)

    # No piece move => no legal move in Amazons, since any queen move always allows
    # at least shooting back to the vacated origin square.
    if my_reach == 0 and opp_reach == 0:
        return 0
    if my_reach == 0:
        return -100000
    if opp_reach == 0:
        return 100000

    myd = queen_distance_map(board, player)
    opd = queen_distance_map(board, opp)

    territory = 0
    influence = 0
    contested = 0
    my_cells = 0
    opp_cells = 0

    for r in range(SIZE):
        for c in range(SIZE):
            if board[r, c] != 0:
                continue
            dm = int(myd[r, c])
            do = int(opd[r, c])

            if dm < do:
                territory += 1
                my_cells += 1
                if do < 99:
                    contested += 1
            elif do < dm:
                territory -= 1
                opp_cells += 1
                if dm < 99:
                    contested += 1
            elif dm < 99:
                contested += 1

            if dm < 99:
                influence += 7 - dm
            if do < 99:
                influence -= 7 - do

    # If the board is effectively split into separate chambers, prioritize owned space.
    if contested == 0:
        return 80 * (my_cells - opp_cells) + 12 * (my_reach - opp_reach)

    return 8 * (my_reach - opp_reach) + 6 * territory + influence


def local_move_bonus(move, opp_positions):
    fr, fc, tr, tc, ar, ac = move

    # Prefer reasonable centrality for the moved amazon, but not too strongly.
    center_score = (
        4.5
        - 0.9 * (abs(tr - 2.5) + abs(tc - 2.5))
        - 0.3 * (abs(ar - 2.5) + abs(ac - 2.5))
    )

    if not opp_positions:
        return center_score

    d_arrow = min(max(abs(ar - r), abs(ac - c)) for r, c in opp_positions)
    d_dest = min(max(abs(tr - r), abs(tc - c)) for r, c in opp_positions)

    block_score = 3.5 - d_arrow
    pressure_score = 2.5 - d_dest

    return center_score + 1.2 * block_score + pressure_score


def order_moves(board, player, moves, cap, deadline):
    n = len(moves)
    if n <= 1:
        return moves[:cap]

    opp = 3 - player
    opp_positions = [(int(r), int(c)) for r, c in np.argwhere(board == opp)]

    # If branch size is modest, use a more informed ordering.
    if n <= 80:
        scored = []
        complete = True
        for i, m in enumerate(moves):
            if (i & 15) == 0 and time.perf_counter() > deadline:
                complete = False
                break
            apply_move(board, m, player)
            s = 4 * (count_reach(board, player) - count_reach(board, opp))
            undo_move(board, m, player)
            s += local_move_bonus(m, opp_positions)
            scored.append((s, m))
        if complete:
            scored.sort(key=lambda x: x[0], reverse=True)
            ordered = [m for _, m in scored]
            return ordered[:cap]

    # Cheap fallback ordering.
    scored = [(local_move_bonus(m, opp_positions), m) for m in moves]
    scored.sort(key=lambda x: x[0], reverse=True)
    ordered = [m for _, m in scored]
    return ordered[:cap]


def negamax(board, depth, alpha, beta, player, deadline):
    if time.perf_counter() > deadline:
        raise TimeoutError

    if depth == 0:
        return evaluate(board, player)

    moves = generate_moves(board, player)
    if not moves:
        return -100000 - depth

    if depth >= 3:
        cap = 10
    elif depth == 2:
        cap = 14
    else:
        cap = 24

    if len(moves) > cap:
        moves = order_moves(board, player, moves, cap, deadline)
    else:
        moves = order_moves(board, player, moves, len(moves), deadline)

    opp = 3 - player
    best = -10**9

    for i, m in enumerate(moves):
        if (i & 7) == 0 and time.perf_counter() > deadline:
            raise TimeoutError
        apply_move(board, m, player)
        val = -negamax(board, depth - 1, -beta, -alpha, opp, deadline)
        undo_move(board, m, player)

        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    return best


def policy(board) -> str:
    board = np.array(board, copy=True)
    deadline = time.perf_counter() + 0.92

    root_moves = generate_moves(board, 1)
    if not root_moves:
        return "0,0:0,0:0,0"

    # Always keep a legal fallback.
    best_move = root_moves[0]

    # Root beam width.
    n_root = len(root_moves)
    if n_root > 150:
        root_cap = 28
    elif n_root > 80:
        root_cap = 32
    elif n_root > 40:
        root_cap = 40
    else:
        root_cap = n_root

    ordered = order_moves(board, 1, root_moves, root_cap, deadline)
    if ordered:
        best_move = ordered[0]

    empty_count = int(np.sum(board == 0))
    if n_root <= 6 or empty_count <= 8:
        max_depth = 5
    elif n_root <= 12 or empty_count <= 12:
        max_depth = 4
    elif n_root <= 30:
        max_depth = 3
    else:
        max_depth = 2

    # Iterative deepening: keep best completed result.
    for depth in range(1, max_depth + 1):
        if time.perf_counter() > deadline:
            break

        current_best_move = None
        current_best_score = -10**9
        scored_root = []
        alpha = -10**9
        beta = 10**9

        try:
            for i, m in enumerate(ordered):
                if (i & 3) == 0 and time.perf_counter() > deadline:
                    raise TimeoutError

                apply_move(board, m, 1)
                val = -negamax(board, depth - 1, -beta, -alpha, 2, deadline)
                undo_move(board, m, 1)

                scored_root.append((val, m))

                if val > current_best_score:
                    current_best_score = val
                    current_best_move = m

                if val > alpha:
                    alpha = val

            if current_best_move is not None:
                best_move = current_best_move
                scored_root.sort(key=lambda x: x[0], reverse=True)
                ordered = [m for _, m in scored_root]

        except TimeoutError:
            break

    return format_move(best_move)

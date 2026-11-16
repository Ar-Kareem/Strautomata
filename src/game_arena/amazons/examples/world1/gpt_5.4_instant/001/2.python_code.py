
import numpy as np

DIRS = [(-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)]

INF = 10**18


def on_board(r, c):
    return 0 <= r < 6 and 0 <= c < 6


def ray_moves(board, r, c):
    moves = []
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        while on_board(nr, nc) and board[nr, nc] == 0:
            moves.append((nr, nc))
            nr += dr
            nc += dc
    return moves


def list_amazons(board, player):
    pts = np.argwhere(board == player)
    return [tuple(x) for x in pts]


def generate_moves(board, player):
    amazons = list_amazons(board, player)
    moves = []
    for fr, fc in amazons:
        tos = ray_moves(board, fr, fc)
        if not tos:
            continue
        for tr, tc in tos:
            b2 = board.copy()
            b2[fr, fc] = 0
            b2[tr, tc] = player
            for ar, ac in ray_moves(b2, tr, tc):
                moves.append((fr, fc, tr, tc, ar, ac))
    return moves


def apply_move(board, move, player):
    fr, fc, tr, tc, ar, ac = move
    b2 = board.copy()
    b2[fr, fc] = 0
    b2[tr, tc] = player
    b2[ar, ac] = -1
    return b2


def count_mobility(board, player):
    total = 0
    for r, c in list_amazons(board, player):
        total += len(ray_moves(board, r, c))
    return total


def amazon_local_mobility_after(board, pos):
    r, c = pos
    return len(ray_moves(board, r, c))


def multi_source_queen_distance(board, sources):
    dist = np.full((6, 6), 99, dtype=np.int16)
    frontier = list(sources)
    for r, c in frontier:
        dist[r, c] = 0

    i = 0
    while i < len(frontier):
        r, c = frontier[i]
        i += 1
        nd = dist[r, c] + 1
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while on_board(nr, nc) and board[nr, nc] == 0:
                if dist[nr, nc] > nd:
                    dist[nr, nc] = nd
                    frontier.append((nr, nc))
                nr += dr
                nc += dc
    return dist


def territorial_score(board):
    my_pos = list_amazons(board, 1)
    op_pos = list_amazons(board, 2)
    if not my_pos or not op_pos:
        return 0.0

    d1 = multi_source_queen_distance(board, my_pos)
    d2 = multi_source_queen_distance(board, op_pos)

    score = 0.0
    empties = np.argwhere(board == 0)
    for r, c in empties:
        a = d1[r, c]
        b = d2[r, c]
        if a < b:
            score += 1.0
        elif a > b:
            score -= 1.0
        elif a < 99:
            score += 0.1 if a == b else 0.0
    return score


def trapped_bonus(board):
    my_immobile = 0
    op_immobile = 0
    my_local = 0
    op_local = 0

    for p in list_amazons(board, 1):
        m = amazon_local_mobility_after(board, p)
        my_local += m
        if m == 0:
            my_immobile += 1

    for p in list_amazons(board, 2):
        m = amazon_local_mobility_after(board, p)
        op_local += m
        if m == 0:
            op_immobile += 1

    return 18.0 * (op_immobile - my_immobile) + 0.25 * (my_local - op_local)


def evaluate(board):
    my_moves = generate_moves(board, 1)
    if not my_moves:
        return -100000.0
    op_moves = generate_moves(board, 2)
    if not op_moves:
        return 100000.0

    my_mob = 0
    op_mob = 0
    # Faster than full move counts while still informative
    for r, c in list_amazons(board, 1):
        my_mob += len(ray_moves(board, r, c))
    for r, c in list_amazons(board, 2):
        op_mob += len(ray_moves(board, r, c))

    terr = territorial_score(board)
    trap = trapped_bonus(board)

    return 7.0 * (len(my_moves) - len(op_moves)) + 1.2 * (my_mob - op_mob) + 2.5 * terr + trap


def quick_move_score(board, move):
    fr, fc, tr, tc, ar, ac = move
    player = 1
    b2 = board.copy()
    b2[fr, fc] = 0
    b2[tr, tc] = player
    b2[ar, ac] = -1

    # Cheap tactical estimate for move ordering / shallow selection
    my_mob = 0
    op_mob = 0
    for r, c in list_amazons(b2, 1):
        my_mob += len(ray_moves(b2, r, c))
    for r, c in list_amazons(b2, 2):
        op_mob += len(ray_moves(b2, r, c))

    # Extra weight on moved amazon and arrow pressure near opponents
    moved_local = len(ray_moves(b2, tr, tc))
    opp_positions = list_amazons(b2, 2)
    pressure = 0
    for rr, cc in opp_positions:
        d = max(abs(ar - rr), abs(ac - cc))
        if d == 1:
            pressure += 2.0
        elif d == 2:
            pressure += 0.5

    return 4.0 * (my_mob - op_mob) + 1.5 * moved_local + pressure


def order_moves(board, moves, player):
    if player == 1:
        scored = [(quick_move_score(board, m), m) for m in moves]
        scored.sort(key=lambda x: x[0], reverse=True)
    else:
        # For opponent ordering, estimate from our perspective after opponent move
        scored = []
        for m in moves:
            b2 = apply_move(board, m, 2)
            scored.append((evaluate(b2), m))
        scored.sort(key=lambda x: x[0])
    return [m for _, m in scored]


def alphabeta(board, depth, alpha, beta, player):
    moves = generate_moves(board, player)
    if depth == 0 or not moves:
        if not moves:
            return (-100000.0 if player == 1 else 100000.0), None
        return evaluate(board), None

    moves = order_moves(board, moves, player)

    # Limit branching to stay within time budget
    if depth >= 2:
        limit = 18 if player == 1 else 14
        moves = moves[:limit]

    best_move = moves[0]

    if player == 1:
        value = -INF
        for m in moves:
            b2 = apply_move(board, m, 1)
            child_val, _ = alphabeta(b2, depth - 1, alpha, beta, 2)
            if child_val > value:
                value = child_val
                best_move = m
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value, best_move
    else:
        value = INF
        for m in moves:
            b2 = apply_move(board, m, 2)
            child_val, _ = alphabeta(b2, depth - 1, alpha, beta, 1)
            if child_val < value:
                value = child_val
                best_move = m
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value, best_move


def move_to_string(move):
    fr, fc, tr, tc, ar, ac = move
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"


def policy(board) -> str:
    board = np.array(board)
    legal_moves = generate_moves(board, 1)

    # Robust fallback; environment should not call with no moves, but be safe.
    if not legal_moves:
        # Return a syntactically valid string; unreachable in proper games.
        return "0,0:0,0:0,0"

    # Immediate win check
    best_immediate = None
    best_immediate_score = -INF
    for m in legal_moves:
        b2 = apply_move(board, m, 1)
        opp = generate_moves(b2, 2)
        if not opp:
            return move_to_string(m)
        s = quick_move_score(board, m)
        if s > best_immediate_score:
            best_immediate_score = s
            best_immediate = m

    # Search depth selection by branching factor
    n = len(legal_moves)
    ordered = order_moves(board, legal_moves, 1)

    if n <= 12:
        _, best = alphabeta(board, 2, -INF, INF, 1)
    elif n <= 28:
        # Search top candidates deeper-ish via reply lookahead
        candidates = ordered[:12]
        best = candidates[0]
        best_val = -INF
        for m in candidates:
            b2 = apply_move(board, m, 1)
            val, _ = alphabeta(b2, 1, -INF, INF, 2)
            if val > best_val:
                best_val = val
                best = m
    else:
        # Large branching: pick best heuristic move among top set
        best = ordered[0]

    if best is None:
        best = best_immediate if best_immediate is not None else legal_moves[0]

    return move_to_string(best)


import numpy as np
from collections import deque
import heapq
import time


# 8 queen directions
DIRS = (
    (-1, 0), (1, 0), (0, -1), (0, 1),
    (-1, -1), (-1, 1), (1, -1), (1, 1)
)

N = 6


def in_bounds(r, c):
    return 0 <= r < N and 0 <= c < N


def queen_targets(board, r, c):
    """All empty squares reachable from (r,c) with queen-like movement."""
    res = []
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        while in_bounds(nr, nc) and board[nr, nc] == 0:
            res.append((nr, nc))
            nr += dr
            nc += dc
    return res


def mobility_count(board, player):
    """Counts total number of reachable empty destination squares for all amazons of 'player'."""
    positions = np.argwhere(board == player)
    if positions.size == 0:
        return 0
    m = 0
    for r, c in positions:
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while in_bounds(nr, nc) and board[nr, nc] == 0:
                m += 1
                nr += dr
                nc += dc
    return m


def bfs_influence(board, player):
    """
    Multi-source BFS (8-neighbor king steps) through empty squares to approximate influence/territory.
    Returns dist array with -1 for unreachable.
    """
    dist = np.full((N, N), -1, dtype=np.int16)
    q = deque()

    sources = np.argwhere(board == player)
    for r, c in sources:
        dist[r, c] = 0
        q.append((r, c))

    while q:
        r, c = q.popleft()
        d = dist[r, c]
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if not in_bounds(nr, nc):
                continue
            if dist[nr, nc] != -1:
                continue
            if board[nr, nc] != 0:
                continue
            dist[nr, nc] = d + 1
            q.append((nr, nc))
    return dist


def territory_score(board):
    """Positive means better for player 1. Based on BFS influence comparison on empty squares."""
    d1 = bfs_influence(board, 1)
    d2 = bfs_influence(board, 2)
    score = 0
    empties = np.argwhere(board == 0)
    for r, c in empties:
        a = d1[r, c]
        b = d2[r, c]
        if a == -1 and b == -1:
            continue
        if a == -1:
            score -= 1
        elif b == -1:
            score += 1
        elif a < b:
            score += 1
        elif b < a:
            score -= 1
    return score


def eval_board(board):
    """
    Evaluation from player 1 perspective.
    Uses mobility plus approximate territory.
    """
    m1 = mobility_count(board, 1)
    m2 = mobility_count(board, 2)

    # Terminal-ish signals
    if m2 == 0 and m1 > 0:
        return 10**9
    if m1 == 0 and m2 > 0:
        return -10**9
    if m1 == 0 and m2 == 0:
        return 0

    t = territory_score(board)
    # Mobility is usually decisive in Amazons; territory refines.
    return 12 * (m1 - m2) + 2 * t


def format_move(fr, fc, tr, tc, ar, ac):
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"


def generate_moves_limited(board, player, max_moves=60, arrows_per_to=8, time_deadline=None):
    """
    Generate (move_tuple, board_after) with pruning:
    - For each amazon -> each destination -> choose only a few arrow placements that best reduce opponent mobility.
    - Then keep only top max_moves moves by a quick ordering score.
    """
    opp = 3 - player
    positions = np.argwhere(board == player)
    if positions.size == 0:
        return []

    candidates = []  # list of (order_score, move_tuple, board_after)

    # For ordering: evaluate from player 1 perspective
    def order_score_for(board_after):
        v = eval_board(board_after)
        return v if player == 1 else -v

    for fr, fc in positions:
        if time_deadline is not None and time.perf_counter() > time_deadline:
            break

        tos = queen_targets(board, fr, fc)
        if not tos:
            continue

        for tr, tc in tos:
            if time_deadline is not None and time.perf_counter() > time_deadline:
                break

            board_moved = board.copy()
            board_moved[fr, fc] = 0
            board_moved[tr, tc] = player

            arrows = queen_targets(board_moved, tr, tc)
            if not arrows:
                continue

            # Select best arrow placements by minimizing opponent mobility (fast, decent heuristic)
            if len(arrows) > arrows_per_to:
                scored_arrows = []
                # For player 1, minimize opponent (2) mobility; for player 2, minimize player 1 mobility
                target_player = opp if player == 1 else 1
                for ar, ac in arrows:
                    b2 = board_moved.copy()
                    b2[ar, ac] = -1
                    mob = mobility_count(b2, target_player)
                    # tie-breaker: prefer more central blocking slightly
                    central = abs(ar - 2.5) + abs(ac - 2.5)
                    scored_arrows.append((mob, central, (ar, ac)))
                best_arrows = [x[2] for x in heapq.nsmallest(arrows_per_to, scored_arrows)]
            else:
                best_arrows = arrows

            for ar, ac in best_arrows:
                if time_deadline is not None and time.perf_counter() > time_deadline:
                    break
                board_after = board_moved.copy()
                board_after[ar, ac] = -1
                mv = (fr, fc, tr, tc, ar, ac)
                candidates.append((order_score_for(board_after), mv, board_after))

    # Keep top max_moves by ordering score
    if not candidates:
        return []

    candidates.sort(key=lambda x: x[0], reverse=True)
    if len(candidates) > max_moves:
        candidates = candidates[:max_moves]
    return [(mv, b) for _, mv, b in candidates]


def policy(board) -> str:
    """
    Returns a legal move string: "from_row,from_col:to_row,to_col:arrow_row,arrow_col"
    """
    # Ensure numpy array
    board = np.asarray(board)
    start = time.perf_counter()
    # Keep some safety margin under 1 second
    deadline = start + 0.92

    # Generate our candidate moves
    my_moves = generate_moves_limited(
        board, player=1, max_moves=70, arrows_per_to=8, time_deadline=deadline
    )

    # Robust fallback: if pruning/time caused empty, try a less-pruned generation once
    if not my_moves and time.perf_counter() < deadline:
        my_moves = generate_moves_limited(
            board, player=1, max_moves=200, arrows_per_to=40, time_deadline=deadline
        )

    # If still none, environment shouldn't call, but return something deterministic (may be illegal if truly no moves)
    if not my_moves:
        # Try to find ANY legal move with a brute attempt without time pruning
        brute = generate_moves_limited(board, player=1, max_moves=1, arrows_per_to=1000, time_deadline=None)
        if brute:
            mv, _ = brute[0]
            return format_move(*mv)
        return "0,0:0,0:0,0"

    # Order by immediate eval
    scored_my = []
    for mv, b_after in my_moves:
        scored_my.append((eval_board(b_after), mv, b_after))
    scored_my.sort(key=lambda x: x[0], reverse=True)

    best_mv = scored_my[0][1]
    best_val = -10**18

    # 2-ply minimax: maximize over our moves, opponent minimizes
    for _, mv, b_after in scored_my:
        if time.perf_counter() > deadline:
            break

        # If opponent has no moves, take immediate win
        if mobility_count(b_after, 2) == 0:
            return format_move(*mv)

        # Opponent replies (limited)
        opp_moves = generate_moves_limited(
            b_after, player=2, max_moves=40, arrows_per_to=7, time_deadline=deadline
        )
        if not opp_moves:
            # Opp stuck => win
            return format_move(*mv)

        worst = 10**18
        # Opponent chooses move that minimizes our eval
        # Order opponent moves by eval ascending (bad for us first) for better pruning
        opp_scored = []
        for omv, ob in opp_moves:
            opp_scored.append((eval_board(ob), omv))
        opp_scored.sort(key=lambda x: x[0])  # opponent wants low

        for val, _ in opp_scored:
            if time.perf_counter() > deadline:
                break
            if val < worst:
                worst = val
            if worst <= best_val:
                break  # prune: opponent already found something as good/bad as our current best

        if worst > best_val:
            best_val = worst
            best_mv = mv

    return format_move(*best_mv)

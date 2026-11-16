
import heapq
from math import hypot

BOARD_SIZE = 11
INF = 10**9

# Neighbor offsets for hex grid described in the problem
NEIGHBORS = [(0, -1), (0, 1), (-1, 0), (-1, 1), (1, 0), (1, -1)]

def shortest_path_cost(me_set, opp_set, color):
    """
    Returns minimal number of empty cells required to connect the two sides for `color`.
    Cost model: my stones cost 0, empty cells cost 1, opponent stones are blocked.
    Uses Dijkstra multi-source from one side to the other.
    """
    dist = [[INF] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    hq = []

    # Determine starting cells and target condition based on color
    if color == 'b':
        # connect top (row=0) to bottom (row=BOARD_SIZE-1)
        starts = [(0, c) for c in range(BOARD_SIZE)]
        target_row = BOARD_SIZE - 1
        is_target = lambda r, c: r == target_row
    else:
        # color == 'w': connect left (col=0) to right (col=BOARD_SIZE-1)
        starts = [(r, 0) for r in range(BOARD_SIZE)]
        target_col = BOARD_SIZE - 1
        is_target = lambda r, c: c == target_col

    # Initialize queue with start cells that are not occupied by opponent
    for (r, c) in starts:
        if (r, c) in opp_set:
            continue  # blocked
        cost = 0 if (r, c) in me_set else 1
        dist[r][c] = cost
        heapq.heappush(hq, (cost, r, c))

    while hq:
        d, r, c = heapq.heappop(hq)
        if d != dist[r][c]:
            continue
        if is_target(r, c):
            return d
        for dr, dc in NEIGHBORS:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE):
                continue
            if (nr, nc) in opp_set:
                continue  # cannot traverse opponent stones
            add = 0 if (nr, nc) in me_set else 1
            nd = d + add
            if nd < dist[nr][nc]:
                dist[nr][nc] = nd
                heapq.heappush(hq, (nd, nr, nc))
    return INF  # no path (blocked completely)

def policy(me, opp, color):
    """
    Decide a move for Hex on 11x11.
    me: list of (r, c) my stones
    opp: list of (r, c) opponent stones
    color: 'b' or 'w' for my color
    Returns a tuple (r, c) for the chosen empty cell.
    """
    me_set = set(me)
    opp_set = set(opp)

    # All empty cells
    empties = [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE)
               if (r, c) not in me_set and (r, c) not in opp_set]

    # If no empties (should not happen), return a safe fallback
    if not empties:
        return (0, 0)

    # Opening: if board empty, play center
    if not me and not opp:
        center = (BOARD_SIZE // 2, BOARD_SIZE // 2)
        if center in empties:
            return center

    # Baseline shortest path costs
    my_current = shortest_path_cost(me_set, opp_set, color)
    opp_color = 'b' if color == 'w' else 'w'
    opp_current = shortest_path_cost(opp_set, me_set, opp_color)

    best_move = None
    best_score = -INF
    best_tiebreak = INF  # smaller is better (distance to center)

    center_coord = (BOARD_SIZE / 2.0 - 0.5, BOARD_SIZE / 2.0 - 0.5)  # center approximation

    for cell in empties:
        # Immediate win check: placing here for me
        me_after = shortest_path_cost(me_set | {cell}, opp_set, color)
        if me_after == 0:
            return cell  # immediate winning move

        # If opponent could win by playing here, consider blocking: compute opp_after when opp takes cell
        opp_after_if_they_play = shortest_path_cost(opp_set | {cell}, me_set, opp_color)
        # If opponent would win immediately by playing elsewhere (opp_current == 1), we try to block high priority
        # Evaluate candidate's effect on opponent and us
        opp_after_if_I_play = shortest_path_cost(opp_set, me_set | {cell}, opp_color)

        # Score components:
        my_improvement = (my_current - me_after)  # positive is good
        opp_degradation = (opp_after_if_I_play - opp_current)  # positive is good (we increase their required moves)

        # If opp could win by playing this cell (opp_after_if_they_play == 0), it's a critical block
        critical_block = 1.0 if opp_after_if_they_play == 0 else 0.0

        # Combined score weights: prioritize winning moves (already returned), then major weight to reducing my required moves,
        # also value blocking opponent
        score = (2.5 * my_improvement) + (1.5 * opp_degradation) + (4.0 * critical_block)

        # Tiebreaker: prefer moves closer to center; also prefer smaller resulting my_after
        dist_center = hypot(cell[0] - center_coord[0], cell[1] - center_coord[1])

        # Secondary tiebreak to prefer lower my_after (fewer moves required after move)
        # Combine into tuple for deterministic selection
        if score > best_score or (abs(score - best_score) < 1e-9 and (my_after < shortest_path_cost(me_set | ({best_move} if best_move else set()), opp_set, color) if best_move else True)) \
           or (abs(score - best_score) < 1e-9 and (abs(my_after - (shortest_path_cost(me_set | ({best_move} if best_move else set()), opp_set, color))) < 1e-9) and dist_center < best_tiebreak):
            best_score = score
            best_move = cell
            best_tiebreak = dist_center

    # Fallback: if best_move somehow None, pick first empty
    if best_move is None:
        return empties[0]
    return best_move


import random
from collections import deque

BOARD_SIZE = 11

# Neighbors for hex grid embedded in (row, col) coordinates.
# For a typical axial/offset-like representation used by this arena,
# the adjacency can be taken as the 6 directions:
# (r-1,c), (r+1,c), (r,c-1), (r,c+1), (r-1,c+1), (r+1,c-1)
# This matches the common neighbor structure for square-indexed hex grids.
DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, 1), (1, -1)]

def in_bounds(r, c):
    return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE

def get_neighbors(r, c):
    for dr, dc in DIRS:
        rr, cc = r + dr, c + dc
        if in_bounds(rr, cc):
            yield (rr, cc)

def legal_moves(me, opp):
    occ = set(me) | set(opp)
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if (r, c) not in occ:
                yield (r, c)

def color_to_sides(color):
    # b connects top(0,*) to bottom(10,*)
    # w connects left(*,0) to right(*,10)
    if color == 'b':
        return ('top', 'bottom')
    else:
        return ('left', 'right')

def has_won(me_set, color):
    # BFS over our stones to see if they connect the required sides.
    # For 'b': connect any stone with row=0 to any stone with row=10 using adjacency.
    # For 'w': connect any stone with col=0 to any stone with col=10.
    if color == 'b':
        starts = [(r, c) for (r, c) in me_set if r == 0]
        target_row = BOARD_SIZE - 1
        if not starts:
            return False
        q = deque(starts)
        seen = set(starts)
        while q:
            r, c = q.popleft()
            if r == target_row:
                return True
            for nr, nc in get_neighbors(r, c):
                if (nr, nc) in me_set and (nr, nc) not in seen:
                    seen.add((nr, nc))
                    q.append((nr, nc))
        return False
    else:
        starts = [(r, c) for (r, c) in me_set if c == 0]
        target_col = BOARD_SIZE - 1
        if not starts:
            return False
        q = deque(starts)
        seen = set(starts)
        while q:
            r, c = q.popleft()
            if c == target_col:
                return True
            for nr, nc in get_neighbors(r, c):
                if (nr, nc) in me_set and (nr, nc) not in seen:
                    seen.add((nr, nc))
                    q.append((nr, nc))
        return False

def shortest_distance_after_move(me, opp, color, move):
    """
    Compute a shortest-path distance where:
    - Our existing stones have cost 0 (already placed).
    - Empty cells cost 1 (placing there needed).
    - Opponent stones are blocked (infinite cost).
    This yields a strong heuristic for connection progress.
    """
    me_set = set(me)
    opp_set = set(opp)
    r0, c0 = move
    me_set.add((r0, c0))

    inf = 10**9

    # Identify start frontier and goal condition.
    if color == 'b':
        # start from any stone on top edge row=0
        starts = [(r, c) for (r, c) in me_set if r == 0]
        goal = lambda rc: rc[0] == BOARD_SIZE - 1
    else:
        starts = [(r, c) for (r, c) in me_set if c == 0]
        goal = lambda rc: rc[1] == BOARD_SIZE - 1

    if not starts:
        # If we don't touch the start side yet, allow starting from the moved cell if it touches.
        # Otherwise, we still can reach the other side through empties, so just start from all of our stones.
        starts = list(me_set)

    dist = {}
    dq = deque()

    # Initialize distances for stones: 0 cost
    for s in starts:
        dist[s] = 0
        dq.append(s)

    # Use 0-1 BFS: moving into our stone is cost 0; into empty is cost 1; opponent is blocked.
    while dq:
        r, c = dq.popleft()
        d = dist[(r, c)]
        if goal((r, c)):
            return d

        for nr, nc in get_neighbors(r, c):
            if (nr, nc) in opp_set:
                continue
            nd = d
            if (nr, nc) in me_set:
                nd = d  # cost 0
            else:
                nd = d + 1  # empty cell cost 1

            old = dist.get((nr, nc), inf)
            if nd < old:
                dist[(nr, nc)] = nd
                if nd == d:
                    dq.appendleft((nr, nc))
                else:
                    dq.append((nr, nc))

    return inf

def policy(me, opp, color):
    me = list(me)
    opp = list(opp)
    me_set = set(me)
    opp_set = set(opp)

    # If already won (shouldn't happen), return any legal move.
    if has_won(me_set, color):
        for mv in legal_moves(me, opp):
            return mv

    opp_color = 'w' if color == 'b' else 'b'
    moves = list(legal_moves(me, opp))
    if not moves:
        # No legal moves; shouldn't occur in standard Hex.
        return (0, 0)

    # 1) Immediate winning move
    for mv in moves:
        new_me = me_set | {mv}
        if has_won(new_me, color):
            return mv

    # 2) Immediate block (opponent could win next)
    for mv in moves:
        new_opp = opp_set | {mv}
        if has_won(new_opp, opp_color):
            return mv

    # 3) Heuristic evaluation via shortest distance
    # Lower distance is better for us. We'll maximize (opp_dist - my_dist).
    # Also incorporate center/edge proximity to reduce dithering.
    target_my = color_to_sides(color)
    center = BOARD_SIZE // 2

    def proximity_score(mv):
        r, c = mv
        # Prefer moves closer to our target sides.
        if color == 'b':
            # closer to either top or bottom edge helps
            return min(r, BOARD_SIZE - 1 - r)
        else:
            return min(c, BOARD_SIZE - 1 - c)

    best_mv = None
    best_val = -10**9

    # Small random jitter to break ties (seeded per call deterministically enough)
    rng = random.Random((len(me) * 73856093) ^ (len(opp) * 19349663) ^ (0 if color == 'b' else 1))

    # Precompute distances for all moves might be heavier (121 moves, each BFS on ~121 nodes)
    # but fits well under 1s.
    for mv in moves:
        my_d = shortest_distance_after_move(me, opp, color, mv)
        opp_d = shortest_distance_after_move(opp, me, opp_color, mv)  # opponent placing at mv

        # If our distance is inf, it's very bad; similarly for opponent.
        if my_d >= 10**8:
            continue

        # Primary objective: reduce our distance and increase opponent's distance
        val = (opp_d - my_d) * 100

        # Secondary: touch influence—encourage moves that get onto our start side soon.
        r, c = mv
        if color == 'b':
            if r == 0 or r == BOARD_SIZE - 1:
                val += 60
        else:
            if c == 0 or c == BOARD_SIZE - 1:
                val += 60

        # Secondary: prefer not being too "far from both targets"
        # (smaller min-distance to target is better, so use negative proximity_score)
        val += -proximity_score(mv) * 3

        # Tertiary: slight preference toward board center to avoid edge-only traps
        val += -((r - center) ** 2 + (c - center) ** 2) * 0.01

        # Tie-breaking jitter
        val += rng.random() * 0.01

        if val > best_val:
            best_val = val
            best_mv = mv

    if best_mv is not None:
        return best_mv

    # Fallback: any move
    return moves[0]

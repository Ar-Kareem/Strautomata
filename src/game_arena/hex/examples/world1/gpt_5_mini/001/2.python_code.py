
import heapq
from typing import List, Tuple, Set

INF = 10**6
N = 11

def neighbors(i: int, j: int):
    # Hex neighbors per problem statement:
    # (i, j-1), (i, j+1), (i-1, j), (i-1, j+1), (i+1, j-1), (i+1, j)
    for di, dj in ((0, -1), (0, 1), (-1, 0), (-1, 1), (1, -1), (1, 0)):
        ni, nj = i + di, j + dj
        if 0 <= ni < N and 0 <= nj < N:
            yield ni, nj

def shortest_side_distance(me_set: Set[Tuple[int,int]], opp_set: Set[Tuple[int,int]], color: str) -> int:
    """
    Compute minimal cost to connect player's two sides.
    Node cost = 0 for 'me' stones, 1 for empty, INF for 'opp' stones.
    Return minimal accumulated cost (number of empties needed on best path).
    """
    # node_cost function
    def node_cost(cell):
        if cell in me_set:
            return 0
        if cell in opp_set:
            return INF
        return 1

    # start and goal predicate depending on color
    if color == 'b':
        start_cells = [(0, c) for c in range(N)]
        goal_pred = lambda cell: cell[0] == N-1
    else:
        start_cells = [(r, 0) for r in range(N)]
        goal_pred = lambda cell: cell[1] == N-1

    dist = {}
    heap = []
    for cell in start_cells:
        c = node_cost(cell)
        if c >= INF:
            continue
        dist[cell] = c
        heapq.heappush(heap, (c, cell))

    while heap:
        d, cell = heapq.heappop(heap)
        if dist.get(cell, INF) != d:
            continue
        if goal_pred(cell):
            return d
        for nb in neighbors(cell[0], cell[1]):
            nd = d + node_cost(nb)
            if nd < dist.get(nb, INF):
                dist[nb] = nd
                heapq.heappush(heap, (nd, nb))
    return INF

def all_empty_cells(me_set: Set[Tuple[int,int]], opp_set: Set[Tuple[int,int]]):
    for i in range(N):
        for j in range(N):
            if (i,j) not in me_set and (i,j) not in opp_set:
                yield (i,j)

def policy(me: List[Tuple[int,int]], opp: List[Tuple[int,int]], color: str) -> Tuple[int,int]:
    me_set = set(me)
    opp_set = set(opp)

    # Quick fallback center
    center = (N//2, N//2)

    # Precompute base distances
    our_before = shortest_side_distance(me_set, opp_set, color)
    # opponent color
    opp_color = 'b' if color == 'w' else 'w'
    # For opponent distance we swap roles: their me_set is opp_set, their opp_set is me_set
    opp_before = shortest_side_distance(opp_set, me_set, opp_color)

    best_move = None
    best_score = -INF
    best_tiebreak = INF

    empties = list(all_empty_cells(me_set, opp_set))
    if not empties:
        # No legal move (shouldn't happen), but return a dummy valid cell
        return (0,0)

    # First check for immediate winning move
    for cell in empties:
        new_me = set(me_set)
        new_me.add(cell)
        our_after = shortest_side_distance(new_me, opp_set, color)
        if our_after == 0:
            return cell  # immediate win

    # Evaluate each empty candidate
    for cell in empties:
        # simulate placing our stone at cell
        new_me = set(me_set)
        new_me.add(cell)
        our_after = shortest_side_distance(new_me, opp_set, color)

        # simulate effect on opponent: the cell becomes our stone (blocked)
        new_opp_blocked = set(opp_set)
        # opponent's perspective: their me set is opp_set, their opp set is new_me
        opp_after = shortest_side_distance(opp_set, new_me, opp_color)

        # Score: combine our improvement and opponent worsening.
        # Give more weight to our distance reduction (we must connect).
        our_gain = max(0, our_before - our_after)  # positive is good
        opp_gain = max(0, opp_after - opp_before) # positive is good (we increased their distance)
        # also if opp_after is INF (blocked), that's excellent; promote heavily
        inf_bonus = 1000 if opp_after >= INF else 0

        # If our_after is INF (weird), penalize
        our_penalty = -1000 if our_after >= INF else 0

        # center proximity tie-break: prefer central moves (smaller distance to center)
        center_dist = abs(cell[0]-center[0]) + abs(cell[1]-center[1])

        score = (2 * our_gain) + (1.5 * opp_gain) + inf_bonus + our_penalty - 0.1 * center_dist

        # further prefer shorter our_after when equal score
        tiebreak = (our_after, -opp_after, center_dist)

        if score > best_score or (abs(score - best_score) < 1e-9 and tiebreak < best_tiebreak):
            best_score = score
            best_move = cell
            best_tiebreak = tiebreak

    if best_move is None:
        # pick center-most empty
        empties.sort(key=lambda c: (abs(c[0]-center[0]) + abs(c[1]-center[1])))
        return empties[0]

    return best_move

# For external tests / quick sanity
if __name__ == "__main__":
    # empty board, black to move -> choose near center
    print(policy([], [], 'b'))


import heapq
from typing import List, Tuple, Set

BOARD_SIZE = 11
INF = 10**9

def neighbors(r, c):
    # Hex grid neighbors
    dirs = [(-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0)]
    for dr, dc in dirs:
        nr, nc = r + dr, c + dc
        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
            yield nr, nc

def shortest_path_cost(color: str, me_set: Set[Tuple[int,int]], opp_set: Set[Tuple[int,int]]) -> int:
    # Dijkstra with multiple sources
    dist = [[INF]*BOARD_SIZE for _ in range(BOARD_SIZE)]
    heap = []
    if color == 'b':  # top to bottom
        for c in range(BOARD_SIZE):
            r = 0
            if (r,c) in opp_set: 
                continue
            cost = 0 if (r,c) in me_set else 1
            dist[r][c] = cost
            heapq.heappush(heap, (cost, r, c))
        target_row = BOARD_SIZE-1
        while heap:
            d, r, c = heapq.heappop(heap)
            if d != dist[r][c]:
                continue
            if r == target_row:
                return d
            for nr, nc in neighbors(r,c):
                if (nr,nc) in opp_set:
                    continue
                nd = d + (0 if (nr,nc) in me_set else 1)
                if nd < dist[nr][nc]:
                    dist[nr][nc] = nd
                    heapq.heappush(heap, (nd, nr, nc))
    else:  # white: left to right
        for r in range(BOARD_SIZE):
            c = 0
            if (r,c) in opp_set: 
                continue
            cost = 0 if (r,c) in me_set else 1
            dist[r][c] = cost
            heapq.heappush(heap, (cost, r, c))
        target_col = BOARD_SIZE-1
        while heap:
            d, r, c = heapq.heappop(heap)
            if d != dist[r][c]:
                continue
            if c == target_col:
                return d
            for nr, nc in neighbors(r,c):
                if (nr,nc) in opp_set:
                    continue
                nd = d + (0 if (nr,nc) in me_set else 1)
                if nd < dist[nr][nc]:
                    dist[nr][nc] = nd
                    heapq.heappush(heap, (nd, nr, nc))
    return INF

def policy(me: List[Tuple[int,int]], opp: List[Tuple[int,int]], color: str) -> Tuple[int,int]:
    me_set = set(me)
    opp_set = set(opp)
    empty = [(r,c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE)
             if (r,c) not in me_set and (r,c) not in opp_set]

    # If first move, take center if available
    center = (BOARD_SIZE//2, BOARD_SIZE//2)
    if center in empty and len(me_set) == 0:
        return center

    best_move = None
    best_my = INF
    best_opp = -INF
    opp_color = 'w' if color == 'b' else 'b'

    for move in empty:
        new_me = me_set | {move}
        my_cost = shortest_path_cost(color, new_me, opp_set)
        opp_cost = shortest_path_cost(opp_color, opp_set, new_me)  # my move blocks opponent

        if my_cost < best_my or (my_cost == best_my and opp_cost > best_opp):
            best_my = my_cost
            best_opp = opp_cost
            best_move = move

    # Fallback: return any legal move
    if best_move is None:
        return empty[0]
    return best_move

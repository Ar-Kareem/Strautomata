
import heapq
from typing import List, Tuple, Set

BOARD_SIZE = 11

def neighbors(r: int, c: int):
    # All 8 neighbors except (r-1,c-1) and (r+1,c+1)
    dirs = [(-1,0), (-1,1), (0,-1), (0,1), (1,0), (1,-1)]
    for dr, dc in dirs:
        nr, nc = r + dr, c + dc
        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
            yield nr, nc

def shortest(color: str, me: Set[Tuple[int,int]], opp: Set[Tuple[int,int]]):
    INF = 10**9
    dist = [[INF]*BOARD_SIZE for _ in range(BOARD_SIZE)]
    pq = []

    if color == 'b':
        # top to bottom
        for c in range(BOARD_SIZE):
            if (0,c) in opp: 
                continue
            cost = 0 if (0,c) in me else 1
            dist[0][c] = cost
            heapq.heappush(pq, (cost, 0, c))
        target_row = BOARD_SIZE - 1
        while pq:
            d,r,c = heapq.heappop(pq)
            if d != dist[r][c]: 
                continue
            if r == target_row:
                return d
            for nr, nc in neighbors(r,c):
                if (nr,nc) in opp: 
                    continue
                nd = d + (0 if (nr,nc) in me else 1)
                if nd < dist[nr][nc]:
                    dist[nr][nc] = nd
                    heapq.heappush(pq, (nd, nr, nc))
    else:
        # left to right
        for r in range(BOARD_SIZE):
            if (r,0) in opp: 
                continue
            cost = 0 if (r,0) in me else 1
            dist[r][0] = cost
            heapq.heappush(pq, (cost, r, 0))
        target_col = BOARD_SIZE - 1
        while pq:
            d,r,c = heapq.heappop(pq)
            if d != dist[r][c]: 
                continue
            if c == target_col:
                return d
            for nr, nc in neighbors(r,c):
                if (nr,nc) in opp: 
                    continue
                nd = d + (0 if (nr,nc) in me else 1)
                if nd < dist[nr][nc]:
                    dist[nr][nc] = nd
                    heapq.heappush(pq, (nd, nr, nc))
    return INF

def policy(me: List[Tuple[int,int]], opp: List[Tuple[int,int]], color: str) -> Tuple[int,int]:
    me_set = set(me)
    opp_set = set(opp)

    # If board empty, play center
    if not me and not opp:
        return (5,5)

    empties = [(r,c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE)
               if (r,c) not in me_set and (r,c) not in opp_set]

    opp_color = 'w' if color == 'b' else 'b'

    best_move = None
    best_score = 10**9
    best_opp = -1

    for move in empties:
        me2 = me_set | {move}
        opp2 = opp_set

        mycost = shortest(color, me2, opp2)
        if mycost == 0:
            return move  # immediate win

        oppcost = shortest(opp_color, opp2, me2)

        score = mycost - 0.5 * oppcost
        if score < best_score or (score == best_score and oppcost > best_opp):
            best_score = score
            best_opp = oppcost
            best_move = move

    # Fallback (shouldn't happen)
    if best_move is None:
        return empties[0]
    return best_move


import heapq
from typing import List, Tuple, Set

N = 11

def _neighbors(r: int, c: int):
    """Yield valid hex neighbors for cell (r, c)."""
    # Hex adjacency: same row, row-1 (right shifted), row+1 (left shifted)
    for dr, dc in ((0, -1), (0, 1), (-1, 0), (-1, 1), (1, -1), (1, 0)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < N and 0 <= nc < N:
            yield (nr, nc)

def _dijkstra(own: Set[Tuple[int, int]], enemy: Set[Tuple[int, int]], color: str) -> int:
    """
    Returns the minimum number of stones `color` needs to place to connect their sides.
    Cost 0 for own stones, 1 for empty, inf for enemy stones.
    """
    dist = [[float('inf')] * N for _ in range(N)]
    pq = []
    
    if color == 'b':
        # Black connects top (row 0) to bottom (row N-1)
        for c in range(N):
            if (0, c) not in enemy:
                d = 0 if (0, c) in own else 1
                if d < dist[0][c]:
                    dist[0][c] = d
                    heapq.heappush(pq, (d, 0, c))
        while pq:
            d, r, c = heapq.heappop(pq)
            if d != dist[r][c]:
                continue
            if r == N - 1:  # Reached bottom
                return d
            for nr, nc in _neighbors(r, c):
                if (nr, nc) in enemy:
                    continue
                nd = d + (0 if (nr, nc) in own else 1)
                if nd < dist[nr][nc]:
                    dist[nr][nc] = nd
                    heapq.heappush(pq, (nd, nr, nc))
        return min(dist[N-1])
    else:
        # White connects left (col 0) to right (col N-1)
        for r in range(N):
            if (r, 0) not in enemy:
                d = 0 if (r, 0) in own else 1
                if d < dist[r][0]:
                    dist[r][0] = d
                    heapq.heappush(pq, (d, r, 0))
        while pq:
            d, r, c = heapq.heappop(pq)
            if d != dist[r][c]:
                continue
            if c == N - 1:  # Reached right side
                return d
            for nr, nc in _neighbors(r, c):
                if (nr, nc) in enemy:
                    continue
                nd = d + (0 if (nr, nc) in own else 1)
                if nd < dist[nr][nc]:
                    dist[nr][nc] = nd
                    heapq.heappush(pq, (nd, nr, nc))
        return min(row[N-1] for row in dist)

def _get_path_cells(own: Set[Tuple[int, int]], enemy: Set[Tuple[int, int]], color: str) -> Set[Tuple[int, int]]:
    """Return the set of cells on the current shortest path."""
    dist = [[float('inf')] * N for _ in range(N)]
    prev = [[None] * N for _ in range(N)]
    pq = []
    target = None
    
    if color == 'b':
        for c in range(N):
            if (0, c) not in enemy:
                d = 0 if (0, c) in own else 1
                if d < dist[0][c]:
                    dist[0][c] = d
                    heapq.heappush(pq, (d, 0, c))
        while pq:
            d, r, c = heapq.heappop(pq)
            if d != dist[r][c]:
                continue
            if r == N - 1:
                target = (r, c)
                break
            for nr, nc in _neighbors(r, c):
                if (nr, nc) in enemy:
                    continue
                nd = d + (0 if (nr, nc) in own else 1)
                if nd < dist[nr][nc]:
                    dist[nr][nc] = nd
                    prev[nr][nc] = (r, c)
                    heapq.heappush(pq, (nd, nr, nc))
    else:
        for r in range(N):
            if (r, 0) not in enemy:
                d = 0 if (r, 0) in own else 1
                if d < dist[r][0]:
                    dist[r][0] = d
                    heapq.heappush(pq, (d, r, 0))
        while pq:
            d, r, c = heapq.heappop(pq)
            if d != dist[r][c]:
                continue
            if c == N - 1:
                target = (r, c)
                break
            for nr, nc in _neighbors(r, c):
                if (nr, nc) in enemy:
                    continue
                nd = d + (0 if (nr, nc) in own else 1)
                if nd < dist[nr][nc]:
                    dist[nr][nc] = nd
                    prev[nr][nc] = (r, c)
                    heapq.heappush(pq, (nd, nr, nc))
    
    cells = set()
    if target is None:
        return cells
    cur = target
    while cur is not None:
        cells.add(cur)
        cur = prev[cur[0]][cur[1]]
    return cells

def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Tuple[int, int]:
    me_set = set(me)
    opp_set = set(opp)
    opp_color = 'w' if color == 'b' else 'b'
    
    empty = [(r, c) for r in range(N) for c in range(N) 
             if (r, c) not in me_set and (r, c) not in opp_set]
    
    # 1. Immediate win
    for cell in empty:
        if _dijkstra(me_set | {cell}, opp_set, color) == 0:
            return cell
    
    # 2. Block opponent immediate win
    for cell in empty:
        if _dijkstra(opp_set | {cell}, me_set, opp_color) == 0:
            return cell
    
    # 3. Evaluate candidates
    my_cost = _dijkstra(me_set, opp_set, color)
    opp_cost = _dijkstra(opp_set, me_set, opp_color)
    
    # Generate candidates: neighbors of stones + cells on shortest paths
    candidates = set()
    for r, c in list(me_set) + list(opp_set):
        for nr, nc in _neighbors(r, c):
            if (nr, nc) not in me_set and (nr, nc) not in opp_set:
                candidates.add((nr, nc))
    
    if my_cost < 100:
        candidates.update(_get_path_cells(me_set, opp_set, color))
    if opp_cost < 100:
        candidates.update(_get_path_cells(opp_set, me_set, opp_color))
    
    if not candidates:
        candidates = set(empty)
    
    best_move = empty[0] if empty else (0, 0)
    best_score = float('-inf')
    best_dist = float('inf')
    
    for r, c in candidates:
        new_me = me_set | {(r, c)}
        new_my_cost = _dijkstra(new_me, opp_set, color)
        new_opp_cost = _dijkstra(opp_set, new_me, opp_color)
        
        # Score: higher is better. We want low new_my_cost and high new_opp_cost
        score = new_opp_cost - new_my_cost
        
        # Tie-breaker: prefer center (5,5)
        dist_center = abs(r - 5) + abs(c - 5)
        
        if score > best_score or (score == best_score and dist_center < best_dist):
            best_score = score
            best_move = (r, c)
            best_dist = dist_center
            
    return best_move

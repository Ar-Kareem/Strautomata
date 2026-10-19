
def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    """
    Hex policy using Dijkstra-based path distance evaluation.
    """
    import random
    from collections import deque
    import heapq
    
    BOARD_SIZE = 11
    
    def get_neighbors(row, col):
        """Get the 6 hex neighbors of a cell."""
        neighbors = []
        deltas = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]
        for dr, dc in deltas:
            r, c = row + dr, col + dc
            if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
                neighbors.append((r, c))
        return neighbors
    
    def is_connected(stones_set, color_to_check):
        """Check if stones form a winning connection."""
        stones = set(stones_set)
        
        if color_to_check == 'b':
            queue = deque()
            visited = set()
            for c in range(BOARD_SIZE):
                if (0, c) in stones:
                    queue.append((0, c))
                    visited.add((0, c))
            
            while queue:
                r, c = queue.popleft()
                if r == BOARD_SIZE - 1:
                    return True
                for nr, nc in get_neighbors(r, c):
                    if (nr, nc) in stones and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        queue.append((nr, nc))
            return False
        else:
            queue = deque()
            visited = set()
            for r in range(BOARD_SIZE):
                if (r, 0) in stones:
                    queue.append((r, 0))
                    visited.add((r, 0))
            
            while queue:
                r, c = queue.popleft()
                if c == BOARD_SIZE - 1:
                    return True
                for nr, nc in get_neighbors(r, c):
                    if (nr, nc) in stones and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        queue.append((nr, nc))
            return False
    
    def dijkstra_distance(stones_set, opp_stones_set, color_to_check):
        """
        Find minimum number of additional stones needed to connect.
        """
        stones = set(stones_set)
        opp_stones = set(opp_stones_set)
        dist = {}
        pq = []
        
        if color_to_check == 'b':
            for c in range(BOARD_SIZE):
                if (0, c) in stones:
                    dist[(0, c)] = 0
                    heapq.heappush(pq, (0, 0, c))
                elif (0, c) not in opp_stones:
                    dist[(0, c)] = 1
                    heapq.heappush(pq, (1, 0, c))
            
            while pq:
                d, r, c = heapq.heappop(pq)
                if d > dist.get((r, c), float('inf')):
                    continue
                if r == BOARD_SIZE - 1:
                    return d
                for nr, nc in get_neighbors(r, c):
                    if (nr, nc) in opp_stones:
                        continue
                    new_dist = d if (nr, nc) in stones else d + 1
                    if new_dist < dist.get((nr, nc), float('inf')):
                        dist[(nr, nc)] = new_dist
                        heapq.heappush(pq, (new_dist, nr, nc))
            return float('inf')
        else:
            for r in range(BOARD_SIZE):
                if (r, 0) in stones:
                    dist[(r, 0)] = 0
                    heapq.heappush(pq, (0, r, 0))
                elif (r, 0) not in opp_stones:
                    dist[(r, 0)] = 1
                    heapq.heappush(pq, (1, r, 0))
            
            while pq:
                d, r, c = heapq.heappop(pq)
                if d > dist.get((r, c), float('inf')):
                    continue
                if c == BOARD_SIZE - 1:
                    return d
                for nr, nc in get_neighbors(r, c):
                    if (nr, nc) in opp_stones:
                        continue
                    new_dist = d if (nr, nc) in stones else d + 1
                    if new_dist < dist.get((nr, nc), float('inf')):
                        dist[(nr, nc)] = new_dist
                        heapq.heappush(pq, (new_dist, nr, nc))
            return float('inf')
    
    me_set = set(me)
    opp_set = set(opp)
    
    empty_cells = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if (r, c) not in me_set and (r, c) not in opp_set:
                empty_cells.append((r, c))
    
    if not empty_cells:
        return (0, 0)
    
    if not me and not opp:
        return (5, 5)
    
    # Check for immediate win
    for cell in empty_cells:
        if is_connected(me_set | {cell}, color):
            return cell
    
    # Check for immediate block
    opp_color = 'w' if color == 'b' else 'b'
    for cell in empty_cells:
        if is_connected(opp_set | {cell}, opp_color):
            return cell
    
    # Generate candidates
    candidates = set()
    for stone in list(me_set) + list(opp_set):
        for neighbor in get_neighbors(stone[0], stone[1]):
            if neighbor not in me_set and neighbor not in opp_set:
                candidates.add(neighbor)
    
    if color == 'b':
        for c in range(BOARD_SIZE):
            if (0, c) not in me_set and (0, c) not in opp_set:
                candidates.add((0, c))
            if (BOARD_SIZE - 1, c) not in me_set and (BOARD_SIZE - 1, c) not in opp_set:
                candidates.add((BOARD_SIZE - 1, c))
    else:
        for r in range(BOARD_SIZE):
            if (r, 0) not in me_set and (r, 0) not in opp_set:
                candidates.add((r, 0))
            if (r, BOARD_SIZE - 1) not in me_set and (r, BOARD_SIZE - 1) not in opp_set:
                candidates.add((r, BOARD_SIZE - 1))
    
    if not candidates:
        candidates = set(empty_cells)
    
    candidates = list(candidates)
    
    if len(candidates) > 50:
        candidates.sort(key=lambda c: abs(c[0] - 5) + abs(c[1] - 5))
        candidates = candidates[:50]
    
    # Evaluate candidates
    best_move = None
    best_score = float('-inf')
    
    for cell in candidates:
        me_with_cell = me_set | {cell}
        my_dist = dijkstra_distance(me_with_cell, opp_set, color)
        opp_dist = dijkstra_distance(opp_set, me_with_cell, opp_color)
        
        # Score: prefer moves that minimize our distance
        # Also add some weight to maximizing opponent's distance
        score = -my_dist * 3.0 + opp_dist * 0.5 + random.random() * 0.001
        
        if score > best_score:
            best_score = score
            best_move = cell
    
    return best_move if best_move else empty_cells[0]

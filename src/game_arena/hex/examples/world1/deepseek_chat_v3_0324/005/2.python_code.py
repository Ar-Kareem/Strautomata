
import heapq
from collections import defaultdict

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    # Determine board size (fixed at 11x11 for this problem)
    size = 11
    
    # All possible moves (empty cells)
    all_moves = {(i, j) for i in range(size) for j in range(size)}
    occupied = set(me) | set(opp)
    possible_moves = list(all_moves - occupied)
    
    # Immediate win check
    for move in possible_moves:
        if has_won(me + [move], color, size):
            return move
    
    # Immediate block check
    for move in possible_moves:
        if has_won(opp + [move], 'w' if color == 'b' else 'b', size):
            return move
    
    # Get best move based on distance and bridges
    return get_best_move(me, opp, color, size, possible_moves)

def has_won(stones, color, size):
    """Check if given stones form a winning connection."""
    if color == 'b':  # Black connects top to bottom
        top = {stone for stone in stones if stone[0] == 0}
        bottom = {stone for stone in stones if stone[0] == size - 1}
        if not top or not bottom:
            return False
        return is_connected(top, bottom, stones)
    else:  # White connects left to right
        left = {stone for stone in stones if stone[1] == 0}
        right = {stone for stone in stones if stone[1] == size - 1}
        if not left or not right:
            return False
        return is_connected(left, right, stones)

def is_connected(group1, group2, stones):
    """Check if two groups are connected through the stone set."""
    visited = set()
    queue = list(group1)
    
    while queue:
        current = queue.pop()
        if current in group2:
            return True
        if current in visited:
            continue
        visited.add(current)
        for neighbor in get_neighbors(current, stones):
            if neighbor not in visited:
                queue.append(neighbor)
    return False

def get_neighbors(cell, stones):
    """Get all neighboring cells that contain stones."""
    i, j = cell
    neighbors = [
        (i-1, j), (i-1, j+1),
        (i, j-1), (i, j+1),
        (i+1, j-1), (i+1, j)
    ]
    return [n for n in neighbors if n in stones]

def get_best_move(me, opp, color, size, possible_moves):
    """Calculate the best move based on distance and bridge patterns."""
    # Calculate distance maps for both players
    my_dist = distance_map(me, color, size)
    opp_dist = distance_map(opp, 'w' if color == 'b' else 'b', size)
    
    # Find bridge moves
    bridge_moves = find_bridge_moves(me, opp, size)
    
    # Score each possible move
    best_score = -float('inf')
    best_move = possible_moves[0]  # default
    
    for move in possible_moves:
        # Calculate score based on distance improvement and blocking
        new_me = me + [move]
        new_my_dist = distance_map(new_me, color, size)
        my_improvement = min(my_dist.values()) - min(new_my_dist.values())
        
        # Opponent's potential improvement if we don't block
        new_opp = opp + [move]
        new_opp_dist = distance_map(new_opp, 'w' if color == 'b' else 'b', size)
        opp_improvement = min(opp_dist.values()) - min(new_opp_dist.values())
        
        # Bridge bonus
        bridge_bonus = 2 if move in bridge_moves else 0
        
        # Edge preference
        edge_bonus = 0.5 if is_edge(move, color, size) else 0
        
        score = my_improvement + opp_improvement + bridge_bonus + edge_bonus
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move

def distance_map(stones, color, size):
    """Calculate distance from each stone to the target sides using Dijkstra's algorithm."""
    if color == 'b':  # Black connects top to bottom
        sources = {stone for stone in stones if stone[0] == 0}
        targets = {stone for stone in stones if stone[0] == size - 1}
    else:  # White connects left to right
        sources = {stone for stone in stones if stone[1] == 0}
        targets = {stone for stone in stones if stone[1] == size - 1}
    
    dist = defaultdict(lambda: float('inf'))
    heap = []
    
    for source in sources:
        dist[source] = 0
        heapq.heappush(heap, (0, source))
    
    while heap:
        current_dist, current = heapq.heappop(heap)
        if current in targets:
            continue
        if current_dist > dist[current]:
            continue
            
        for neighbor in get_neighbors(current, stones):
            new_dist = current_dist + 1
            if new_dist < dist[neighbor]:
                dist[neighbor] = new_dist
                heapq.heappush(heap, (new_dist, neighbor))
    
    return dist

def find_bridge_moves(me, opp, size):
    """Find moves that create bridge patterns."""
    occupied = set(me) | set(opp)
    bridges = set()
    
    for stone1 in me:
        for stone2 in me:
            if stone1 == stone2:
                continue
            # Check for potential bridge pattern
            if (abs(stone1[0] - stone2[0]) == 1 and 
                abs(stone1[1] - stone2[1]) == 1):
                bridge1 = (stone1[0], stone2[1])
                bridge2 = (stone2[0], stone1[1])
                if bridge1 not in occupied and 0 <= bridge1[0] < size and 0 <= bridge1[1] < size:
                    bridges.add(bridge1)
                if bridge2 not in occupied and 0 <= bridge2[0] < size and 0 <= bridge2[1] < size:
                    bridges.add(bridge2)
    
    return bridges

def is_edge(move, color, size):
    """Check if move is on a relevant edge."""
    if color == 'b':
        return move[0] == 0 or move[0] == size - 1
    else:
        return move[1] == 0 or move[1] == size - 1

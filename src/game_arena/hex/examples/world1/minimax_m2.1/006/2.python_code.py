
import heapq
from collections import deque

def get_neighbors(pos, board_size=11):
    """Get the 6 neighboring positions on a hex grid."""
    i, j = pos
    neighbors = [
        (i, j-1), (i, j+1),      # same row
        (i-1, j), (i-1, j+1),    # top row
        (i+1, j-1), (i+1, j)     # bottom row
    ]
    return [(r, c) for r, c in neighbors if 0 <= r < board_size and 0 <= c < board_size]

def build_graph(stones, board_size=11):
    """Build adjacency graph for given stones."""
    graph = {stone: [] for stone in stones}
    for stone in stones:
        for neighbor in get_neighbors(stone, board_size):
            if neighbor in stones:
                graph[stone].append(neighbor)
    return graph

def get_goal_sides(color, board_size=11):
    """Get the two sides a player needs to connect."""
    if color == 'b':  # Black: top (row 0) to bottom (row 10)
        return [(0, c) for c in range(board_size)], [(board_size-1, c) for c in range(board_size)]
    else:  # White: left (col 0) to right (col 10)
        return [(r, 0) for r in range(board_size)], [(r, board_size-1) for r in range(board_size)]

def bfs_shortest_path(start_set, end_set, stones, board_size=11):
    """Find shortest path from start_set to end_set through stones."""
    graph = build_graph(stones, board_size)
    visited = set()
    queue = deque([(start, [start]) for start in start_set if start in stones])
    
    while queue:
        current, path = queue.popleft()
        if current in visited:
            continue
        visited.add(current)
        
        if current in end_set:
            return path
        
        for neighbor in graph.get(current, []):
            if neighbor not in visited:
                queue.append((neighbor, path + [neighbor]))
    
    return None

def calculate_path_length(path):
    """Calculate the effective path length."""
    if path is None:
        return float('inf')
    return len(path) - 1

def count_shared_neighbors(pos, stones, board_size=11):
    """Count how many neighbors are occupied by stones."""
    count = 0
    for neighbor in get_neighbors(pos, board_size):
        if neighbor in stones:
            count += 1
    return count

def evaluate_move(move, me, opp, color, board_size=11):
    """Score a potential move."""
    score = 0
    
    # Distance to goal sides
    goal_start, goal_end = get_goal_sides(color, board_size)
    start_dist = min(abs(move[0] - s[0]) + abs(move[1] - s[1]) for s in goal_start)
    end_dist = min(abs(move[0] - e[0]) + abs(move[1] - e[1]) for e in goal_end)
    score -= (start_dist + end_dist) * 2  # Prefer closer to goals
    
    # Connectivity to existing stones
    my_neighbors = count_shared_neighbors(move, me, board_size)
    opp_neighbors = count_shared_neighbors(move, opp, board_size)
    score += my_neighbors * 3  # Strong preference for connecting to own stones
    score -= opp_neighbors * 2  # Avoid placing near opponent stones
    
    # Central position bonus for flexibility
    center_dist = abs(move[0] - board_size//2) + abs(move[1] - board_size//2)
    score += (board_size - center_dist) * 0.5
    
    # Check if move blocks opponent
    if color == 'b':
        opp_goal_start, opp_goal_end = [(r, 0) for r in range(board_size)], [(r, board_size-1) for r in range(board_size)]
    else:
        opp_goal_start, opp_goal_end = [(0, c) for c in range(board_size)], [(board_size-1, c) for c in range(board_size)]
    
    # Blocking potential
    potential_path = bfs_shortest_path(opp_goal_start, opp_goal_end, opp, board_size)
    if potential_path and move in potential_path:
        score += 100  # Block opponent winning path
    
    return score

def detect_immediate_threat(opp, color, board_size=11):
    """Detect if opponent has a nearly completed path."""
    goal_start, goal_end = get_goal_sides(color, board_size)
    path = bfs_shortest_path(goal_start, goal_end, opp, board_size)
    
    if path:
        # Find critical empty cells on the path
        critical_cells = []
        for i, cell in enumerate(path):
            neighbors = get_neighbors(cell, board_size)
            empty_neighbors = [n for n in neighbors if n not in opp]
            
            # Check if this cell is adjacent to the next cell in path
            if i < len(path) - 1:
                next_cell = path[i + 1]
                if next_cell not in opp:
                    continue
            
            # Count how many path-connected neighbors this cell has
            path_connections = 0
            for n in neighbors:
                if n in opp and n in path:
                    path_connections += 1
            
            # If cell has path connections, remaining empty neighbors are threats
            if path_connections > 0:
                for empty_n in empty_neighbors:
                    critical_cells.append(empty_n)
        
        return critical_cells
    return []

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    """Determine the next move."""
    board_size = 11
    all_stones = set(me + opp)
    empty_cells = [(r, c) for r in range(board_size) for c in range(board_size) 
                   if (r, c) not in all_stones]
    
    if not empty_cells:
        raise ValueError("No empty cells available")
    
    # Check for immediate winning move
    goal_start, goal_end = get_goal_sides(color, board_size)
    
    # First, check if we can win immediately
    for move in empty_cells:
        test_stones = me + [move]
        path = bfs_shortest_path(goal_start, goal_end, test_stones, board_size)
        if path is not None:
            return move
    
    # Second, check if opponent can win immediately - must block
    for move in empty_cells:
        test_opp = opp + [move]
        path = bfs_shortest_path(goal_start, goal_end, test_opp, board_size)
        if path is not None:
            return move
    
    # Detect opponent threats and prioritize blocking
    threats = detect_immediate_threat(opp, color, board_size)
    blocking_moves = [m for m in threats if m in empty_cells]
    
    if blocking_moves:
        # Return the best blocking move
        best_block = max(blocking_moves, 
                        lambda m: evaluate_move(m, me, opp, color, board_size))
        return best_block
    
    # Score all possible moves
    scored_moves = [(evaluate_move(move, me, opp, color, board_size), move) 
                   for move in empty_cells]
    
    # Add some randomness to avoid deterministic play
    scored_moves.sort(reverse=True)
    
    # Select from top moves with some randomness
    top_n = min(5, len(scored_moves))
    best_score, best_move = scored_moves[0]
    
    # Return top scored move
    return best_move

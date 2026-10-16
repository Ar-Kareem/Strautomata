
import numpy as np

def get_neighbors(r, col, N):
    # Hexagonal neighbors in the 2D array representation
    # (r-1, c), (r+1, c), (r, c-1), (r, c+1), (r-1, c-1), (r+1, c+1)
    potential = [(r-1, col), (r+1, col), (r, col-1), (r, col+1), (r-1, col-1), (r+1, col+1)]
    return [(nr, nc) for nr, nc in potential if 0 <= nr < N and 0 <= nc < N]

def get_group(start_node, stones_set, N):
    group = set()
    stack = [start_node]
    while stack:
        node = stack.pop()
        if node not in group:
            group.add(node)
            for neighbor in get_neighbors(node[0], node[1], N):
                if neighbor in stones_set and neighbor not in group:
                    stack.append(neighbor)
    return group

def is_corner(r, c, N):
    # Havannah 15x15 corners (simplified for hexagonal grid mapped to square)
    corners = [(0, 0), (0, 7), (7, 0), (14, 7), (7, 14), (14, 14)]
    return (r, c) in corners

def get_edge(r, c, N):
    # Returns edge index 0-5, or -1 if not an edge/is a corner
    if is_corner(r, c, N): return -1
    if r == 0: return 0
    if c == 0: return 1
    if r == 14 and c >= 7: return 2
    if c == 14 and r >= 7: return 3
    if r - c == 7: return 4
    if c - r == 7: return 5
    return -1

def check_win(stones_list, N):
    stones_set = set(stones_list)
    visited = set()
    for stone in stones_list:
        if stone not in visited:
            group = get_group(stone, stones_set, N)
            visited.update(group)
            
            # Bridge: 2 corners
            corners_hit = sum(1 for p in group if is_corner(p[0], p[1], N))
            if corners_hit >= 2: return True
            
            # Fork: 3 edges
            edges_hit = set()
            for p in group:
                e = get_edge(p[0], p[1], N)
                if e != -1: edges_hit.add(e)
            if len(edges_hit) >= 3: return True
            
            # Ring: Checked implicitly by connectivity logic usually involves detecting cycles
            # In a fast heuristic, we prioritize connectivity and skip complex ring detection
    return False

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    N = 15
    me_set = set(me)
    opp_set = set(opp)
    
    # Get all possible moves
    possible_moves = []
    for r in range(N):
        for c in range(N):
            if valid_mask[r][c] and (r, c) not in me_set and (r, c) not in opp_set:
                possible_moves.append((r, c))
    
    if not possible_moves:
        return (0, 0)
    
    # 1. Check for immediate win
    for move in possible_moves:
        if check_win(me + [move], N):
            return move
            
    # 2. Check for immediate block
    for move in possible_moves:
        if check_win(opp + [move], N):
            return move

    # 3. Heuristic Scoring
    best_score = -1
    best_move = possible_moves[0]
    
    center = 7
    for move in possible_moves:
        score = 0
        neighbors = get_neighbors(move[0], move[1], N)
        
        for neighbor in neighbors:
            if neighbor in me_set:
                score += 10 # Value of connecting own stones
            if neighbor in opp_set:
                score += 8  # Value of blocking opponent
        
        # Prefer center control early on
        dist_to_center = abs(move[0] - center) + abs(move[1] - center)
        score += (20 - dist_to_center) * 0.1
        
        # Prefer corners and edges slightly for Fork/Bridge setup
        if is_corner(move[0], move[1], N):
            score += 5
        elif get_edge(move[0], move[1], N) != -1:
            score += 2

        if score > best_score:
            best_score = score
            best_move = move
            
    return best_move

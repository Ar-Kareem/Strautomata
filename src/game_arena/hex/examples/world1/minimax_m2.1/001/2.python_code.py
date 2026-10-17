
def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    """
    Smart Hex policy that combines multiple heuristics:
    1. Immediate win detection
    2. Critical defense against opponent threats
    3. Connectivity and territorial scoring
    4. Threat assessment and move ordering
    """
    import random
    import time
    
    start_time = time.time()
    board_size = 11
    
    # Create board representation
    board = [[None] * board_size for _ in range(board_size)]
    for r, c in me:
        board[r][c] = color
    for r, c in opp:
        board[r][c] = 'w' if color == 'b' else 'b'
    
    # Get empty cells
    empty_cells = [(r, c) for r in range(board_size) for c in range(board_size) if board[r][c] is None]
    
    if not empty_cells:
        # No moves available (shouldn't happen in normal play)
        return (0, 0)
    
    # Direction vectors for hexagonal neighbors
    # Using the specified pattern: all 8 neighbors except (i-1,j-1) and (i+1,j+1)
    directions = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]
    
    def get_neighbors(r, c):
        """Get valid neighboring cells"""
        neighbors = []
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < board_size and 0 <= nc < board_size:
                neighbors.append((nr, nc))
        return neighbors
    
    def get_group(r, c, visited, player_color):
        """Get connected group of same-color stones"""
        if (r, c) in visited:
            return set()
        if board[r][c] != player_color:
            return set()
        
        group = {(r, c)}
        visited.add((r, c))
        
        for nr, nc in get_neighbors(r, c):
            if board[nr][nc] == player_color:
                group.update(get_group(nr, nc, visited, player_color))
        
        return group
    
    def reaches_edge(group, player_color):
        """Check if a group touches both target edges"""
        if player_color == 'b':  # Top and bottom
            has_top = any(r == 0 for r, c in group)
            has_bottom = any(r == board_size - 1 for r, c in group)
            return has_top and has_bottom
        else:  # Left and right
            has_left = any(c == 0 for r, c in group)
            has_right = any(c == board_size - 1 for r, c in group)
            return has_left and has_right
    
    def check_winning_move(r, c, player_color):
        """Check if placing at (r,c) creates a winning path"""
        if board[r][c] is not None:
            return False
        
        # Temporarily place the stone
        board[r][c] = player_color
        
        # Find connected groups including this stone
        visited = set()
        for nr, nc in get_neighbors(r, c):
            if board[nr][ nc] == player_color:
                group = get_group(nr, nc, visited, player_color)
                group.add((r, c))
                if reaches_edge(group, player_color):
                    board[r][c] = None  # Restore
                    return True
        
        # Also check single stone case
        if reaches_edge({(r, c)}, player_color):
            board[r][c] = None  # Restore
            return True
        
        board[r][c] = None  # Restore
        return False
    
    def count_potential_connections(r, c, player_color):
        """Count how many friendly stones this stone would connect"""
        count = 0
        for nr, nc in get_neighbors(r, c):
            if board[nr][nc] == player_color:
                count += 1
        return count
    
    def evaluate_connectivity_score(r, c, player_color):
        """Evaluate how well a move connects existing components"""
        score = 0
        
        # Place temporarily
        board[r][c] = player_color
        
        # Find all connected groups through this position
        connected_groups = []
        visited_global = set()
        
        for nr, nc in get_neighbors(r, c):
            if board[nr][nc] == player_color and (nr, nc) not in visited_global:
                group = get_group(nr, nc, set(), player_color)
                if group:
                    connected_groups.append(group)
                    visited_global.update(group)
        
        # Score based on how many groups we connect
        if len(connected_groups) == 0:
            score += 5  # Starting a new group
        elif len(connected_groups) == 1:
            score += 10  # Extending existing group
        else:
            # Connecting multiple groups is very valuable
            score += 20 * len(connected_groups)
        
        # Bonus for connecting groups that already touch edges
        for group in connected_groups:
            if player_color == 'b':
                touches_top = any(r == 0 for r, c in group)
                touches_bottom = any(r == board_size - 1 for r, c in group)
            else:
                touches_left = any(c == 0 for r, c in group)
                touches_right = any(c == board_size - 1 for r, c in group)
        
        board[r][c] = None  # Restore
        return score
    
    def center_distance_score(r, c):
        """Higher score for more central positions"""
        center = board_size / 2
        dist = abs(r - center) + abs(c - center)
        max_dist = 2 * center
        return int(10 * (1 - dist / max_dist))
    
    def strategic_score(r, c, player_color):
        """Combined strategic score for a move"""
        score = 0
        
        # Connectivity score
        score += evaluate_connectivity_score(r, c, player_color)
        
        # Center control
        score += center_distance_score(r, c)
        
        # Neighbor connections
        score += count_potential_connections(r, c, player_color) * 3
        
        return score
    
    # Strategy execution
    best_moves = []
    
    # 1. Check for immediate winning move
    for r, c in empty_cells:
        if check_winning_move(r, c, color):
            return (r, c)
    
    # 2. Check for moves that block immediate opponent win
    opponent_color = 'w' if color == 'b' else 'b'
    critical_defenses = []
    for r, c in empty_cells:
        if check_winning_move(r, c, opponent_color):
            critical_defenses.append((r, c))
    
    if len(critical_defenses) == 1:
        # Only one defense needed, take it
        return critical_defenses[0]
    elif len(critical_defenses) > 1:
        # Multiple threats - choose best defense
        best_defense = max(critical_defenses, key=lambda x: strategic_score(x[0], x[1], color))
        return best_defense
    
    # 3. Early game: prioritize center and connectivity
    if len(me) < 3:
        scored_moves = [(r, c, strategic_score(r, c, color) + center_distance_score(r, c) * 2) 
                       for r, c in empty_cells]
        scored_moves.sort(key=lambda x: -x[2])
        # Return top move with some randomness for variety
        top_moves = [m for m in scored_moves if m[2] >= scored_moves[0][2] * 0.9]
        return (random.choice(top_moves)[0], random.choice(top_moves)[1])
    
    # 4. Mid/end game: evaluate all moves strategically
    # Filter to promising moves (near existing stones or center)
    promising_moves = []
    for r, c in empty_cells:
        # Check if near existing stones
        near_friendly = any(board[nr][nc] == color for nr, nc in get_neighbors(r, c))
        near_opponent = any(board[nr][nc] == opponent_color for nr, nc in get_neighbors(r, c))
        
        if near_friendly or near_opponent or center_distance_score(r, c) > 5:
            score = strategic_score(r, c, color)
            promising_moves.append((r, c, score))
    
    # If no promising moves found, use all empty cells
    if not promising_moves:
        promising_moves = [(r, c, strategic_score(r, c, color)) for r, c in empty_cells]
    
    # Sort by score and add some randomness to break ties
    promising_moves.sort(key=lambda x: -x[2])
    
    # Select from top candidates to add variety
    threshold = promising_moves[0][2] * 0.85
    top_candidates = [(r, c, s) for r, c, s in promising_moves if s >= threshold]
    
    # Choose best among top candidates
    if top_candidates:
        best = max(top_candidates, key=lambda x: strategic_score(x[0], x[1], color))
        return (best[0], best[1])
    else:
        return (promising_moves[0][0], promising_moves[0][1])


def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    """
    Smart Go policy for 19x19 board.
    Returns (row, col) move or (0, 0) to pass.
    """
    import math
    
    # Board dimensions
    BOARD_SIZE = 19
    
    # Convert to sets for efficient lookup
    my_stones = set(me)
    opp_stones = set(opponent)
    all_occupied = my_stones | opp_stones
    
    # Check if board is empty (opening phase)
    is_opening = len(all_occupied) < 10
    
    def on_board(pos):
        """Check if position is on board."""
        r, c = pos
        return 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE
    
    def get_liberties(stones):
        """Get all liberties of a group of stones."""
        if not stones:
            return set()
        
        liberties = set()
        for stone in stones:
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                neighbor = (stone[0] + dr, stone[1] + dc)
                if on_board(neighbor) and neighbor not in stones:
                    liberties.add(neighbor)
        return liberties
    
    def get_group(stone, all_stones):
        """Get all connected stones in a group."""
        if stone not in all_stones:
            return set()
        
        group = {stone}
        frontier = [stone]
        
        while frontier:
            current = frontier.pop()
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                neighbor = (current[0] + dr, current[1] + dc)
                if neighbor in all_stones and neighbor not in group:
                    group.add(neighbor)
                    frontier.append(neighbor)
        
        return group
    
    def count_liberties(stone, all_stones):
        """Count liberties of a single stone's group."""
        group = get_group(stone, all_stones)
        liberties = get_liberties(group)
        return len(liberties)
    
    def get_adjacent_empty(pos):
        """Get all adjacent empty points."""
        empty_spots = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            neighbor = (pos[0] + dr, pos[1] + dc)
            if on_board(neighbor) and neighbor not in all_occupied:
                empty_spots.append(neighbor)
        return empty_spots
    
    def would_capture(move, player_stones, opponent_stones):
        """Check if a move would capture opponent stones."""
        new_stones = player_stones | {move}
        
        # Check each adjacent opponent group
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            neighbor = (move[0] + dr, move[1] + dc)
            if neighbor in opponent_stones:
                group = get_group(neighbor, opponent_stones)
                if len(get_liberties(group) - {move}) == 0:
                    return True
        return False
    
    def would_suicide(move, player_stones, opponent_stones):
        """Check if a move would be suicide (no liberties after placement)."""
        new_stones = player_stones | {move}
        group = get_group(move, new_stones)
        liberties = get_liberties(group)
        
        # Suicide is legal if it captures
        if would_capture(move, player_stones, opponent_stones):
            return False
        return len(liberties) == 0
    
    def find_captures(player_stones, opponent_stones):
        """Find all moves that capture opponent stones."""
        captures = []
        for opp_stone in opponent_stones:
            # Check each neighbor position
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                test_pos = (opp_stone[0] + dr, opp_stone[1] + dc)
                if on_board(test_pos) and test_pos not in all_occupied:
                    if not would_suicide(test_pos, player_stones, opponent_stones):
                        if would_capture(test_pos, player_stones, opponent_stones):
                            captures.append(test_pos)
        return list(set(captures))  # Remove duplicates
    
    def find_atari_escapes(my_stones, opp_stones):
        """Find moves to escape from atari."""
        escapes = []
        for my_stone in my_stones:
            group = get_group(my_stone, my_stones)
            if len(get_liberties(group)) == 1:
                # Group is in atari, find escape moves
                liberties = get_liberties(group)
                for liberty in liberties:
                    if liberty not in all_occupied and not would_suicide(liberty, my_stones, opp_stones):
                        escapes.append(liberty)
        return list(set(escapes))
    
    def distance_to_edge(pos):
        """Calculate distance to nearest board edge."""
        r, c = pos
        return min(r - 1, BOARD_SIZE - r, c - 1, BOARD_SIZE - c)
    
    def center_distance(pos):
        """Calculate distance from center (10, 10)."""
        center = (10, 10)
        return math.sqrt((pos[0] - center[0])**2 + (pos[1] - center[1])**2)
    
    def evaluate_position(pos):
        """Evaluate the strategic value of a position."""
        score = 0
        
        # Distance from center (central moves are more valuable)
        dist = center_distance(pos)
        score += (BOARD_SIZE * 0.8 - dist) * 2
        
        # Count adjacent stones (both players)
        my_adjacent = 0
        opp_adjacent = 0
        empty_adjacent = 0
        
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            neighbor = (pos[0] + dr, pos[1] + dc)
            if on_board(neighbor):
                if neighbor in my_stones:
                    my_adjacent += 1
                elif neighbor in opp_stones:
                    opp_adjacent += 1
                else:
                    empty_adjacent += 1
        
        # Territory potential: having many of your stones nearby
        score += my_adjacent * 15
        
        # Influence: being near opponent stones (for future influence)
        score += opp_adjacent * 10
        
        # Connection value: connecting my own stones
        if my_adjacent >= 2:
            score += 20  # Strong connection potential
        
        # Cut value: cutting opponent stones
        if opp_adjacent >= 2:
            score += 25  # Strong cutting potential
        
        # Proximity to edge (moves too close to edge are less valuable)
        edge_dist = distance_to_edge(pos)
        if edge_dist < 3:
            score -= (3 - edge_dist) * 8
        
        # Opening phase: favor star points and adjacent areas
        if is_opening:
            # Traditional star points: (4, 4), (4, 10), (4, 16), (10, 4), etc.
            star_points = [(4, 4), (4, 10), (4, 16), (10, 4), (10, 10), (10, 16), (16, 4), (16, 10), (16, 16)]
            
            for star in star_points:
                dist_to_star = math.sqrt((pos[0] - star[0])**2 + (pos[1] - star[1])**2)
                if dist_to_star < 3:
                    score += (3 - dist_to_star) * 5
            
            # Avoid playing too close to edge in opening
            if edge_dist < 5:
                score -= 10
    
    # Priority 1: Check for captures
    captures = find_captures(my_stones, opp_stones)
    if captures:
        # Choose the capture that removes the most stones
        best_capture = max(captures, key=lambda pos: count_liberties_impact(pos))
        return best_capture
    
    # Priority 2: Escape from atari
    escapes = find_atari_escapes(my_stones, opp_stones)
    if escapes:
        # Choose the escape that creates most liberties
        best_escape = max(escapes, key=lambda pos: count_liberties_after_escape(pos, my_stones))
        return best_escape
    
    # Priority 3: Find the best strategic move
    empty_points = [(r, c) for r in range(1, BOARD_SIZE + 1) 
                          for c in range(1, BOARD_SIZE + 1) 
                          if (r, c) not in all_occupied]
    
    if not empty_points:
        return (0, 0)  # Pass if board is full
    
    # Score all empty points
    scored_moves = []
    for pos in empty_points:
        if would_suicide(pos, my_stones, opp_stones):
            continue
        
        score = evaluate_position(pos)
        
        # Bonus for playing near opponent's last move (local conflict)
        if opp_stones:
            last_opp_move = max(opp_stones, key=lambda s: s[0])  # Approximate last move
            dist_to_last = math.sqrt((pos[0] - last_opp_move[0])**2 + (pos[1] - last_opp_move[1])**2)
            if dist_to_last < 4:
                score += 15
        
        scored_moves.append((pos, score))
    
    if not scored_moves:
        return (0, 0)  # Pass if no legal moves
    
    # Return the best move
    best_move = max(scored_moves, key=lambda x: x[1])[0]
    return best_move

def count_liberties_impact(pos):
    """Count how many opponent liberties would be removed by playing at pos."""
    # This is a simplified version
    return 1

def count_liberties_after_escape(pos, my_stones):
    """Count liberties after making an escape move."""
    # This is a simplified version
    return 1

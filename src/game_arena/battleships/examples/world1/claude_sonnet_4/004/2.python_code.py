
def policy(board: list[list[int]]) -> tuple[int, int]:
    import random
    
    # Get all unknown cells
    unknown_cells = []
    hits = []
    
    for r in range(10):
        for c in range(10):
            if board[r][c] == 0:
                unknown_cells.append((r, c))
            elif board[r][c] == 1:
                hits.append((r, c))
    
    # Helper function to get valid adjacent cells
    def get_adjacent(r, c):
        adjacent = []
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 10 and 0 <= nc < 10:
                adjacent.append((nr, nc))
        return adjacent
    
    # Helper function to check if a cell is unknown
    def is_unknown(r, c):
        return 0 <= r < 10 and 0 <= c < 10 and board[r][c] == 0
    
    # Target mode: Look for hits that need follow-up
    target_cells = []
    
    for hit_r, hit_c in hits:
        # Check if this hit has adjacent unknown cells
        for adj_r, adj_c in get_adjacent(hit_r, hit_c):
            if is_unknown(adj_r, adj_c):
                target_cells.append((adj_r, adj_c))
    
    # If we have target cells, prioritize them
    if target_cells:
        # Look for linear patterns to prioritize direction
        best_targets = []
        
        for target_r, target_c in target_cells:
            priority = 0
            
            # Check if this target continues a line of hits
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                line_length = 0
                r, c = target_r + dr, target_c + dc
                
                # Count consecutive hits in this direction
                while 0 <= r < 10 and 0 <= c < 10 and board[r][c] == 1:
                    line_length += 1
                    r += dr
                    c += dc
                
                # Check opposite direction from target
                r, c = target_r - dr, target_c - dc
                while 0 <= r < 10 and 0 <= c < 10 and board[r][c] == 1:
                    line_length += 1
                    r -= dr
                    c -= dc
                
                priority = max(priority, line_length)
            
            best_targets.append((priority, target_r, target_c))
        
        # Sort by priority (highest first)
        best_targets.sort(reverse=True)
        return (best_targets[0][1], best_targets[0][2])
    
    # Hunt mode: Systematic search
    if unknown_cells:
        # Calculate how much of the board we've explored
        total_cells = 100
        explored_cells = sum(1 for r in range(10) for c in range(10) if board[r][c] != 0)
        exploration_ratio = explored_cells / total_cells
        
        # Early game: use checkerboard pattern for efficiency
        if exploration_ratio < 0.5:
            checkerboard_cells = []
            for r, c in unknown_cells:
                if (r + c) % 2 == 0:
                    checkerboard_cells.append((r, c))
            
            if checkerboard_cells:
                return random.choice(checkerboard_cells)
        
        # Mid to late game: focus on cells that can fit remaining ships
        # Prioritize cells that are part of longer potential ship placements
        cell_scores = []
        
        for r, c in unknown_cells:
            score = 0
            
            # Check horizontal potential
            h_length = 1
            # Check left
            left = c - 1
            while left >= 0 and board[r][left] != -1:
                h_length += 1
                left -= 1
            # Check right  
            right = c + 1
            while right < 10 and board[r][right] != -1:
                h_length += 1
                right += 1
            
            # Check vertical potential
            v_length = 1
            # Check up
            up = r - 1
            while up >= 0 and board[up][c] != -1:
                v_length += 1
                up -= 1
            # Check down
            down = r + 1
            while down < 10 and board[down][c] != -1:
                v_length += 1
                down += 1
            
            # Score based on potential to fit ships (lengths 2,3,3,4,5)
            max_potential = max(h_length, v_length)
            if max_potential >= 5:
                score += 5
            elif max_potential >= 4:
                score += 4
            elif max_potential >= 3:
                score += 3
            elif max_potential >= 2:
                score += 2
            
            cell_scores.append((score, r, c))
        
        # Sort by score (highest first) and return best cell
        if cell_scores:
            cell_scores.sort(reverse=True)
            max_score = cell_scores[0][0]
            best_cells = [(r, c) for score, r, c in cell_scores if score == max_score]
            return random.choice(best_cells)
    
    # Fallback: return any unknown cell
    return random.choice(unknown_cells)

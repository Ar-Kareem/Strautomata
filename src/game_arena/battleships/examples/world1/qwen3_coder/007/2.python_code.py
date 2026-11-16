
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert to list of lists if needed for easier handling
    # But board is already in the right format
    
    # Look for hits that need to be followed up
    hits = []
    for r in range(10):
        for c in range(10):
            if board[r][c] == 1:  # Hit
                hits.append((r, c))
    
    # If we have hits, look for adjacent unshot cells
    if hits:
        # Look for adjacent unshot cells to any hit
        potential_targets = []
        for r, c in hits:
            # Check up, down, left, right
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                    potential_targets.append((nr, nc))
        
        if potential_targets:
            # If we have multiple potential targets, 
            # let's try to be smart about which direction to continue in
            # Look for hits that form a line pattern
            for r, c in hits:
                # Check horizontal line
                left_hit = (r, c-1) in hits
                right_hit = (r, c+1) in hits
                
                # If we have horizontal adjacency, prioritize horizontal continuation
                if left_hit or right_hit:
                    horizontal_targets = []
                    if c > 0 and board[r][c-1] == 0:
                        horizontal_targets.append((r, c-1))
                    if c < 9 and board[r][c+1] == 0:
                        horizontal_targets.append((r, c+1))
                    if horizontal_targets:
                        return random.choice(horizontal_targets)
                
                # Check vertical line
                up_hit = (r-1, c) in hits
                down_hit = (r+1, c) in hits
                
                # If we have vertical adjacency, prioritize vertical continuation
                if up_hit or down_hit:
                    vertical_targets = []
                    if r > 0 and board[r-1][c] == 0:
                        vertical_targets.append((r-1, c))
                    if r < 9 and board[r+1][c] == 0:
                        vertical_targets.append((r+1, c))
                    if vertical_targets:
                        return random.choice(vertical_targets)
            
            # If no clear line pattern, return any potential target
            return random.choice(potential_targets)
    
    # No current hits to follow up - use search pattern
    # Parity search - target cells where (r+c) is even (or odd), 
    # which ensures we cover the board efficiently for ships of length >= 2
    unshot_parity_cells = []
    unshot_cells = []
    
    for r in range(10):
        for c in range(10):
            if board[r][c] == 0:  # Unshot
                unshot_cells.append((r, c))
                if (r + c) % 2 == 0:  # Even parity
                    unshot_parity_cells.append((r, c))
    
    # If we have parity cells, shoot those first
    if unshot_parity_cells:
        return random.choice(unshot_parity_cells)
    
    # Fallback to any unshot cell
    if unshot_cells:
        return random.choice(unshot_cells)
    
    # This should never happen if the game is ongoing
    # but just in case, choose a random cell
    return (random.randint(0, 9), random.randint(0, 9))

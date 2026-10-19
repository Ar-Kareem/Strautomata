
def policy(state: list[list[object]], role: str) -> str:
    # Parse the board state
    board = [[None for _ in range(6)] for _ in range(6)]
    for prop in state:
        if prop[0] == "cell":
            row, col, color = int(prop[1]) - 1, int(prop[2]) - 1, prop[3]
            board[row][col] = color
    
    # Determine opponent color
    opponent = "blue" if role == "red" else "red"
    
    # Find all legal moves and their flip counts
    legal_moves = []
    
    for row in range(6):
        for col in range(6):
            if board[row][col] is not None:
                continue
            
            # Check if this move is legal and count flips
            total_flips = count_flips(board, row, col, role, opponent)
            
            if total_flips > 0:
                legal_moves.append((total_flips, row, col))
    
    if not legal_moves:
        # No legal moves found - shouldn't happen in a valid game state
        # Return a default move
        return "move(1,1)"
    
    # Sort by flip count (descending), then by corner/edge preference
    def move_priority(move):
        flips, row, col = move
        # Prioritize by flips (descending), then corners, then edges
        is_corner = (row in [0, 5]) and (col in [0, 5])
        is_edge = (row in [0, 5]) or (col in [0, 5])
        
        priority = (-flips, -is_corner, -is_edge)
        return priority
    
    legal_moves.sort(key=move_priority)
    best_move = legal_moves[0]
    
    return f"move({best_move[2] + 1},{best_move[1] + 1})"

def count_flips(board, row, col, role, opponent):
    """Count total flips for placing role's piece at (row, col)"""
    directions = [
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)
    ]
    
    total_flips = 0
    
    for dr, dc in directions:
        flips = count_flips_in_direction(board, row, col, dr, dc, role, opponent)
        total_flips += flips
    
    return total_flips

def count_flips_in_direction(board, row, col, dr, dc, role, opponent):
    """Count flips in a specific direction"""
    flips = 0
    r, c = row + dr, col + dc
    
    # Count consecutive opponent pieces
    while 0 <= r < 6 and 0 <= c < 6 and board[r][c] == opponent:
        flips += 1
        r += dr
        c += dc
    
    # Check if we found a role piece to complete the line
    if 0 <= r < 6 and 0 <= c < 6 and board[r][c] == role:
        return flips
    
    return 0

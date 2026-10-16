
def policy(state: list[list[object]], role: str) -> str:
    # Build board state
    board = {}
    played_boards = set()
    
    for prop in state:
        if prop[0] == "cell":
            board[(prop[1], int(prop[2]), int(prop[3]))] = prop[4]
        elif prop[0] == "played":
            played_boards.add(prop[1])
    
    # Check if we should tick (both boards have played)
    if len(played_boards) == 2:
        return "tick"
    
    # Determine if role is red (rows 3-4, moving up) or black (rows 1-2, moving down)
    is_red = role == "red"
    
    # Find all pieces of current role
    my_pieces = []
    for (board_id, row, col), color in board.items():
        if color == role:
            my_pieces.append((board_id, row, col))
    
    # Generate and evaluate moves
    best_moves = []
    
    for board_id, row, col in my_pieces:
        # Try jumps (captures) first - they're worth more points
        jump_moves = []
        
        for dr, dc in [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]:
            mid_r, mid_c = row + dr // 2, col + dc // 2
            dest_r, dest_c = row + dr, col + dc
            
            # Check bounds
            if 1 <= mid_r <= 4 and 1 <= mid_c <= 4 and 1 <= dest_r <= 4 and 1 <= dest_c <= 4:
                mid_piece = board.get((board_id, mid_r, mid_c), "blank")
                dest_piece = board.get((board_id, dest_r, dest_c), "blank")
                
                # Valid jump: same color in middle, empty destination
                if mid_piece == role and dest_piece == "blank":
                    move_str = f"jump({board_id},{col},{row},{mid_c},{mid_r},{dest_c},{dest_r})"
                    jump_moves.append(move_str)
        
        if jump_moves:
            best_moves.extend(jump_moves)
    
    # If we have jump moves, return the first one
    if best_moves:
        return best_moves[0]
    
    # Otherwise, try regular moves (forward movement)
    regular_moves = []
    
    for board_id, row, col in my_pieces:
        # Red moves up (decreasing row), Black moves down (increasing row)
        if is_red:
            forward_row = row - 1
        else:
            forward_row = row + 1
        
        # Try moving forward in adjacent columns or same column
        for new_col in [col - 1, col, col + 1]:
            if 1 <= forward_row <= 4 and 1 <= new_col <= 4:
                target_piece = board.get((board_id, forward_row, new_col), "blank")
                if target_piece == "blank":
                    move_str = f"move({board_id},{col},{row},{new_col},{forward_row})"
                    regular_moves.append(move_str)
    
    if regular_moves:
        return regular_moves[0]
    
    # Fallback: tick if no moves available
    return "tick"

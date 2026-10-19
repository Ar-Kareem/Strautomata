
def policy(state: list[list[object]], role: str) -> str:
    # Parse the state to build a board representation
    board = {}  # (col, row) -> color
    
    for fact in state:
        if fact[0] == "cell":
            col = fact[1]  # 'a' to 'h'
            row = int(fact[2])  # 1 to 8
            color = fact[3]  # 'white' or 'black'
            board[(col, row)] = color
    
    # Helper functions for coordinate conversion
    def col_to_num(col):
        return ord(col) - ord('a')
    
    def num_to_col(num):
        return chr(ord('a') + num)
    
    # Find all pieces of our color
    our_pieces = []
    for (col, row), color in board.items():
        if color == role:
            our_pieces.append((col, row))
    
    # Generate legal moves
    valid_moves = []
    
    for col, row in our_pieces:
        col_num = col_to_num(col)
        
        if role == "white":
            # White moves upward (increasing row)
            knight_moves = [
                (1, 2), (1, -2), (2, 1), (2, -1),
                (-1, 2), (-1, -2), (-2, 1), (-2, -1)
            ]
            # Filter for forward moves only (increasing row)
            forward_moves = [(dc, dr) for dc, dr in knight_moves if dr > 0]
        else:  # black
            # Black moves downward (decreasing row)
            knight_moves = [
                (1, 2), (1, -2), (2, 1), (2, -1),
                (-1, 2), (-1, -2), (-2, 1), (-2, -1)
            ]
            # Filter for forward moves only (decreasing row)
            forward_moves = [(dc, dr) for dc, dr in knight_moves if dr < 0]
        
        for dc, dr in forward_moves:
            new_col_num = col_num + dc
            new_row = row + dr
            
            # Check bounds
            if 0 <= new_col_num < 8 and 1 <= new_row <= 8:
                new_col = num_to_col(new_col_num)
                
                # Check if destination is empty or occupied by opponent
                if (new_col, new_row) not in board or board[(new_col, new_row)] != role:
                    # Calculate progress toward goal
                    if role == "white":
                        progress = new_row
                    else:
                        progress = 8 - new_row
                    
                    valid_moves.append((progress, col, row, new_col, new_row))
    
    # Sort by progress (descending) to prioritize advancing furthest
    valid_moves.sort(reverse=True)
    
    if valid_moves:
        # Pick the best move
        _, from_col, from_row, to_col, to_row = valid_moves[0]
        return f"move({from_col},{from_row},{to_col},{to_row})"
    
    # Fallback: shouldn't reach here if state is valid
    return "move(a,1,b,3)"

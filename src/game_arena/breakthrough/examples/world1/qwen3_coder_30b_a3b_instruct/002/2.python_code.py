
def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    import numpy as np
    
    # Convert to sets for easier lookups
    me_set = set(me)
    opp_set = set(opp)
    
    # Helper function to check if a position is on the board
    def is_valid(row, col):
        return 0 <= row < 8 and 0 <= col < 8
    
    # Helper to get opponent home row
    def get_opponent_home_row():
        return 0 if color == 'b' else 7
    
    # Helper to get player home row
    def get_player_home_row():
        return 7 if color == 'b' else 0
    
    # Helper function to get possible moves for a piece
    def get_piece_moves(row, col):
        moves = []
        # Determine forward direction based on color
        forward_row = row - 1 if color == 'b' else row + 1
        
        # Check straight forward move
        if is_valid(forward_row, col) and (forward_row, col) not in me_set and (forward_row, col) not in opp_set:
            moves.append((forward_row, col))
        
        # Check diagonal moves (capture)
        for dc in [-1, 1]:
            new_row, new_col = forward_row, col + dc
            if is_valid(new_row, new_col) and (new_row, new_col) in opp_set:
                moves.append((new_row, new_col))
        
        return moves
    
    # Check if any move wins the game
    opponent_home_row = get_opponent_home_row()
    player_home_row = get_player_home_row()
    
    # Check for winning moves
    for (row, col) in me:
        # Check if this piece is already in the winning position
        if (color == 'b' and row == 0) or (color == 'w' and row == 7):
            continue
            
        # Check straight forward moves
        forward_row = row - 1 if color == 'b' else row + 1
        
        # Check if we can reach opponent home row
        if (color == 'b' and forward_row == 0) or (color == 'w' and forward_row == 7):
            if is_valid(forward_row, col) and (forward_row, col) not in me_set and (forward_row, col) not in opp_set:
                return ((row, col), (forward_row, col))
        
        # Check diagonal captures that win
        for dc in [-1, 1]:
            new_row, new_col = forward_row, col + dc
            if is_valid(new_row, new_col) and (new_row, new_col) in opp_set:
                return ((row, col), (new_row, new_col))
    
    # Look for captures that win by eliminating all opponent pieces
    # First try to identify any move that captures an opponent piece
    capture_moves = []
    forward_moves = []
    all_moves = []
    
    for (row, col) in me:
        moves = get_piece_moves(row, col)
        for (new_row, new_col) in moves:
            if (new_row, new_col) in opp_set:
                capture_moves.append(((row, col), (new_row, new_col)))
            else:
                forward_moves.append(((row, col), (new_row, new_col)))
            all_moves.append(((row, col), (new_row, new_col)))
    
    # Prefer captures if available
    if capture_moves:
        # Prefer captures that maximize opponent piece removal
        # For simplicity and speed, take the first capture
        return capture_moves[0]
    
    # Check for any moves that would put a piece in the opponent's home row
    winning_moves = []
    for (row, col) in me:
        forward_row = row - 1 if color == 'b' else row + 1
        # Check straight forward moves that can win
        if (color == 'b' and forward_row == 0) or (color == 'w' and forward_row == 7):
            if is_valid(forward_row, col) and (forward_row, col) not in me_set and (forward_row, col) not in opp_set:
                winning_moves.append(((row, col), (forward_row, col)))
    
    if winning_moves:
        return winning_moves[0]
    
    # If we want to avoid going for easy wins, prioritize moves that are less likely to expose us
    if forward_moves:
        # Prefer moves that don't put pieces near edge
        best_move = forward_moves[0]
        best_score = 0
        
        for move in forward_moves:
            (from_row, from_col), (to_row, to_col) = move
            # Score based on how central the piece is
            center_distance = max(abs(to_row - 3.5), abs(to_col - 3.5))
            # Prefer moves that stay in center area
            score = 8 - center_distance  # Higher score = more central
            
            # Prefer moves that are not too close to opponent home row for safety
            if color == 'b':
                row_bonus = 7 - to_row  # Higher row = closer to safety
            else:
                row_bonus = to_row  # Higher row = closer to safety
                
            score += row_bonus
            
            if score > best_score:
                best_score = score
                best_move = move
                
        return best_move
    
    # If all else fails, just move forward if possible
    if all_moves:
        # Prefer moving forward and avoid edge positions
        best_move = all_moves[0]
        best_score = 0
        
        for move in all_moves:
            (from_row, from_col), (to_row, to_col) = move
            
            # Prefer central positions
            center_distance = max(abs(to_row - 3.5), abs(to_col - 3.5))
            score = 8 - center_distance
            
            # Prefer staying further from opponent home region
            if color == 'b':
                score += (7 - to_row) * 0.5
            else:
                score += to_row * 0.5
            
            if score > best_score:
                best_score = score
                best_move = move
                
        return best_move
    
    # Final fallback: if no legal moves, that means no pieces can move, but that shouldn't happen
    # In a real implementation we would have already ensured there's at least one valid move
    
    # Return the first valid move if we got here (shouldn't happen in valid game state)
    for (row, col) in me:
        moves = get_piece_moves(row, col)
        if moves:
            return ((row, col), moves[0])
    
    # Just in case, return a basic move
    return (me[0], (me[0][0], me[0][1] + 1))

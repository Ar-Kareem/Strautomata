
import random

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    # Convert to sets for faster lookup
    my_pieces = set(me)
    opp_pieces = set(opp)
    
    # Determine direction based on color
    direction = 1 if color == 'b' else -1  # Black moves down (increasing row), white moves up (decreasing row)
    
    # Generate all legal moves
    moves = []
    
    for row, col in my_pieces:
        # Forward move
        new_row = row + direction
        if 0 <= new_row <= 7 and (new_row, col) not in my_pieces and (new_row, col) not in opp_pieces:
            moves.append(((row, col), (new_row, col)))
            
        # Diagonal captures/moves
        for dcol in [-1, 1]:
            new_col = col + dcol
            if 0 <= new_row <= 7 and 0 <= new_col <= 7:
                # Capture move
                if (new_row, new_col) in opp_pieces:
                    moves.append(((row, col), (new_row, new_col)))
                # Diagonal forward move
                elif (new_row, new_col) not in my_pieces and (new_row, new_col) not in opp_pieces:
                    moves.append(((row, col), (new_row, new_col)))
    
    # If no moves available (shouldn't happen in normal gameplay), return a default
    if not moves:
        return ((0, 0), (0, 0))
    
    # Check for winning moves (reaching opponent's home row)
    winning_moves = []
    opponent_home_row = 0 if color == 'b' else 7
    
    for move in moves:
        (_, _), (to_row, _) = move
        if to_row == opponent_home_row:
            winning_moves.append(move)
    
    # If we have winning moves, pick one randomly
    if winning_moves:
        return random.choice(winning_moves)
    
    # Evaluate moves based on tactical value
    best_moves = []
    best_value = float('-inf')
    
    for move in moves:
        (from_row, from_col), (to_row, to_col) = move
        value = 0
        
        # Value captures
        if (to_row, to_col) in opp_pieces:
            value += 10
            
        # Value advancement
        advancement = to_row - from_row if color == 'b' else from_row - to_row
        value += advancement * 2
        
        # Prefer center control
        if 2 <= to_col <= 5:
            value += 1
            
        # Avoid moving pieces already advanced
        if (color == 'b' and from_row >= 5) or (color == 'w' and from_row <= 2):
            value -= 1
            
        if value > best_value:
            best_value = value
            best_moves = [move]
        elif value == best_value:
            best_moves.append(move)
    
    # If multiple best moves, choose one that doesn't put piece at risk
    safe_moves = []
    for move in best_moves:
        (from_row, from_col), (to_row, to_col) = move
        # Check if the moved piece would be immediately capturable
        safe = True
        
        # After moving, check if any opponent piece can capture it next turn
        # This is a simplified safety check
        for opp_row, opp_col in opp_pieces:
            # Check if opponent can move to where we're going
            opp_direction = -1 if color == 'b' else 1
            # Directly forward (not possible to capture)
            # Diagonally forward
            for dcol in [-1, 1]:
                if (opp_row + opp_direction, opp_col + dcol) == (to_row, to_col):
                    # This opponent piece could potentially capture our moved piece
                    # We'll still consider the move but prefer safer ones if value is similar
                    pass
        
        safe_moves.append((move, value))
    
    # Return the best move (or a random one among equally good moves)
    return random.choice(best_moves)


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    # Determine movement direction based on color
    if color == 'b':
        direction = -1  # Black moves down
        home_row = 7  # Black's home row
    else:
        direction = 1  # White moves up
        home_row = 0  # White's home row
    
    # Generate all possible moves
    possible_moves = []
    
    for piece in me:
        row, col = piece
        
        # Move forward
        forward_move = (row + direction, col)
        if 0 <= forward_move[0] < 8:
            possible_moves.append((piece, forward_move))
        
        # Capture diagonally
        for d_col in [-1, 1]:  # Both diagonal directions
            diagonal_move = (row + direction, col + d_col)
            if (0 <= diagonal_move[0] < 8 and 0 <= diagonal_move[1] < 8 and
                diagonal_move in opp):
                possible_moves.append((piece, diagonal_move))
    
    # Check for winning move
    for move in possible_moves:
        if move[1][0] == home_row:
            return move  # Immediate win
    
    # If no winning move, prioritize capturing
    capture_moves = [move for move in possible_moves if move[1] in opp]
    if capture_moves:
        return capture_moves[0]  # Capture the first available piece
    
    # If no captures, return the first available move
    if possible_moves:
        return possible_moves[0]  # Just move forward if nothing else

    raise ValueError("No valid moves available, which should not happen.")


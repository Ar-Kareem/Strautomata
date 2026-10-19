
def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    # Identify the direction of movement based on color
    direction = -1 if color == 'b' else 1
    home_row = 0 if color == 'b' else 7

    # Possible movements for a piece
    moves = []
    
    for (from_row, from_col) in me:
        # Check for a straight move forward
        straight_move = (from_row + direction, from_col)
        if straight_move[0] == home_row:
            return (from_row, from_col), (home_row, from_col)  # Winning move
        
        if straight_move[0] in range(8) and straight_move[1] in range(8):
            if straight_move not in me and straight_move not in opp:
                moves.append((from_row, from_col, straight_move))
        
        # Check for diagonal captures
        for delta_col in [-1, 1]:
            diagonal_move = (from_row + direction, from_col + delta_col)
            if diagonal_move[0] in range(8) and diagonal_move[1] in range(8):
                if diagonal_move in opp:
                    moves.append((from_row, from_col, diagonal_move))  # Capture move

    # Select the best move:
    # Give priority to captures first, then to advancing moves
    if moves:
        # Prioritize capturing
        capture_moves = [move for move in moves if move[2] in opp]
        if capture_moves:
            # Perform the first capturing move found
            best_move = capture_moves[0]
            return (best_move[0], best_move[1]), best_move[2]
        
        # Otherwise, perform a normal advancing move
        advancing_moves = [move for move in moves if move[2] not in opp]
        if advancing_moves:
            best_move = advancing_moves[0]
            return (best_move[0], best_move[1]), best_move[2]
    
    # If no moves are possible (should never happen), return a no-op
    return None

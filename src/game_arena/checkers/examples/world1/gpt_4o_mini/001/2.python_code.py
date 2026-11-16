
def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    def get_moves(piece):
        moves = []
        row, col = piece
        directions = []

        # Determine moves based on the color since they move in different directions
        if color == 'b':
            directions = [(1, -1), (1, 1)]  # Moving down the board
        else:
            directions = [(-1, -1), (-1, 1)]  # Moving up the board
        
        # Check normal moves
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < 8 and 0 <= new_col < 8 and (new_row + new_col) % 2 == 1:
                if (new_row, new_col) not in my_men and (new_row, new_col) not in my_kings and (new_row, new_col) not in opp_men and (new_row, new_col) not in opp_kings:
                    moves.append((new_row, new_col))

        # Check captures
        for dr, dc in directions:
            capture_row, capture_col = row + dr, col + dc
            landing_row, landing_col = row + 2*dr, col + 2*dc
            if (0 <= capture_row < 8 and 0 <= capture_col < 8 and (capture_row + capture_col) % 2 == 1 and
                    (landing_row, landing_col) not in my_men and (landing_row, landing_col) not in my_kings and
                    (landing_row, landing_col) not in opp_men and (landing_row, landing_col) not in opp_kings):
                if (capture_row, capture_col) in opp_men or (capture_row, capture_col) in opp_kings:
                    moves.append((landing_row, landing_col))

        return moves
    
    # Generate all possible moves for both pieces and kings
    all_moves = []
    for piece in my_men + my_kings:
        all_moves.extend(get_moves(piece))

    # If any capture move is available, prioritize it
    capture_moves = [move for move in all_moves if move not in my_men and move not in my_kings]
    if capture_moves:
        return capture_moves[0][0:2], capture_moves[0][2:4]  # Return any capture move

    # Otherwise, return any normal move
    if all_moves:
        return all_moves[0][0:2], all_moves[0][2:4]  # Return any available move

    return my_men[0], my_men[0]  # Fallback: Stay on the first piece if no moves available

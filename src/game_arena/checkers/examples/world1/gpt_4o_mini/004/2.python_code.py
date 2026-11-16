
def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    def get_moves(piece, is_king):
        moves = []
        row, col = piece
        directions = []
        
        if is_king:
            # Kings can move in all four diagonal directions
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        else:
            # Regular pieces move differently based on color
            if color == 'b':
                directions = [(-1, -1), (-1, 1)]  # Move up
            else:
                directions = [(1, -1), (1, 1)]     # Move down
        
        for dr, dc in directions:
            # Regular move
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                if (new_row, new_col) not in my_men and (new_row, new_col) not in my_kings and (new_row, new_col) not in opp_men and (new_row, new_col) not in opp_kings:
                    moves.append(((row, col), (new_row, new_col)))

            # Capture move
            capture_row, capture_col = row + 2 * dr, col + 2 * dc
            opponent_row, opponent_col = row + dr, col + dc
            if 0 <= capture_row < 8 and 0 <= capture_col < 8:
                if (opponent_row, opponent_col) in opp_men or (opponent_row, opponent_col) in opp_kings:
                    if (capture_row, capture_col) not in my_men and (capture_row, capture_col) not in my_kings:
                        moves.append(((row, col), (capture_row, capture_col)))
        
        return moves

    # Collect all possible moves
    possible_moves = []
    
    for piece in my_men:
        possible_moves.extend(get_moves(piece, False))

    for piece in my_kings:
        possible_moves.extend(get_moves(piece, True))
    
    # If there are capturing moves, prioritize them
    capturing_moves = [move for move in possible_moves if abs(move[0][0] - move[1][0]) == 2]

    if capturing_moves:
        # Return the first capturing move available
        return capturing_moves[0]
    
    # If no capturing moves, return the first possible move
    if possible_moves:
        return possible_moves[0]
    
    # Return an illegal move if there's no other case (though, according to rules, we should never reach here)
    return ((-1, -1), (-1, -1))  # Fallback to an illegal move (shouldn't happen)

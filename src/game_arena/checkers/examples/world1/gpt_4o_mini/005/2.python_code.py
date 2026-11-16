
def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    def get_moves(piece, is_king):
        moves = []
        
        if is_king:
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        else:
            directions = [(-1, -1), (-1, 1)] if color == 'w' else [(1, -1), (1, 1)]
        
        for dx, dy in directions:
            for jump in range(1, 2):  # Check single step move or jump
                new_row = piece[0] + dx * jump
                new_col = piece[1] + dy * jump
                
                if 0 <= new_row < 8 and 0 <= new_col < 8:
                    moves.append((new_row, new_col))
                    
                    # Check for capturing move
                    if jump == 1:
                        # Check if there is an opponent piece to capture
                        capture_row = piece[0] + dx
                        capture_col = piece[1] + dy
                        if (capture_row, capture_col) in opp_men or (capture_row, capture_col) in opp_kings:
                            jump_row = new_row + dx
                            jump_col = new_col + dy
                            if 0 <= jump_row < 8 and 0 <= jump_col < 8 and (jump_row, jump_col) not in my_men and (jump_row, jump_col) not in my_kings:
                                moves.append((jump_row, jump_col))
        
        return moves

    def get_captures():
        captures = []
        for piece in my_men + my_kings:
            is_king = piece in my_kings
            moves = get_moves(piece, is_king)
            for move in moves:
                if (move[0], move[1]) in my_men or (move[0], move[1]) in my_kings:
                    continue  # Exclude moves that land on my own pieces
                if move not in my_men and move not in my_kings:
                    captures.append((piece, move))
        return captures

    # Get all possible captures
    captures = get_captures()

    # If there are captures available, prioritize them
    if captures:
        piece, move = max(captures, key=lambda cap: cap[1])  # generic heuristic, can be improved
        return piece, move

    # TODO: You can implement normal moves if no captures are found, for simplicity move first found piece
    for piece in my_men + my_kings:
        is_king = piece in my_kings
        moves = get_moves(piece, is_king)
        if moves:
            return piece, moves[0]

    # Fallback case (should not reach here as there should always be a move)
    return ((0, 0), (0, 0))

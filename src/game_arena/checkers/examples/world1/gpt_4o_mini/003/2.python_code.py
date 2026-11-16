
def policy(my_men, my_kings, opp_men, opp_kings, color):
    def get_valid_moves(men, kings):
        moves = []
        for piece in men + kings:
            row, col = piece
            # Regular piece moves
            if piece in my_men:
                if color == 'b':  # Moving down
                    if row > 0:
                        if col > 0 and (row - 1, col - 1) not in opp_men and (row - 1, col - 1) not in my_men and ((row - 1, col - 1) not in my_kings):
                            moves.append((piece, (row - 1, col - 1)))
                        if col < 7 and (row - 1, col + 1) not in opp_men and (row - 1, col + 1) not in my_men and ((row - 1, col + 1) not in my_kings):
                            moves.append((piece, (row - 1, col + 1)))
                else:  # Moving up
                    if row < 7:
                        if col > 0 and (row + 1, col - 1) not in opp_men and (row + 1, col - 1) not in my_men and ((row + 1, col - 1) not in my_kings):
                            moves.append((piece, (row + 1, col - 1)))
                        if col < 7 and (row + 1, col + 1) not in opp_men and (row + 1, col + 1) not in my_men and ((row + 1, col + 1) not in my_kings):
                            moves.append((piece, (row + 1, col + 1)))
            
            # King moves (can move diagonally in any direction)
            if piece in my_kings:
                for dr in [-1, 1]:
                    for dc in [-1, 1]:
                        r, c = row, col
                        while True:
                            r, c = r + dr, c + dc
                            if 0 <= r < 8 and 0 <= c < 8:
                                if (r, c) not in opp_men and (r, c) not in my_men:
                                    moves.append((piece, (r, c)))
                                elif (r, c) in opp_men:
                                    jump_row = r + dr
                                    jump_col = c + dc
                                    if 0 <= jump_row < 8 and 0 <= jump_col < 8 and (jump_row, jump_col) not in opp_men and (jump_row, jump_col) not in my_men:
                                        moves.append((piece, (jump_row, jump_col)))
                                    break
                                else:
                                    break
                            else:
                                break

        return moves

    # Function to simulate capture moves and their evaluation
    def evaluate_capture(from_piece, to_piece):
        # For simplicity, we just enumerate the captures
        captured_positions = set()
        for move in get_valid_moves([from_piece], []):
            if move[1] != to_piece:
                continue
            r1, c1 = from_piece
            r2, c2 = to_piece
            if (r2, c2) in opp_men or (r2, c2) in opp_kings:
                captured_positions.add((r2, c2))
        return captured_positions
    
    all_moves = get_valid_moves(my_men, my_kings)
    captures = []

    for move in all_moves:
        from_pos, to_pos = move
        r_from, c_from = from_pos
        r_to, c_to = to_pos
        if abs(r_to - r_from) == 2:  # a capture
            captures.append(move)
    
    # If there are capture moves, prioritize those
    if captures:
        return captures[0]  # return the first capture found
    
    # Otherwise return a normal move if no captures
    if all_moves:
        return all_moves[0]  # return the first valid move found
    
    # Fallback (though we should always have moves)
    return None

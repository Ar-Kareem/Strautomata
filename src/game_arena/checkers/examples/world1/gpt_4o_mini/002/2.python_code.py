
def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    def get_valid_moves(pos):
        row, col = pos
        moves = []
        directions = [(-1, -1), (-1, 1)] if color == 'b' else [(1, -1), (1, 1)]
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            if (0 <= new_row < 8) and (0 <= new_col < 8) and (new_row + new_col) % 2 == 1:
                moves.append((new_row, new_col))
        
        return moves

    def get_captures(pos):
        row, col = pos
        captures = []
        directions = [(-2, -2), (-2, 2)] if color == 'b' else [(2, -2), (2, 2)]
        for dr, dc in directions:
            middle_row = row + dr // 2
            middle_col = col + dc // 2
            new_row, new_col = row + dr, col + dc
            if (0 <= new_row < 8) and (0 <= new_col < 8) and (new_row + new_col) % 2 == 1:
                if (middle_row, middle_col) in opp_men or (middle_row, middle_col) in opp_kings:
                    captures.append((new_row, new_col))
        
        return captures

    def evaluate_board(my_men, my_kings, opp_men, opp_kings):
        return (len(my_men) + 2 * len(my_kings)) - (len(opp_men) + 2 * len(opp_kings))

    best_move = None
    best_value = float('-inf')

    possible_moves = []
    for piece in my_men + my_kings:
        captures = get_captures(piece)
        if captures:
            for capture in captures:
                possible_moves.append((piece, capture))
        else:
            moves = get_valid_moves(piece)
            for move in moves:
                possible_moves.append((piece, move))

    for (from_square, to_square) in possible_moves:
        new_my_men = my_men[:]
        new_my_kings = my_kings[:]
        new_opp_men = opp_men[:]
        new_opp_kings = opp_kings[:]

        if from_square in new_my_men:
            new_my_men.remove(from_square)
        else:
            new_my_kings.remove(from_square)

        if to_square in new_opp_men or to_square in new_opp_kings:
            opp_piece = (to_square if to_square in new_opp_men else new_opp_kings[0])
            if opp_piece in new_opp_men:
                new_opp_men.remove(opp_piece)
            else:
                new_opp_kings.remove(opp_piece)

        new_my_positions = new_my_men + new_my_kings
        new_value = evaluate_board(new_my_men, new_my_kings, new_opp_men, new_opp_kings)

        if new_value > best_value:
            best_value = new_value
            best_move = (from_square, to_square)

    return best_move


def policy(my_men, my_kings, opp_men, opp_kings, color):
    from collections import deque
    import random

    def is_inside_board(pos):
        row, col = pos
        return 0 <= row < 8 and 0 <= col < 8

    def is_valid_square(pos):
        row, col = pos
        # Check if it's a dark square
        return (row + col) % 2 == 1

    def get_all_possible_moves():
        all_moves = []
        all_captures = []
        my_pieces = my_men + my_kings
        opponent_pieces = opp_men + opp_kings
        opponent_positions = set(opponent_pieces)
        my_positions = set(my_pieces)
        empty_positions = {(row, col) for row in range(8) for col in range(8) 
                          if (row, col) not in my_positions and (row, col) not in opponent_positions and is_valid_square((row, col))}

        directions = []
        if color == 'w':  # white moves upwards (row increases)
            directions_for_men = [(1, 1), (1, -1)]
            directions_for_kings = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        else:  # black moves downwards (row decreases)
            directions_for_men = [(-1, 1), (-1, -1)]
            directions_for_kings = [(1, 1), (1, -1), (-1, 1), (-1, -1)]

        # Check for each piece
        for piece in my_pieces:
            piece_row, piece_col = piece
            is_king = piece in my_kings
            directions = directions_for_kings if is_king else directions_for_men
            captures_for_piece = []
            moves_for_piece = []

            # Look for captures first
            for dr, dc in directions:
                mid_row, mid_col = piece_row + dr, piece_col + dc
                if (mid_row, mid_col) in opponent_positions:
                    jump_row, jump_col = piece_row + 2*dr, piece_col + 2*dc
                    if is_inside_board((jump_row, jump_col)) and (jump_row, jump_col) in empty_positions:
                        captures_for_piece.append(((piece_row, piece_col), (jump_row, jump_col)))

            if captures_for_piece:
                # Explore multi-captures
                max_captures = []
                max_captured = 0

                for cap in captures_for_piece:
                    from_pos, to_pos = cap
                    # Simulate the capture and look for further jumps
                    captured = [((mid_row, mid_col) for (from_pos, to_pos) in [cap])]
                    current_pos = to_pos
                    current_captures = [cap]
                    temp_opp_positions = opponent_positions - set(captured)
                    temp_my_positions = (my_positions - {from_pos}) | {to_pos}
                    queue = deque()
                    queue.append((current_pos, current_captures, temp_my_positions, temp_opp_positions))
                    best_sequence = current_captures
                    best_len = 1

                    while queue:
                        pos, captures_seq, my_pos, opp_pos = queue.popleft()
                        row, col = pos
                        found_more = False
                        current_directions = directions_for_kings if pos in my_kings or (to_pos in [(0, i) for i in range(8)] if color == 'w' else to_pos in [(7, i) for i in range(8)]) else directions_for_men
                        for dr, dc in current_directions:
                            mid_r, mid_c = row + dr, col + dc
                            if (mid_r, mid_c) in opp_pos:
                                jump_r, jump_c = row + 2*dr, col + 2*dc
                                if is_inside_board((jump_r, jump_c)) and (jump_r, jump_c) not in my_pos and (jump_r, jump_c) not in opp_pos and is_valid_square((jump_r, jump_c)):
                                    new_captures_seq = captures_seq + [((row, col), (jump_r, jump_c))]
                                    new_my_pos = (my_pos - {(row, col)}) | {(jump_r, jump_c)}
                                    new_opp_pos = opp_pos - {(mid_r, mid_c)}
                                    queue.append(((jump_r, jump_c), new_captures_seq, new_my_pos, new_opp_pos))
                                    if len(new_captures_seq) > best_len:
                                        best_len = len(new_captures_seq)
                                        best_sequence = new_captures_seq
                                    found_more = True
                        if not found_more and len(captures_seq) > len(best_sequence):
                            best_sequence = captures_seq
                    if len(best_sequence) > max_captured:
                        max_captured = len(best_sequence)
                        max_captures = best_sequence
                if max_captures:
                    all_captures.extend(max_captures)
            else:
                # No captures, look for regular moves
                for dr, dc in directions:
                    new_row, new_col = piece_row + dr, piece_col + dc
                    if is_inside_board((new_row, new_col)) and (new_row, new_col) in empty_positions:
                        moves_for_piece.append(((piece_row, piece_col), (new_row, new_col)))
                all_moves.extend(moves_for_piece)

        if all_captures:
            # Find the capture sequence that captures the most pieces
            best_capture = max(all_captures, key=lambda x: len(x) if isinstance(x, list) else 1)
            return best_capture[-1] if isinstance(best_capture, list) else best_capture
        else:
            if not all_moves:
                return None  # should not happen as game should end first
            # Select a move that promotes a man to king if possible
            promoting_moves = []
            safe_moves = []
            for move in all_moves:
                from_pos, to_pos = move
                if from_pos in my_men:
                    if (color == 'w' and to_pos[0] == 7) or (color == 'b' and to_pos[0] == 0):
                        promoting_moves.append(move)
            if promoting_moves:
                return random.choice(promoting_moves)
            # Otherwise, prioritize moving towards the opponent's side
            if color == 'w':
                all_moves.sort(key=lambda x: -x[1][0])  # higher row first
            else:
                all_moves.sort(key=lambda x: x[1][0])  # lower row first
            return all_moves[0]
    
    move = get_all_possible_moves()
    if move is None:
        # Fallback in case no moves found (shouldn't happen in legal game state)
        my_pieces = my_men + my_kings
        for piece in my_pieces:
            row, col = piece
            directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)] if piece in my_kings else \
                         [(1, 1), (1, -1)] if color == 'w' else [(-1, 1), (-1, -1)]
            for dr, dc in directions:
                new_row, new_col = row + dr, col + dc
                if is_inside_board((new_row, new_col)) and is_valid_square((new_row, new_col)) and \
                   (new_row, new_col) not in (my_men + my_kings + opp_men + opp_kings):
                    return ((row, col), (new_row, new_col))
    return move

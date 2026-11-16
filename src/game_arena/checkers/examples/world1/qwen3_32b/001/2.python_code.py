
def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    def evaluate_position(r, c, color):
        if color == 'w':
            row_value = r
        else:
            row_value = 7 - r
        col_value = 4 - abs(c - 3.5)
        return row_value + col_value

    def get_jump_directions(is_king, color):
        if color == 'w':
            forward = 1
        else:
            forward = -1
        directions = []
        if is_king:
            for dr in [-2, 2]:
                for dc in [-2, 2]:
                    directions.append((dr, dc))
        else:
            directions.extend([(2 * forward, -2), (2 * forward, 2)])
        return directions

    def get_non_jump_directions(is_king, color):
        if color == 'w':
            forward = 1
        else:
            forward = -1
        directions = []
        if is_king:
            for dr in [-1, 1]:
                for dc in [-1, 1]:
                    if dr != 0 and dc != 0:
                        directions.append((dr, dc))
        else:
            directions.extend([(forward, -1), (forward, 1)])
        return directions

    def generate_captures(r, c, is_king, opp_pieces, my_pieces):
        all_moves = []
        directions = get_jump_directions(is_king, color)
        for dr, dc in directions:
            mid_r = r + dr // 2
            mid_c = c + dc // 2
            to_r = r + dr
            to_c = c + dc
            if 0 <= mid_r < 8 and 0 <= mid_c < 8 and 0 <= to_r < 8 and 0 <= to_c < 8:
                mid_pos = (mid_r, mid_c)
                to_pos = (to_r, to_c)
                if mid_pos in opp_pieces:
                    if to_pos not in opp_pieces and to_pos not in my_pieces:
                        new_opp_pieces = opp_pieces - {mid_pos}
                        all_moves.append(((r, c), to_pos, 1))
                        further_moves = generate_captures(to_r, to_c, is_king, new_opp_pieces, my_pieces)
                        for fm_start, fm_end, fm_count in further_moves:
                            all_moves.append(((r, c), fm_end, 1 + fm_count))
        return all_moves

    def generate_non_captures(r, c, is_king, opp_pieces, my_pieces):
        possible_moves = []
        directions = get_non_jump_directions(is_king, color)
        for dr, dc in directions:
            to_r = r + dr
            to_c = c + dc
            to_pos = (to_r, to_c)
            if 0 <= to_r < 8 and 0 <= to_c < 8:
                if to_pos not in opp_pieces and to_pos not in my_pieces:
                    possible_moves.append(((r, c), to_pos))
        return possible_moves

    opp_pieces = set(opp_men) | set(opp_kings)
    my_pieces = set(my_men) | set(my_kings)

    all_captures = []
    for piece in my_men + my_kings:
        r, c = piece
        is_king = piece in my_kings
        captures = generate_captures(r, c, is_king, opp_pieces, my_pieces)
        all_captures.extend(captures)

    if all_captures:
        def capture_key(move):
            _, end, count = move
            return (-count, -evaluate_position(end[0], end[1], color))
        sorted_captures = sorted(all_captures, key=capture_key)
        best_start, best_end, _ = sorted_captures[0]
        return (best_start, best_end)
    else:
        all_non_captures = []
        for piece in my_men + my_kings:
            r, c = piece
            is_king = piece in my_kings
            moves = generate_non_captures(r, c, is_king, opp_pieces, my_pieces)
            all_non_captures.extend(moves)
        if not all_non_captures:
            return ((0, 0), (0, 0))
        def non_capture_key(move):
            (start_r, start_c), (end_r, end_c) = move
            return evaluate_position(end_r, end_c, color) - evaluate_position(start_r, start_c, color)
        sorted_moves = sorted(all_non_captures, key=non_capture_key, reverse=True)
        return sorted_moves[0]


def policy(pieces: dict[str, str], to_play: str, memory: dict) -> tuple[str, dict]:
    def square_to_coords(square):
        file = ord(square[0]) - ord('a')
        rank = int(square[1]) - 1
        return (file, rank)

    def coords_to_square(x, y):
        return chr(ord('a') + x) + str(y + 1)

    piece_values = {
        'P': 1,
        'N': 3,
        'B': 3,
        'R': 5,
        'Q': 9,
        'K': 0
    }

    candidate_moves = []

    for from_sq, piece in pieces.items():
        if piece[0] != to_play[0]:
            continue
        piece_type = piece[1]

        if piece_type == 'P':
            color = 'w' if to_play == 'white' else 'b'
            direction = 1 if to_play == 'white' else -1
            start_rank = 1 if to_play == 'white' else 6
            from_x, from_y = square_to_coords(from_sq)
            to_sqs = []
            new_y = from_y + direction
            new_sq = coords_to_square(from_x, new_y)
            if new_sq not in pieces:
                to_sqs.append(new_sq)
                if from_y == start_rank:
                    new_y2 = from_y + 2 * direction
                    new_sq2 = coords_to_square(from_x, new_y2)
                    if new_sq2 not in pieces:
                        to_sqs.append(new_sq2)
            for dx in [-1, 1]:
                new_x = from_x + dx
                new_y_c = from_y + direction
                if 0 <= new_x <= 7 and 0 <= new_y_c <= 7:
                    capture_sq = coords_to_square(new_x, new_y_c)
                    if capture_sq in pieces and pieces[capture_sq][0] != color:
                        to_sqs.append(capture_sq)
            final_rank = 7 if to_play == 'white' else 0
            for to_sq in to_sqs:
                to_x, to_y = square_to_coords(to_sq)
                is_promotion = (to_y == final_rank)
                move_str = from_sq + to_sq
                if is_promotion:
                    move_str += 'q'
                candidate_moves.append(move_str)
        elif piece_type == 'N':
            from_x, from_y = square_to_coords(from_sq)
            directions = [(2, 1), (2, -1), (-2, 1), (-2, -1),
                          (1, 2), (1, -2), (-1, 2), (-1, -2)]
            for dx, dy in directions:
                new_x = from_x + dx
                new_y = from_y + dy
                if 0 <= new_x <= 7 and 0 <= new_y <= 7:
                    to_sq = coords_to_square(new_x, new_y)
                    if to_sq not in pieces or pieces[to_sq][0] != to_play[0]:
                        candidate_moves.append(from_sq + to_sq)
        elif piece_type == 'B':
            from_x, from_y = square_to_coords(from_sq)
            directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
            for dx, dy in directions:
                new_x, new_y = from_x + dx, from_y + dy
                while True:
                    if not (0 <= new_x <= 7 and 0 <= new_y <= 7):
                        break
                    to_sq = coords_to_square(new_x, new_y)
                    if to_sq in pieces and pieces[to_sq][0] == to_play[0]:
                        break
                    candidate_moves.append(from_sq + to_sq)
                    if to_sq in pieces and pieces[to_sq][0] != to_play[0]:
                        break
                    new_x += dx
                    new_y += dy
        elif piece_type == 'R':
            from_x, from_y = square_to_coords(from_sq)
            directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
            for dx, dy in directions:
                new_x, new_y = from_x + dx, from_y + dy
                while True:
                    if not (0 <= new_x <= 7 and 0 <= new_y <= 7):
                        break
                    to_sq = coords_to_square(new_x, new_y)
                    if to_sq in pieces and pieces[to_sq][0] == to_play[0]:
                        break
                    candidate_moves.append(from_sq + to_sq)
                    if to_sq in pieces and pieces[to_sq][0] != to_play[0]:
                        break
                    new_x += dx
                    new_y += dy
        elif piece_type == 'Q':
            from_x, from_y = square_to_coords(from_sq)
            directions = [(1, 0), (-1, 0), (0, 1), (0, -1),
                          (1, 1), (1, -1), (-1, 1), (-1, -1)]
            for dx, dy in directions:
                new_x, new_y = from_x + dx, from_y + dy
                while True:
                    if not (0 <= new_x <= 7 and 0 <= new_y <= 7):
                        break
                    to_sq = coords_to_square(new_x, new_y)
                    if to_sq in pieces and pieces[to_sq][0] == to_play[0]:
                        break
                    candidate_moves.append(from_sq + to_sq)
                    if to_sq in pieces and pieces[to_sq][0] != to_play[0]:
                        break
                    new_x += dx
                    new_y += dy
        elif piece_type == 'K':
            from_x, from_y = square_to_coords(from_sq)
            directions = [(1, 0), (-1, 0), (0, 1), (0, -1),
                          (1, 1), (1, -1), (-1, 1), (-1, -1)]
            for dx, dy in directions:
                new_x = from_x + dx
                new_y = from_y + dy
                if 0 <= new_x <= 7 and 0 <= new_y <= 7:
                    to_sq = coords_to_square(new_x, new_y)
                    if to_sq not in pieces or pieces[to_sq][0] != to_play[0]:
                        candidate_moves.append(from_sq + to_sq)

    best_move = None
    best_gain = -float('inf')

    for move in candidate_moves:
        if len(move) == 5:
            from_sq = move[0:2]
            to_sq = move[2:4]
            is_promotion = True
            promoted = move[4]
        else:
            from_sq = move[0:2]
            to_sq = move[2:4]
            is_promotion = False

        if from_sq not in pieces:
            continue
        moving_piece = pieces[from_sq]
        if moving_piece[0] != to_play[0]:
            continue

        moving_type = moving_piece[1]
        moving_value = piece_values[moving_type]
        captured_value = 0
        if to_sq in pieces and pieces[to_sq][0] != to_play[0]:
            captured_type = pieces[to_sq][1]
            captured_value = piece_values[captured_type]

        gain = captured_value - moving_value
        if is_promotion:
            if moving_type == 'P':
                promoted_value = piece_values[promoted.upper()]
                gain += (promoted_value - piece_values['P'])

        if (gain > best_gain) or (gain == best_gain and best_move is None):
            best_gain = gain
            best_move = move

    return (best_move, memory)

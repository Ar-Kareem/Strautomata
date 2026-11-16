
def policy(pieces: dict[str, str], to_play: str) -> str:
    import sys
    from collections import defaultdict

    piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 100}
    color = 'w' if to_play == 'white' else 'b'
    opponent_color = 'b' if color == 'w' else 'w'
    best_move = None
    best_score = -sys.maxsize

    def is_checkmate(new_pieces, king_pos):
        file, rank = king_pos[0], int(king_pos[1])
        king_offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        for df, dr in king_offsets:
            f = ord(file) - ord('a') + df
            r = rank + dr
            if 0 <= f < 8 and 1 <= r <= 8:
                new_square = f"{chr(ord('a') + f)}{r}"
                if new_square not in new_pieces or new_pieces[new_square][0] != opponent_color:
                    return False
        return True

    def is_square_attacked(square, pieces, opp_color):
        file, rank = square[0], square[1]
        f_num = ord(file) - ord('a')
        r_num = int(rank)

        directions = {
            'P': [(-1, 1), (1, 1)] if opp_color == 'w' else [(-1, -1), (1, -1)],
            'N': [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)],
            'K': [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)],
            'B': [(-1, -1), (-1, 1), (1, -1), (1, 1)],
            'R': [(-1, 0), (1, 0), (0, -1), (0, 1)],
            'Q': [(-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)]
        }

        for piece_type, offsets in directions.items():
            for df, dr in offsets:
                if piece_type == 'P' or piece_type == 'N' or piece_type == 'K':
                    new_f = f_num + df
                    new_r = r_num + dr
                    if 0 <= new_f < 8 and 1 <= new_r <= 8:
                        square_name = f"{chr(ord('a') + new_f)}{new_r}"
                        piece = pieces.get(square_name, '')
                        if piece and piece[0] == opp_color and piece[1] == piece_type:
                            return True
                else:
                    step = 1
                    while True:
                        new_f = f_num + df * step
                        new_r = r_num + dr * step
                        if not (0 <= new_f < 8 and 1 <= new_r <= 8):
                            break
                        square_name = f"{chr(ord('a') + new_f)}{new_r}"
                        piece = pieces.get(square_name, '')
                        if piece:
                            if piece[0] == opp_color and (piece[1] == piece_type or piece[1] == 'Q'):
                                return True
                            break
                        step += 1

        return False

    for from_sq in list(pieces.keys()):
        piece = pieces[from_sq]
        if piece[0] != color:
            continue

        piece_type = piece[1]
        from_file, from_rank = from_sq[0], int(from_sq[1])

        moves = []
        if piece_type == 'P':
            direction = 1 if color == 'w' else -1
            start_rank = 2 if color == 'w' else 7
            if f"{from_file}{from_rank + direction}" not in pieces:
                moves.append((from_file + str(from_rank) + from_file + str(from_rank + direction), False))
                if from_rank == start_rank and f"{from_file}{from_rank + 2*direction}" not in pieces:
                    moves.append((from_file + str(from_rank) + from_file + str(from_rank + 2*direction), False))
            for df in [-1, 1]:
                new_file = chr(ord(from_file) + df)
                if 'a' <= new_file <= 'h':
                    to_sq = f"{new_file}{from_rank + direction}"
                    if to_sq in pieces and pieces[to_sq][0] == opponent_color:
                        moves.append((from_sq + to_sq, True))
                    if from_rank == (4 if color == 'w' else 5):
                        pass  # En passant is omitted for simplicity
            if from_rank + direction in [1, 8]:
                for promo in ['q', 'r', 'b', 'n']:
                    moves.append((from_sq + to_sq + promo, True))
        elif piece_type == 'N':
            knight_moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
            for df, dr in knight_moves:
                new_file = chr(ord(from_file) + df)
                new_rank = from_rank + dr
                if 'a' <= new_file <= 'h' and 1 <= new_rank <= 8:
                    to_sq = f"{new_file}{new_rank}"
                    capture = to_sq in pieces and pieces[to_sq][0] == opponent_color
                    moves.append((from_sq + to_sq, capture))
        elif piece_type in ['B', 'R', 'Q']:
            directions = []
            if piece_type in ['B', 'Q']:
                directions += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
            if piece_type in ['R', 'Q']:
                directions += [(-1, 0), (1, 0), (0, -1), (0, 1)]
            for df, dr in directions:
                step = 1
                while True:
                    new_file = chr(ord(from_file) + df * step)
                    new_rank = from_rank + dr * step
                    if not ('a' <= new_file <= 'h' and 1 <= new_rank <= 8):
                        break
                    to_sq = f"{new_file}{new_rank}"
                    if to_sq in pieces and pieces[to_sq][0] == color:
                        break
                    capture = to_sq in pieces and pieces[to_sq][0] == opponent_color
                    moves.append((from_sq + to_sq, capture))
                    if capture:
                        break
                    step += 1
        elif piece_type == 'K':
            king_moves = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
            for df, dr in king_moves:
                new_file = chr(ord(from_file) + df)
                new_rank = from_rank + dr
                if 'a' <= new_file <= 'h' and 1 <= new_rank <= 8:
                    to_sq = f"{new_file}{new_rank}"
                    if to_sq not in pieces or pieces[to_sq][0] == opponent_color:
                        moves.append((from_sq + to_sq, to_sq in pieces))
            # Castling is omitted for simplicity

        for move_info in moves:
            move_str, is_capture = move_info if len(move_info) == 2 else (move_info[0], False)
            new_pieces = pieces.copy()
            from_sq_move = move_str[:2]
            to_sq_move = move_str[2:4]
            if len(move_str) == 5:
                promo_piece = move_str[4]
                new_pieces[to_sq_move] = color + promo_piece.upper()
            else:
                new_pieces[to_sq_move] = new_pieces[from_sq_move]
            del new_pieces[from_sq_move]
            if is_capture:
                captured_piece = pieces.get(to_sq_move, '')
                if captured_piece:
                    captured_value = piece_values.get(captured_piece[1], 0)
            else:
                captured_value = 0

            score = 0
            if is_capture:
                score += captured_value * 10
            if to_sq == from_sq + 'q':
                score += 8
            if is_square_attacked(to_sq_move, new_pieces, opponent_color):
                moved_piece_value = piece_values.get(new_pieces[to_sq_move][1], 0)
                score -= moved_piece_value

            opp_king_pos = None
            for sq, pc in new_pieces.items():
                if pc == opponent_color + 'K':
                    opp_king_pos = sq
                    break
            if opp_king_pos and is_square_attacked(opp_king_pos, new_pieces, opponent_color):
                if is_checkmate(new_pieces, opp_king_pos):
                    score += 10000
                else:
                    score += 50

            if score > best_score:
                best_score = score
                best_move = move_str

    if best_move is None:
        for move_str in pieces:
            if pieces[move_str][0] == color:
                return move_str[:4]
        return list(pieces.keys())[0][:4]
    return best_move

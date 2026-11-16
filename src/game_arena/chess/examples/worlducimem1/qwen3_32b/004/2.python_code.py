
def policy(pieces: dict[str, str], to_play: str, memory: dict) -> tuple[str, dict]:
    piece_values = {'P':1, 'N':3, 'B':3, 'R':5, 'Q':9, 'K':0}
    
    def generate_pseudo_legal_moves(pieces, color):
        moves = []
        for square, piece in pieces.items():
            if piece[0] != color:
                continue
            piece_type = piece[1]
            if piece_type == 'P':
                moves.extend(generate_pawn_moves(square, pieces, color))
            elif piece_type == 'N':
                moves.extend(generate_knight_moves(square, pieces))
            elif piece_type == 'B':
                moves.extend(generate_bishop_moves(square, pieces))
            elif piece_type == 'R':
                moves.extend(generate_rook_moves(square, pieces))
            elif piece_type == 'Q':
                moves.extend(generate_queen_moves(square, pieces))
            elif piece_type == 'K':
                moves.extend(generate_king_moves(square, pieces))
        return moves

    def generate_pawn_moves(square, pieces, color):
        moves = []
        file = square[0]
        rank = int(square[1])
        direction = 1 if color == 'w' else -1
        is_white = color == 'w'
        start_rank = 2 if is_white else 7
        promotion_rank = 8 if is_white else 1

        # Forward move
        front_square = f"{file}{rank + direction}"
        if front_square not in pieces:
            # Normal move
            if is_white:
                if rank + direction == promotion_rank:
                    for promo in ['q', 'r', 'b', 'n']:
                        moves.append(f"{square}{front_square}{promo}")
                else:
                    moves.append(f"{square}{front_square}")
            else:
                if rank + direction == promotion_rank:
                    for promo in ['q', 'r', 'b', 'n']:
                        moves.append(f"{square}{front_square}{promo}")
                else:
                    moves.append(f"{square}{front_square}")
            # Double move from starting rank
            if rank == start_rank and rank + direction + direction in [3, 6]:
                double_front = f"{file}{rank + 2 * direction}"
                if double_front not in pieces:
                    moves.append(double_front)
        # Captures
        for delta in [-1, 1]:
            target_file = chr(ord(file) + delta)
            if 'a' <= target_file <= 'h':
                target_square = f"{target_file}{rank + direction}"
                if target_square in pieces and pieces[target_square][0] != color:
                    # Capture move with possible promotion
                    if is_white:
                        if rank + direction == promotion_rank:
                            for promo in ['q', 'r', 'b', 'n']:
                                moves.append(f"{square}{target_square}{promo}")
                        else:
                            moves.append(f"{square}{target_square}")
                    else:
                        if rank + direction == promotion_rank:
                            for promo in ['q', 'r', 'b', 'n']:
                                moves.append(f"{square}{target_square}{promo}")
                        else:
                            moves.append(f"{square}{target_square}")
        return moves

    def generate_knight_moves(square, pieces):
        moves = []
        file = square[0]
        rank = int(square[1])
        deltas = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
        for dr, df in deltas:
            new_rank = rank + dr
            new_file = ord(file) + df
            if new_rank < 1 or new_rank > 8 or new_file < ord('a') or new_file > ord('h'):
                continue
            new_square = chr(new_file) + str(new_rank)
            if new_square not in pieces or pieces[new_square][0] != pieces[square][0]:
                moves.append(square + new_square)
        return moves

    def generate_bishop_moves(square, pieces):
        return generate_sliding_moves(square, pieces, [(1, 1), (1, -1), (-1, 1), (-1, -1)])

    def generate_rook_moves(square, pieces):
        return generate_sliding_moves(square, pieces, [(1, 0), (-1, 0), (0, 1), (0, -1)])

    def generate_queen_moves(square, pieces):
        return generate_sliding_moves(square, pieces, [(1, 0), (0, 1), (-1, 0), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)])

    def generate_king_moves(square, pieces):
        moves = []
        file = ord(square[0])
        rank = int(square[1])
        for dr, df in [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
            new_rank = rank + dr
            new_file = file + df
            if new_rank < 1 or new_rank > 8 or new_file < ord('a') or new_file > ord('h'):
                continue
            new_square = chr(new_file) + str(new_rank)
            if new_square not in pieces or pieces[new_square][0] != pieces[square][0]:
                moves.append(square + new_square)
        return moves

    def generate_sliding_moves(square, pieces, directions):
        moves = []
        file = square[0]
        rank = int(square[1])
        color = pieces[square][0]
        for dr, df in directions:
            r, f = rank, ord(file)
            while True:
                r += dr
                f += df
                if r < 1 or r > 8 or f < ord('a') or f > ord('h'):
                    break
                new_square = chr(f) + str(r)
                if new_square in pieces:
                    if pieces[new_square][0] != color:
                        moves.append(square + new_square)
                    break
                else:
                    moves.append(square + new_square)
        return moves

    def parse_move(move):
        from_square = move[:2]
        to_square = move[2:4]
        promo = move[4:] if len(move) > 4 else ''
        return from_square, to_square, promo

    def simulate_move(pieces, move):
        from_square, to_square, promo = parse_move(move)
        new_pieces = {k: v for k, v in pieces.items()}
        from_piece = new_pieces[from_square]
        del new_pieces[from_square]
        if promo:
            new_pieces[to_square] = from_piece[0] + promo.upper()
        else:
            new_pieces[to_square] = from_piece
        return new_pieces

    def is_square_attacked(square, pieces, color):
        opponent_color = 'b' if color == 'w' else 'w'
        for piece_square, piece in pieces.items():
            if piece[0] != opponent_color:
                continue
            piece_type = piece[1]
            piece_rank = int(piece_square[1])
            piece_file = ord(piece_square[0])
            square_rank = int(square[1])
            square_file = ord(square[0])
            
            if piece_type == 'P':
                if (abs(ord(square[0]) - piece_file) == 1 and
                    (color == 'w' and piece_rank + 1 == square_rank or
                     color == 'b' and piece_rank - 1 == square_rank)):
                    return True
            elif piece_type == 'N':
                if any((piece_rank + dr == square_rank) and (piece_file + df == square_file) for dr, df in [(-2,-1), (-2,1), (-1,-2), (-1,2), (1,-2), (1,2), (2,-1), (2,1)]):
                    return True
            elif piece_type == 'B':
                dr = piece_rank - square_rank
                df = piece_file - square_file
                if abs(dr) != abs(df):
                    continue
                step_r = 1 if square_rank < piece_rank else -1
                step_f = 1 if square_file < piece_file else -1
                for i in range(1, abs(dr)):
                    check_square = chr(piece_file + (step_f * i)) + str(piece_rank + (step_r * i))
                    if check_square in pieces:
                        break
                else:
                    return True
            elif piece_type == 'R':
                if piece_rank == square_rank or piece_file == square_file:
                    if piece_rank == square_rank:
                        for i in range(min(piece_file, square_file) + 1, max(piece_file, square_file)):
                            check_square = chr(i) + str(piece_rank)
                            if check_square in pieces:
                                break
                        else:
                            return True
                    else:
                        for i in range(min(piece_rank, square_rank) + 1, max(piece_rank, square_rank)):
                            check_square = chr(piece_file) + str(i)
                            if check_square in pieces:
                                break
                        else:
                            return True
            elif piece_type == 'Q':
                if is_square_attacked(square, pieces, color, 'B') or is_square_attacked(square, pieces, color, 'R'):
                    return True
            elif piece_type == 'K':
                if abs(piece_rank - square_rank) <= 1 and abs(piece_file - square_file) <= 1:
                    return True
        return False

    def is_check_after_move(move, pieces, color):
        new_pieces = simulate_move(pieces, move)
        opponent_color = 'b' if color == 'w' else 'w'
        for square, piece in new_pieces.items():
            if piece == opponent_color + 'K':
                king_square = square
                break
        else:
            return False
        return is_square_attacked(king_square, new_pieces, color)

    color = to_play[0]
    pseudo_moves = generate_pseudo_legal_moves(pieces, color)
    legal_moves = []

    for move in pseudo_moves:
        new_pieces = simulate_move(pieces, move)
        king_square = None
        for sq, p in new_pieces.items():
            if p[0] == color and p[1] == 'K':
                king_square = sq
                break
        if king_square and not is_square_attacked(king_square, new_pieces, color):
            legal_moves.append(move)

    best_move = ''
    max_score = float('-inf')

    for move in legal_moves:
        from_sq, to_sq, promo = parse_move(move)
        to_sq_piece = pieces.get(to_sq, '')
        is_capture = to_sq_piece and to_sq_piece[0] != color
        captured_value = piece_values.get(to_sq_piece[1], 0) if is_capture else 0
        moving_value = piece_values.get(pieces[from_sq][1], 0)
        material_gain = captured_value - moving_value
        is_promotion = len(move) > 4
        promoted_value = piece_values.get(move[-1].upper(), 0) if is_promotion else 0

        score = 0
        if is_check_after_move(move, pieces, color):
            score += 100
        if material_gain > 0:
            score += material_gain * 10
        elif is_capture:
            score += material_gain * 2
        if is_promotion:
            score += (promoted_value - moving_value) * 10

        if score > max_score:
            max_score = score
            best_move = move

    return best_move, memory


import string

def policy(pieces, to_play):
    def square_to_coords(square):
        return ord(square[0]) - ord('a'), int(square[1]) - 1

    def coords_to_square(x, y):
        return string.ascii_lowercase[x] + str(y + 1)

    def is_square_under_attack(square, pieces, color):
        opponent_color = 'b' if color == 'white' else 'w'
        for sq, p in pieces.items():
            piece_color, piece_type = p[0], p[1]
            if piece_color != opponent_color:
                continue
            if can_attack(sq, piece_type, square, pieces):
                return True
        return False

    def can_attack(from_sq, piece_type, to_sq, pieces):
        from_x, from_y = square_to_coords(from_sq)
        to_x, to_y = square_to_coords(to_sq)
        dx = to_x - from_x
        dy = to_y - from_y

        if piece_type == 'P':
            direction = 1 if pieces[from_sq][0] == 'w' else -1
            if abs(dx) == 1 and dy == direction:
                return True
            return False

        elif piece_type == 'N':
            if (abs(dx) == 1 and abs(dy) == 2) or (abs(dx) == 2 and abs(dy) == 1):
                return True
            return False

        elif piece_type == 'K':
            if abs(dx) <= 1 and abs(dy) <= 1:
                return True
            return False

        elif piece_type == 'R':
            if dx == 0 or dy == 0:
                return slide_check(from_sq, to_sq, pieces)
            return False

        elif piece_type == 'B':
            if abs(dx) == abs(dy):
                return slide_check(from_sq, to_sq, pieces)
            return False

        elif piece_type == 'Q':
            if dx == 0 or dy == 0 or abs(dx) == abs(dy):
                return slide_check(from_sq, to_sq, pieces)
            return False
        return False

    def slide_check(from_sq, to_sq, pieces):
        from_x, from_y = square_to_coords(from_sq)
        to_x, to_y = square_to_coords(to_sq)
        dx = to_x - from_x
        dy = to_y - from_y
        step_x = 1 if dx > 0 else -1 if dx < 0 else 0
        step_y = 1 if dy > 0 else -1 if dy < 0 else 0
        dist = max(abs(dx), abs(dy))
        for i in range(1, dist):
            check_x = from_x + step_x * i
            check_y = from_y + step_y * i
            check_sq = coords_to_square(check_x, check_y)
            if check_sq in pieces:
                return False
        return True

    def generate_pawn_pseudo_moves(square, pieces, color):
        x, y = square_to_coords(square)
        moves = []
        direction = 1 if color == 'w' else -1
        target_y = y + direction

        f1_square = coords_to_square(x, target_y)
        if f1_square not in pieces:
            moves.append(square + f1_square)
            if ((color == 'w' and y == 1) or (color == 'b' and y == 6)):
                target_y2 = y + 2 * direction
                f2_square = coords_to_square(x, target_y2)
                if f2_square not in pieces:
                    moves.append(square + f2_square)

        for dx in [-1, 1]:
            target_x = x + dx
            if 0 <= target_x <= 7:
                capture_square = coords_to_square(target_x, target_y)
                if capture_square in pieces and pieces[capture_square][0] != color:
                    moves.append(square + capture_square)
        return moves

    def generate_rook_pseudo_moves(square, pieces, color):
        x, y = square_to_coords(square)
        directions = [(1,0), (-1,0), (0,1), (0,-1)]
        moves = []
        for dx, dy in directions:
            for dist in range(1, 8):
                new_x = x + dx * dist
                new_y = y + dy * dist
                new_square = coords_to_square(new_x, new_y)
                if new_square not in pieces:
                    moves.append(square + new_square)
                else:
                    target_color = pieces[new_square][0]
                    if target_color != color:
                        moves.append(square + new_square)
                    break
        return moves

    def generate_knight_pseudo_moves(square, pieces, color):
        x, y = square_to_coords(square)
        knight_moves = [
            (2,1), (2,-1), (-2,1), (-2,-1),
            (1,2), (1,-2), (-1,2), (-1,-2)
        ]
        moves = []
        for dx, dy in knight_moves:
            new_x = x + dx
            new_y = y + dy
            if 0 <= new_x <= 7 and 0 <= new_y <=7:
                new_square = coords_to_square(new_x, new_y)
                if new_square not in pieces:
                    moves.append(square + new_square)
                else:
                    target_color = pieces[new_square][0]
                    if target_color != color:
                        moves.append(square + new_square)
        return moves

    def generate_bishop_pseudo_moves(square, pieces, color):
        x, y = square_to_coords(square)
        directions = [(1,1), (1,-1), (-1,1), (-1,-1)]
        moves = []
        for dx, dy in directions:
            for dist in range(1, 8):
                new_x = x + dx * dist
                new_y = y + dy * dist
                new_square = coords_to_square(new_x, new_y)
                if new_square not in pieces:
                    moves.append(square + new_square)
                else:
                    target_color = pieces[new_square][0]
                    if target_color != color:
                        moves.append(square + new_square)
                    break
        return moves

    def generate_queen_pseudo_moves(square, pieces, color):
        return generate_rook_pseudo_moves(square, pieces, color) + generate_bishop_pseudo_moves(square, pieces, color)

    def generate_king_pseudo_moves(square, pieces, color):
        x, y = square_to_coords(square)
        king_moves = [
            (0,1), (0,-1), (1,0), (-1,0),
            (1,1), (1,-1), (-1,1), (-1,-1)
        ]
        moves = []
        for dx, dy in king_moves:
            new_x = x + dx
            new_y = y + dy
            if 0 <= new_x <= 7 and 0 <= new_y <=7:
                new_square = coords_to_square(new_x, new_y)
                if new_square not in pieces:
                    moves.append(square + new_square)
                else:
                    target_color = pieces[new_square][0]
                    if target_color != color:
                        moves.append(square + new_square)
        return moves

    def generate_pseudo_moves(piece, square, pieces, color):
        piece_type = piece[1]
        if piece_type == 'P':
            return generate_pawn_pseudo_moves(square, pieces, color)
        elif piece_type == 'R':
            return generate_rook_pseudo_moves(square, pieces, color)
        elif piece_type == 'N':
            return generate_knight_pseudo_moves(square, pieces, color)
        elif piece_type == 'B':
            return generate_bishop_pseudo_moves(square, pieces, color)
        elif piece_type == 'Q':
            return generate_queen_pseudo_moves(square, pieces, color)
        elif piece_type == 'K':
            return generate_king_pseudo_moves(square, pieces, color)
        return []

    legal_moves = []

    current_king = None
    for square, p in pieces.items():
        if p[0] == ('w' if to_play == 'white' else 'b') and p[1] == 'K':
            current_king = square
            break

    color = 'w' if to_play == 'white' else 'b'

    for square, p in pieces.items():
        if p[0] == color:
            piece_type = p[1]
            pseudo_moves = generate_pseudo_moves(p, square, pieces, color)
            for move in pseudo_moves:
                from_sq = move[:2]
                to_sq = move[2:]
                new_pieces = pieces.copy()
                is_capture = to_sq in new_pieces
                if is_capture:
                    captured_piece = new_pieces[to_sq]
                is_promotion = (piece_type == 'P') and (to_sq[1] in ('1', '8'))
                if is_promotion:
                    new_pieces[to_sq] = color + 'Q'
                    move = move + 'q'
                else:
                    new_pieces[to_sq] = p
                del new_pieces[from_sq]
                new_king_pos = current_king
                if from_sq == current_king:
                    new_king_pos = to_sq
                if not is_square_under_attack(new_king_pos, new_pieces, color):
                    legal_moves.append(move)

    piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
    best_move = None
    best_score = -float('inf')

    for move in legal_moves:
        move_from = move[:2]
        move_to = move[2:4]  # ignore promotion character if present
        is_capture = move_to in pieces
        capture_score = 0
        if is_capture:
            captured_value = piece_values[pieces[move_to][1]]
            moving_value = piece_values[pieces[move_from][1]]
            capture_score = captured_value - moving_value
        is_check = False
        new_pieces = pieces.copy()
        moving_piece = new_pieces[move_from]
        del new_pieces[move_from]
        if move_to in new_pieces:
            del new_pieces[move_to]
        new_pieces[move_to] = moving_piece
        for sq, p in new_pieces.items():
            if p[0] != color and p[1] == 'K':
                opponent_king_pos = sq
                break
        is_check = is_square_under_attack(opponent_king_pos, new_pieces, p[0] if color == 'b' else 'w')
        check_bonus = 0.1 if is_check else 0
        is_promotion_move = len(move) > 4
        promotion_bonus = 9 if is_promotion_move else 0
        total_score = capture_score + check_bonus + promotion_bonus
        if total_score > best_score:
            best_score = total_score
            best_move = move

    return best_move

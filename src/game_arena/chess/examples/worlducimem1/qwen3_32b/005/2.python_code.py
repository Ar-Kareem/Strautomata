
import copy

def policy(pieces: dict[str, str], to_play: str, memory: dict) -> tuple[str, dict]:
    def square_to_coords(square):
        x = ord(square[0]) - ord('a')
        y = int(square[1]) - 1
        return x, y

    def coords_to_square(x, y):
        return chr(ord('a') + x) + str(y + 1)

    def coords_to_move(x1, y1, x2, y2):
        return coords_to_square(x1, y1) + coords_to_square(x2, y2)

    def generate_pawn_moves(x, y, pieces, current_color, candidate_moves):
        direction = 1 if current_color == 'w' else -1
        ny = y + direction
        if 0 <= ny < 8:
            to_square = coords_to_square(x, ny)
            if to_square not in pieces:
                move = coords_to_move(x, y, x, ny)
                if (current_color == 'w' and ny == 7) or (current_color == 'b' and ny == 0):
                    move += 'q'
                candidate_moves.append(move)
                if ((current_color == 'w' and y == 1) or (current_color == 'b' and y == 6)):
                    double_ny = y + 2 * direction
                    if 0 <= double_ny < 8:
                        double_square = coords_to_square(x, double_ny)
                        if double_square not in pieces:
                            candidate_moves.append(coords_to_move(x, y, x, double_ny))
            for dx in [-1, 1]:
                nx = x + dx
                ny = y + direction
                if 0 <= nx < 8 and 0 <= ny < 8:
                    target_square = coords_to_square(nx, ny)
                    if target_square in pieces:
                        if pieces[target_square][0] != current_color:
                            capture_move = coords_to_move(x, y, nx, ny)
                            if (current_color == 'w' and ny == 7) or (current_color == 'b' and ny == 0):
                                capture_move += 'q'
                            candidate_moves.append(capture_move)

    def generate_knight_moves(x, y, pieces, current_color, candidate_moves):
        knight_moves = [ (2,1), (2,-1), (-2,1), (-2,-1), (1,2), (1,-2), (-1,2), (-1,-2) ]
        for dx, dy in knight_moves:
            nx = x + dx
            ny = y + dy
            if 0 <= nx < 8 and 0 <= ny < 8:
                target_square = coords_to_square(nx, ny)
                if target_square not in pieces or pieces[target_square][0] != current_color:
                    candidate_moves.append(coords_to_move(x, y, nx, ny))

    def generate_sliding_moves(x, y, pieces, current_color, directions, candidate_moves):
        for dx, dy in directions:
            for step in range(1, 8):
                nx = x + dx * step
                ny = y + dy * step
                if not (0 <= nx < 8 and 0 <= ny < 8):
                    break
                target_square = coords_to_square(nx, ny)
                if target_square in pieces:
                    target_color = pieces[target_square][0]
                    if target_color != current_color:
                        candidate_moves.append(coords_to_move(x, y, nx, ny))
                    break
                else:
                    candidate_moves.append(coords_to_move(x, y, nx, ny))

    def generate_king_moves(x, y, pieces, current_color, candidate_moves):
        king_directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
        for dx, dy in king_directions:
            nx = x + dx
            ny = y + dy
            if 0 <= nx < 8 and 0 <= ny < 8:
                target_square = coords_to_square(nx, ny)
                if target_square not in pieces or pieces[target_square][0] != current_color:
                    candidate_moves.append(coords_to_move(x, y, nx, ny))

    def find_king(pieces, current_color):
        for square, piece in pieces.items():
            if piece[0] == current_color and piece[1] == 'K':
                return square
        return None

    def is_in_check(pieces, current_color):
        king_square = find_king(pieces, current_color)
        if not king_square:
            return False
        opponent_color = 'b' if current_color == 'w' else 'w'
        for square, piece in pieces.items():
            if piece[0] != opponent_color:
                continue
            piece_type = piece[1]
            if can_attack(square, piece_type, king_square, pieces, piece[0]):
                return True
        return False

    def can_attack(start_square, piece_type, target_square, pieces, color):
        x1, y1 = square_to_coords(start_square)
        x2, y2 = square_to_coords(target_square)
        if piece_type == 'P':
            direction = 1 if color == 'w' else -1
            dx = abs(x1 - x2)
            dy = y1 - y2
            if dx == 1 and dy == direction:
                return True
            return False
        elif piece_type == 'N':
            dx = abs(x1 - x2)
            dy = abs(y1 - y2)
            if (dx == 2 and dy == 1) or (dx == 1 and dy == 2):
                return True
            return False
        elif piece_type == 'B':
            dx = abs(x1 - x2)
            dy = abs(y1 - y2)
            if dx == dy and is_line_clear(x1, y1, x2, y2, pieces):
                return True
            return False
        elif piece_type == 'R':
            if (x1 == x2 or y1 == y2) and is_line_clear(x1, y1, x2, y2, pieces):
                return True
            return False
        elif piece_type == 'Q':
            if (x1 == x2 or y1 == y2 or abs(x1 - x2) == abs(y1 - y2)) and is_line_clear(x1, y1, x2, y2, pieces):
                return True
            return False
        elif piece_type == 'K':
            dx = abs(x1 - x2)
            dy = abs(y1 - y2)
            if dx <= 1 and dy <= 1 and (dx + dy) > 0:
                return True
            return False
        return False

    def is_line_clear(x1, y1, x2, y2, pieces):
        dx = x2 - x1
        dy = y2 - y1
        steps = max(abs(dx), abs(dy))
        if steps == 0:
            return False
        x_step = 0 if dx == 0 else (1 if dx > 0 else -1)
        y_step = 0 if dy == 0 else (1 if dy > 0 else -1)
        for i in range(1, steps):
            x = x1 + x_step * i
            y = y1 + y_step * i
            square = coords_to_square(x, y)
            if square in pieces:
                return False
        return True

    def simulate_move(pieces, move_str):
        from_pos = move_str[:2]
        to_pos = move_str[2:4]
        promotion = move_str[4:] if len(move_str) > 4 else ''
        new_pieces = pieces.copy()
        from_piece = new_pieces.pop(from_pos, None)
        if from_piece is None:
            return new_pieces
        to_square = to_pos
        if from_piece[1] == 'P':
            color = from_piece[0]
            destination_rank = int(to_square[1])
            if (color == 'w' and destination_rank == 8) or (color == 'b' and destination_rank == 1):
                new_pieces[to_square] = color + (promotion.upper() if promotion else 'Q')
            else:
                new_pieces[to_square] = from_piece
        else:
            new_pieces[to_square] = from_piece
        return new_pieces

    def generate_legal_moves(pieces, current_color):
        candidate_moves = []
        for square, piece in pieces.items():
            if piece[0] != current_color:
                continue
            piece_type = piece[1]
            x, y = square_to_coords(square)
            if piece_type == 'P':
                generate_pawn_moves(x, y, pieces, current_color, candidate_moves)
            elif piece_type == 'N':
                generate_knight_moves(x, y, pieces, current_color, candidate_moves)
            elif piece_type == 'B':
                generate_sliding_moves(x, y, pieces, current_color, [(1,1), (1,-1), (-1,1), (-1,-1)], candidate_moves)
            elif piece_type == 'R':
                generate_sliding_moves(x, y, pieces, current_color, [(1,0), (-1,0), (0,1), (0,-1)], candidate_moves)
            elif piece_type == 'Q':
                generate_sliding_moves(x, y, pieces, current_color, [(1,0), (-1,0), (0,1), (0,-1), (1,1), (1,-1), (-1,1), (-1,-1)], candidate_moves)
            elif piece_type == 'K':
                generate_king_moves(x, y, pieces, current_color, candidate_moves)
        legal_moves = []
        for move in candidate_moves:
            new_pieces = simulate_move(pieces, move)
            if new_pieces and not is_in_check(new_pieces, current_color):
                legal_moves.append(move)
        return legal_moves

    def evaluate_position(pieces, current_color):
        material = 0
        piece_values = {'P':1, 'N':3, 'B':3, 'R':5, 'Q':9, 'K':0}
        for square, piece in pieces.items():
            piece_color = piece[0]
            piece_type = piece[1]
            value = piece_values.get(piece_type, 0)
            if piece_color == current_color:
                material += value
            else:
                material -= value
        return material

    def is_checkmate(pieces, current_color):
        if not is_in_check(pieces, current_color):
            return False
        legal_moves_opponent = generate_legal_moves(pieces, current_color)
        return len(legal_moves_opponent) == 0

    def select_best_move(pieces, to_play, legal_moves):
        current_color = 'w' if to_play == 'white' else 'b'
        for move in legal_moves:
            new_pieces = simulate_move(pieces, move)
            if is_checkmate(new_pieces, current_color):
                return move
        best_score = -float('inf')
        best_moves = []
        for move in legal_moves:
            new_pieces = simulate_move(pieces, move)
            from_sq, to_sq = move[:2], move[2:4]
            from_piece = pieces[from_sq]
            to_piece = pieces.get(to_sq, None)
            is_capture = to_piece is not None and to_piece[0] != from_piece[0]
            score = evaluate_position(new_pieces, current_color)
            if is_capture and to_piece:
                captured_type = to_piece[1]
                score += {'P':1, 'N':3, 'B':3, 'R':5, 'Q':9}.get(captured_type, 0) * 2
            if is_in_check(new_pieces, 'b' if current_color == 'w' else 'w'):
                score += 0.5
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)
        return best_moves[0] if best_moves else legal_moves[0]

    current_color = 'w' if to_play == 'white' else 'b'
    legal_moves = generate_legal_moves(pieces, current_color)
    if not legal_moves:
        return '', memory
    best_move = select_best_move(pieces, to_play, legal_moves)
    return (best_move, memory)

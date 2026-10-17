
import time
import numpy as np

piece_values = {
    'P': 100,
    'N': 320,
    'B': 330,
    'R': 500,
    'Q': 900,
    'K': 20000
}

piece_square_tables = {
    'P': np.array([
        [0, 0, 0, 0, 0, 0, 0, 0],
        [5, 5, 5, 5, 5, 5, 5, 5],
        [1, 1, 2, 3, 3, 2, 1, 1],
        [0.5, 0.5, 1, 2.5, 2.5, 1, 0.5, 0.5],
        [0, 0, 0, 2, 2, 0, 0, 0],
        [0.5, -0.5, -1, 0, 0, -1, -0.5, 0.5],
        [0.5, 1, 1, -2, -2, 1, 1, 0.5],
        [0, 0, 0, 0, 0, 0, 0, 0]
    ]),
    'N': np.array([
        [-5, -4, -3, -3, -3, -3, -4, -5],
        [-4, -2, 0, 0, 0, 0, -2, -4],
        [-3, 0, 1, 1.5, 1.5, 1, 0, -3],
        [-3, 0.5, 1.5, 2, 2, 1.5, 0.5, -3],
        [-3, 0, 1.5, 2, 2, 1.5, 0, -3],
        [-3, 0.5, 1, 1.5, 1.5, 1, 0.5, -3],
        [-4, -2, 0, 0.5, 0.5, 0, -2, -4],
        [-5, -4, -3, -3, -3, -3, -4, -5]
    ]),
    'B': np.array([
        [-2, -1, -1, -1, -1, -1, -1, -2],
        [-1, 0, 0, 0, 0, 0, 0, -1],
        [-1, 0, 0.5, 1, 1, 0.5, 0, -1],
        [-1, 0.5, 0.5, 1, 1, 0.5, 0.5, -1],
        [-1, 0, 1, 1, 1, 1, 0, -1],
        [-1, 1, 0.5, 0, 0, 0.5, 1, -1],
        [-1, 0, 0, 0, 0, 0, 0, -1],
        [-2, -1, -1, -1, -1, -1, -1, -2]
    ]),
    'R': np.array([
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0.5, 1, 1, 1, 1, 1, 1, 0.5],
        [-0.5, 0, 0, 0, 0, 0, 0, -0.5],
        [-0.5, 0, 0, 0, 0, 0, 0, -0.5],
        [-0.5, 0, 0, 0, 0, 0, 0, -0.5],
        [-0.5, 0, 0, 0, 0, 0, 0, -0.5],
        [-0.5, 0, 0, 0, 0, 0, 0, -0.5],
        [0, 0, 0, 0, 0, 0, 0, 0]
    ]),
    'Q': np.array([
        [-2, -1, -1, -0.5, -0.5, -1, -1, -2],
        [-1, 0, 0, 0, 0, 0, 0, -1],
        [-1, 0, 0.5, 0.5, 0.5, 0.5, 0, -1],
        [-0.5, 0, 0.5, 0.5, 0.5, 0.5, 0, -0.5],
        [0, 0, 0.5, 0.5, 0.5, 0.5, 0, -0.5],
        [-1, 0.5, 0.5, 0.5, 0.5, 0.5, 0, -1],
        [-1, 0, 0, 0, 0, 0, 0, -1],
        [-2, -1, -1, -0.5, -0.5, -1, -1, -2]
    ]),
    'K': np.array([
        [-3, -4, -4, -5, -5, -4, -4, -3],
        [-3, -4, -4, -5, -5, -4, -4, -3],
        [-3, -4, -4, -5, -5, -4, -4, -3],
        [-3, -4, -4, -5, -5, -4, -4, -3],
        [-2, -3, -3, -4, -4, -3, -3, -2],
        [-1, -2, -2, -2, -2, -2, -2, -1],
        [2, 2, 0, 0, 0, 0, 2, 2],
        [2, 3, 1, 0, 0, 1, 3, 2]
    ])
}

def evaluate_board(pieces, to_play):
    evaluation = 0
    for square, piece in pieces.items():
        color = piece[0]
        piece_type = piece[1]
        row = 8 - int(square[1])
        col = ord(square[0]) - ord('a')
        pst_value = piece_square_tables[piece_type].item((row, col)) if piece_type in piece_square_tables else 0

        if color == 'w':
            evaluation += piece_values[piece_type] + pst_value
        else:
            evaluation -= piece_values[piece_type] + pst_value
    return evaluation if to_play == 'white' else -evaluation


def generate_legal_moves(pieces, to_play):
    legal_moves = []

    def is_valid_move(start_square, end_square, promotion=''):
        if not (0 <= ord(end_square[0]) - ord('a') < 8 and 1 <= int(end_square[1]) <= 8):
            return False
        
        orig_piece = pieces.get(start_square)
        dest_piece = pieces.get(end_square)
        
        # Check for same color pieces
        if dest_piece and orig_piece[0] == dest_piece[0]:
            return False
        
        temp_pieces = pieces.copy()
        temp_pieces[end_square] = temp_pieces.pop(start_square)

        # Simulate the move and do not allow the player to check himself
        opponent_color = 'b' if to_play == 'white' else 'w'

        if is_check(temp_pieces, opponent_color):
            return False

        return True

    def is_check(pieces, color):
      king_square = None
      for square, piece in pieces.items():
        if piece == color + 'K':
          king_square = square
          break

      if not king_square:
        return False
        
      opponent_color = 'w' if color == 'b' else 'b' 
      for square, piece in pieces.items():
          if piece[0] == opponent_color:
              opponent_moves = piece_moves(square, piece, pieces, opponent_color == 'w')
              if king_square in opponent_moves:
                  return True

      return False
      
    def piece_moves(square, piece, pieces, white_to_move):
        moves = []
        row = int(square[1])
        col = square[0]
        
        def try_add_move(new_col, new_row):
            new_square = new_col + str(new_row)
            if 1 <= new_row <= 8 and 'a' <= new_col <= 'h':
                if new_square not in pieces or pieces[new_square][0] != piece[0]:
                    return new_square
            return None

        if piece[1] == 'P':
            direction = 1 if white_to_move else -1
            # Move one square forward
            new_row = row + direction
            new_square = col + str(new_row)
            if 1 <= new_row <= 8 and new_square not in pieces:
                moves.append(new_square)
                # Move two squares forward from starting position
                if row == (2 if white_to_move else 7):
                    new_row = row + 2 * direction
                    new_square = col + str(new_row)
                    if new_square not in pieces:
                        moves.append(new_square)

            # Capture diagonally
            new_col = chr(ord(col) + 1)
            new_square = new_col + str(row + direction)
            if 'a' <= new_col <= 'h' and 1 <= row + direction <= 8 and new_square in pieces and pieces[new_square][0] != piece[0]:
                moves.append(new_square)

            new_col = chr(ord(col) - 1)
            new_square = new_col + str(row + direction)
            if 'a' <= new_col <= 'h' and 1 <= row + direction <= 8 and new_square in pieces and pieces[new_square][0] != piece[0]:
                moves.append(new_square)
        elif piece[1] == 'N':
            knight_moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
            for dr, dc in knight_moves:
                new_row = row + dr
                new_col = chr(ord(col) + dc)
                new_square = new_col + str(new_row)
                if 'a' <= new_col <= 'h' and 1 <= new_row <= 8 and (new_square not in pieces or pieces[new_square][0] != piece[0]):
                    moves.append(new_square)
        elif piece[1] == 'B':
            directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
            for dr, dc in directions:
                for i in range(1, 8):
                    new_row = row + dr * i
                    new_col = chr(ord(col) + dc * i)
                    new_square = new_col + str(new_row)
                    if 'a' <= new_col <= 'h' and 1 <= new_row <= 8:
                        if new_square not in pieces:
                            moves.append(new_square)
                        else:
                            if pieces[new_square][0] != piece[0]:
                                moves.append(new_square)
                            break
                    else:
                        break
        elif piece[1] == 'R':
            directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
            for dr, dc in directions:
                for i in range(1, 8):
                    new_row = row + dr * i
                    new_col = chr(ord(col) + dc * i)
                    new_square = new_col + str(new_row)
                    if 'a' <= new_col <= 'h' and 1 <= new_row <= 8:
                        if new_square not in pieces:
                            moves.append(new_square)
                        else:
                            if pieces[new_square][0] != piece[0]:
                                moves.append(new_square)
                            break
                    else:
                        break
        elif piece[1] == 'Q':
            directions = [(1, 1), (1, -1), (-1, 1), (-1, -1), (1, 0), (-1, 0), (0, 1), (0, -1)]
            for dr, dc in directions:
                for i in range(1, 8):
                    new_row = row + dr * i
                    new_col = chr(ord(col) + dc * i)
                    new_square = new_col + str(new_row)
                    if 'a' <= new_col <= 'h' and 1 <= new_row <= 8:
                        if new_square not in pieces:
                            moves.append(new_square)
                        else:
                            if pieces[new_square][0] != piece[0]:
                                moves.append(new_square)
                            break
                    else:
                        break
        elif piece[1] == 'K':
            king_moves = [(1, 1), (1, -1), (-1, 1), (-1, -1), (1, 0), (-1, 0), (0, 1), (0, -1)]
            for dr, dc in king_moves:
                new_row = row + dr
                new_col = chr(ord(col) + dc)
                new_square = new_col + str(new_row)
                if 'a' <= new_col <= 'h' and 1 <= new_row <= 8 and (new_square not in pieces or pieces[new_square][0] != piece[0]):
                    moves.append(new_square)
            
            # Castling moves
            if to_play == 'white':
                king_start_square = 'e1'
                if square == king_start_square and piece == 'wK':
                    # Kingside castling
                    if pieces.get('f1') is None and pieces.get('g1') is None and pieces.get('h1') == 'wR':
                        if not is_check(pieces, 'w') and not is_check({**pieces, 'e1': None, 'f1': 'wK'}, 'w') and not is_check({**pieces, 'e1': None, 'g1': 'wK'}, 'w'):
                            moves.append('g1')
                    # Queenside castling
                    if pieces.get('d1') is None and pieces.get('c1') is None and pieces.get('b1') is None and pieces.get('a1') == 'wR':
                        if not is_check(pieces, 'w') and not is_check({**pieces, 'e1': None, 'd1': 'wK'}, 'w') and not is_check({**pieces, 'e1': None, 'c1': 'wK'}, 'w'):
                            moves.append('c1')
            else:
                king_start_square = 'e8'
                if square == king_start_square and piece == 'bK':
                    # Kingside castling
                    if pieces.get('f8') is None and pieces.get('g8') is None and pieces.get('h8') == 'bR':
                        if not is_check(pieces, 'b') and not is_check({**pieces, 'e8': None, 'f8': 'bK'}, 'b') and not is_check({**pieces, 'e8': None, 'g8': 'bK'}, 'b'):
                            moves.append('g8')
                    # Queenside castling
                    if pieces.get('d8') is None and pieces.get('c8') is None and pieces.get('b8') is None and pieces.get('a8') == 'bR':
                        if not is_check(pieces, 'b') and not is_check({**pieces, 'e8': None, 'd8': 'bK'}, 'b') and not is_check({**pieces, 'e8': None, 'c8': 'bK'}, 'b'):
                            moves.append('c8')

        valid_moves = []
        for end_square in moves:
            if is_valid_move(square, end_square):
                valid_moves.append(end_square)
        return valid_moves

    for square, piece in pieces.items():
        if piece[0] == ('w' if to_play == 'white' else 'b'):
            end_squares = piece_moves(square, piece, pieces, to_play == 'white')
            for end_square in end_squares:
                move_str = square + end_square
                
                if piece[1] == 'P' and (end_square[1] == '8' or end_square[1] == '1'):
                    legal_moves.append(move_str + 'q')
                    legal_moves.append(move_str + 'r')
                    legal_moves.append(move_str + 'b')
                    legal_moves.append(move_str + 'n')
                else:
                    legal_moves.append(move_str)
    return legal_moves


def minimax(pieces, to_play, depth, alpha, beta, maximizing_player, start_time, time_limit):
    if time.time() - start_time > time_limit:
        return 0, None

    legal_moves = generate_legal_moves(pieces, to_play)

    if depth == 0 or not legal_moves:
        return evaluate_board(pieces, 'white' if maximizing_player else 'black'), None

    if maximizing_player:
        max_eval = float('-inf')
        best_move = None

        #Move ordering (captures first)
        ordered_moves = sorted(legal_moves, key=lambda move: -piece_values.get(pieces.get(move[2:4])[1],0) if pieces.get(move[2:4]) else 0)

        for move in ordered_moves:
            new_pieces = pieces.copy()
            start_square = move[:2]
            end_square = move[2:4]
            piece = new_pieces[start_square]
            
            if len(move) > 4:
                new_pieces[end_square] = piece[0] + move[4].upper()  # Promotion
            else:
                new_pieces[end_square] = piece
            del new_pieces[start_square]

            eval, _ = minimax(new_pieces, 'black', depth - 1, alpha, beta, False, start_time, time_limit)
            
            if eval > max_eval:
                max_eval = eval
                best_move = move
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
            if time.time() - start_time > time_limit :
              break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        best_move = None

        #Move ordering
        ordered_moves = sorted(legal_moves, key=lambda move: piece_values.get(pieces.get(move[2:4])[1],0) if pieces.get(move[2:4]) else 0, reverse=True)

        for move in ordered_moves:
            new_pieces = pieces.copy()
            start_square = move[:2]
            end_square = move[2:4]
            piece = new_pieces[start_square]
            
            if len(move) > 4:
                new_pieces[end_square] = piece[0] + move[4].upper()  # Promotion
            else:
                new_pieces[end_square] = piece
            del new_pieces[start_square]

            eval, _ = minimax(new_pieces, 'white', depth - 1, alpha, beta, True, start_time, time_limit)

            if eval < min_eval:
                min_eval = eval
                best_move = move
            beta = min(beta, eval)
            if beta <= alpha:
                break
            if time.time() - start_time > time_limit:
              break
        return min_eval, best_move

def policy(pieces: dict[str, str], to_play: str) -> str:

    start_time = time.time()
    time_limit = 0.9

    legal_moves = generate_legal_moves(pieces, to_play)

    # 1. Checkmate detection.
    for move in legal_moves:
        new_pieces = pieces.copy()
        start_square = move[:2]
        end_square = move[2:4]
        piece = new_pieces[start_square]
        if len(move) > 4:
            new_pieces[end_square] = piece[0] + move[4].upper()
        else:
            new_pieces[end_square] = piece
        del new_pieces[start_square]

        opponent_to_play = 'black' if to_play == 'white' else 'white'
        if not generate_legal_moves(new_pieces, opponent_to_play):
            king_square = None
            opponent_color = 'b' if to_play == 'white' else 'w'
            for square, piece in new_pieces.items():
                if piece == opponent_color + 'K':
                    king_square = square
                    break
            if king_square and is_check(new_pieces, opponent_color):
                return move

    # 2. Minimax search.
    depth = 2
    best_eval, best_move = minimax(pieces, to_play, depth, float('-inf'), float('inf'), to_play == 'white', start_time, time_limit)
    if best_move:
      return best_move

    # 3. Capture high value piece
    for move in legal_moves:
        end_square = move[2:4]
        if end_square in pieces:
            captured_piece = pieces[end_square]
            if captured_piece[0] != ('w' if to_play == 'white' else 'b'):
                return move

    # 4. Return a legal move (avoid being disqualified)
    return legal_moves[0]

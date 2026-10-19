
import random

def evaluate_capture(pieces, move, to_play):
    """Evaluates the value of a capture."""
    target_square = move[2:4]
    if target_square in pieces:
        captured_piece = pieces[target_square]
        if captured_piece[0] != to_play[0]:  # Only consider captures of opponent's pieces
            piece_value = {'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'P': 1, 'K': 100}
            return piece_value.get(captured_piece[1], 0)  # Default to 0 if piece type is unknown
    return 0

def find_legal_moves(pieces, to_play):
    """Very basic move generator (no castling, en passant, etc.)
       Intended to be replaced by legal_moves received externally.
    """

    def get_piece_color(piece):
        return piece[0]
    
    def get_piece_type(piece):
        return piece[1]

    def algebraic_to_indices(square):
      col = ord(square[0]) - ord('a')
      row = int(square[1]) - 1
      return row, col

    def indices_to_algebraic(row, col):
      return chr(ord('a') + col) + str(row + 1)
    
    legal_moves = []
    color = 'w' if to_play == 'white' else 'b'
    opponent_color = 'b' if to_play == 'white' else 'w'

    for start_square, piece in pieces.items():
        if get_piece_color(piece) != color:
           continue
        
        start_row, start_col = algebraic_to_indices(start_square)

        if get_piece_type(piece) == 'P':
            # Pawn moves (simplified)
            direction = 1 if color == 'w' else -1
            new_row = start_row + direction

            # Move one square forward
            if 0 <= new_row < 8:
                new_square = indices_to_algebraic(new_row, start_col)
                if new_square not in pieces:
                   if new_row == 0 or new_row == 7: #promotion
                        legal_moves.extend([start_square + new_square + 'q', start_square + new_square + 'r', start_square + new_square + 'n', start_square + new_square + 'b'])
                   else:
                        legal_moves.append(start_square + new_square)
                
                # Capture diagonally (only if opponent is present)
                if start_col > 0:
                    new_col = start_col - 1
                    new_square = indices_to_algebraic(new_row, new_col)
                    if new_square in pieces and get_piece_color(pieces[new_square]) == opponent_color:
                        if new_row == 0 or new_row == 7:
                            legal_moves.extend([start_square + new_square + 'q', start_square + new_square + 'r', start_square + new_square + 'n', start_square + new_square + 'b'])
                        else:
                            legal_moves.append(start_square + new_square)   
                if start_col < 7:
                    new_col = start_col + 1
                    new_square = indices_to_algebraic(new_row, new_col)
                    if new_square in pieces and get_piece_color(pieces[new_square]) == opponent_color:
                         if new_row == 0 or new_row == 7:
                            legal_moves.extend([start_square + new_square + 'q', start_square + new_square + 'r', start_square + new_square + 'n', start_square + new_square + 'b'])
                         else:
                            legal_moves.append(start_square + new_square)

        elif get_piece_type(piece) == "R":  # Rook
            
            for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                for i in range(1, 8):
                    new_row, new_col = start_row + i*dr, start_col + i*dc
                    if not (0 <= new_row < 8 and 0 <= new_col < 8):
                        break
                    new_square = indices_to_algebraic(new_row, new_col)
                    if new_square in pieces:
                        if get_piece_color(pieces[new_square]) == color:
                            break  # Blocked by own piece
                        else:  # Capture opponent's piece
                            legal_moves.append(start_square + new_square)
                            break
                    else:
                        legal_moves.append(start_square + new_square)

        elif get_piece_type(piece) == "N": # Knight
             for dr, dc in [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]:
                new_row, new_col = start_row + dr, start_col + dc
                if  (0 <= new_row < 8 and 0 <= new_col < 8):
                    new_square = indices_to_algebraic(new_row, new_col)
                    if new_square in pieces:
                        if get_piece_color(pieces[new_square]) != color:
                              legal_moves.append(start_square + new_square)
                    else:
                        legal_moves.append(start_square + new_square)

        elif get_piece_type(piece) == "B": # Bishop
            for dr, dc in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
                for i in range(1, 8):
                    new_row, new_col = start_row + i*dr, start_col + i*dc
                    if not (0 <= new_row < 8 and 0 <= new_col < 8):
                        break
                    new_square = indices_to_algebraic(new_row, new_col)
                    if new_square in pieces:
                        if get_piece_color(pieces[new_square]) == color:
                            break  # Blocked by own piece
                        else:  # Capture opponent's piece
                            legal_moves.append(start_square + new_square)
                            break
                    else:
                        legal_moves.append(start_square + new_square)
        
        elif get_piece_type(piece) == "Q": # Queen
            for dr, dc in [(1, 1), (1, -1), (-1, 1), (-1, -1), (1, 0), (-1, 0), (0, 1), (0, -1)]:
                for i in range(1, 8):
                    new_row, new_col = start_row + i*dr, start_col + i*dc
                    if not (0 <= new_row < 8 and 0 <= new_col < 8):
                        break
                    new_square = indices_to_algebraic(new_row, new_col)
                    if new_square in pieces:
                        if get_piece_color(pieces[new_square]) == color:
                            break  # Blocked by own piece
                        else:  # Capture opponent's piece
                            legal_moves.append(start_square + new_square)
                            break
                    else:
                        legal_moves.append(start_square + new_square)
                        
        elif get_piece_type(piece) == "K":  # King
            for dr, dc in [(1, 1), (1, -1), (-1, 1), (-1, -1), (1, 0), (-1, 0), (0, 1), (0, -1)]:
                new_row, new_col = start_row + dr, start_col + dc
                if  (0 <= new_row < 8 and 0 <= new_col < 8):
                    new_square = indices_to_algebraic(new_row, new_col)
                    if new_square in pieces:
                        if get_piece_color(pieces[new_square]) != color:
                            legal_moves.append(start_square + new_square)
                    else:
                        legal_moves.append(start_square + new_square)
                
    return legal_moves

def policy(pieces: dict[str, str], to_play: str, memory: dict) -> tuple[str, dict]:
    """
    Selects the next move based on the given game state.
    """

    legal_moves = find_legal_moves(pieces, to_play)
    #legal_moves = ['f5e4', 'f5f4', 'g3d6', 'g3e1', 'g3e5', 'g3f2', 'g3f4', 'g3h2'] # For Testing the example
    
    if not legal_moves:
        return None, memory  # No legal moves available

    # 1. Check for winning moves (checkmate) - Not Implemented
    # 2. Check for Captures
    capture_moves = []
    for move in legal_moves:
        capture_value = evaluate_capture(pieces, move, to_play)
        if capture_value > 0:
            capture_moves.append((move, capture_value))

    if capture_moves:
        # Prioritize captures with higher value
        best_capture_move = max(capture_moves, key=lambda item: item[1])[0]
        return best_capture_move, memory

    # 3. King Safety - Not Implemented
    # 4. Pawn Promotion
    promotion_moves = [move for move in legal_moves if len(move) == 5]
    if promotion_moves:
        # Always promote to queen (simple strategy)
        for move in promotion_moves:
             if move[-1] == 'q':
                return move, memory
        return promotion_moves[0], memory

    # 5. Simple Move Selection (random)
    return random.choice(legal_moves), memory

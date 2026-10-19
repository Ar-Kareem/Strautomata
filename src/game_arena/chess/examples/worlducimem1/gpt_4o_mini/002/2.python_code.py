
def policy(pieces: dict[str, str], to_play: str, memory: dict) -> tuple[str, dict]:
    piece_values = {'K': 0, 'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'P': 1}
    king_positions = { 'w': None, 'b': None }
    legal_moves = []  # This will be populated with the legal moves passed to the function

    # Function to evaluate the state of the pieces
    def evaluate_board(pieces):
        value = 0
        for pos, piece in pieces.items():
            color = piece[0]
            piece_type = piece[1]
            value += piece_values[piece_type] if color == to_play[0] else -piece_values[piece_type]
        return value
    
    current_value = evaluate_board(pieces)

    # Evaluate possible responses and select the best legal move
    best_move = None
    best_value_change = float('-inf')

    # Basic evaluation logic for possible moves
    for move in pieces.get('legal_moves', []):
        from_square = move[:2]
        to_square = move[2:4]
        moved_piece = pieces.get(from_square, None)

        if moved_piece and moved_piece[0] == to_play[0]:
            # Make the move virtually
            captured_piece = pieces.get(to_square, None)
            temp_pieces = pieces.copy()

            if captured_piece:
                del temp_pieces[to_square]  # Remove captured piece
            
            temp_pieces[to_square] = moved_piece  # Move the piece
            del temp_pieces[from_square]  # Remove from original square
            
            # Evaluate the new board state
            new_value = evaluate_board(temp_pieces)
            value_change = new_value - current_value
            
            # Check if the move is better than the current best
            if value_change > best_value_change:
                best_value_change = value_change
                best_move = move

    # If no move is found (defensive fallback)
    return (best_move if best_move else legal_moves[0], memory)

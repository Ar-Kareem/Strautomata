
def policy(pieces: dict[str, str], to_play: str) -> str:
    # Define piece values for material evaluation
    piece_values = {
        'Q': 9,
        'R': 5,
        'B': 3,
        'N': 3,
        'P': 1,
        'K': 0  # King is priceless, but we don't want to capture it
    }

    # Determine the opponent's color
    opponent = 'black' if to_play == 'white' else 'white'
    my_color = 'w' if to_play == 'white' else 'b'
    opponent_color = 'b' if to_play == 'white' else 'w'

    # Generate all legal moves (this is a placeholder; in practice, you'd need to generate legal moves)
    # For the sake of this example, assume legal_moves is provided or generated elsewhere
    # Here, we'll assume legal_moves is a list of UCI move strings
    legal_moves = generate_legal_moves(pieces, to_play)  # Placeholder function

    # Step 1: Check for checkmate
    for move in legal_moves:
        # Simulate the move and check if it results in checkmate
        new_pieces = simulate_move(pieces, move)
        if is_checkmate(new_pieces, opponent):
            return move

    # Step 2: Prioritize captures
    captures = []
    for move in legal_moves:
        # Check if the move is a capture
        if is_capture(pieces, move):
            # Evaluate the value of the captured piece
            captured_piece = get_captured_piece(pieces, move)
            if captured_piece:
                value = piece_values.get(captured_piece[1], 0)
                captures.append((move, value))

    if captures:
        # Return the capture with the highest value
        captures.sort(key=lambda x: x[1], reverse=True)
        return captures[0][0]

    # Step 3: Prioritize king safety (castling or moving king away from threats)
    king_safety_moves = []
    for move in legal_moves:
        if is_castling(move) or is_king_move(pieces, move, my_color):
            king_safety_moves.append(move)

    if king_safety_moves:
        return king_safety_moves[0]  # Simple heuristic: pick the first one

    # Step 4: Default to central control and piece development
    # Assign a score to each move based on central control and development
    move_scores = []
    for move in legal_moves:
        score = evaluate_move(pieces, move, my_color)
        move_scores.append((move, score))

    if move_scores:
        move_scores.sort(key=lambda x: x[1], reverse=True)
        return move_scores[0][0]

    # Fallback: return the first legal move if no other criteria apply
    return legal_moves[0]

# Placeholder functions (these would need to be implemented)
def generate_legal_moves(pieces, to_play):
    # In a real implementation, this would generate all legal moves for the current position
    # For this example, we'll assume it's provided or generated elsewhere
    return []  # Replace with actual legal moves

def simulate_move(pieces, move):
    # Simulate the move and return the new board state
    new_pieces = pieces.copy()
    # Update the board state based on the move
    # This is a simplified placeholder
    return new_pieces

def is_checkmate(pieces, opponent):
    # Check if the opponent is in checkmate
    # This is a simplified placeholder
    return False

def is_capture(pieces, move):
    # Check if the move is a capture
    # This is a simplified placeholder
    return False

def get_captured_piece(pieces, move):
    # Return the piece that is captured by the move
    # This is a simplified placeholder
    return None

def is_castling(move):
    # Check if the move is a castling move
    # This is a simplified placeholder
    return False

def is_king_move(pieces, move, my_color):
    # Check if the move is a king move
    # This is a simplified placeholder
    return False

def evaluate_move(pieces, move, my_color):
    # Evaluate the move based on central control and development
    # This is a simplified placeholder
    return 0

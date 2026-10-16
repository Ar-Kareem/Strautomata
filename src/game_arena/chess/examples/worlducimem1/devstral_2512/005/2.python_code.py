
def policy(pieces: dict[str, str], to_play: str, memory: dict) -> tuple[str, dict]:
    # Initialize memory if empty
    if 'move_count' not in memory:
        memory['move_count'] = 0
    memory['move_count'] += 1

    # Get legal moves (this would be provided in the actual implementation)
    # For this example, we'll assume legal_moves is available
    legal_moves = get_legal_moves(pieces, to_play)  # This function would be provided

    # Piece values for material evaluation
    piece_values = {
        'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0
    }

    # Evaluate each move
    best_move = None
    best_score = -float('inf')

    for move in legal_moves:
        # Simulate the move
        new_pieces = simulate_move(pieces, move)

        # Evaluate the position
        score = evaluate_position(new_pieces, to_play, piece_values)

        # Update best move if this is better
        if score > best_score:
            best_score = score
            best_move = move

    # If no move found (shouldn't happen as legal_moves is provided), return first move
    if best_move is None and legal_moves:
        best_move = legal_moves[0]

    return (best_move, memory)

def get_legal_moves(pieces: dict[str, str], to_play: str) -> list[str]:
    """
    This function would be provided by the environment.
    For this example, we'll return a mock list of legal moves.
    """
    # In a real implementation, this would be provided by the chess environment
    return ['e2e4', 'd2d4', 'g1f3', 'b1c3']  # Example moves

def simulate_move(pieces: dict[str, str], move: str) -> dict[str, str]:
    """
    Simulate a move on the board.
    Returns a new pieces dictionary with the move applied.
    """
    new_pieces = pieces.copy()

    # Parse the move
    from_sq = move[:2]
    to_sq = move[2:4]
    promotion = move[4:] if len(move) > 4 else None

    # Get the moving piece
    piece = new_pieces.get(from_sq, None)
    if piece is None:
        return new_pieces  # Invalid move, return original

    # Remove the piece from the original square
    del new_pieces[from_sq]

    # Handle promotion
    if promotion and piece[1] == 'P':
        # Promotion piece is the last character of the move
        promoted_piece = piece[0] + promotion.upper()
        new_pieces[to_sq] = promoted_piece
    else:
        # Normal move
        new_pieces[to_sq] = piece

    return new_pieces

def evaluate_position(pieces: dict[str, str], to_play: str, piece_values: dict) -> float:
    """
    Evaluate the position based on material and basic positional factors.
    """
    score = 0

    # Material evaluation
    for square, piece in pieces.items():
        color = piece[0]
        piece_type = piece[1]

        # Add material value
        value = piece_values.get(piece_type, 0)
        if color == 'w':
            score += value
        else:
            score -= value

    # Simple positional evaluation (center control)
    center_squares = ['d4', 'e4', 'd5', 'e5']
    for square in center_squares:
        if square in pieces:
            piece = pieces[square]
            if piece[0] == 'w':
                score += 0.1
            else:
                score -= 0.1

    # Return score from the perspective of the player to move
    return score if to_play == 'white' else -score

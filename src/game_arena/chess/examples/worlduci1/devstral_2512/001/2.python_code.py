
def policy(pieces: dict[str, str], to_play: str) -> str:
    # Define piece values for material evaluation
    piece_values = {
        'P': 1,
        'N': 3,
        'B': 3,
        'R': 5,
        'Q': 9,
        'K': 0  # King's value is not considered in material evaluation
    }

    # Determine the opponent's color
    opponent_color = 'b' if to_play == 'white' else 'w'

    # Generate all legal moves (this is a placeholder; in a real scenario, legal_moves would be provided)
    # For the purpose of this example, we assume legal_moves is provided as a global variable or passed in
    # Here, we simulate legal_moves as a list of possible moves
    legal_moves = generate_legal_moves(pieces, to_play)  # This function is not implemented here

    # Evaluate each move
    best_move = None
    best_score = -float('inf')

    for move in legal_moves:
        # Simulate the move
        new_pieces = simulate_move(pieces, move, to_play)

        # Evaluate the new position
        score = evaluate_position(new_pieces, to_play, opponent_color, piece_values)

        # Update the best move if this move has a higher score
        if score > best_score:
            best_score = score
            best_move = move

    # If no move is found (should not happen as legal_moves is non-empty), return the first legal move
    return best_move if best_move is not None else legal_moves[0]

def generate_legal_moves(pieces: dict[str, str], to_play: str) -> list[str]:
    # This is a placeholder function. In a real scenario, legal moves would be provided.
    # For the purpose of this example, we return a list of possible moves.
    # In practice, you would use a chess library or implement move generation logic.
    return ['e2e4', 'd2d4', 'g1f3']  # Example moves

def simulate_move(pieces: dict[str, str], move: str, to_play: str) -> dict[str, str]:
    # This is a placeholder function to simulate a move.
    # In a real scenario, you would update the pieces dictionary based on the move.
    new_pieces = pieces.copy()
    # Example: move 'e2e4' would update the pieces dictionary accordingly
    return new_pieces

def evaluate_position(pieces: dict[str, str], to_play: str, opponent_color: str, piece_values: dict[str, int]) -> int:
    # Evaluate the position based on material and other factors
    score = 0

    # Material evaluation
    for square, piece in pieces.items():
        color = piece[0]
        piece_type = piece[1]
        if color == ('w' if to_play == 'white' else 'b'):
            score += piece_values[piece_type]
        else:
            score -= piece_values[piece_type]

    # Additional evaluations can be added here, such as king safety, piece activity, etc.
    return score

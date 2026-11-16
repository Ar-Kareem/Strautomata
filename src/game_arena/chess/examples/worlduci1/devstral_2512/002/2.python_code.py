
def policy(pieces: dict[str, str], to_play: str) -> str:
    # Define piece values for material evaluation
    piece_values = {
        'Q': 9,
        'R': 5,
        'B': 3,
        'N': 3,
        'P': 1,
        'K': 0  # King is invaluable, but we don't want to trade it
    }

    # Determine the opponent's color
    opponent_color = 'b' if to_play == 'white' else 'w'
    my_color = 'w' if to_play == 'white' else 'b'

    # Get all legal moves (this would be provided in the actual environment)
    # For the sake of this example, we assume legal_moves is provided
    legal_moves = get_legal_moves(pieces, to_play)  # Placeholder function

    # Evaluate each legal move
    best_move = None
    best_score = -float('inf')

    for move in legal_moves:
        # Simulate the move
        new_pieces = simulate_move(pieces, move)

        # Check if the move results in checkmate (simplified for example)
        if is_checkmate(new_pieces, opponent_color):
            return move  # Prioritize checkmate

        # Evaluate material advantage
        material_score = evaluate_material(new_pieces, my_color, opponent_color, piece_values)

        # Evaluate positional advantage (simplified for example)
        positional_score = evaluate_position(new_pieces, my_color)

        # Combine scores (weights can be adjusted)
        total_score = material_score + 0.5 * positional_score

        # Update best move if this move is better
        if total_score > best_score:
            best_score = total_score
            best_move = move

    return best_move if best_move else legal_moves[0]  # Fallback to first legal move if no best move found

# Placeholder functions (these would be implemented in the actual environment)
def get_legal_moves(pieces: dict[str, str], to_play: str) -> list[str]:
    # In the actual environment, this would be provided
    return ['f5e4', 'f5f4', 'g3d6', 'g3e1', 'g3e5', 'g3f2', 'g3f4', 'g3h2']

def simulate_move(pieces: dict[str, str], move: str) -> dict[str, str]:
    # Simulate the move and return the new board state
    new_pieces = pieces.copy()
    # Update the board state based on the move
    # This is a simplified example; actual implementation would handle captures, promotions, etc.
    return new_pieces

def is_checkmate(pieces: dict[str, str], color: str) -> bool:
    # Check if the given color is in checkmate
    # Simplified for example
    return False

def evaluate_material(pieces: dict[str, str], my_color: str, opponent_color: str, piece_values: dict[str, int]) -> float:
    # Calculate material advantage
    my_material = 0
    opponent_material = 0
    for piece in pieces.values():
        if piece[0] == my_color:
            my_material += piece_values.get(piece[1], 0)
        elif piece[0] == opponent_color:
            opponent_material += piece_values.get(piece[1], 0)
    return my_material - opponent_material

def evaluate_position(pieces: dict[str, str], my_color: str) -> float:
    # Evaluate positional advantage (simplified for example)
    # This could include center control, piece development, king safety, etc.
    return 0.0

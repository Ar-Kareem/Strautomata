
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    # Helper function to evaluate the significance of a move
    def evaluate_move(move):
        # Check if the move is a check or checkmate
        if 'x' in move:
            return 2  # Priority for capturing
        if '+' in move or 'checkmate' in move:
            return 3  # High priority for check/checkmate
        if '=' in move:
            return 4  # Priority for promotion
        return 1  # Default

    # Identify the best move
    best_move = None
    best_value = 0

    for move in legal_moves:
        move_value = evaluate_move(move)

        # Select the best move based on evaluation
        if move_value > best_value:
            best_value = move_value
            best_move = move

    return best_move


def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    def is_checkmate(move):
        # Check if the move results in checkmate (not fully implemented here)
        # Placeholder for checkmate logic (requires understanding of the game state)
        return False

    def evaluate_capture(move):
        # Basic logic for evaluating material captured by a move
        piece_val = {
            'K': 0, 'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9
        }
        if 'x' in move:
            target_piece = move[move.index('x') + 1] if move.index('x') + 1 < len(move) else ''
            if target_piece in pieces.values():
                return piece_val.get(target_piece[1], 0)  # Value of the captured piece
        return 0

    # Check for immediate checkmate moves
    for move in legal_moves:
        if is_checkmate(move):
            return move

    # Evaluate captures
    best_capture = None
    max_capture_value = -1
    for move in legal_moves:
        capture_value = evaluate_capture(move)
        if capture_value > max_capture_value:
            max_capture_value = capture_value
            best_capture = move

    if best_capture:
        return best_capture

    # Placeholder for king safety and threat prevention logic
    # ... (Add checks and logic to evaluate king safety and prevent threats)

    # Select a positional move as a fallback
    return legal_moves[0]  # Just take the first legal move for now

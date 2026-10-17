
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    # Define a basic value system for pieces
    piece_values = {
        'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0
    }
    
    # Define a function to evaluate the potential outcomes of moves
    def evaluate_move(move: str) -> int:
        score = 0
        
        # Check if the move is a capture
        if 'x' in move:
            target_square = move[-2:]
            captured_piece = pieces.get(target_square, None)
            if captured_piece:
                piece_type = captured_piece[1]  # Get the type (ignore color)
                score += piece_values.get(piece_type, 0)

        # Check if the move puts the opponent in check (not for evaluation, but we want to prefer it)
        if '+' in move or 'x' not in move and 'O-O' not in move and 'O-O-O' not in move:
            score += 10  # Arbitrary score for giving check

        # Additional checks can be implemented for king safety, etc.
        
        return score

    # Start with a basic checking mechanism for the best move
    best_move = None
    best_score = -1  # Scores below 0 are considered bad

    for move in legal_moves:
        move_score = evaluate_move(move)

        # Update best move found
        if move_score > best_score:
            best_score = move_score
            best_move = move
    
    # If no moves are suitable, fallback to the first legal move (shouldn't happen)
    if not best_move:
        best_move = legal_moves[0]

    return best_move, memory

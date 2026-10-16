
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    value_map = {
        'P': 1,
        'N': 3,
        'B': 3,
        'R': 5,
        'Q': 9,
        'K': float('inf'),  # King is invaluable
    }
    
    def evaluate_move(move):
        if 'x' in move:  # Capture
            target_square = move[move.index('x') + 1:move.index('x') + 3]
            if target_square in pieces:
                target_piece = pieces[target_square]
                if target_piece[0] != to_play[0]:  # Different color
                    return value_map[target_piece[1]]  # Return piece value
        return 0  # No value for non-captures

    # Check for check or checkmate moves first
    for move in legal_moves:
        if '+' in move or '=' in move or 'mate' in move:
            return move, memory

    # Evaluate other moves for their value
    move_values = []
    for move in legal_moves:
        move_value = evaluate_move(move)
        move_values.append((move, move_value))

    # Sort moves by value (descending) and prioritize capturing moves
    move_values.sort(key=lambda x: x[1], reverse=True)

    # Choose the best available move
    best_move = move_values[0][0]
    
    return best_move, memory

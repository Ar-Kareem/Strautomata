
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    # Define material values for pieces
    piece_values = {
        'P': 1,
        'N': 3,
        'B': 3,
        'R': 5,
        'Q': 9,
        'K': 0,  # King is invaluable
    }

    trying_win = []
    trying_promotion = []
    trying_capture = []
    trying_safe = []
    
    def evaluate_move(move):
        # Analyze the move
        # Check if the move is a promotion
        if '=' in move:
            return 10  # Promotion is highest priority
        if 'x' in move:  # It's a capture
            target_square = move[-2:]  # Get the target square
            if target_square in pieces:
                target_piece = pieces[target_square]
                if target_piece[0] != to_play[0]:  # It's an enemy piece
                    return piece_values[target_piece[1]]  # Return its value
        return 0   # Not a capture or promotion

    # Evaluate moves
    for move in legal_moves:
        if 'mate' in move:  # This would indicate checkmate
            return move, memory  # If checkmate is found, return immediately

        move_value = evaluate_move(move)
        if move_value == 10:
            trying_promotion.append(move)
        elif move_value > 0:
            trying_capture.append((move, move_value))
        else:
            trying_safe.append(move)

    if trying_promotion:
        return trying_promotion[0], memory  # Return the first promotion move

    if trying_capture:
        best_capture = max(trying_capture, key=lambda x: x[1])
        return best_capture[0], memory  # Return the most valuable capture

    # If no promotions or captures, return a safe move
    if trying_safe:
        return trying_safe[0], memory  # Return the first safe move

    # Fallback - return any legal move if nothing else matches
    return legal_moves[0], memory

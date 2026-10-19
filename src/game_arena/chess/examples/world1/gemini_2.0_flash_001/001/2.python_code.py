
import random

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    """
    Selects a move from the given legal moves based on a simple policy.
    """

    def material_value(piece_type: str) -> int:
        """Assigns a material value to each piece."""
        if piece_type == 'Q':
            return 9
        elif piece_type == 'R':
            return 5
        elif piece_type == 'B':
            return 3
        elif piece_type == 'N':
            return 3
        elif piece_type == 'P':
            return 1
        else:
            return 0  # King or empty square


    # 1. Checkmate detection
    for move in legal_moves:
        if '#' in move:
            return move

    # 2. Check detection
    for move in legal_moves:
        if '+' in move:
            return move

    # 3. Material advantage (captures)
    best_capture_move = None
    best_capture_value = -1

    for move in legal_moves:
        if 'x' in move:
            # Determine the captured piece type.  Simple parsing based on the move string.
            captured_piece_type = move[move.find('x') + 1]

            # Handling pawn promotions that look like captures, and other moves where the piece is not immediately next to 'x'.
            if '=' in move :
                continue # ignore promotions
            if captured_piece_type.islower():
                captured_piece_type = 'P'
            piece_value = material_value(captured_piece_type.upper())
            if piece_value > best_capture_value:
                best_capture_value = piece_value
                best_capture_move = move

    if best_capture_move:
        return best_capture_move
     
    # 4. Pawn promotion
    for move in legal_moves:
        if "=" in move:
            return move


    # 5. Random move (fallback)
    return random.choice(legal_moves)


import random

def value(piece):
    if piece == 'Q':
        return 9
    elif piece == 'R':
        return 5
    elif piece == 'B':
        return 3
    elif piece == 'N':
        return 3
    elif piece == 'P':
        return 1
    elif piece == 'K':
        return 0  # King has no material value in this context
    return 0

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    """
    Selects the next move based on a simple policy.
    """

    best_move = None
    best_value = -10000 if to_play == 'white' else 10000 # Initialize with a very bad score

    for move in legal_moves:
        # 1. Checkmate (Simplified - just look for # in the move string)
        if '#' in move:
            return move, memory

        # 2. Captures
        capture_value = 0
        if 'x' in move:
            captured_piece = move.split('x')[-1][0].upper()  # Extract captured piece type (assuming it's before promotion if present)
            capture_value = value(captured_piece)

        # 3. Checks
        check_value = 0
        if '+' in move:
            check_value = 0.5 # slight preference for checks

        move_value = capture_value + check_value

        if to_play == 'white':
             if move_value > best_value:
                best_value = move_value
                best_move = move
        else:
            if move_value > best_value: # Same code will work for black or white
                best_value = move_value
                best_move = move

    if best_move:
        return best_move, memory


    # Default: If no capture or check, pick a random legal move
    return random.choice(legal_moves), memory

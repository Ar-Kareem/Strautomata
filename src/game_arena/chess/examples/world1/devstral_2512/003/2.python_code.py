
import random

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    # Determine the color to play
    color = 'w' if to_play == 'white' else 'b'

    # Define piece values for material evaluation
    piece_values = {'K': 0, 'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'P': 1}

    # Categorize moves
    checkmate_moves = []
    capture_moves = []
    castling_moves = []
    other_moves = []

    for move in legal_moves:
        # Check for checkmate (indicated by '#' in the move string)
        if '#' in move:
            checkmate_moves.append(move)
        # Check for captures (indicated by 'x' in the move string)
        elif 'x' in move:
            capture_moves.append(move)
        # Check for castling
        elif move in ['O-O', 'O-O-O']:
            castling_moves.append(move)
        else:
            other_moves.append(move)

    # If there's a checkmate move, return it immediately
    if checkmate_moves:
        return random.choice(checkmate_moves)

    # If there are capture moves, evaluate them based on material gain
    if capture_moves:
        # Find the best capture move
        best_capture = None
        best_value = -1
        for move in capture_moves:
            # Extract the captured piece (the part after 'x')
            captured_part = move.split('x')[1]
            # The captured piece is the first character of the captured_part
            captured_piece = captured_part[0]
            # Get the value of the captured piece
            value = piece_values.get(captured_piece, 0)
            if value > best_value:
                best_value = value
                best_capture = move
        return best_capture

    # If there are castling moves, return one of them
    if castling_moves:
        return random.choice(castling_moves)

    # If none of the above, return a random move
    return random.choice(other_moves)

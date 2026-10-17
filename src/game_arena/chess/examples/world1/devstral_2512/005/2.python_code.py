
import random

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    # Define piece values for material evaluation
    piece_values = {
        'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0
    }

    # Determine the opponent's color
    opponent = 'black' if to_play == 'white' else 'white'

    # Initialize best move and best score
    best_move = None
    best_score = -float('inf')

    for move in legal_moves:
        score = 0

        # Check for checkmate (highest priority)
        if '#' in move:
            return move

        # Check for check (second priority)
        if '+' in move:
            score += 100

        # Check for captures (third priority)
        if 'x' in move:
            # Extract the captured piece (if any)
            captured_piece = None
            if len(move) > 2 and move[1] == 'x':
                # Handle cases like 'Bxf5' or 'Nxf5'
                captured_piece = move[2:3]
            elif len(move) > 3 and move[2] == 'x':
                # Handle cases like 'Nec3' (not a capture)
                pass
            else:
                # Handle pawn captures like 'exd5'
                if len(move) > 3 and move[1] == 'x':
                    captured_piece = move[2:3]

            if captured_piece:
                # Get the full piece code (color + type)
                # Find the square being captured (last 2 characters)
                target_square = move[-2:]
                if target_square in pieces:
                    captured_piece_full = pieces[target_square]
                    if captured_piece_full[0] == opponent[0]:
                        # Calculate material gain
                        captured_value = piece_values.get(captured_piece_full[1], 0)
                        score += captured_value * 10

        # Prefer moves that develop pieces (e.g., moving knights and bishops from back rank)
        if len(move) >= 2 and move[0] in ['N', 'B'] and move[1:].lower() not in ['a1', 'b1', 'c1', 'd1', 'e1', 'f1', 'g1', 'h1',
                                                                                 'a8', 'b8', 'c8', 'd8', 'e8', 'f8', 'g8', 'h8']:
            score += 1

        # Prefer central moves (e4, d4, e5, d5)
        if len(move) >= 2:
            target_square = move[-2:]
            if target_square in ['e4', 'd4', 'e5', 'd5']:
                score += 1

        # Update best move if current move has higher score
        if score > best_score:
            best_score = score
            best_move = move

    # If no move is selected (unlikely), return a random legal move
    if best_move is None:
        return random.choice(legal_moves)

    return best_move

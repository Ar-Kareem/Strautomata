
import random

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    # Initialize memory if empty
    if 'material' not in memory:
        memory['material'] = {'w': 0, 'b': 0}
        memory['piece_values'] = {'K': 0, 'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'P': 1}

    # Update material balance
    current_material = {'w': 0, 'b': 0}
    for square, piece in pieces.items():
        color = piece[0]
        piece_type = piece[1]
        current_material[color] += memory['piece_values'][piece_type]
    memory['material'] = current_material

    # Helper function to evaluate move
    def evaluate_move(move):
        score = 0
        # Check for checkmate
        if '#' in move:
            return float('inf')
        # Check for check
        if '+' in move:
            score += 1
        # Check for capture
        if 'x' in move:
            # Extract captured piece (e.g., 'Bxf5' -> 'f5' is the target square)
            if '=' in move:  # Promotion with capture (e.g., 'b8=Q')
                target_square = move.split('=')[0][-2:]
            else:
                target_square = move.split('x')[-1]
            if target_square in pieces:
                captured_piece = pieces[target_square]
                if captured_piece[0] != to_play[0]:  # Opponent's piece
                    score += memory['piece_values'][captured_piece[1]]
        # Check for promotion
        if '=' in move:
            score += memory['piece_values']['Q']  # Assume promotion to Queen
        # Check for castling
        if move in ['O-O', 'O-O-O']:
            score += 2  # Castling is generally good
        # Check for central control (e4, d4, e5, d5)
        central_squares = ['e4', 'd4', 'e5', 'd5']
        if move[-2:] in central_squares:
            score += 0.5
        return score

    # Evaluate all moves
    move_scores = []
    for move in legal_moves:
        score = evaluate_move(move)
        move_scores.append((move, score))

    # Sort moves by score (descending)
    move_scores.sort(key=lambda x: x[1], reverse=True)

    # Select the best move (or random if multiple have same score)
    best_moves = [move for move, score in move_scores if score == move_scores[0][1]]
    chosen_move = random.choice(best_moves)

    return chosen_move, memory

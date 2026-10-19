
import random

piece_values = {
    'K': 0,
    'Q': 9,
    'R': 5,
    'B': 3,
    'N': 3,
    'P': 1
}

def policy(pieces, to_play, legal_moves, memory):
    # Update the move count in memory
    if 'move_count' not in memory:
        memory['move_count'] = 0
    memory['move_count'] += 1

    best_moves = []
    best_score = -float('inf')

    for move in legal_moves:
        score = 0
        # Check for mate
        if move.endswith('#'):
            score += 1000
        # Check for check
        elif '+' in move:
            score += 400
        # Check for castling
        if move.startswith('O-O') or move.startswith('O-O-O'):
            score += 50
        # Check for promotion
        if '=' in move:
            score += 100
        # Check for pawn move (non-capture)
        if move and move[0].islower():
            if 'x' not in move:
                score += 5
        # Check for capture
        if 'x' in move:
            # Clean the move string to find the destination square
            clean_move = move.replace('+', '').replace('#', '').replace('=', '')
            if len(clean_move) >= 2:
                dest_square = clean_move[-2:]
                captured_piece = pieces.get(dest_square)
                if captured_piece:
                    piece_type = captured_piece[1]
                    if piece_type in piece_values:
                        score += piece_values[piece_type] * 500

        # Compare scores to find best moves
        if score > best_score:
            best_score = score
            best_moves = [move]
        elif score == best_score:
            best_moves.append(move)

    # Choose a random move from the best moves
    chosen_move = random.choice(best_moves)

    return chosen_move, memory

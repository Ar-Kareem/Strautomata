
import random
from collections import defaultdict

# Piece values for evaluation
PIECE_VALUES = {
    'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0
}

def evaluate_move(move, pieces, to_play):
    """Evaluate a move based on material gain/loss and other factors"""
    score = 0
    color = 'w' if to_play == 'white' else 'b'

    # Check for captures
    if 'x' in move:
        # Extract the captured piece (after 'x' and before any other notation)
        parts = move.split('x')
        if len(parts) > 1:
            captured_square = parts[1].split('+')[0].split('#')[0].split('=')[0]
            if captured_square in pieces:
                captured_piece = pieces[captured_square]
                if captured_piece[0] != color:  # Only count if capturing opponent's piece
                    score += PIECE_VALUES[captured_piece[1]] * 10  # High weight for captures

    # Check for promotions
    if '=' in move:
        promotion_piece = move.split('=')[1]
        score += PIECE_VALUES[promotion_piece] * 5  # High weight for promotions

    # Check for checks
    if '+' in move:
        score += 1  # Small bonus for giving check

    # Check for castling (good for king safety)
    if move in ['O-O', 'O-O-O']:
        score += 2

    return score

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    # Initialize memory if empty
    if not memory:
        memory = {
            'move_count': 0,
            'game_phase': 'opening'  # opening, middlegame, endgame
        }

    memory['move_count'] += 1

    # Update game phase based on move count
    if memory['move_count'] < 20:
        memory['game_phase'] = 'opening'
    elif memory['move_count'] < 40:
        memory['game_phase'] = 'middlegame'
    else:
        memory['game_phase'] = 'endgame'

    color = 'w' if to_play == 'white' else 'b'
    opponent_color = 'b' if to_play == 'white' else 'w'

    # First check for checkmate moves
    checkmate_moves = [move for move in legal_moves if '#' in move]
    if checkmate_moves:
        return (random.choice(checkmate_moves), memory)

    # Evaluate all moves
    move_scores = []
    for move in legal_moves:
        score = evaluate_move(move, pieces, to_play)

        # Additional considerations based on game phase
        if memory['game_phase'] == 'opening':
            # In opening, prefer developing moves (knights and bishops to central squares)
            if move[0] in ['N', 'B'] and len(move) == 3 and move[1:3] in ['c3', 'f3', 'c6', 'f6']:
                score += 1

        # Avoid moves that might expose king (simple heuristic)
        if move[0] == 'K' and len(move) == 3:
            # Check if moving king to a square that might be dangerous
            # (This is a very simple heuristic - in a real engine we'd do proper attack detection)
            score -= 0.5

        move_scores.append((move, score))

    # Sort moves by score (descending)
    move_scores.sort(key=lambda x: x[1], reverse=True)

    # Get the best moves (top 3 to add some variety)
    best_moves = [move for move, score in move_scores[:3]]

    # Choose randomly among best moves to add some unpredictability
    chosen_move = random.choice(best_moves)

    return (chosen_move, memory)

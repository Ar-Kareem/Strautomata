
import random

def evaluate_move(move, pieces, to_play):
    """Evaluates a chess move based on material gain."""
    piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 100}
    score = 0
    if 'x' in move:
        captured_piece = move.split('x')[-1][0].upper()
        if captured_piece in piece_values:
            score += piece_values[captured_piece]

    # Simple checkmate detection (doesn't fully validate)
    if '#' in move:
        score = 1000

    # Simple check detection
    if '+' in move:
        score += 0.5 # Small bonus for checks

    return score


def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    """
    Selects a chess move from the list of legal moves based on a simple evaluation.
    """

    best_move = None
    best_score = -float('inf')

    # Check for immediate checkmate avoidance (very basic)
    for move in legal_moves:
        if '#' in move:
            return (move, memory)

    #Opening Book
    opening_book = {
        ('white', 0): 'e4',
        ('white', 1): 'Nf3',
        ('white', 2): 'd4',
        ('black', 0): 'e5',
        ('black', 1): 'Nc6',
        ('black', 2): 'd5'
    }

    turn_count = memory.get('turn_count', 0)

    if (to_play, turn_count) in opening_book and opening_book[(to_play, turn_count)] in legal_moves:
        action = opening_book[(to_play, turn_count)]
        memory['turn_count'] = turn_count + 1
        return (action, memory)

    for move in legal_moves:
        score = evaluate_move(move, pieces, to_play)
        if score > best_score:
            best_score = score
            best_move = move

    if best_move:
        return (best_move, memory)
    else:
        # If no tactical advantages, choose a random legal move.
        return (random.choice(legal_moves), memory)

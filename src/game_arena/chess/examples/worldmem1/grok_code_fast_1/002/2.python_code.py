
import random
from collections import defaultdict

piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}

def parse_to_sq(move):
    if '=' in move:
        parts = move.split('=')
        return parts[0][-2:]
    elif move in ['O-O', 'O-O-O']:
        return None
    else:
        return move[-2:]

def move_score(move, pieces, to_play):
    if move in ['O-O', 'O-O-O']:
        # Prioritize castling for king safety
        return 10.0
    if '=' in move:
        if move.endswith('=Q'):
            return 9.0
        else:
            return 1.0
    to_sq = parse_to_sq(move)
    if to_sq is None:
        return 0.0
    captured = pieces.get(to_sq, None)
    if captured:
        cap_value = piece_values[captured[1]]
        return cap_value
    else:
        # Non-capture: bonus for pawn advances
        if len(move) == 2 and move[0].islower():
            rank = int(move[1])
            if (to_play == 'white' and rank >= 4) or (to_play == 'black' and rank <= 5):
                return 0.1
        return 0.0

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    random.seed(42)  # Deterministic randomness
    if not legal_moves:
        return random.choice(legal_moves), memory  # Shouldn't happen
    # Compute scores
    move_scores = {}
    for move in legal_moves:
        score = move_score(move, pieces, to_play)
        move_scores[move] = score
    # Find max score
    max_score = max(move_scores.values())
    # Get moves with max score
    best_moves = [m for m, s in move_scores.items() if s == max_score]
    # Select randomly among ties
    chosen_move = random.choice(best_moves)
    return chosen_move, memory

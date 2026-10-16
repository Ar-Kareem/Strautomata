
import random

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    if not legal_moves:
        raise ValueError("No legal moves provided")
    
    # Assign scores to moves
    def score_move(move: str) -> int:
        score = 0
        if move.endswith('#'):
            score += 1000  # Highest priority for mate
        elif move.endswith('+'):
            score += 100   # Second priority for check
        if 'x' in move:
            score += 10    # Bonus for capture
        if 'O-O' in move:
            score += 1     # Small bonus for castling
        return score
    
    # Get scores for all moves
    scored_moves = [(score_move(m), m) for m in legal_moves]
    
    # Find the max score
    max_score = max(scored_moves, key=lambda x: x[0])[0]
    
    # Select moves with max score
    best_moves = [m for s, m in scored_moves if s == max_score]
    
    # Return a random one among the best
    return random.choice(best_moves)

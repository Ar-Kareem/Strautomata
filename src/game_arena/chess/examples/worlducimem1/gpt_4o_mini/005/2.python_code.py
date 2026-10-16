
def policy(pieces: dict[str, str], to_play: str, memory: dict) -> tuple[str, dict]:
    import numpy as np
    
    piece_values = {
        'P': 1,
        'N': 3,
        'B': 3,
        'R': 5,
        'Q': 9,
        'K': 0  # King value is usually not assigned as we don't capture it
    }
    
    def evaluate_move(move):
        from_square = move[:2]
        to_square = move[2:4]
        piece = pieces.get(from_square, '')
        target_piece = pieces.get(to_square, '')

        score = 0

        if target_piece:  # If it captures an opponent piece
            target_value = piece_values.get(target_piece[1], 0)
            score += target_value  # Gain material for capturing opponent's piece

        # Add more assessment based on safety, strategic positions etc.
        return score
    
    best_move = None
    best_score = -np.inf
    legal_moves = memory.get('legal_moves', [])

    # Iterating over all legal moves and scoring them
    for move in legal_moves:
        score = evaluate_move(move)
        
        # Check for special cases like checkmate or promotion
        # For checkmate, we could insert logic here if we have a way to detect it
        # This is a simple way to prioritize moves but doesn't actually implement checking
        if score >= 100:  # Assuming a high score like 100 indicates a checkmate or close to it
            best_move = move
            break
        
        if score > best_score:
            best_move = move
            best_score = score

    return best_move, memory

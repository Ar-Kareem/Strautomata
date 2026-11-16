
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    """
    Simple policy that prioritizes checkmate, then castling, promotions, captures, checks, and other moves.
    """
    best_move = legal_moves[0]
    best_score = -1
    
    for move in legal_moves:
        score = 0
        
        # Checkmate: highest priority
        if move.endswith('#'):
            score = 3000000
        # Castling: king safety
        elif move in ['O-O', 'O-O-O']:
            score = 2000000
        # Promotion to queen: best promotion
        elif '=' in move and move[-1] == 'Q':
            score = 9
        # Other promotions
        elif '=' in move:
            score = 3
        # Capture moves
        elif 'x' in move:
            score = 5
        # Check moves
        elif '+' in move:
            score = 3
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move

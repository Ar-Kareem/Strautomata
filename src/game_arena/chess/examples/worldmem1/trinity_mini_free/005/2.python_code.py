
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    # Piece values for material evaluation
    PIECE_VALUES = {'p': 1, 'n': 3, 'b': 3, 'r': 5, 'q': 9, 'k': 10000}
    
    # Helper function to parse move into source/destination squares
    def parse_move(move: str) -> tuple[str, str]:
        if move == 'O-O' or move == 'O-O-O':
            return ('', move)  # Castling handled separately
        if '=' in move:  # Promotion
            dest = move.split('=')[-1]
            src = move[:-len(dest) - 1]
        elif 'x' in move:  # Capture
            dest = move.split('x')[-1]
            src = move.split('x')[0]
        else:  # Standard move
            dest = move[-2:]
            src = move[:-2]
        return src, dest
    
    # Helper function to evaluate material gain
    def material_score(move: str) -> int:
        src, dest = parse_move(move)
        score = 0
        
        # Check for captures
        if 'x' in move:
            captured_piece = pieces.get(dest, '')
            if captured_piece:
                score += PIECE_VALUES[captured_piece[1]]
        
        # Check for promotions
        if '=' in move:
            promoted_piece = move.split('=')[-1]
            score += PIECE_VALUES[promoted_piece]
        
        return score
    
    # Helper function to check for check status
    def is_check(move: str) -> bool:
        return '+' in move
    
    # Evaluate each move
    best_move = None
    best_score = -10**9
    
    for move in legal_moves:
        # Skip castling for material evaluation
        if move in ['O-O', 'O-O-O']:
            continue
        
        # Calculate move score
        score = material_score(move)
        if is_check(move):
            score += 100  # Bonus for checks
        
        # Select best move
        if score > best_score:
            best_score = score
            best_move = move
    
    # Handle castling if no other moves found
    if best_move is None:
        best_move = next((m for m in legal_moves if m in ['O-O', 'O-O-O']), legal_moves[0])
    
    return best_move, {}

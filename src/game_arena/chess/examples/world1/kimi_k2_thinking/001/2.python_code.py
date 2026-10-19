
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    """
    Heuristic-based chess policy optimized for rapid evaluation.
    Strategy hierarchy: Checkmate > Checks/Captures > Promotions > 
    Castling > Center Control > King Safety > Material Preservation
    """
    
    # Material values
    PIECE_VALUES = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
    
    # Positional bonuses
    CENTER_SQUARES = {'d4', 'e4', 'd5', 'e5'}
    MY_COLOR = 'w' if to_play == 'white' else 'b'
    
    # Cache opponent pieces
    opponent_pieces = {
        sq: pc for sq, pc in pieces.items() 
        if pc[0] != MY_COLOR
    }
    
    def get_target_square(move: str):
        """Extract destination square from move string."""
        # Castling moves
        if move == 'O-O':
            return 'g1' if MY_COLOR == 'w' else 'g8'
        if move == 'O-O-O':
            return 'c1' if MY_COLOR == 'w' else 'c8'
        
        # Remove check/mate annotations for parsing
        clean = move.rstrip('#+')
        
        # Remove promotion part
        if '=' in clean:
            clean = clean.split('=')[0]
        
        # Find the target square (last coordinate pair)
        for i in range(len(clean) - 1, 0, -1):
            if clean[i-1] in 'abcdefgh' and clean[i] in '12345678':
                return clean[i-1:i+1]
        return None
    
    def get_piece_type(move: str):
        """Determine moving piece type from notation."""
        if move.startswith('O-O'):
            return 'K'
        if move[0] in 'NBRQK':
            return move[0]
        return 'P'
    
    def evaluate(move: str) -> int:
        """Calculate heuristic score for a move."""
        score = 0
        
        # 1. Checkmate (highest priority)
        if move.endswith('#'):
            return 1_000_000
        
        # 2. Check bonus
        if move.endswith('+'):
            score += 200
        
        # 3. Castling bonus (king safety)
        if move in ('O-O', 'O-O-O'):
            score += 150
        
        # Get target square for subsequent evaluations
        target_sq = get_target_square(move)
        
        # 4. Capture evaluation
        if 'x' in move and target_sq and target_sq in opponent_pieces:
            captured_type = opponent_pieces[target_sq][1]
            score += PIECE_VALUES.get(captured_type, 0) * 100
        
        # 5. Promotion bonus
        if '=' in move:
            promoted_type = move.split('=')[-1][0]
            score += PIECE_VALUES.get(promoted_type, 0) * 100
        
        # 6. Positional bonuses
        if target_sq:
            # Center control
            if target_sq in CENTER_SQUARES:
                score += 20
            
            # Penalize moving king to center
            piece_type = get_piece_type(move)
            if piece_type == 'K' and target_sq in CENTER_SQUARES:
                score -= 50
        
        return score
    
    # Return the move with highest heuristic score
    return max(legal_moves, key=evaluate)


def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    # Simple evaluation based on piece values and centralization
    piece_values = {'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'P': 1, 'K': 0}  # King value 0 to avoid trades
    
    # Helper to parse a move string and determine its type (capture, check, etc.)
    def parse_move(move: str):
        # Check for checkmate or check
        is_checkmate = move.endswith('#')
        is_check = move.endswith('+') or is_checkmate
        
        # Check for capture
        is_capture = 'x' in move
        
        # Check for castling
        is_castle = move in ['O-O', 'O-O-O']
        
        # Identify piece moved (first character if uppercase, otherwise 'P' for pawn moves)
        piece_moved = move[0] if move[0].isupper() else 'P'
        
        # Identify promotion if any
        promotion = None
        if '=' in move:
            promotion = move.split('=')[1][0]  # e.g., "=Q" -> "Q"
        
        # Identify target square (last two characters, ignoring promotion and check symbols)
        target = move[-2:]
        if promotion:
            target = move.split('=')[0][-2:]  # e.g., "b8=Q" -> "b8"
        
        return {
            'move': move,
            'piece': piece_moved,
            'is_capture': is_capture,
            'is_check': is_check,
            'is_checkmate': is_checkmate,
            'is_castle': is_castle,
            'promotion': promotion,
            'target': target
        }
    
    # Evaluate each legal move
    best_move = None
    best_score = -float('inf')
    
    for move in legal_moves:
        parsed = parse_move(move)
        score = 0.0
        
        # Priority 1: Checkmate
        if parsed['is_checkmate']:
            best_move = move
            break  # Immediate win
        
        # Priority 2: Check
        if parsed['is_check']:
            score += 5.0  # Bonus for checking
        
        # Priority 3: Captures (material gain)
        if parsed['is_capture']:
            # Simple heuristic: assume captured piece is of average value (3) or higher
            # Since we don't know the exact captured piece, we estimate based on the moving piece's typical capture opportunities
            # For simplicity, add piece value of the moving piece (aggressive) or a fixed capture bonus
            # We'll add a base capture bonus + potential material gain
            score += 3.0  # Base capture bonus
            
            # If we can infer a promotion, add that value
            if parsed['promotion']:
                score += piece_values.get(parsed['promotion'], 0) - 1  # Net gain from promotion (since pawn is worth 1)
        
        # Priority 4: Castling (king safety)
        if parsed['is_castle']:
            score += 4.0
        
        # Priority 5: Centralization (for non-pawn moves, prioritize center squares)
        center_squares = ['d4', 'd5', 'e4', 'e5', 'd3', 'e3', 'd6', 'e6']
        if parsed['piece'] != 'P' and parsed['target'] in center_squares:
            score += 1.5
        
        # Priority 6: Pawn advancement (especially in opening)
        if parsed['piece'] == 'P':
            # Reward moving pawns forward (higher rank for white, lower for black)
            if to_play == 'white':
                rank = int(parsed['target'][1])
                score += (rank - 2) * 0.5  # Base rank 2, so advancing is good
            else:
                rank = int(parsed['target'][1])
                score += (7 - rank) * 0.5  # Base rank 7 for black
        
        # Tie-breaker: Prefer moves by higher-value pieces (if scores equal)
        score += piece_values.get(parsed['piece'], 0) * 0.1
        
        # Update best move
        if score > best_score:
            best_score = score
            best_move = move
    
    # If no move found (should not happen), return first legal move
    if best_move is None:
        best_move = legal_moves[0]
    
    # Return the move and an empty memory (stateless policy)
    return best_move, {}

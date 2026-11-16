
def policy(pieces: dict[str, str], to_play: str) -> str:
    import random
    
    # Helper function to determine piece value
    def get_piece_value(piece):
        if not piece:
            return 0
        piece_type = piece[1]
        if piece_type == 'P': return 1
        if piece_type == 'N' or piece_type == 'B': return 3
        if piece_type == 'R': return 5
        if piece_type == 'Q': return 9
        if piece_type == 'K': return 0
        return 0
    
    # Simple move scoring function
    def score_move(move, pieces, to_play):
        score = 0
        from_sq = move[:2]
        to_sq = move[2:]
        
        # Check if it's a capture
        captured_piece = pieces.get(to_sq)
        if captured_piece:
            score += get_piece_value(captured_piece) * 100
        
        # Check if it's a check
        # For simplicity, we'll give a minor bonus for checks
        # This would require a full board simulation in a real engine
        score += 5
        
        # Prefer moves that develop pieces (center control)
        center_squares = ['d4', 'd5', 'e4', 'e5']
        if to_sq in center_squares:
            score += 30
            
        # Prefer pawn advancement
        piece_type = pieces.get(from_sq, '')[1] if from_sq in pieces else ''
        if piece_type == 'P':
            from_rank = int(from_sq[1])
            to_rank = int(to_sq[1])
            if to_play == 'white':
                if to_rank > from_rank:
                    score += 5
            else:
                if to_rank < from_rank:
                    score += 5
        
        # Prefer capturing the king (if possible - should be checkmate)
        if captured_piece and captured_piece[1] == 'K':
            score += 10000
            
        # Prefer moving pieces that are under attack or protecting something important
        # This is a simplified version - in full engine, would use attacked squares etc.
        
        return score
    
    # Dummy implementation - select a random move among legal ones
    # In a competition, this would be replaced with a real chess engine
    legal_moves = [
        'f5e4', 'f5f4', 'g3d6', 'g3e1', 'g3e5', 'g3f2', 'g3f4', 'g3h2', 
        'f1g1', 'e1g1', 'e1c1', 'e8g8', 'e8c8', 'b4b5', 'a2a1r', 'a2a1q'
    ]
    
    # Filter legal moves to only those that fit in the provided state
    # Simple heuristic: prefer captures, then development, then random
    captures = []
    checks = []
    development = []
    others = []
    
    for move in legal_moves:
        # Filter moves based on what pieces we have
        from_sq = move[:2]
        to_sq = move[2:]
        
        # Check if we have a piece at from_sq
        if from_sq in pieces:
            piece = pieces[from_sq]
            if to_sq in pieces and piece[0] != pieces[to_sq][0]:
                # Capture
                captures.append(move)
            elif to_sq not in pieces or piece[0] == pieces[to_sq][0]:
                # Non-capture
                if to_sq in ['d4', 'd5', 'e4', 'e5']:
                    development.append(move)
                elif to_sq in ['g3', 'h3', 'f1', 'f2', 'e1', 'd1']:
                    development.append(move)
                else:
                    others.append(move)
    
    # Prioritize: captures > development > others
    if captures:
        return random.choice(captures)
    elif development:
        return random.choice(development)
    else:
        return random.choice(legal_moves)

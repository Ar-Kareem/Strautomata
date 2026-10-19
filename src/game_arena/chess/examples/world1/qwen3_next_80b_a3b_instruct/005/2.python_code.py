
import itertools

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    # Piece values for material evaluation
    piece_values = {'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'P': 1, 'K': 0}
    
    # Determine color abbreviation
    color = 'w' if to_play == 'white' else 'b'
    opponent_color = 'b' if to_play == 'white' else 'w'
    
    # If there's only one legal move, return it
    if len(legal_moves) == 1:
        return legal_moves[0]
    
    # Check for checkmate (immediate win)
    for move in legal_moves:
        # Simple heuristic: moves with '+' are often check/checkmate
        # But the input may not always include '+' — so we need to infer
        # For now, we assume if a move is given as 'move+', it's checkmate.
        # Since the problem does not offer simulation, we can't truly calculate mate,
        # so we rely on the move string having '+' as indicator (common in practice).
        if move.endswith('+') and len(move) > 1:
            # This might be check or mate; without simulation, we assume it's winning
            return move
    
    # We'll assume that any capture of a queen or a move that leads to a forced mate is in the list.
    # Try to detect any capture of opponent's queen
    best_move = legal_moves[0]
    best_score = -float('inf')
    
    for move in legal_moves:
        score = 0.0
        
        # Handle castling: high priority for king safety
        if move == "O-O" or move == "O-O-O":
            score += 10.0  # Strong bonus for castling
            
        # Handle promotions
        if "=" in move:
            if "=Q" in move:
                score += 15.0  # Promotion to queen is strongest
            elif "=R" in move:
                score += 12.0
            elif "=B" in move or "=N" in move:
                score += 10.0
            # Also, if promoting on 8th rank, add positional bonus
            # e.g., 'a8=Q' -> promoted on central file? not really, but still good
            score += 5.0  # General promotion bonus
            
        # Handle captures
        if 'x' in move:
            # Extract the captured piece type from the target square
            # The format is usually: [Piece][file][rank]x[file][rank]
            # But we don't have piece type on target, so we infer: what piece was on the target square?
            # We can check current board state
            target_square = move.split('x')[-1]
            if target_square in pieces:
                captured_piece = pieces[target_square]
                if len(captured_piece) == 2 and captured_piece[0] == opponent_color:
                    piece_type = captured_piece[1]
                    score += piece_values.get(piece_type, 0) * 2  # Double weight for capture
                    
                    # Additional bonus for capturing high-value pieces
                    if piece_type == 'Q':
                        score += 20.0  # Huge bonus for queen capture
                    elif piece_type == 'R':
                        score += 10.0
                    
        # Positional bonuses: centralizing pieces
        # For non-capture moves, check if moving into central squares
        # Central squares: d4, e4, d5, e5 (classical center)
        central_squares = {'d4', 'e4', 'd5', 'e5'}
        # Also consider surrounding squares: c3, c4, c5, c6, d3, d6, e3, e6, f3, f4, f5, f6
        strong_squares = central_squares | {'c3', 'c4', 'c5', 'c6', 'd3', 'd6', 'e3', 'e6', 'f3', 'f4', 'f5', 'f6'}
        
        # Extract destination square: handle cases like 'Nec3', 'Bxc5', 'e4', 'O-O'
        dest_square = None
        if 'x' in move:
            dest_square = move.split('x')[-1]
        elif '=' in move:
            # Promotion: last two chars are '=X', but square is before
            parts = move.split('=')
            dest_square = parts[0][-2:] if len(parts[0]) >= 2 else parts[0][-1:]
        elif move in {'O-O', 'O-O-O'}:
            # Castling doesn't have a destination in the same way
            pass
        else:
            # Simple move: last 2 characters are the destination (e.g., 'e4', 'Nc3', 'Rab1')
            if len(move) >= 2:
                dest_square = move[-2:]
            # Handle cases like 'Na3', where the piece letter is before, but file+rank is last 2
            # We'll check if the last two chars are a valid algebraic square
            if dest_square and len(dest_square) == 2:
                if dest_square[0] not in 'abcdefgh' or dest_square[1] not in '12345678':
                    dest_square = None
            else:
                dest_square = None
                
        if dest_square and dest_square in strong_squares:
            # Only if it's a piece (not pawn) or pawn advance towards center
            # For pawns: advancing to d4/e4 is good
            if move[0] in ('B', 'N', 'R', 'Q', 'K') or (len(move) >= 2 and move[0] in 'abcdefgh' and move[0] in 'de' and dest_square[1] in '45'):
                score += 2.0
                
        # Reduce score if moving king to edge (unless castling)
        if move.startswith('K') and move[1:].startswith('K') is False:
            # 'K' followed by square
            if len(move) >= 3:
                king_dest = move[1:3]
                if king_dest in {'a1', 'h1', 'a8', 'h8'}:
                    score -= 3.0  # King on corner is bad
                elif king_dest[0] in 'ah' or king_dest[1] in '18':
                    score -= 1.0  # King on edge is risky
        
        # Prefer moves that don't expose king to checks
        # Without simulation, we can't be sure, so we avoid moves that move king if under threat? 
        # We assume the legal_moves list is correct, so king won't move into check.
        # So we don't penalize here.
        
        # If move gives check, give small bonus (might lead to mate)
        if move.endswith('+') and not move.endswith('++'):
            score += 3.0
        
        # Bonus for moving a piece that hasn't moved (development)
        # We'd need to know if piece moved before — but we don't have game history
        # So we skip this.
        
        # Avoid moving the same piece twice in early game? We don't have history.
        
        # Score is higher if the move is more aggressive and protective
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move


import copy

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    """
    Chess policy that selects the best move from legal_moves based on chess principles.
    Prioritizes: checkmate > material gain > development > king safety > positional advantage
    """
    
    # Define piece values
    piece_values = {
        'P': 1,
        'N': 3,
        'B': 3,
        'R': 5,
        'Q': 9,
        'K': 100  # King value is for threat detection, not material count
    }
    
    # Determine our color
    our_color = 'w' if to_play == 'white' else 'b'
    opponent_color = 'b' if our_color == 'w' else 'w'
    
    # Helper function to get piece color and type from code
    def get_piece_info(square):
        if square in pieces:
            return pieces[square][0], pieces[square][1]
        return None, None
    
    # Helper function to get piece value
    def get_piece_value(piece_code):
        if piece_code is None:
            return 0
        _, piece_type = piece_code[0], piece_code[1]
        return piece_values.get(piece_type, 0)
    
    # Find best move
    best_move = legal_moves[0]  # default fallback
    best_score = float('-inf')
    
    for move in legal_moves:
        score = 0
        
        # 1. Check for checkmate (highest priority)
        if '+' in move and '++' in move:  # Checkmate often has double check symbol
            return move, memory
        elif move.endswith('+') and is_checkmate_candidate(move, pieces, our_color, opponent_color):
            return move, memory
        elif move.endswith('++'):  # Double check, likely mate
            return move, memory
            
        # 2. Check for captures
        if 'x' in move:
            # Extract captured square - it's after 'x'
            capture_square = move.split('x')[-1]
            # If it's a promotion with capture
            if '=' in capture_square:
                capture_square = capture_square.split('=')[0]
            cap_piece_code = pieces.get(capture_square, '')
            if cap_piece_code and cap_piece_code[0] == opponent_color:
                captured_piece_type = cap_piece_code[1]
                score += piece_values.get(captured_piece_type, 0) * 10  # High weight for captures
                
                # Bonus for capturing high value pieces
                if captured_piece_type == 'Q':
                    score += 50
                elif captured_piece_type == 'R':
                    score += 30
                elif captured_piece_type in ['B', 'N']:
                    score += 15
        
        # 3. Check for promotions
        if '=' in move:
            # Promotion to Queen is best
            if '=Q' in move:
                score += 20
            elif '=R' in move:
                score += 15
            elif '=B' in move or '=N' in move:
                score += 10
        
        # 4. Castling - very valuable for king safety
        if move in ['O-O', 'O-O-O']:
            score += 25
            
        # 5. Check moves - gaining initiative
        if move.endswith('+'):
            score += 8
            
        # 6. Central control: prefer moves to center squares
        center_squares = {'d4', 'd5', 'e4', 'e5'}
        # Extract destination square (handle various move formats)
        dest_square = extract_destination(move)
        if dest_square in center_squares:
            score += 3
        
        # 7. Development: prioritize moving pieces off back rank early
        # If we're early game (many pawns still on rank 2/7), favor development
        if is_early_game(pieces):
            if dest_square and dest_square[1] in ['3', '4', '5', '6']:
                # If moving a knight or bishop from starting position
                origin_square = extract_origin(move, pieces, our_color)
                if origin_square:
                    if origin_square[1] in ['1', '2', '7', '8'] and dest_square[1] in ['3', '4', '5', '6']:
                        score += 5
                
        # 8. Avoid moving the same piece twice early (development penalty for repeated moves)
        # We'll track in memory if needed, but without persistent state across games, we can't fully implement
        
        # 9. Avoid moves that expose king (we'll do a simple check)
        # If our king is on e1/e8 and we're moving a piece that was protecting the king
        king_pos = find_king(pieces, our_color)
        if king_pos:
            # Check if move potentially exposes king to diagonal attack
            if dest_square and is_king_exposed_after_move(move, king_pos, pieces, our_color):
                score -= 10
        
        # 10. Prevent opponent threats (simple heuristic: if opponent has a piece that can capture our piece next turn)
        # This is complex without full simulation, so we skip for now
        
        # Update best move
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move, memory

def extract_destination(move):
    """Extract destination square from move string"""
    # Handle different move formats
    if 'x' in move:
        parts = move.split('x')
        dest_part = parts[-1]
    else:
        dest_part = move
    
    # Handle promotion
    if '=' in dest_part:
        dest_part = dest_part.split('=')[0]
    
    # Handle disambiguation (like Nec3 -> c3)
    # We want the last 2 characters if they form a valid square
    possible_dest = dest_part[-2:]
    if len(possible_dest) == 2 and possible_dest[0] in 'abcdefgh' and possible_dest[1] in '12345678':
        return possible_dest
    
    # For castling/other special moves
    if move in ['O-O', 'O-O-O']:
        return 'g1' if move == 'O-O' else 'c1'  # assuming white, need to handle both colors
    
    return None

def extract_origin(move, pieces, our_color):
    """Extract origin square from move string, returns None if can't determine"""
    if move in ['O-O', 'O-O-O']:
        return 'e1' if our_color == 'w' else 'e8'
    
    # For moves like "Nec3" and "R1c3"
    if len(move) > 2:
        # Check if starts with a piece letter
        if move[0] in 'NBRQKP':
            if move[1] in 'abcdefgh' and move[2] in '12345678':
                # Disambiguated file
                return move[1] + move[2]
            elif move[1] in '12345678' and move[2] in 'abcdefgh' and len(move) >= 3:
                # Disambiguated rank
                return move[1] + move[2]
            else:
                # Normal piece move
                dest = move[-2:]
                if len(dest) == 2 and dest[0] in 'abcdefgh' and dest[1] in '12345678':
                    # Look for piece of type move[0] on our color that can reach dest
                    piece_type = move[0]
                    for square, piece_code in pieces.items():
                        if piece_code[0] == our_color and piece_code[1] == piece_type:
                            # Simple heuristic: return first matching piece, in real implementation we'd calculate paths
                            return square
    else:
        # Simple pawn move
        dest = move[-2:]
        if len(dest) == 2 and dest[0] in 'abcdefgh' and dest[1] in '12345678':
            # Pawn moves - need to determine origin from file
            file = dest[0]
            rank = int(dest[1])
            if our_color == 'w':
                # White pawn: can come from rank 2 or 3
                if dest[1] == '4' and f'{file}2' in pieces and pieces[f'{file}2'] == our_color + 'P':
                    return f'{file}2'
                elif dest[1] == '3' and f'{file}2' in pieces and pieces[f'{file}2'] == our_color + 'P':
                    return f'{file}2'
            else:
                # Black pawn: can come from rank 7 or 6
                if dest[1] == '5' and f'{file}7' in pieces and pieces[f'{file}7'] == our_color + 'P':
                    return f'{file}7'
                elif dest[1] == '6' and f'{file}7' in pieces and pieces[f'{file}7'] == our_color + 'P':
                    return f'{file}7'
    
    return None

def find_king(pieces, color):
    """Return king position for given color"""
    for square, piece_code in pieces.items():
        if piece_code == color + 'K':
            return square
    return None

def is_early_game(pieces):
    """Determine if game is in early stages (many pawns on original ranks)"""
    white_pawns_on_rank2 = sum(1 for square, piece in pieces.items() if piece == 'wP' and square[1] == '2')
    black_pawns_on_rank7 = sum(1 for square, piece in pieces.items() if piece == 'bP' and square[1] == '7')
    return white_pawns_on_rank2 >= 5 and black_pawns_on_rank7 >= 5

def is_checkmate_candidate(move, pieces, our_color, opponent_color):
    """Simple check for checkmate candidate - heuristic: check with high material advantage"""
    # This is a simplified version - true checkmate detection would require simulation
    # Just check if it's a check and we have significant material advantage
    if not move.endswith('+'):
        return False
    
    # Count material for both sides
    our_material = sum(piece_values.get(p[1], 0) for p in pieces.values() if p[0] == our_color)
    opp_material = sum(piece_values.get(p[1], 0) for p in pieces.values() if p[0] == opponent_color)
    
    # If we're much ahead and delivered a check, it might be mate
    return our_material > opp_material + 10  # Heuristic threshold

def is_king_exposed_after_move(move, king_pos, pieces, our_color):
    """Simple heuristic to detect if king might be exposed after move"""
    # Check if move removes a defender of the king
    if not king_pos:
        return False
    
    # Extract destination
    dest_square = extract_destination(move)
    if not dest_square:
        return False
    
    # If king is on e1/e8 and we're moving a piece near it (especially f1/f8 or d1/d8)
    if king_pos in ['e1', 'e8']:
        # Check if we're moving a piece that is protecting the king
        # For white king on e1, pieces on d1, f1, d2, f2, e2 protect the king
        protective_squares = {'d1', 'f1', 'd2', 'f2', 'e2', 'c1', 'g1'}
        if dest_square in protective_squares:
            # If we're moving that piece, then king is exposed
            return True
            
    return False

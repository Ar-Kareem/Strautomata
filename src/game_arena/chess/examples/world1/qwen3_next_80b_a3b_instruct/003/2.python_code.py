
import re

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    # Define piece values
    piece_values = {'Q': 900, 'R': 500, 'B': 300, 'N': 300, 'P': 100}
    
    # Helper: get piece color
    def get_color(piece_code):
        return piece_code[0]
    
    # Helper: get piece type
    def get_piece_type(piece_code):
        return piece_code[1]
    
    # Determine our color
    our_color = 'w' if to_play == 'white' else 'b'
    
    # Helper: square to coordinate (0-7, 0-7)
    def sq_to_coord(sq):
        file, rank = sq[0], sq[1]
        return ord(file) - ord('a'), int(rank) - 1
    
    # Helper: check if square is in center
    def is_center_square(sq):
        file, rank = sq[0], sq[1]
        return file in ['d', 'e'] and rank in ['4', '5']
    
    # Helper: get piece at square, or None
    def get_piece_at(sq):
        return pieces.get(sq, None)
    
    # Helper: check if a move is a capture
    def is_capture(move):
        return 'x' in move
    
    # Helper: extract captured piece type from move (if any)
    def extract_captured_piece(move):
        if not is_capture(move):
            return None
        # For standard moves like "Nxf5", the last two chars are the destination
        # The piece captured is at destination, so we look at the board
        dest_sq = move[-2:]
        return get_piece_at(dest_sq)
    
    # Helper: check for promotion
    def is_promotion(move):
        return '=' in move
    
    # Helper: extract promoted piece
    def get_promoted_piece(move):
        if not is_promotion(move):
            return None
        return move.split('=')[1]
    
    # Helper: check for castling
    def is_castling(move):
        return move in ['O-O', 'O-O-O']
    
    # Helper: get destination square of a move
    def get_dest_sq(move):
        # Handle special cases: O-O, O-O-O
        if move in ['O-O', 'O-O-O']:
            return 'g1' if our_color == 'w' else 'g8' if move == 'O-O' else 'c1' if our_color == 'w' else 'c8'
        
        # Remove check/checkmate symbols
        move = move.rstrip('+').rstrip('#')
        
        # Handle promotions: e.g., "e8=Q"
        if '=' in move:
            move = move.split('=')[0]
        
        # Handle disambiguation: e.g., "Nec3" -> "c3"
        # If the move has 3 or more chars, and the first char is a piece letter, and second is a file,
        # then last two are destination
        if len(move) > 2 and move[0] in 'NBRQK' and move[1] in 'abcdefgh':
            return move[-2:]
        elif len(move) >= 2 and move[-2] in 'abcdefgh' and move[-1] in '12345678':
            return move[-2:]
        else:
            return None
  
    # Helper: check if move puts opponent in check
    # Note: We don't have full board state for dynamic checks, so we'll assume any capture or pawn advance to 7th/2nd rank that attacks king is a threat
    # This is conservative: a move that captures or checks is flagged as giving check if it leads to possible king attack
    # We can't fully simulate, so we'll use a simple heuristic: if it's a capture near king or a move to a square that attacks king, assume it's giving check
    # Actually, we cannot reliably simulate opponent's check vulnerability without board simulation — so we skip this and rely on capture and promotion.
    # Instead: We'll assume that if the move is a capture, and the captured piece is near the enemy king, or if the move is a check-move (has +), then it's possibly checking.
    # But moves in `legal_moves` may include `+` or `#` — so we check for those.
    def gives_check(move):
        return '+' in move or '#' in move
    
    def gives_mate(move):
        return '#' in move

    # Evaluate a move
    def evaluate_move(move):
        score = 0
        
        # Check for checkmate
        if gives_mate(move):
            return 10000
        
        # Check for check
        if gives_check(move):
            score += 150  # Small bonus for checking
            
        # Promotion
        if is_promotion(move):
            promoted_to = get_promoted_piece(move)
            if promoted_to == 'Q':
                score += 800
            else:
                score += 400
            return score  # High priority, skip other evaluation
        
        # Castling
        if is_castling(move):
            # Castling increases king safety
            score += 200
            return score
        
        # Capture
        if is_capture(move):
            captured = extract_captured_piece(move)
            if captured:
                piece_type = get_piece_type(captured)
                if piece_type in piece_values:
                    score += piece_values[piece_type]
            # Additional bonus for capturing with lower-value piece
            # This is strategic — always prefer captures
    
        # Center control: check destination
        dest_sq = get_dest_sq(move)
        if dest_sq:
            if is_center_square(dest_sq):
                score += 50
            # Bonus for moving to open squares (if not occupied by own piece)
            piece_at_dest = get_piece_at(dest_sq)
            if not piece_at_dest:  # empty square
                score += 10
            # If it's a pawn move to 4th or 5th rank (in center), bonus
            if move[0] == 'P' and dest_sq[1] in ['4','5'] and dest_sq[0] in ['d','e']:
                score += 30
        
        # Avoid putting king in danger (heuristic)
        # If we are moving a piece and king square is attacked, avoid — but we don't have full analysis
        # As a proxy: if move is not castling and king is on e1/e8, avoid moving pieces that guard king?
        # Too complex — instead, let material and center control drive choice.
        
        return score
    
    # Find best move
    best_move = None
    best_score = float('-inf')
    
    for move in legal_moves:
        score = evaluate_move(move)
        if score > best_score:
            best_score = score
            best_move = move
    
    # Fallback: if none chosen (shouldn't happen due to legal_moves non-empty), pick first
    if best_move is None:
        best_move = legal_moves[0]
    
    return best_move

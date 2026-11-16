
import numpy as np

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    # Define piece values for material evaluation
    piece_values = {'P': 100, 'N': 300, 'B': 300, 'R': 500, 'Q': 900, 'K': 0}
    
    # Determine opponent color
    opponent_color = 'b' if to_play == 'white' else 'w'
    
    # Check for checkmate moves (any move that ends with '+'))
    mate_moves = [m for m in legal_moves if '+' in m and len(m) >= 3 and m[-1] == '+']
    if mate_moves:
        # Return the first mate move — in practice there should be at most one, but take any
        return mate_moves[0]
    
    # Prefer captures — especially high-value ones
    capture_moves = [m for m in legal_moves if 'x' in m]
    if capture_moves:
        best_capture = None
        best_value = -1
        for move in capture_moves:
            # Extract target square (last two chars, excluding any promotion or check)
            square = move.split('x')[-1]
            # Remove any trailing + or =X
            if '=' in square:
                square = square.split('=')[0]
            if '+' in square:
                square = square.replace('+', '')
            if len(square) != 2:
                continue
            # If opponent piece is on that square, evaluate its value
            if square in pieces:
                captured_piece = pieces[square][1]  # piece type
                if captured_piece in piece_values:
                    value = piece_values[captured_piece]
                    if value > best_value:
                        best_value = value
                        best_capture = move
        if best_capture:
            # Also consider if capture leads to back-rank or other threats, but for now, take highest material
            return best_capture
    
    # Check for castling — king safety priority
    castling_moves = [m for m in legal_moves if m in ['O-O', 'O-O-O']]
    if castling_moves:
        # Prefer O-O-O if king is under threat? But usually O-O is safer and faster
        # Simple heuristic: prefer kingside castle unless queen side is only option
        if 'O-O' in castling_moves:
            return 'O-O'
        else:
            return castling_moves[0]
    
    # Prioritize pawn promotions on last rank
    promotion_moves = [m for m in legal_moves if '=' in m]
    if promotion_moves:
        # Promote to Queen unless a different piece is tactically better (e.g., underpromotion to knight for check)
        # Default: promote to Queen
        queen_promotions = [m for m in promotion_moves if '=Q' in m]
        if queen_promotions:
            return queen_promotions[0]
        # Otherwise take any promotion
        return promotion_moves[0]
    
    # Evaluate non-capture moves by central control and development
    central_squares = ['d4', 'd5', 'e4', 'e5', 'c4', 'c5', 'f4', 'f5']
    best_move = legal_moves[0]  # fallback
    
    # Heuristic: prefer moves to center or developing moves
    score_best = -float('inf')
    for move in legal_moves:
        # Skip captures and promotions and castling (already handled)
        if 'x' in move or '=' in move or move in ['O-O', 'O-O-O']:
            continue
            
        # Extract destination square (remove any disambiguation prefix and check symbol)
        dest_sq = move
        if len(move) >= 3 and move[0] in 'abcdefgh' and move[1] in '12345678':
            # Likely a pawn move
            dest_sq = move
        else:
            # Clean the move: remove first char if it's a letter (disambiguation file/rank)
            if len(move) >= 3 and move[0] in 'NBRQK' and move[1] in 'abcdefgh' and move[2] in '12345678':
                dest_sq = move[1:3]
            elif len(move) >= 2 and move[0] in 'NBRQK' and move[1:3] in ['11','12','13','14','15','16','17','18','21','22','23','24','25','26','27','28','31','32','33','34','35','36','37','38','41','42','43','44','45','46','47','48','51','52','53','54','55','56','57','58','61','62','63','64','65','66','67','68','71','72','73','74','75','76','77','78','81','82','83','84','85','86','87','88']:
                # Malformed if up here... check last 2
                dest_sq = move[-2:]
            else:
                dest_sq = move[-2:]
        
        # Ensure dest_sq is a valid square
        if len(dest_sq) != 2 or dest_sq[0] not in 'abcdefgh' or dest_sq[1] not in '12345678':
            continue
            
        score = 0.0
        
        # Central control bonus
        if dest_sq in central_squares:
            score += 50
        elif dest_sq[0] in ['d','e'] or dest_sq[1] in ['4','5']:  # near center
            score += 20
            
        # Bonus for advancing pawns in center
        if move[0] == 'P' or (move[0] in 'abcdefgh' and len(move) == 2 and move[1] in '45'):
            if dest_sq in ['d4','d5','e4','e5']:
                score += 30
            
        # Avoid moving the same piece twice early? Not needed with limited context
        # Check if move increases king safety or decreases opponent threats
        # Simple avoidance of moves that open king diagonal (e.g., f-pawn moved when king on e1)
        # We don't have full board state to compute threats deeply — stick to heuristics
        
        # Bonus for developing minor pieces
        if move[0] in 'N' or move[0] == 'B':
            if dest_sq[0] not in ['a','h'] and dest_sq[1] not in ['1','8']:
                score += 10  # avoid edges
            if move[0] == 'N' and dest_sq in ['c3','c6','f3','f6']:  # natural knight posts
                score += 25
        
        # Prefer moves that don't hang pieces (this is risky without full board analysis)
        # We'll assume opponent won't take immediately if no capture
        # Use a simple heuristic: avoid moving piece that is already attacked? We lack that info.
        # So we focus on proactive moves
        
        if score > score_best:
            score_best = score
            best_move = move
    
    # If all else fails, return any legal move (guaranteed non-empty per API)
    return best_move


import re
from collections import defaultdict

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    """
    Select the best move based on multi-factor heuristic evaluation.
    Prioritizes checkmate, material, checks, king safety, and development.
    """
    if not legal_moves:
        return ""
    
    # Piece values for evaluation
    PIECE_VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}
    
    # Central squares for positional evaluation
    CENTER_SQUARES = {'e4', 'd4', 'e5', 'd5', 'e3', 'd3', 'e6', 'd6'}
    ADJACENT_CENTER = {'c3', 'c4', 'c5', 'c6', 'd2', 'e2', 'f2', 'g2', 'd7', 'e7', 'f7', 'g7', 'f3', 'f4', 'f5', 'f6'}
    
    # Parse pieces by color
    my_color = 'w' if to_play == 'white' else 'b'
    opp_color = 'b' if to_play == 'white' else 'w'
    
    my_pieces = {square: piece for square, piece in pieces.items() if piece[0] == my_color}
    opp_pieces = {square: piece for square, piece in pieces.items() if piece[0] == opp_color}
    
    # Build attack maps
    my_attacks = defaultdict(list)  # square -> list of attackers
    opp_attacks = defaultdict(list)
    
    for square, piece in pieces.items():
        piece_type = piece[1]
        color = piece[0]
        if color == my_color:
            my_attacks[square] = []
            for target in legal_moves:
                if target.startswith(square):
                    dest = target[2:] if len(target) > 3 and target[2] in 'x:#+' else target[-2:]
                    my_attacks[dest].append(square)
        else:
            opp_attacks[square] = []
    
    def get_piece_at(square):
        return pieces.get(square, '')
    
    def is_check(move):
        """Check if a move results in check"""
        # Simulate the move
        match = re.match(r'^([KQRBNP]?)([a-h]?[1-8]?)?x?([a-h][1-8])(?:=[QRBN])?(?:\+|#)?$', move)
        if not match:
            return False
        
        # Get destination
        if 'x' in move:
            dest = move.split('x')[-1].replace('+', '').replace('#', '')
        else:
            # Remove any disambiguation
            if len(move) == 2:
                dest = move
            else:
                # Handle special notation
                dest = move[-2:]
        
        dest = dest[:2]
        if dest not in pieces:
            return False
        
        target_piece = pieces[dest]
        return target_piece[1] == 'K'
    
    def is_checkmate(move):
        """Check if a move results in checkmate"""
        if not is_check(move):
            return False
        
        # Get destination
        if 'x' in move:
            dest = move.split('x')[-1].replace('+', '').replace('#', '')
        else:
            dest = move[-2:]
        
        dest = dest[:2]
        
        # For simplicity, assume checkmate if it gives check
        # In a real engine, we'd verify no escape moves
        return '+' in move or '#' in move
    
    def parse_move_dest(move):
        """Extract destination square from move notation"""
        move = move.replace('O-O', '').replace('O-O-O', '')
        if 'x' in move:
            parts = move.split('x')
            dest = parts[-1].replace('+', '').replace('#', '')
        else:
            # Remove disambiguation and piece letter
            if move[0] in 'KQRBN':
                move = move[1:]
            # Handle promotions
            if '=' in move:
                move = move.split('=')[0]
            dest = move[-2:]
        return dest[:2]
    
    def evaluate_move(move):
        score = 0
        
        # 1. Checkmate detection (highest priority)
        if is_checkmate(move):
            return 10000
        
        # 2. Checks
        if '+' in move:
            score += 50
        
        # 3. Captures
        if 'x' in move:
            dest = parse_move_dest(move)
            captured = get_piece_at(dest)
            if captured:
                captured_type = captured[1]
                if move[0] in 'KQRBNP':
                    moving_piece = move[0]
                else:
                    # Pawn capture
                    moving_piece = 'P'
                    if captured_type == '':
                        # En passant
                        captured_type = 'P'
                
                capture_value = PIECE_VALUES.get(captured_type, 0)
                # Penalty for walking into defended piece
                if dest in opp_attacks and opp_attacks[dest]:
                    score += capture_value - PIECE_VALUES.get(moving_piece, 100) * 0.5
                else:
                    score += capture_value
        
        # 4. Castling
        if move in ['O-O', 'O-O-O']:
            score += 40
            return score
        
        # 5. Extract piece and destination
        piece_letter = ''
        if move[0] in 'KQRBN':
            piece_letter = move[0]
            move_content = move[1:]
        else:
            move_content = move
        
        dest = parse_move_dest(move)
        
        # 6. Central control bonus
        if dest in CENTER_SQUARES:
            score += 15
        elif dest in ADJACENT_CENTER:
            score += 8
        
        # 7. Development (pieces moving from starting position)
        if piece_letter in 'NBR' and len(move) <= 3:
            # Starting squares: knights b1/g1 or b8/g8, bishops c1/f1 or c8/f8, rooks a1/h1 or a8/h8
            start_positions = {
                'N': {'b1', 'g1', 'b8', 'g8'},
                'B': {'c1', 'f1', 'c8', 'f8'},
                'R': {'a1', 'h1', 'a8', 'h8'}
            }
            if dest in start_positions.get(piece_letter, set()):
                score += 20
        
        # 8. King safety - don't move king unnecessarily
        if piece_letter == 'K':
            # Penalty for moving king (already handled castling)
            score -= 10
        
        # 9. Queen development (later in game)
        if piece_letter == 'Q' and len(move) <= 3:
            score += 5
        
        # 10. Pawn advances
        if piece_letter == 'P' or (move[0].islower() and 'x' not in move and '=' not in move):
            pawn_move = True
            if piece_letter == 'P':
                pawn_move = True
            elif move[0].islower() and len(move) == 2:
                pawn_move = True
            
            if pawn_move:
                # Pawn to 4th rank or beyond
                rank = int(dest[1])
                if (my_color == 'w' and rank >= 4) or (my_color == 'b' and rank <= 5):
                    score += 10
                
                # Central pawn advance
                if dest[0] in 'de':
                    score += 5
        
        # 11. Piece coordination - avoid blocking own pieces
        if piece_letter == 'B' or piece_letter == 'Q':
            file = dest[0]
            rank = dest[1]
            # Bishop/queen on long diagonal bonus
            if file == rank or chr(ord('a') + 8 - int(rank)) == file:
                score += 10
        
        # 12. Avoid moving same piece twice early (unless capture or check)
        if move[0] in 'NBRQK' and '+' not in move and 'x' not in move:
            # Count how many times this piece has moved
            move_count = len([m for m in legal_moves if m.startswith(move[:2])])
            if move_count > 1:
                score -= 5
        
        return score
    
    # Evaluate all moves and select the best
    best_move = legal_moves[0]
    best_score = float('-inf')
    
    for move in legal_moves:
        score = evaluate_move(move)
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move

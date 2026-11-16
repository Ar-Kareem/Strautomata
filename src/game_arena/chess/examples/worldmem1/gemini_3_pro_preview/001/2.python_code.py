
import re

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    """
    A smart 1-ply chess policy that evaluates moves based on material gain, 
    tactical safety (pawn threats), and positional heuristics.
    """
    
    # --- Configuration ---
    # Material values: P=1, N=3, B=3.2, R=5, Q=9, K=0 (King safety handled via legality/checks)
    piece_values = {'P': 1, 'N': 3, 'B': 3.2, 'R': 5, 'Q': 9, 'K': 0}
    
    # Board coordinate helpers
    files = 'abcdefgh'
    ranks = '12345678'
    files_map = {c: i for i, c in enumerate(files)}
    ranks_map = {c: i for i, c in enumerate(ranks)}
    
    def get_sq_str(f_idx, r_idx):
        if 0 <= f_idx < 8 and 0 <= r_idx < 8:
            return files[f_idx] + ranks[r_idx]
        return None

    def parse_sq_str(sq):
        if sq and len(sq) == 2 and sq[0] in files_map and sq[1] in ranks_map:
            return files_map[sq[0]], ranks_map[sq[1]]
        return None, None

    # --- Pre-computation: Safety Map ---
    # Identify all squares attacked by opponent pawns to avoid hanging pieces.
    
    my_color = 'w' if to_play == 'white' else 'b'
    opp_color = 'b' if to_play == 'white' else 'w'
    opp_pawn_code = opp_color + 'P'
    
    # Determine opponent pawn direction (rank index delta)
    # White pawns rank 2->8 (idx increase). Black pawns rank 7->1 (idx decrease).
    # If I am White, opponent is Black (idx decreases).
    opp_dy = -1 if to_play == 'white' else 1
    
    opp_pawn_attacks = set()
    
    for sq, code in pieces.items():
        if code == opp_pawn_code:
            f, r = parse_sq_str(sq)
            if f is not None:
                # Pawns capture diagonally forward
                for df in [-1, 1]:
                    chk_sq = get_sq_str(f + df, r + opp_dy)
                    if chk_sq:
                        opp_pawn_attacks.add(chk_sq)
    
    # --- Move Evaluation ---
    
    best_move = legal_moves[0] if legal_moves else ''
    best_score = -float('inf')
    
    # Squares of interest
    center_sqs = {'d4', 'd5', 'e4', 'e5'}
    dev_sqs = {'c3', 'f3', 'c6', 'f6', 'd3', 'e3', 'd6', 'e6'}

    for move in legal_moves:
        score = 0.0
        
        # 1. Immediate Game Enders
        if '#' in move:
            score += 20000.0 # Checkmate is best
        elif '+' in move:
            score += 50.0 # Checks are disruptive
            
        # 2. Parse Move Details
        # Identify piece type
        piece_type = 'P' # Default to pawn
        if move[0] in 'NBRQK':
            piece_type = move[0]
        elif 'O-O' in move:
            piece_type = 'K'
            score += 60.0 # Bonus for castling (safety + dev)
            
        # Identify Target Square
        target_sq = None
        if 'O-O' in move:
            # Castling destination
            r_char = '1' if to_play == 'white' else '8'
            target_sq = ('g' if move == 'O-O' else 'c') + r_char
        else:
            # Extract target from algebraic string (last matching coordinate)
            # Regex finds all squares; last one is usually destination (e.g. Nbd7, R1a3)
            # Exclude promotion artifacts like '=Q' which regex won't match anyway mostly
            matches = re.findall(r'[a-h][1-8]', move)
            if matches:
                target_sq = matches[-1]

        # 3. Material (Captures & Promotions)
        captured_val = 0
        if 'x' in move:
            # Determine victim value
            victim_code = pieces.get(target_sq)
            if victim_code:
                # Standard capture
                captured_val = piece_values.get(victim_code[1], 0)
            elif piece_type == 'P':
                # En Passant (target square is empty in `pieces` but we capture a pawn)
                captured_val = 1 
            else:
                 # Fallback if state slightly desync or weird notation
                 captured_val = 1 

            aggressor_val = piece_values.get(piece_type, 0)
            
            # MVV-LVA scoring
            # Gain victim value
            score += captured_value * 100.0
            # Tie-break/Risk adjustment: prefer capturing with lower value piece
            score -= (aggressor_val * 0.1)

        if '=' in move:
            # Promotion
            promo_p = move.split('=')[1][0] # e.g., "a8=Q" -> 'Q'
            score += piece_values.get(promo_p, 0) * 100.0
            
        # 4. Tactical Safety (Avoid Blunders)
        # If moving to a square attacked by a pawn, apply penalty
        if target_sq in opp_pawn_attacks:
            my_val = piece_values.get(piece_type, 1)
            # Penalty: anticipate losing the piece
            # Note: if we captured something valuable, correct score is (Capture - MyVal).
            # Current score has +Capture. Now subtract MyVal.
            score -= my_val * 100.0
        
        # 5. Positional Heuristics
        if target_sq:
            # Control Center
            if target_sq in center_sqs:
                score += 10.0
            elif target_sq in dev_sqs:
                score += 5.0
                
            # Encouraging Pawn pushes in center files
            if piece_type == 'P' and target_sq[0] in 'de':
                score += 5.0
                
        # Develop Minor Pieces
        if piece_type in ['N', 'B']:
            score += 3.0
            
        # Penalize King exposure (unless endgame/castling)
        if piece_type == 'K' and 'O-O' not in move:
            # Primitive check: if board is crowded, don't walk King around
            if len(pieces) > 12:
                score -= 20.0

        # Update best
        if score > best_score:
            best_score = score
            best_move = move
            
    return best_move, memory

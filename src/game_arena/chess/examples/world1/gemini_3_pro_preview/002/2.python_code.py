
import random

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    # --- Constants & Helpers ---
    FILES = 'abcdefgh'
    RANKS = '12345678'
    # Simplified piece values
    PIECE_VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}
    
    my_color = 'w' if to_play == 'white' else 'b'
    enemy_color = 'b' if to_play == 'white' else 'w'
    
    def to_coords(sq):
        return RANKS.index(sq[1]), FILES.index(sq[0]) # returns (row, col) i.e., (rank_idx, file_idx)
    
    def to_sq(r, f):
        return FILES[f] + RANKS[r]
        
    def is_on_board(r, f):
        return 0 <= r < 8 and 0 <= f < 8
        
    def get_piece(board, r, f):
        return board.get(to_sq(r, f))

    # --- Attack Logic ---
    def get_attackers(board, r, f, attacker_col):
        # Returns list of pieces of attacker_col explicitly attacking (r,f)
        attackers = []
        
        # 1. Pawns
        # If attacker is White, they are at r-1. Black at r+1.
        p_r = r - 1 if attacker_col == 'w' else r + 1
        for dc in [-1, 1]:
            if is_on_board(p_r, f + dc):
                pc = get_piece(board, p_r, f + dc)
                if pc == attacker_col + 'P':
                    attackers.append(pc)
                    
        # 2. Knights
        kn_shifts = [(1,2), (1,-2), (-1,2), (-1,-2), (2,1), (2,-1), (-2,1), (-2,-1)]
        for dr, df in kn_shifts:
            if is_on_board(r+dr, f+df):
                pc = get_piece(board, r+dr, f+df)
                if pc == attacker_col + 'N':
                    attackers.append(pc)
                    
        # 3. Sliding (B, R, Q) & King
        dirs_diag = [(-1,-1), (-1,1), (1,-1), (1,1)]
        dirs_strt = [(-1,0), (1,0), (0,-1), (0,1)]
        
        # Diagonals (B, Q, K)
        for dr, df in dirs_diag:
            cr, cf = r+dr, f+df
            dist = 0
            while is_on_board(cr, cf):
                dist += 1
                pc = get_piece(board, cr, cf)
                if pc:
                    if pc[0] == attacker_col:
                        if pc[1] in 'BQ': attackers.append(pc)
                        if pc[1] == 'K' and dist == 1: attackers.append(pc)
                    break 
                cr, cf = cr+dr, cf+df
                
        # Straight (R, Q, K)
        for dr, df in dirs_strt:
            cr, cf = r+dr, f+df
            dist = 0
            while is_on_board(cr, cf):
                dist += 1
                pc = get_piece(board, cr, cf)
                if pc:
                    if pc[0] == attacker_col:
                        if pc[1] in 'RQ': attackers.append(pc)
                        if pc[1] == 'K' and dist == 1: attackers.append(pc)
                    break
                cr, cf = cr+dr, cf+df
                
        return attackers

    # --- Move Parsing ---
    def parse_san(move):
        # Returns (target_r, target_f, piece_type, promotion_type)
        # Remove annotations
        clean = move.replace('+', '').replace('#', '').replace('x', '')
        prom = None
        if '=' in clean:
            parts = clean.split('=')
            clean = parts[0]
            prom = parts[1]
            
        target_str = clean[-2:]
        tr, tf = to_coords(target_str)
        
        # Determine piece type
        p_type = 'P'
        if clean[0].isupper():
            p_type = clean[0]
            
        return tr, tf, p_type, prom

    # --- Main Selection Loop ---
    # Default to first legal move
    best_move = legal_moves[0]
    best_score = -float('inf')
    
    for move in legal_moves:
        # Priority 1: Checkmate
        if '#' in move: return move
        
        score = 0
        
        # Special Case: Castling
        # Treat castling as a positional bonus move (safe king, active rook)
        if 'O-O' in move:
            score = 60 # Better than nothing, usually good
            # Minimal randomness
            score += random.random()
            if score > best_score:
                best_score = score
                best_move = move
            continue

        # Parse Standard Move
        try:
            tr, tf, p_type, prom = parse_san(move)
        except:
            # If parsing fails for edge cases, skip logic
            continue

        target_sq = to_sq(tr, tf)
        
        # 1. Determine Capture Value
        captured_val = 0
        if target_sq in pieces:
            enemy_piece = pieces[target_sq]
            captured_val = PIECE_VALUES.get(enemy_piece[1], 0)
        elif 'x' in move and p_type == 'P':
            # En Passant
            captured_val = 100
        
        # 2. Determine Moving Piece Value
        my_val = PIECE_VALUES.get(prom if prom else p_type, 100)
        
        # 3. Positional Bonus (Center Control)
        # Ranks 3,4 (0-indexed) and Files 3,4 (d, e)
        if 3 <= tr <= 4 and 3 <= tf <= 4:
            score += 20
        elif 2 <= tr <= 5 and 2 <= tf <= 5:
            score += 10
            
        # 4. Promotion Bonus
        if prom:
            score += (PIECE_VALUES.get(prom, 0) - 100) # Net gain from pawn

        # 5. Safety / Exchange Calculation
        # Simulate the board state LOCALLY to check for threats
        sim_board = pieces.copy()
        sim_board[target_sq] = my_color + (prom if prom else p_type)
        # Note: We do not remove the piece from source because source resolution is complex.
        # Leaving the "ghost" piece at source might block some attack lines, making us 'optimistic'.
        # However, checking if the destination is attacked is the primary safety concern.
        
        attackers = get_attackers(sim_board, tr, tf, enemy_color)
        
        score += captured_val
        
        if attackers:
            # If the square we move to is attacked, assume we trade.
            # Score = Gained (captured) - Lost (my piece)
            # This handles:
            #  - Hanging a piece (Gained=0, Lost=Val) -> Negative score
            #  - Bad trade (Gained=320, Lost=500) -> Negative score
            #  - Good trade (Gained=900, Lost=500) -> Positive score
            #  - Equal trade (Gained=320, Lost=320) -> Neutral (0)
            score -= my_val
            
            # Simple heuristic: heavily discourage King exposure even if trade seems equal
            if p_type == 'K':
                score -= 1000

        # Small randomness to prevent deterministic loops in equal positions
        score += random.random() 

        if score > best_score:
            best_score = score
            best_move = move
            
    return best_move

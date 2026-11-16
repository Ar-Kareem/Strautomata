
import math
import random
import re

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    """
    A heuristic policy for Chess. Evaluates legal moves based on material, 
    safety (hanging pieces), and positional Piece-Square Tables.
    """
    
    # ---------------- Constants & Config ---------------- #
    
    PIECE_VALUES = {
        'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000
    }
    
    # Simplified Piece-Square Tables (PST) - flipped for black naturally by index mapping
    # Oriented for White (Rank 0 = 1st rank, Rank 7 = 8th rank)
    PST = {
        'P': [
            [ 0,  0,  0,  0,  0,  0,  0,  0],
            [ 5, 10, 10,-20,-20, 10, 10,  5],
            [ 5, -5,-10,  0,  0,-10, -5,  5],
            [ 0,  0,  0, 20, 20,  0,  0,  0],
            [ 5,  5, 10, 25, 25, 10,  5,  5],
            [10, 10, 20, 30, 30, 20, 10, 10],
            [50, 50, 50, 50, 50, 50, 50, 50],
            [ 0,  0,  0,  0,  0,  0,  0,  0]
        ],
        'N': [
            [-50,-40,-30,-30,-30,-30,-40,-50],
            [-40,-20,  0,  5,  5,  0,-20,-40],
            [-30,  5, 10, 15, 15, 10,  5,-30],
            [-30,  0, 15, 20, 20, 15,  0,-30],
            [-30,  5, 15, 20, 20, 15,  5,-30],
            [-30,  0, 10, 15, 15, 10,  0,-30],
            [-40,-20,  0,  0,  0,  0,-20,-40],
            [-50,-40,-30,-30,-30,-30,-40,-50]
        ],
        'B': [
            [-20,-10,-10,-10,-10,-10,-10,-20],
            [-10,  5,  0,  0,  0,  0,  5,-10],
            [-10, 10, 10, 10, 10, 10, 10,-10],
            [-10,  0, 10, 10, 10, 10,  0,-10],
            [-10,  5,  5, 10, 10,  5,  5,-10],
            [-10,  0,  5, 10, 10,  5,  0,-10],
            [-10,  0,  0,  0,  0,  0,  0,-10],
            [-20,-10,-10,-10,-10,-10,-10,-20]
        ],
        'R': [
            [  0,  0,  0,  5,  5,  0,  0,  0],
            [ -5,  0,  0,  0,  0,  0,  0, -5],
            [ -5,  0,  0,  0,  0,  0,  0, -5],
            [ -5,  0,  0,  0,  0,  0,  0, -5],
            [ -5,  0,  0,  0,  0,  0,  0, -5],
            [ -5,  0,  0,  0,  0,  0,  0, -5],
            [  5, 10, 10, 10, 10, 10, 10,  5],
            [  0,  0,  0,  0,  0,  0,  0,  0]
        ],
        'Q': [
            [-20,-10,-10, -5, -5,-10,-10,-20],
            [-10,  0,  0,  0,  0,  0,  0,-10],
            [-10,  0,  5,  5,  5,  5,  0,-10],
            [ -5,  0,  5,  5,  5,  5,  0, -5],
            [  0,  0,  5,  5,  5,  5,  0, -5],
            [-10,  5,  5,  5,  5,  5,  0,-10],
            [-10,  0,  5,  0,  0,  0,  0,-10],
            [-20,-10,-10, -5, -5,-10,-10,-20]
        ],
        'K': [
            [ 20, 30, 10,  0,  0, 10, 30, 20],
            [ 20, 20,  0,  0,  0,  0, 20, 20],
            [-10,-20,-20,-20,-20,-20,-20,-10],
            [-20,-30,-30,-40,-40,-30,-30,-20],
            [-30,-40,-40,-50,-50,-40,-40,-30],
            [-30,-40,-40,-50,-50,-40,-40,-30],
            [-30,-40,-40,-50,-50,-40,-40,-30],
            [-30,-40,-40,-50,-50,-40,-40,-30]
        ]
    }

    # ---------------- Helper Functions ---------------- #
    
    def sq_to_idx(sq):
        # 'a1' -> (0, 0), 'h8' -> (7, 7)
        f = ord(sq[0]) - ord('a')
        r = int(sq[1]) - 1
        return r, f

    def idx_to_sq(r, f):
        return f"{chr(f + ord('a'))}{r + 1}"

    # Build dense board
    # board[r][f] = code (e.g. 'wP') or None
    board = [[None for _ in range(8)] for _ in range(8)]
    my_color_char = 'w' if to_play == 'white' else 'b'
    opp_color_char = 'b' if to_play == 'white' else 'w'
    
    my_pieces = [] # list of (r, f, type) for fast lookup
    
    for sq, p_code in pieces.items():
        r, f = sq_to_idx(sq)
        board[r][f] = p_code
        if p_code[0] == my_color_char:
            my_pieces.append((r, f, p_code[1]))

    def get_pst_score(ptype, r, f, color_char):
        if ptype not in PST: return 0
        # If white, use r directly. If black, mirror r (r=7 is home, r=0 is promotion)
        row = r if color_char == 'w' else 7 - r
        return PST[ptype][row][f]

    def is_on_board(r, f):
        return 0 <= r < 8 and 0 <= f < 8

    def is_attacked(r, f, by_color_char):
        # Check if square (r,f) is attacked by any piece of `by_color_char`.
        # This is expensive, so we optimize.
        
        # 1. Pawn attacks
        pawn_dir = -1 if by_color_char == 'w' else 1 # White attacks 'up' (positive rank index relative to them? No. White pawns at r=1 attack r=2. So direction from pawn is +1. From target is -1)
        # Wait, simple logic: check (r - pawn_dir, f +/- 1) for enemy pawn.
        # White pawns move +1 rank. Attacking a square at R means pawns at R-1.
        p_dir = 1 if by_color_char == 'w' else -1 
        # Check for pawns at (r - p_dir)
        check_r = r - p_dir
        if 0 <= check_r < 8:
            for dc in [-1, 1]:
                if 0 <= f + dc < 8:
                    p = board[check_r][f+dc]
                    if p and p[0] == by_color_char and p[1] == 'P':
                        return True
        
        # 2. Knight attacks
        n_moves = [(2,1), (2,-1), (-2,1), (-2,-1), (1,2), (1,-2), (-1,2), (-1,-2)]
        for dr, df in n_moves:
            nr, nf = r + dr, f + df
            if is_on_board(nr, nf):
                p = board[nr][nf]
                if p and p[0] == by_color_char and p[1] == 'N':
                    return True
        
        # 3. King attacks
        k_moves = [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]
        for dr, df in k_moves:
            nr, nf = r + dr, f + df
            if is_on_board(nr, nf):
                p = board[nr][nf]
                if p and p[0] == by_color_char and p[1] == 'K':
                    return True
                    
        # 4. Sliding pieces (R, B, Q)
        # Orthogonal
        orth_dirs = [(1,0), (-1,0), (0,1), (0,-1)]
        for dr, df in orth_dirs:
            cr, cf = r + dr, f + df
            while is_on_board(cr, cf):
                p = board[cr][cf]
                if p:
                    if p[0] == by_color_char and p[1] in ['R', 'Q']:
                        return True
                    break # Blocked
                cr += dr
                cf += df
        
        # Diagonal
        diag_dirs = [(1,1), (1,-1), (-1,1), (-1,-1)]
        for dr, df in diag_dirs:
            cr, cf = r + dr, f + df
            while is_on_board(cr, cf):
                p = board[cr][cf]
                if p:
                    if p[0] == by_color_char and p[1] in ['B', 'Q']:
                        return True
                    break # Blocked
                cr += dr
                cf += df
                
        return False

    def get_source_from_san(san_move, target_r, target_f, p_type):
        """
        Deduce which piece moved based on the SAN string, piece type, and target.
        Handles disambiguation (e.g. 'Nbd7').
        """
        # Extract hint if any. e.g. Nbd7 -> hint 'b'. N5f3 -> hint '5'. Nexf3 -> hint 'e'.
        # Remove suffix '+', '#', check promotion.
        clean = san_move.rstrip("+#").split('=')[0] # Remove promotion part
        
        # Regex to capture hints. 
        # Structure: [Piece][Hint?][x?][Target]
        # But we know P_type.
        
        # If castling, handled separately in main loop.
        
        # Identify source coordinates candidates
        candidates = []
        
        for (r, f, pt) in my_pieces:
            if pt != p_type: continue
            
            # Check geometric plausibility
            valid_geom = False
            
            dr = target_r - r
            df = target_f - f
            
            if p_type == 'N':
                if abs(dr) * abs(df) == 2: valid_geom = True
            elif p_type == 'P':
                # Pawn logic (simplified, assuming move is legal)
                direction = 1 if my_color_char == 'w' else -1
                # Move forward 1
                if df == 0 and dr == direction: valid_geom = True
                # Move forward 2
                elif df == 0 and dr == 2 * direction and ( (r==1 and direction==1) or (r==6 and direction==-1) ): valid_geom = True
                # Capture
                elif abs(df) == 1 and dr == direction: valid_geom = True
            elif p_type == 'K':
                if max(abs(dr), abs(df)) == 1: valid_geom = True
            elif p_type in ['B', 'R', 'Q']:
                # Ray check
                if (p_type == 'B' and abs(dr) != abs(df)): pass
                elif (p_type == 'R' and dr != 0 and df != 0): pass
                elif (p_type == 'Q' and (abs(dr) != abs(df) and dr != 0 and df != 0)): pass
                else:
                    # Check path clear
                    step_r = 0 if dr == 0 else (1 if dr > 0 else -1)
                    step_f = 0 if df == 0 else (1 if df > 0 else -1)
                    cr, cf = r + step_r, f + step_f
                    blocked = False
                    while (cr, cf) != (target_r, target_f):
                        if board[cr][cf] is not None:
                            blocked = True
                            break
                        cr += step_r
                        cf += step_f
                    if not blocked: valid_geom = True
            
            if valid_geom:
                candidates.append((r, f))
        
        # Filter by hint
        # Hint is usually in clean string between piece char and target
        # Standard: Piece usually 0th char (unless P). Target is last 2.
        # Hint is in between. Remove 'x'.
        
        if len(candidates) == 0: return None # Should not happen for legal moves
        if len(candidates) == 1: return candidates[0]
        
        # Disambiguation logic: match file or rank char in string
        hint_match = []
        for cand in candidates:
            cr, cf = cand
            c_file = chr(cf + ord('a'))
            c_rank = str(cr + 1)
            
            # Simple check: does the move string contain the rank or file of the source?
            # We must permit "Nbd7" (contains 'b') but also "Nb1d2" (contains 'b', '1') is rare but possible.
            # We strip the target and piece type from string to find hint.
            
            target_str = clean[-2:]
            
            # Start index: 0 if pawn, else 1
            start_idx = 0 if p_type == 'P' else 1
            prefix = clean[start_idx : -2].replace('x', '')
            
            if not prefix: 
                # Ambiguity exists but no hint? Usually engine won't give ambiguous move without hint.
                # Just take first.
                hint_match.append(cand)
            else:
                # Check if prefix matches file or rank
                if prefix in c_file or prefix in c_rank or prefix == (c_file + c_rank):
                    hint_match.append(cand)
        
        if hint_match: return hint_match[0]
        return candidates[0]

    # ---------------- Main Scoring Loop ---------------- #

    best_move = None
    best_score = -float('inf')
    
    # Shuffle checks to perform random choice on ties naturally
    random.shuffle(legal_moves)
    
    for move in legal_moves:
        score = 0
        
        # 1. Immediate Mate
        if '#' in move:
            return move
        
        # 2. Parse Move
        # Detect Castling
        is_castling = 'O-O' in move
        piece_type = 'P'
        target_sq_str = ''
        target_r, target_f = -1, -1
        source_r, source_f = -1, -1
        
        if is_castling:
            piece_type = 'K'
            # Determine target for King
            r = 0 if my_color_char == 'w' else 7
            source_r, source_f = r, 4  # e1/e8
            if move == 'O-O': # Kingside
                target_r, target_f = r, 6 # g1/g8
            else: # Queenside
                target_r, target_f = r, 2 # c1/c8
        else:
            # Standard SAN
            # Get Piece Type
            first_char = move[0]
            if first_char in ['N', 'B', 'R', 'Q', 'K']:
                piece_type = first_char
            else:
                piece_type = 'P' # Pawn moves often start with file e.g. 'e4', 'exd5'
            
            # Get Target Square (last 2 chars before suffix)
            # Suffixes: +, #, =Q
            trunc = move.replace('+', '').replace('#', '')
            promotion = None
            if '=' in trunc:
                parts = trunc.split('=')
                promotion = parts[1] # e.g. Q
                trunc = parts[0]
                score += PIECE_VALUES.get(promotion, 0) - PIECE_VALUES['P']
            
            target_sq_str = trunc[-2:]
            if re.match(r'[a-h][1-8]', target_sq_str):
                target_r, target_f = sq_to_idx(target_sq_str)
                source_coords = get_source_from_san(move, target_r, target_f, piece_type)
                if source_coords:
                    source_r, source_f = source_coords
            else:
                # Parsing failed (rare), skip logic
                source_r, source_f = -1, -1
        
        if source_r != -1:
            # 3. Material Evaluation (Capture)
            captured_piece_val = 0
            # Check target on board
            victim = board[target_r][target_f]
            if victim:
                captured_piece_val = PIECE_VALUES.get(victim[1], 0)
            elif piece_type == 'P' and 'x' in move: 
                # En Passant likely
                captured_piece_val = PIECE_VALUES['P']
            
            score += captured_piece_val * 1.5  # Weight captures
            
            # 4. Positional (PST)
            pst_diff = get_pst_score(piece_type, target_r, target_f, my_color_char) - \
                       get_pst_score(piece_type, source_r, source_f, my_color_char)
            score += pst_diff * 0.1 # Weight structural less than material
            
            # 5. Safety / Tactics
            
            my_val = PIECE_VALUES[piece_type]
            
            # Is Target Attacked?
            # To do this accurately, we should simulate the move on a temp board, but 
            # for speed/simplicity, we check attacks on current board. 
            # Note: Capturing an enemy removes their attack, so we must be careful not to check 'victim'.
            # Limitation: Ray attacks through the moving piece (discovered attacks) are not detected.
            # We assume static analysis.
            
            under_attack_at_dest = is_attacked(target_r, target_f, opp_color_char)
            
            if under_attack_at_dest:
                # SEE approximation
                # If we capture something, we get Value(Victim). If we lose ours, we lose Value(Self).
                # Score change = Val(Victim) - Val(Self) (if not protected? assume we lose it).
                # We already added Val(Victim). Now subtract Val(Self) if hanging.
                # Only subtract if the exchange is bad.
                
                trade_score = captured_piece_val - my_val
                
                # If trade is negative (e.g. QxP and Q is lost), BIG penalty.
                if trade_score < 0:
                    score += trade_score # Penalty
            
            # Was Source safe? Or were we hanging?
            # If we move a piece that is currently attacked, that is good.
            under_attack_at_source = is_attacked(source_r, source_f, opp_color_char)
            if under_attack_at_source:
                # Bonus for escaping
                # Only if destination is not instant death or bad trade
                if not under_attack_at_dest or (captured_piece_val > my_val):
                    score += my_val * 0.5 # Escape bonus
                    
            # 6. King Safety Heuristic
            # Penalize moving King to center or corners early game? Handled by PST.
            # Penalize opening castled position? Hard to detect without full state.
            
            # Promotion bias
            if '=' in move:
                score += 800
        
        if score > best_score:
            best_score = score
            best_move = move
            
    # Fallback
    if best_move is None:
        return legal_moves[0]
        
    return best_move

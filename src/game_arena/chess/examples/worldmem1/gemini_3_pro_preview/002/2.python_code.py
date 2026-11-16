
import math

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    """
    A 1-ply greedy policy that parses SAN moves, applies them to a state representation,
    and evaluates the resulting position using Material + Piece-Square Tables.
    """
    
    # --- Constants & Heuristics ---
    
    # Piece values
    P_VAL, N_VAL, B_VAL, R_VAL, Q_VAL, K_VAL = 100, 320, 330, 500, 900, 20000
    VALUES = {'P': P_VAL, 'N': N_VAL, 'B': B_VAL, 'R': R_VAL, 'Q': Q_VAL, 'K': K_VAL}
    
    # Simplified Piece-Square Tables (interpolated for 8x8) from perspective of White
    # We will mirror these for Black.
    # Arrays are 64 length, 0=a1, 7=h1, ..., 63=h8
    
    def make_pst(base_list):
        # Helper to map 8x8 visual grid to index list
        return list(reversed(base_list)) 

    # Tables defined from rank 8 (top) to rank 1 (bottom) as standard visual
    Pawn_PST = [
        0,  0,  0,  0,  0,  0,  0,  0,
        50, 50, 50, 50, 50, 50, 50, 50,
        10, 10, 20, 30, 30, 20, 10, 10,
        5,  5, 10, 25, 25, 10,  5,  5,
        0,  0,  0, 20, 20,  0,  0,  0,
        5, -5,-10,  0,  0,-10, -5,  5,
        5, 10, 10,-20,-20, 10, 10,  5,
        0,  0,  0,  0,  0,  0,  0,  0
    ]
    
    Knight_PST = [
        -50,-40,-30,-30,-30,-30,-40,-50,
        -40,-20,  0,  0,  0,  0,-20,-40,
        -30,  0, 10, 15, 15, 10,  0,-30,
        -30,  5, 15, 20, 20, 15,  5,-30,
        -30,  0, 15, 20, 20, 15,  0,-30,
        -30,  5, 10, 15, 15, 10,  5,-30,
        -40,-20,  0,  5,  5,  0,-20,-40,
        -50,-40,-30,-30,-30,-30,-40,-50
    ]
    
    Bishop_PST = [
        -20,-10,-10,-10,-10,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5, 10, 10,  5,  0,-10,
        -10,  5,  5, 10, 10,  5,  5,-10,
        -10,  0, 10, 10, 10, 10,  0,-10,
        -10, 10, 10, 10, 10, 10, 10,-10,
        -10,  5,  0,  0,  0,  0,  5,-10,
        -20,-10,-10,-10,-10,-10,-10,-20
    ]
    
    Rook_PST = [
        0,  0,  0,  0,  0,  0,  0,  0,
        5, 10, 10, 10, 10, 10, 10,  5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        0,  0,  0,  5,  5,  0,  0,  0
    ]
    
    Queen_PST = [
        -20,-10,-10, -5, -5,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5,  5,  5,  5,  0,-10,
        -5,  0,  5,  5,  5,  5,  0, -5,
        0,  0,  5,  5,  5,  5,  0, -5,
        -10,  5,  5,  5,  5,  5,  0,-10,
        -10,  0,  5,  0,  0,  0,  0,-10,
        -20,-10,-10, -5, -5,-10,-10,-20
    ]

    # Convert visual grid to 0-63 list (0=a1)
    # The visual lists are Top-Left (a8) to Bottom-Right (h1) if read row by row.
    # 0=a1 corresponds to the last element of the last row of visual representation? No.
    # Algebraic: a1 is 0. Visual representation usually prints rank 8 first.
    # So index 0 (a1) is index 56 in a row-major 8x8 flattened list starting a8.
    
    def flip_pst(pst):
        # Input is 64 ints, starting a8...h8, a7...h7...
        # We want to access by sq index 0..63 where 0 is a1.
        # sq=0 (a1) is at index 56 in the array.
        # sq=7 (h1) is at index 63.
        # sq=8 (a2) is at index 48.
        recoded = [0]*64
        for r in range(8):
            for f in range(8):
                sq_idx = r * 8 + f
                # visual index: row (7-r), col f
                vis_idx = (7-r)*8 + f
                recoded[sq_idx] = pst[vis_idx]
        return recoded

    ps_tables = {
        'P': flip_pst(Pawn_PST),
        'N': flip_pst(Knight_PST),
        'B': flip_pst(Bishop_PST),
        'R': flip_pst(Rook_PST),
        'Q': flip_pst(Queen_PST),
        'K': [0]*64
    }

    # --- Helper Functions ---

    def sq_to_idx(s):
        f = ord(s[0]) - ord('a')
        r = int(s[1]) - 1
        return r * 8 + f

    def idx_to_sq(i):
        r = i // 8
        f = i % 8
        return f"{chr(f + ord('a'))}{r + 1}"

    def get_piece_at(board_map, idx):
        return board_map.get(idx_to_sq(idx), None)

    # Convert input pieces dict to an optimized map {idx: code}
    board = {sq_to_idx(k): v for k, v in pieces.items()}
    
    my_color = 'w' if to_play == 'white' else 'b'

    def evaluate(current_board):
        score = 0
        w_mat, b_mat = 0, 0
        
        for idx, code in current_board.items():
            c = code[0]
            pt = code[1]
            val = VALUES.get(pt, 0)
            
            # Position score
            pst_val = 0
            if pt in ps_tables:
                # If white, use index directly. If black, mirror index vertically.
                table_idx = idx if c == 'w' else (7 - (idx // 8)) * 8 + (idx % 8)
                pst_val = ps_tables[pt][table_idx]
            
            total = val + pst_val
            
            if c == 'w':
                score += total
                w_mat += val
            else:
                score -= total
                b_mat += val

        # Simple endgame logic: drive enemy king to edge? (omitted for brevity)
        
        # Return score relative to `to_play`
        if to_play == 'white':
            return score
        else:
            return -score

    def is_path_clear(board_map, start, end):
        r1, f1 = start // 8, start % 8
        r2, f2 = end // 8, end % 8
        dr = r2 - r1
        df = f2 - f1
        step_r = (dr // abs(dr)) if dr != 0 else 0
        step_f = (df // abs(df)) if df != 0 else 0
        
        curr = start + step_r * 8 + step_f
        while curr != end:
            if curr in board_map:
                return False
            curr += step_r * 8 + step_f
        return True

    def get_valid_source(move_san, target_idx, board_map, is_capture):
        # This function tries to identify which piece moved based on SAN
        # Returns source_idx or None
        
        # Clean move string
        # Handle Castling
        if move_san == 'O-O' or move_san == 'O-O-O':
            # King moves
            rank = 0 if my_color == 'w' else 7
            king_src = rank * 8 + 4 # e1/e8
            return king_src

        clean = move_san.replace('+', '').replace('#', '')
        promotion = None
        if '=' in clean:
            parts = clean.split('=')
            clean = parts[0]
            promotion = parts[1] # Q, R, B, N

        # Parse target info is already known (target_idx passed in loop)
        # We need piece type and specifiers
        # Logic: last two chars are target. Before that is optional 'x'. Before that is source spec.
        
        target_str = idx_to_sq(target_idx) # Re-verify
        
        # Remove target from string
        # Problem: capture 'exd5', 'Nf3', 'Raxd1'
        # Heuristic:
        # 1. Determine Piece Type
        ptype = 'P'
        if clean[0] in 'NBRQK':
            ptype = clean[0]
            prefix = clean[1:]
        else:
            prefix = clean # Pawn move
        
        # Remove target (last 2 chars)
        prefix = prefix.replace('x', '')
        prefix = prefix[:-2] # Should be disambiguation info
        
        disambig_file = None
        disambig_rank = None
        if len(prefix) > 0:
            if prefix[0].isalpha():
                disambig_file = ord(prefix[0]) - ord('a')
            if prefix[-1].isdigit():
                disambig_rank = int(prefix[-1]) - 1
                if len(prefix) == 2 and prefix[0].isalpha(): # e.g. 'e1' in 'Qe1xf2' rare
                     disambig_file = ord(prefix[0]) - ord('a')

        # Find candidates
        candidates = []
        for loc, code in board_map.items():
            if code[0] != my_color: continue
            if code[1] != ptype: continue
            
            # File/Rank Filters
            r, f = loc // 8, loc % 8
            if disambig_file is not None and f != disambig_file: continue
            if disambig_rank is not None and r != disambig_rank: continue
            
            # Geometric Checks
            tr, tf = target_idx // 8, target_idx % 8
            dr, df = tr - r, tf - f
            
            can_move = False
            if ptype == 'N':
                if (abs(dr), abs(df)) in [(1,2), (2,1)]: can_move = True
            elif ptype == 'K':
                if max(abs(dr), abs(df)) == 1: can_move = True
            elif ptype == 'P':
                direction = 1 if my_color == 'w' else -1
                # Capture
                if is_capture:
                    if dr == direction and abs(df) == 1: can_move = True
                else:
                    # Push
                    if abs(df) == 0:
                        if dr == direction: can_move = True
                        if dr == 2 * direction and ((r==1 and my_color=='w') or (r==6 and my_color=='b')):
                             # Check path clear for double push
                             mid = loc + 8*direction
                             if mid not in board_map: can_move = True
            elif ptype in 'BRQ':
                # Check line
                is_diag = abs(dr) == abs(df)
                is_orth = dr == 0 or df == 0
                if (ptype == 'B' and is_diag) or \
                   (ptype == 'R' and is_orth) or \
                   (ptype == 'Q' and (is_diag or is_orth)):
                    if is_path_clear(board_map, loc, target_idx):
                        can_move = True
            
            if can_move:
                candidates.append(loc)
        
        # If multiple candidates, we rely on the fact that legal_moves implies uniqueness 
        # combined with disambig. If we still have multiple, pick first (rare in valid SAN).
        if candidates:
            return candidates[0]
        return None

    def apply_move(board_map, move_san):
        new_board = board_map.copy()
        
        # Check special: Castling
        if move_san == 'O-O':
            rank = 0 if my_color == 'w' else 7
            k_src, k_dst = rank*8+4, rank*8+6
            r_src, r_dst = rank*8+7, rank*8+5
            code = my_color + 'K'
            # Move King
            if k_src in new_board: del new_board[k_src]
            new_board[k_dst] = code
            # Move Rook
            if r_src in new_board: del new_board[r_src]
            new_board[r_dst] = my_color + 'R'
            return new_board
        elif move_san == 'O-O-O':
            rank = 0 if my_color == 'w' else 7
            k_src, k_dst = rank*8+4, rank*8+2
            r_src, r_dst = rank*8+0, rank*8+3
            code = my_color + 'K'
            if k_src in new_board: del new_board[k_src]
            new_board[k_dst] = code
            if r_src in new_board: del new_board[r_src]
            new_board[r_dst] = my_color + 'R'
            return new_board

        # Standard Move
        # Extract target
        clean = move_san.replace('+', '').replace('#', '')
        promo_piece = None
        if '=' in clean:
            clean, p_char = clean.split('=')
            promo_piece = my_color + p_char
            
        # Target square is last 2 chars
        target_sq = clean[-2:]
        target_idx = sq_to_idx(target_sq)
        is_capture = 'x' in move_san
        
        src_idx = get_valid_source(move_san, target_idx, board_map, is_capture)
        
        if src_idx is not None:
            piece = new_board.pop(src_idx)
            
            # Handle En Passant
            # If pawn moves diagonally to empty square, it's EP
            if piece[1] == 'P' and abs(src_idx % 8 - target_idx % 8) == 1 and target_idx not in board_map:
                # Capture pawn logic
                cap_idx = src_idx // 8 * 8 + target_idx % 8 # Same rank as source, file of target
                if cap_idx in new_board:
                    del new_board[cap_idx]
            
            # Promotion
            if promo_piece:
                piece = promo_piece
            
            new_board[target_idx] = piece
            
        return new_board

    # --- Main Search Logic ---
    
    best_move = legal_moves[0]
    best_score = -float('inf')
    
    # Try to sort legal moves by simple heuristics to improve robustness if time cuts (unlikely here)
    # Check captures and promotions first
    sorted_moves = sorted(legal_moves, key=lambda m: ('#' in m, 'x' in m, '=' in m), reverse=True)

    for move in sorted_moves:
        try:
            # Immediate Checkmate Check
            if '#' in move:
                return move, {}
                
            sim_board = apply_move(board, move)
            score = evaluate(sim_board)
            
            # Basic hanging piece heuristic (1-ply penalty)
            # Evaluate if the piece we just moved moved to a square attacked by a pawn?
            # This requires calculating attacked squares. Expensive.
            # Instead simple bonus:
            if '+' in move:
                score += 50
            if 'x' in move:
                score += 10 # small bonus to break ties towards aggression
            
            if score > best_score:
                best_score = score
                best_move = move
                
        except Exception:
            # Fallback if SAN parsing fails
            continue
            
    return best_move, {}

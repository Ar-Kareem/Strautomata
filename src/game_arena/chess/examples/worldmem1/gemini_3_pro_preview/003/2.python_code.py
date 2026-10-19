
import math

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    """
    Chess policy that evaluates legal moves based on material and positional heuristics (depth 1).
    """
    
    # --- Constants and Lookups ---
    
    FILE_MAP = {c: i for i, c in enumerate('abcdefgh')}
    RANK_MAP = {c: i for i, c in enumerate('12345678')}
    FILES = 'abcdefgh'
    RANKS = '12345678'
    
    # Material Values
    VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}
    
    # Piece Square Tables (Simplified for Midgame)
    # Defined for White. Mirror for Black.
    # Higher value = better square.
    PST_P = [
         0,  0,  0,  0,  0,  0,  0,  0,
        50, 50, 50, 50, 50, 50, 50, 50,
        10, 10, 20, 30, 30, 20, 10, 10,
         5,  5, 10, 25, 25, 10,  5,  5,
         0,  0,  0, 20, 20,  0,  0,  0,
         5, -5,-10,  0,  0,-10, -5,  5,
         5, 10, 10,-20,-20, 10, 10,  5,
         0,  0,  0,  0,  0,  0,  0,  0
    ]
    
    PST_N = [
        -50,-40,-30,-30,-30,-30,-40,-50,
        -40,-20,  0,  0,  0,  0,-20,-40,
        -30,  0, 10, 15, 15, 10,  0,-30,
        -30,  5, 15, 20, 20, 15,  5,-30,
        -30,  0, 15, 20, 20, 15,  0,-30,
        -30,  5, 10, 15, 15, 10,  5,-30,
        -40,-20,  0,  5,  5,  0,-20,-40,
        -50,-40,-30,-30,-30,-30,-40,-50
    ]
    
    PST_K = [
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -20,-30,-30,-40,-40,-30,-30,-20,
        -10,-20,-20,-20,-20,-20,-20,-10,
         20, 20,  0,  0,  0,  0, 20, 20,
         20, 30, 10,  0,  0, 10, 30, 20
    ]
    
    # Generic center bias for others
    PST_GEN = [
        -20,-10,-10,-10,-10,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5, 10, 10,  5,  0,-10,
        -10,  5,  5, 10, 10,  5,  5,-10,
        -10,  0, 10, 10, 10, 10,  0,-10,
        -10, 10, 10, 10, 10, 10, 10,-10,
        -10,  5,  0,  0,  0,  0,  5,-10,
        -20,-10,-10,-10,-10,-10,-10,-20
    ]
    
    PSTS = {'P': PST_P, 'N': PST_N, 'B': PST_GEN, 'R': PST_GEN, 'Q': PST_GEN, 'K': PST_K}

    # --- Utility Functions ---

    def parse_sq(sq_str):
        return FILE_MAP[sq_str[0]] + RANK_MAP[sq_str[1]] * 8

    def sq_to_str(idx):
        return FILES[idx % 8] + RANKS[idx // 8]

    def get_piece_at(board, idx):
        if 0 <= idx < 64:
            return board[idx]
        return None

    def get_attackers(board, target_sq, attacker_color):
        """Returns list of squares containing pieces of `attacker_color` attacking `target_sq`."""
        attackers = []
        # Pawn attacks
        pawn_dir = -1 if attacker_color == 'w' else 1 # Attack direction (pawns capture diagonally "forward" relative to their color)
        # However, checking incoming attacks means looking "backwards"
        # If I am looking for White pawns attacking Me (on target_sq), I look at target_sq + 7 and + 9?
        # NO. White pawns move +8. They attack +7 and +9. 
        # So a white pawn at `x` attacks `x+7` and `x+9`.
        # So to check if `target` is attacked by white pawn, check `target-7` and `target-9`.
        
        check_dirs = []
        if attacker_color == 'w':
            check_dirs = [-7, -9]
        else:
            check_dirs = [7, 9]

        for d in check_dirs:
            p_sq = target_sq + d
            if 0 <= p_sq < 64:
                # Boundary check: pawns wrap around board if we aren't careful with 1D array
                # Distance in file must be 1
                if abs((p_sq % 8) - (target_sq % 8)) == 1:
                    p = board[p_sq]
                    if p == attacker_color + 'P':
                        attackers.append(p_sq)
        
        # Knights
        n_moves = [-17, -15, -10, -6, 6, 10, 15, 17]
        for d in n_moves:
            src = target_sq + d
            if 0 <= src < 64:
                # Knight jump row/col diff check
                dr = abs((src // 8) - (target_sq // 8))
                df = abs((src % 8) - (target_sq % 8))
                if (dr == 1 and df == 2) or (dr == 2 and df == 1):
                    if board[src] == attacker_color + 'N':
                        attackers.append(src)
        
        # Sliding (B, R, Q) + King
        # Directions: Orthogonal (R, Q), Diagonal (B, Q)
        orth = [-8, -1, 1, 8]
        diag = [-9, -7, 7, 9]
        
        for dirs, piece_types in [(orth, ['R', 'Q']), (diag, ['B', 'Q'])]:
            for d in dirs:
                # Ray trace
                curr = target_sq
                dist = 0
                while True:
                    dist += 1
                    curr += d
                    if not (0 <= curr < 64): break
                    # Check wrapping
                    curr_f, prev_f = curr % 8, (curr - d) % 8
                    curr_r, prev_r = curr // 8, (curr - d) // 8
                    # If we moved straight/diag, coordinates change predictably. 
                    # Simpler wrapping check: |df| <= 1 and |dr| <= 1 for single step
                    if abs(curr_f - prev_f) > 1 or abs(curr_r - prev_r) > 1: break
                    
                    p = board[curr]
                    if p is not None:
                        if p[0] == attacker_color:
                            if p[1] in piece_types:
                                attackers.append(curr)
                            elif p[1] == 'K' and dist == 1:
                                attackers.append(curr) # King attack
                        break # Blocked by any piece
        return attackers

    def is_path_clear(board, start, end):
        """Check if straight/diagonal path is clear (exclusive of start and end)."""
        diff = end - start
        step = 0
        
        dr = (end // 8) - (start // 8)
        df = (end % 8) - (start % 8)
        
        if dr == 0: step = 1 if df > 0 else -1
        elif df == 0: step = 8 if dr > 0 else -8
        elif abs(dr) == abs(df): 
            # Diagonal
            r_step = 8 if dr > 0 else -8
            f_step = 1 if df > 0 else -1
            step = r_step + f_step
        else:
            return False # Not a line
            
        curr = start + step
        while curr != end:
            if board[curr] is not None:
                return False
            curr += step
        return True

    # --- Setup ---
    
    my_color = to_play[0] # 'w' or 'b'
    opp_color = 'b' if my_color == 'w' else 'w'
    
    # Board Init
    board_state = [None] * 64
    my_king_sq = 0
    
    for sq_code, piece_code in pieces.items():
        idx = parse_sq(sq_code)
        board_state[idx] = piece_code
        if piece_code == my_color + 'K':
            my_king_sq = idx

    def evaluate(board):
        score = 0
        
        for i in range(64):
            p = board[i]
            if p is None: continue
            
            p_color = p[0]
            p_type = p[1]
            val = VALUES[p_type]
            
            # PST Score
            pst_val = 0
            if p_type in PSTS:
                # Flip table for black
                table_idx = i if p_color == 'w' else 63 - i
                pst_val = PSTS[p_type][table_idx]
            
            term = val + pst_val
            
            if p_color == my_color:
                score += term
            else:
                score -= term
        return score

    # --- Move Parsing & Selection ---

    best_move = legal_moves[0] if legal_moves else '0000'
    best_eval = -float('inf')

    for move_str in legal_moves:
        # 1. Decode Move
        clean_move = move_str.replace('+', '').replace('#', '')
        
        src_sq = -1
        dst_sq = -1
        promotion = None
        moving_piece_type = 'P'
        is_castling = False
        
        # Castling
        if clean_move == 'O-O':
            is_castling = True
            if my_color == 'w':
                src_sq, dst_sq = 4, 6 # e1, g1
            else:
                src_sq, dst_sq = 60, 62 # e8, g8
            moving_piece_type = 'K'
        elif clean_move == 'O-O-O':
            is_castling = True
            if my_color == 'w':
                src_sq, dst_sq = 4, 2 # e1, c1
            else:
                src_sq, dst_sq = 60, 58 # e8, c8
            moving_piece_type = 'K'
        else:
            # Standard SAN
            if '=' in clean_move:
                parts = clean_move.split('=')
                clean_move = parts[0]
                promotion = parts[1]
            
            # Extract target
            target_str = clean_move[-2:]
            dst_sq = parse_sq(target_str)
            remainder = clean_move[:-2]
            
            # Extract capture
            if remainder.endswith('x'):
                remainder = remainder[:-1]
            
            # Extract Piece
            if len(remainder) > 0 and remainder[0].isupper():
                moving_piece_type = remainder[0]
                remainder = remainder[1:]
            
            # Remainder is now disambiguation (files 'a'-'h' or ranks '1'-'8')
            disambig = remainder
            
            # Find Source Candidate
            candidates = []
            
            # Scan all squares for possible source
            for idx in range(64):
                p = board_state[idx]
                if p == my_color + moving_piece_type:
                    # Check geometric validity first
                    
                    dr = abs(idx // 8 - dst_sq // 8)
                    df = abs(idx % 8 - dst_sq % 8)
                    
                    valid_geo = False
                    path_check_needed = False
                    
                    if moving_piece_type == 'N':
                        if (dr, df) in [(1,2), (2,1)]: valid_geo = True
                    elif moving_piece_type == 'B':
                        if dr == df: valid_geo = True; path_check_needed = True
                    elif moving_piece_type == 'R':
                        if dr == 0 or df == 0: valid_geo = True; path_check_needed = True
                    elif moving_piece_type == 'Q':
                        if (dr == df) or (dr == 0 or df == 0): valid_geo = True; path_check_needed = True
                    elif moving_piece_type == 'K':
                        if dr <= 1 and df <= 1: valid_geo = True
                    elif moving_piece_type == 'P':
                        # Pawn logic
                        direction = 1 if my_color == 'w' else -1
                        row_diff = (dst_sq // 8) - (idx // 8)
                        col_diff = (dst_sq % 8) - (idx % 8)
                        
                        target_empty = (board_state[dst_sq] is None)
                        
                        # Move forward
                        if col_diff == 0 and target_empty:
                            if row_diff == direction: valid_geo = True
                            elif row_diff == 2 * direction:
                                start_rank = 1 if my_color == 'w' else 6
                                if (idx // 8) == start_rank:
                                    valid_geo = True
                                    path_check_needed = True
                        # Capture
                        elif abs(col_diff) == 1 and row_diff == direction:
                            # Standard capture or En Passant
                            # We assume if SAN implies capture ('x'), it's valid
                            if 'x' in move_str or board_state[dst_sq] is not None:
                                valid_geo = True
                            # Note: En Passant is tricky to detect from static board if 'x' not in string (rare)
                            # But standard SAN usually includes 'x'. 
                            # If parser fails to see 'x' but it is a diagonal pawn move to empty square, it's EP.
                            elif board_state[dst_sq] is None:
                                valid_geo = True # EP

                    if valid_geo:
                        if path_check_needed:
                            if not is_path_clear(board_state, idx, dst_sq):
                                continue
                        
                        # Check disambiguation
                        src_str = sq_to_str(idx)
                        match = True
                        for char in disambig:
                            if char not in src_str:
                                match = False
                                break
                        if match:
                            candidates.append(idx)

            # Resolving ambiguity by checking legality (pseudo-legal move shouldn't expose King)
            real_candidates = []
            for c in candidates:
                # Simulate move to check if self-check
                # Simplified simulation just for check detection
                temp_board = list(board_state)
                temp_board[dst_sq] = temp_board[c]
                temp_board[c] = None
                
                # Find King (might be the mover)
                k_sq = my_king_sq
                if moving_piece_type == 'K': k_sq = dst_sq
                
                # Verify King safety
                if not get_attackers(temp_board, k_sq, opp_color):
                    real_candidates.append(c)
            
            if real_candidates:
                src_sq = real_candidates[0]
            else:
                # Should not happen with correct inputs. Fallback.
                continue

        # 2. Make Move (Simulation)
        new_board = list(board_state)
        new_board[dst_sq] = new_board[src_sq] # Move piece
        new_board[src_sq] = None
        
        # Handle Promotion
        if promotion:
            new_board[dst_sq] = my_color + promotion
        
        # Handle Castling (Move Rook)
        if is_castling:
            # White O-O: e1->g1 (handled), R h1->f1
            if dst_sq == 6:  # wK g1, R h1(7)->f1(5)
                new_board[5] = new_board[7]; new_board[7] = None
            elif dst_sq == 2: # wK c1, R a1(0)->d1(3)
                new_board[3] = new_board[0]; new_board[0] = None
            elif dst_sq == 62: # bK g8, R h8(63)->f8(61)
                new_board[61] = new_board[63]; new_board[63] = None
            elif dst_sq == 58: # bK c8, R a8(56)->d8(59)
                new_board[59] = new_board[56]; new_board[56] = None

        # Handle En Passant Capture
        if moving_piece_type == 'P' and (dst_sq % 8 != src_sq % 8) and board_state[dst_sq] is None:
            # Diagonal move to empty square = EP
            cap_sq = dst_sq - 8 if my_color == 'w' else dst_sq + 8
            new_board[cap_sq] = None

        # 3. Evaluate Result
        score = evaluate(new_board)
        
        # 4. Tactical Safety Filter
        # Check if the piece we just moved is hanging (attacked by lower value or undefended).
        # We only look at `dst_sq`.
        
        # Who attacks the destination?
        attackers = get_attackers(new_board, dst_sq, opp_color)
        if attackers:
            # Get value of piece at dst
            my_val = VALUES[new_board[dst_sq][1]]
            
            # Find cheapest attacker
            cheapest_attacker_val = 99999
            for atk_sq in attackers:
                atk_piece = new_board[atk_sq]
                v = VALUES[atk_piece[1]]
                if v < cheapest_attacker_val:
                    cheapest_attacker_val = v
            
            # Basic exchange logic:
            # If (my_val > cheapest_attacker) -> Bad (e.g. Q taken by P)
            # If (my_val <= cheapest_attacker) -> Maybe ok (exchange), but if undefended it's bad.
            # Simplified: If attacked by lower value, penalize heavily.
            if cheapest_attacker_val < my_val:
                score -= (my_val - cheapest_attacker_val) * 10
            
            # Check for simple hanging (attacked but not defended).
            # This requires `get_defenders` which is expensive.
            # Instead, we rely on the `evaluate` function's material score to catch loss next turn,
            # but standard evaluation doesn't see "next turn". 
            # So we penalize "Attacked Piece" slightly if trade is equal, to encourage solidity.
            elif cheapest_attacker_val == my_val:
                score -= 50 # Avoid tension if not necessary or profitable (simple engine preference)

        if score > best_eval:
            best_eval = score
            best_move = move_str

    return best_move, {}

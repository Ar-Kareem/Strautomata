
def policy(pieces: dict[str, str], to_play: str, memory: dict) -> tuple[str, dict]:
    # ---------------------------------------------------------
    # 1. BOARD INITIALIZATION & HELPERS
    # ---------------------------------------------------------
    
    # Piece values for evaluation
    VALUES = {'P': 100, 'N': 300, 'B': 320, 'R': 500, 'Q': 900, 'K': 20000}
    
    # Piece Square Tables (simplified for speed and generic play)
    # Defined relative to White (will be flipped for Black)
    PST = {
        'P': [
             0,  0,  0,  0,  0,  0,  0,  0,
            50, 50, 50, 50, 50, 50, 50, 50,
            10, 10, 20, 30, 30, 20, 10, 10,
             5,  5, 10, 25, 25, 10,  5,  5,
             0,  0,  0, 20, 20,  0,  0,  0,
             5, -5,-10,  0,  0,-10, -5,  5,
             5, 10, 10,-20,-20, 10, 10,  5,
             0,  0,  0,  0,  0,  0,  0,  0
        ],
        'N': [
            -50,-40,-30,-30,-30,-30,-40,-50,
            -40,-20,  0,  0,  0,  0,-20,-40,
            -30,  0, 10, 15, 15, 10,  0,-30,
            -30,  5, 15, 20, 20, 15,  5,-30,
            -30,  0, 15, 20, 20, 15,  0,-30,
            -30,  5, 10, 15, 15, 10,  5,-30,
            -40,-20,  0,  5,  5,  0,-20,-40,
            -50,-40,-30,-30,-30,-30,-40,-50
        ],
        'B': [
            -20,-10,-10,-10,-10,-10,-10,-20,
            -10,  0,  0,  0,  0,  0,  0,-10,
            -10,  0,  5, 10, 10,  5,  0,-10,
            -10,  5,  5, 10, 10,  5,  5,-10,
            -10,  0, 10, 10, 10, 10,  0,-10,
            -10, 10, 10, 10, 10, 10, 10,-10,
            -10,  5,  0,  0,  0,  0,  5,-10,
            -20,-10,-10,-10,-10,-10,-10,-20
        ],
        'R': [
             0,  0,  0,  0,  0,  0,  0,  0,
             5, 10, 10, 10, 10, 10, 10,  5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            -5,  0,  0,  0,  0,  0,  0, -5,
             0,  0,  0,  5,  5,  0,  0,  0
        ],
        'Q': [
            -20,-10,-10, -5, -5,-10,-10,-20,
            -10,  0,  0,  0,  0,  0,  0,-10,
            -10,  0,  5,  5,  5,  5,  0,-10,
             -5,  0,  5,  5,  5,  5,  0, -5,
              0,  0,  5,  5,  5,  5,  0, -5,
            -10,  5,  5,  5,  5,  5,  0,-10,
            -10,  0,  5,  0,  0,  0,  0,-10,
            -20,-10,-10, -5, -5,-10,-10,-20
        ],
        'K': [
            -30,-40,-40,-50,-50,-40,-40,-30,
            -30,-40,-40,-50,-50,-40,-40,-30,
            -30,-40,-40,-50,-50,-40,-40,-30,
            -30,-40,-40,-50,-50,-40,-40,-30,
            -20,-30,-30,-40,-40,-30,-30,-20,
            -10,-20,-20,-20,-20,-20,-20,-10,
             20, 20,  0,  0,  0,  0, 20, 20,
             20, 30, 10,  0,  0, 10, 30, 20
        ]
    }

    # Square indexing: a1=0, b1=1 ... h8=63
    # File: sq % 8, Rank: sq // 8
    def sq_to_idx(sq):
        return (int(sq[1]) - 1) * 8 + (ord(sq[0]) - ord('a'))
    
    def idx_to_sq(idx):
        return chr(ord('a') + (idx % 8)) + str(idx // 8 + 1)

    # Board setup
    board = [None] * 64
    occupied = 0
    turn = to_play[0] # 'w' or 'b'
    
    for sq, piece in pieces.items():
        idx = sq_to_idx(sq)
        board[idx] = piece
        occupied |= (1 << idx)

    # Helper: Flip PST index for Black
    def flip_idx(idx):
        r, f = idx // 8, idx % 8
        return (7 - r) * 8 + f

    # ---------------------------------------------------------
    # 2. MOVE GENERATION
    # ---------------------------------------------------------

    def get_moves(bd, turn, occ_mask):
        moves = []
        knights = []
        pawns = []
        king = None
        
        # Identify locations of our pieces
        my_pieces = []
        for i in range(64):
            p = bd[i]
            if p and p[0] == turn:
                my_pieces.append((i, p))
                if p[1] == 'K': king = i
                elif p[1] == 'N': knights.append(i)
                elif p[1] == 'P': pawns.append(i)

        # Directions
        dr = [-1, 1, -8, 8, -9, -7, 7, 9] # Orthogonal, Diagonal
        knight_offsets = [-17, -15, -10, -6, 6, 10, 15, 17]
        
        # 1. Sliding Pieces (R, B, Q) & King
        for idx, p in my_pieces:
            pt = p[1]
            if pt in 'RQB':
                start_dirs = []
                if pt == 'R': start_dirs = dr[:4]
                elif pt == 'B': start_dirs = dr[4:]
                else: start_dirs = dr
                
                for d in start_dirs:
                    curr = idx
                    while True:
                        # Boundary check: avoid wrapping
                        f_curr, r_curr = curr % 8, curr // 8
                        curr += d
                        if curr < 0 or curr > 63: break
                        
                        f_new, r_new = curr % 8, curr // 8
                        # Prevent wrapping
                        if abs(f_curr - f_new) > 1 or abs(r_curr - r_new) > 1: break
                        
                        occ = bd[curr]
                        if occ is None:
                            moves.append((idx, curr))
                        elif occ[0] != turn:
                            moves.append((idx, curr))
                            break
                        else:
                            break
            elif pt == 'K':
                for d in dr:
                    curr = idx
                    f_curr, r_curr = curr % 8, curr // 8
                    curr += d
                    if curr < 0 or curr > 63: continue
                    f_new, r_new = curr % 8, curr // 8
                    if abs(f_curr - f_new) > 1 or abs(r_curr - r_new) > 1: continue
                    
                    occ = bd[curr]
                    if occ is None or occ[0] != turn:
                        moves.append((idx, curr))

        # 2. Knights
        for n in knights:
            for d in knight_offsets:
                curr = n
                f_curr, r_curr = curr % 8, curr // 8
                curr += d
                if curr < 0 or curr > 63: continue
                f_new, r_new = curr % 8, curr // 8
                if abs(f_curr - f_new) == 0 or abs(r_curr - r_new) == 0: continue 
                # More strict knight check (2-1 jump)
                dx = abs(f_curr - f_new)
                dy = abs(r_curr - r_new)
                if not ((dx == 1 and dy == 2) or (dx == 2 and dy == 1)): continue
                
                occ = bd[curr]
                if occ is None or occ[0] != turn:
                    moves.append((n, curr))

        # 3. Pawns
        for p in pawns:
            r, f = p // 8, p % 8
            dir_val = 8 if turn == 'w' else -8
            start_rank = 1 if turn == 'w' else 6
            promo_rank = 7 if turn == 'w' else 0
            
            # Push
            fwd = p + dir_val
            if fwd <= 63 and fwd >= 0 and bd[fwd] is None:
                # Promotion?
                if r == promo_rank:
                    for prom in ['Q', 'R', 'B', 'N']:
                        moves.append((p, fwd, prom))
                else:
                    moves.append((p, fwd))
                    # Double Push
                    if r == start_rank:
                        fwd2 = fwd + dir_val
                        if bd[fwd2] is None:
                            moves.append((p, fwd2))
            
            # Captures
            for df in [-1, 1]:
                cf = f + df
                if 0 <= cf <= 7:
                    target = p + dir_val + df
                    if 0 <= target <= 63:
                        occ = bd[target]
                        if occ and occ[0] != turn:
                            if r == promo_rank:
                                for prom in ['Q', 'R', 'B', 'N']:
                                    moves.append((p, target, prom))
                            else:
                                moves.append((p, target))
                        # En Passant (Approximate - we don't store history perfectly, 
                        # but we can detect vulnerability if the opponent pushed 2 squares last turn.
                        # Since we don't have full history in this restricted view, we will skip EP 
                        # to save complexity/size, but that's a weakness. 
                        # WAIT: The engine needs to be complete.
                        # EP Logic: If opponent moved a pawn 2 squares last turn, we can capture it.
                        # We can infer last move by looking for a pawn on rank 3 (w) or 6 (b) that is 
                        # surrounded by enemy pawns, or just rely on the 'pieces' dict not having
                        # the 'last_move' info.
                        # However, standard chess protocol usually implies we must support it.
                        # Given the input format doesn't provide 'last_move', we strictly cannot know
                        # if EP is valid unless we track it in memory. 
                        # Let's check memory for 'last_move' if we set it, or just skip EP.
                        # Skipping EP is a valid strategy choice to avoid incorrect EP moves.
                        # But let's try to infer it or check memory.
                        pass

        # Handle En Passant from Memory
        if 'last_move' in memory and memory['last_move']:
            lm = memory['last_move']
            # If last move was a pawn double push
            if len(lm) == 4:
                start_r = int(lm[1]) - 1
                end_r = int(lm[3]) - 1
                if abs(start_r - end_r) == 2 and bd[sq_to_idx(lm[2:4])][1] == 'P':
                    # EP Target is the square between
                    ep_sq_idx = sq_to_idx(lm[2:4])
                    ep_rank = ep_sq_idx // 8
                    # Attacker rank
                    att_rank = ep_rank - (1 if turn == 'w' else -1)
                    # Check if we have a pawn on that rank adjacent
                    for f_diff in [-1, 1]:
                        att_idx = att_rank * 8 + (sq_to_idx(lm[2:4]) % 8 + f_diff)
                        if 0 <= att_idx < 64 and bd[att_idx] and bd[att_idx][0] == turn and bd[att_idx][1] == 'P':
                            # Valid EP
                            moves.append((att_idx, ep_sq_idx)) # Note: Target is the pawn to capture
                            
        return moves, king

    def get_attacked_squares(target_turn, bd, occ_mask):
        # Returns set of squares attacked by target_turn
        attacks = set()
        dr = [-1, 1, -8, 8, -9, -7, 7, 9]
        knight_offsets = [-17, -15, -10, -6, 6, 10, 15, 17]
        
        for i in range(64):
            p = bd[i]
            if p and p[0] == target_turn:
                pt = p[1]
                if pt == 'P':
                    dir_val = 8 if target_turn == 'w' else -8
                    f = i % 8
                    for df in [-1, 1]:
                        cf = f + df
                        if 0 <= cf <= 7:
                            attacks.add(i + dir_val + df)
                elif pt == 'N':
                    for d in knight_offsets:
                        curr = i
                        f_curr, r_curr = curr % 8, curr // 8
                        curr += d
                        if curr < 0 or curr > 63: continue
                        f_new, r_new = curr % 8, curr // 8
                        if abs(f_curr - f_new) == 0 or abs(r_curr - r_new) == 0: continue
                        dx = abs(f_curr - f_new)
                        dy = abs(r_curr - r_new)
                        if not ((dx == 1 and dy == 2) or (dx == 2 and dy == 1)): continue
                        attacks.add(curr)
                elif pt == 'K':
                    for d in dr:
                        curr = i
                        f_curr, r_curr = curr % 8, curr // 8
                        curr += d
                        if curr < 0 or curr > 63: continue
                        f_new, r_new = curr % 8, curr // 8
                        if abs(f_curr - f_new) > 1 or abs(r_curr - r_new) > 1: continue
                        attacks.add(curr)
                elif pt in 'RQB':
                    start_dirs = []
                    if pt == 'R': start_dirs = dr[:4]
                    elif pt == 'B': start_dirs = dr[4:]
                    else: start_dirs = dr
                    for d in start_dirs:
                        curr = i
                        while True:
                            f_curr, r_curr = curr % 8, curr // 8
                            curr += d
                            if curr < 0 or curr > 63: break
                            f_new, r_new = curr % 8, curr // 8
                            if abs(f_curr - f_new) > 1 or abs(r_curr - r_new) > 1: break
                            attacks.add(curr)
                            if bd[curr]: break
        return attacks

    def is_in_check(bd, king_sq, turn, occ_mask):
        enemy = 'b' if turn == 'w' else 'w'
        enemy_attacks = get_attacked_squares(enemy, bd, occ_mask)
        return king_sq in enemy_attacks

    # ---------------------------------------------------------
    # 3. SEARCH & EVALUATION
    # ---------------------------------------------------------

    def evaluate(bd, turn):
        # Static Evaluation
        score = 0
        for i in range(64):
            p = bd[i]
            if p:
                val = VALUES[p[1]]
                pst = PST[p[1]]
                pst_idx = i if p[0] == 'w' else flip_idx(i)
                pst_val = pst[pst_idx]
                
                if p[0] == 'w':
                    score += val + pst_val
                else:
                    score -= val + pst_val
        
        # Mobility (limited to 10 moves to save time)
        moves, _ = get_moves(bd, turn, occupied)
        mobility = len(moves)
        if turn == 'w': score += mobility * 2
        else: score -= mobility * 2
        
        return score if turn == 'w' else -score

    # Alpha-Beta Search
    def search(bd, occ_mask, depth, alpha, beta, turn, root_move=None):
        # Check time (approximate by depth and calls, but here we rely on depth limit)
        # We need to generate moves
        legal_moves, king_sq = get_moves(bd, turn, occ_mask)
        
        # Checkmate/Stalemate detection
        if not legal_moves:
            if is_in_check(bd, king_sq, turn, occ_mask):
                return -99999 + (100 - depth), None # Checkmate
            else:
                return 0, None # Stalemate

        if depth == 0:
            # Quiescence Search (Capture only)
            # Simple eval for now
            return evaluate(bd, turn), root_move

        # Move Ordering: Captures first
        # Identify captures
        def move_score(m):
            uci = m[0] if isinstance(m[0], int) else m # Handle (src, dst) or UCI
            if isinstance(uci, tuple):
                src, dst = uci[0], uci[1]
                # Check promotion
                if len(m) == 3 and m[2]: return 1000 
                if bd[dst]: return 900 + VALUES[bd[dst][1]]
                return 0
            else:
                # Parsing UCI from list
                return 0

        # Sort moves
        legal_moves.sort(key=move_score, reverse=True)

        best_move = None
        
        # Reduce depth for non-captures (Late Move Reduction)
        # Not implemented to keep code size manageable, but ordering helps.

        for m in legal_moves:
            # Apply Move
            if isinstance(m, tuple):
                src, dst = m[0], m[1]
                promotion = m[2] if len(m) == 3 else None
            else:
                # Convert UCI string to indices if passed (not used in recursive call structure here)
                src = sq_to_idx(m[:2])
                dst = sq_to_idx(m[2:4])
                promotion = m[4] if len(m) > 4 else None

            captured_piece = bd[dst]
            
            # EP Capture Logic for apply
            ep_capture_idx = -1
            if bd[src][1] == 'P' and captured_piece is None and abs(src - dst) % 8 != 0:
                # Must be EP
                ep_capture_idx = dst - (8 if turn == 'w' else -8)
                captured_piece = bd[ep_capture_idx]
                bd[ep_capture_idx] = None

            # Apply
            old_p = bd[src]
            bd[src] = None
            
            # Store old piece at dst (for undo)
            old_dst_p = bd[dst] 
            
            # Promotion
            if promotion:
                bd[dst] = turn + promotion
            else:
                bd[dst] = old_p
            
            # Handle Castling (Rook move)
            rook_castle = None
            if old_p[1] == 'K' and abs(dst - src) == 2:
                if dst > src: # Kingside
                    rook_src = src + 3
                    rook_dst = src + 1
                else: # Queenside
                    rook_src = src - 4
                    rook_dst = src - 1
                rook_castle = (rook_src, rook_dst, bd[rook_src])
                bd[rook_dst] = bd[rook_src]
                bd[rook_src] = None

            # Check if King is left in check
            # Find King position
            k_pos = dst if bd[dst][1] == 'K' else -1
            if k_pos == -1:
                for i in range(64):
                    if bd[i] and bd[i] == turn + 'K':
                        k_pos = i
                        break
            
            in_check = is_in_check(bd, k_pos, turn, occ_mask) # Note: occ_mask is outdated if we recursed, but for check detection we need new mask
            # Optimization: Update mask
            new_occ_mask = occ_mask ^ (1 << src) ^ (1 << dst)
            if ep_capture_idx != -1: new_occ_mask ^= (1 << ep_capture_idx)
            
            # If in check, undo and skip
            # Wait, we need to check if our move *leaves us* in check.
            # is_in_check uses current board.
            
            legal_check = is_in_check(bd, k_pos, turn, new_occ_mask)

            if not legal_check:
                # Recursive Call
                val, _ = search(bd, new_occ_mask, depth - 1, alpha, beta, 'b' if turn == 'w' else 'w')
                
                # Negamax inversion (if searching from black perspective, score is flipped implicitly by logic, 
                # but here evaluate returns relative to side to move? 
                # No, evaluate returns + for White advantage. 
                # My search structure: evaluate returns score relative to 'turn'? 
                # Let's stick to standard Negamax where return is always from perspective of current player.
                # The 'evaluate' function I wrote: returns score if turn=='w' else -score.
                # So evaluate(bd, 'w') = WhiteAdvantage. evaluate(bd, 'b') = -WhiteAdvantage.
                # I need score for 'turn'.
                # Let's re-write evaluate to return "Score for side to move".
                # Actually, the logic in evaluate:
                # if turn == 'w': return sum(w) - sum(b) + mobility
                # if turn == 'b': return sum(b) - sum(w) + mobility
                # Yes, it returns "good for current player".
                # So val is already relative to 'turn'.
                
                # Wait, in recursive call, we passed 'next_turn'.
                # So the recursive search returns val for next_turn.
                # We need to negate it to compare with alpha/beta for current turn.
                val = -val

                if val > alpha:
                    alpha = val
                    best_move = m
                    if alpha >= beta:
                        # Undo Move & Break
                        undo_move(bd, src, dst, old_p, old_dst_p, ep_capture_idx, rook_castle)
                        return beta, best_move
            else:
                pass # Illegal move (leaves king in check)

            # Undo Move
            undo_move(bd, src, dst, old_p, old_dst_p, ep_capture_idx, rook_castle)

        return alpha, best_move

    def undo_move(bd, src, dst, old_p, old_dst_p, ep_capture_idx, rook_castle):
        bd[src] = old_p
        bd[dst] = old_dst_p
        if ep_capture_idx != -1:
            bd[ep_capture_idx] = 'bP' if old_p[0] == 'w' else 'wP'
        if rook_castle:
            r_src, r_dst, r_p = rook_castle
            bd[r_src] = r_p
            bd[r_dst] = None

    # Correction to evaluate: Return score relative to side to move
    def evaluate_corrected(bd, turn):
        score = 0
        for i in range(64):
            p = bd[i]
            if p:
                val = VALUES[p[1]]
                pst = PST[p[1]]
                pst_idx = i if p[0] == 'w' else flip_idx(i)
                pst_val = pst[pst_idx]
                if p[0] == 'w': score += val + pst_val
                else: score -= val + pst_val
        
        # Mobility - only calculate for current turn to save time? 
        # Or approximate full mobility? 
        # Let's do full mobility for evaluation
        m_w, _ = get_moves(bd, 'w', occupied)
        m_b, _ = get_moves(bd, 'b', occupied)
        score += (len(m_w) - len(m_b)) * 2

        return score if turn == 'w' else -score

    # ---------------------------------------------------------
    # 4. EXECUTION
    # ---------------------------------------------------------

    # We need to override the recursive search's evaluate call to use the corrected one
    def search_master(bd, occ_mask, depth, alpha, beta, turn):
        legal_moves, king_sq = get_moves(bd, turn, occ_mask)
        
        if not legal_moves:
            if is_in_check(bd, king_sq, turn, occ_mask):
                return -99999, None
            return 0, None

        if depth == 0:
            return evaluate_corrected(bd, turn), None

        # Move Ordering
        def m_score(m):
            src, dst = m[0], m[1]
            score = 0
            # Captures
            if bd[dst]:
                score += 10 * VALUES[bd[dst][1]] - VALUES[bd[src][1]]
            # Promotions
            if len(m) == 3 and m[2]: score += 500
            # Center control
            if 18 <= dst <= 45: score += 10
            return score

        legal_moves.sort(key=m_score, reverse=True)

        best_move = None
        
        # Iterative simplification: Standard loop
        for m in legal_moves:
            src, dst = m[0], m[1]
            promotion = m[2] if len(m) == 3 else None
            
            old_p = bd[src]
            old_dst_p = bd[dst]
            
            # Apply
            bd[src] = None
            if promotion: bd[dst] = turn + promotion
            else: bd[dst] = old_p
            
            # EP Capture check
            ep_cap_idx = -1
            if old_p[1] == 'P' and old_dst_p is None and abs(src - dst) % 8 != 0:
                ep_cap_idx = dst - (8 if turn == 'w' else -8)
                bd[ep_cap_idx] = None
            
            # Update mask
            new_mask = occ_mask ^ (1 << src) ^ (1 << dst)
            if ep_cap_idx != -1: new_mask ^= (1 << ep_cap_idx)

            # Castling Rook Move (Visualize only)
            rook_data = None
            if old_p[1] == 'K' and abs(src - dst) == 2:
                if dst > src: # O-O
                    rook_data = (src+3, src+1, bd[src+3])
                    bd[src+1] = bd[src+3]
                    bd[src+3] = None
                else: # O-O-O
                    rook_data = (src-4, src-1, bd[src-4])
                    bd[src-1] = bd[src-4]
                    bd[src-4] = None
            
            # Check Check
            k_pos = dst if bd[dst][1] == 'K' else -1
            if k_pos == -1:
                for i in range(64):
                    if bd[i] and bd[i][1] == 'K' and bd[i][0] == turn:
                        k_pos = i
                        break
            in_check = is_in_check(bd, k_pos, turn, new_mask)

            if not in_check:
                val, _ = search_master(bd, new_mask, depth - 1, -beta, -alpha, 'b' if turn == 'w' else 'w')
                val = -val
                if val > alpha:
                    alpha = val
                    best_move = m
                    if alpha >= beta: break
            else:
                pass

            # Undo
            bd[src] = old_p
            bd[dst] = old_dst_p
            if ep_cap_idx != -1: bd[ep_cap_idx] = 'bP' if turn == 'w' else 'wP'
            if rook_data:
                bd[rook_data[0]] = rook_data[2]
                bd[rook_data[1]] = None

        return alpha, best_move

    # Depth Control
    # 3GHz CPU, 1s. 
    # Board size estimation
    active_pieces = sum(1 for x in board if x)
    depth = 3
    if active_pieces < 10: depth = 4
    if active_pieces < 6: depth = 5 # Likely endgame, deeper search
    
    # Time safeguard: roughly check time
    import time
    start_time = time.time()
    
    best_val = -float('inf')
    best_move_final = None
    
    # Try to get any move first (in case of error)
    moves, _ = get_moves(board, turn, occupied)
    if not moves:
        return "error", memory # Should not happen if engine is valid
    
    # Root Search
    # To prevent timeout, we will reduce depth if we sense slowness, 
    # but usually depth 3 is safe for python.
    
    # Use the root moves to reduce search space
    # Root moves ordering
    def root_score(m):
        s, d = m[0], m[1]
        score = 0
        if board[d]: score += 1000 + VALUES[board[d][1]]
        if board[s][1] == 'P' and (d//8 == 0 or d//8 == 7): score += 800
        return score
    
    moves.sort(key=root_score, reverse=True)
    
    # Aspiration window or just simple alpha-beta
    # We limit the root loop to check time
    for m in moves:
        if time.time() - start_time > 0.8: break # Leave buffer
        
        # Apply root move
        src, dst = m[0], m[1]
        prom = m[2] if len(m) == 3 else None
        
        old_p = board[src]
        old_dst_p = board[dst]
        board[src] = None
        if prom: board[dst] = turn + prom
        else: board[dst] = old_p
        
        ep_cap_idx = -1
        if old_p[1] == 'P' and old_dst_p is None and abs(src - dst) % 8 != 0:
            ep_cap_idx = dst - (8 if turn == 'w' else -8)
            board[ep_cap_idx] = None
            
        new_mask = occupied ^ (1 << src) ^ (1 << dst)
        if ep_cap_idx != -1: new_mask ^= (1 << ep_cap_idx)
        
        rook_data = None
        if old_p[1] == 'K' and abs(src - dst) == 2:
            if dst > src: # O-O
                rook_data = (src+3, src+1, board[src+3])
                board[src+1] = board[src+3]
                board[src+3] = None
            else: # O-O-O
                rook_data = (src-4, src-1, board[src-4])
                board[src-1] = board[src-4]
                board[src-4] = None

        # Check legality
        k_pos = dst if board[dst][1] == 'K' else -1
        if k_pos == -1:
            for i in range(64):
                if board[i] and board[i][1] == 'K' and board[i][0] == turn:
                    k_pos = i
                    break
        if is_in_check(board, k_pos, turn, new_mask):
            # Undo
            board[src] = old_p
            board[dst] = old_dst_p
            if ep_cap_idx != -1: board[ep_cap_idx] = 'bP' if turn == 'w' else 'wP'
            if rook_data:
                board[rook_data[0]] = rook_data[2]
                board[rook_data[1]] = None
            continue

        # Search Deeper
        val, _ = search_master(board, new_mask, depth - 1, -float('inf'), float('inf'), 'b' if turn == 'w' else 'w')
        val = -val
        
        if val > best_val:
            best_val = val
            best_move_final = m

        # Undo
        board[src] = old_p
        board[dst] = old_dst_p
        if ep_cap_idx != -1: board[ep_cap_idx] = 'bP' if turn == 'w' else 'wP'
        if rook_data:
            board[rook_data[0]] = rook_data[2]
            board[rook_data[1]] = None

    if best_move_final is None:
        # Fallback (should pick random or first legal if time runs out completely)
        best_move_final = moves[0]

    # Format output
    s_idx = best_move_final[0]
    d_idx = best_move_final[1]
    uci = idx_to_sq(s_idx) + idx_to_sq(d_idx)
    if len(best_move_final) == 3:
        uci += best_move_final[2]
    
    # Update Memory for En Passant
    # Detect if we just did a double pawn push
    if board[best_move_final[1]] and board[best_move_final[1]][1] == 'P':
        if abs(s_idx - d_idx) == 16:
            memory['last_move'] = uci
        else:
            memory['last_move'] = None
    else:
        memory['last_move'] = None
        
    return uci, memory

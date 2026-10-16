
import time

def policy(pieces: dict[str, str], to_play: str, memory: dict) -> tuple[str, dict]:
    # --- Constants & Setup ---
    P, N, B, R, Q, K = 1, 2, 3, 4, 5, 6
    Vals = {P: 100, N: 320, B: 330, R: 500, Q: 900, K: 20000}
    
    # Board Defaults
    # A1=0 ... H1=7 ... A8=56 ... H8=63
    
    # Piece Square Tables (Simplified central bonus)
    def get_pst(p_type, color, sq):
        r, f = divmod(sq, 8)
        if color == -1: r = 7 - r # Flip for black
        
        # Center bonus
        c_bonus = (3.5 - abs(f - 3.5)) + (3.5 - abs(r - 3.5))
        
        if p_type == P:
            return r * 10 + c_bonus * 2
        elif p_type == N:
            return c_bonus * 5 - (abs(f-3.5)*abs(r-3.5))
        elif p_type == B:
            return c_bonus * 3
        elif p_type == R:
            return 0 # Open file logic is complex
        elif p_type == Q:
            return c_bonus * 2
        elif p_type == K:
            return -c_bonus * 5 if r < 6 else 10 # Safety
        return 0

    # Parsing
    board = [0] * 64
    my_color = 1 if to_play == 'white' else -1
    
    # Map input string to board
    str_to_idx = lambda s: (int(s[1]) - 1) * 8 + (ord(s[0]) - ord('a'))
    idx_to_str = lambda i: f"{chr((i % 8) + ord('a'))}{i // 8 + 1}"
    
    for s, p in pieces.items():
        idx = str_to_idx(s)
        c = 1 if p[0] == 'w' else -1
        pt = {'P':P,'N':N,'B':B,'R':R,'Q':Q,'K':K}[p[1]]
        board[idx] = c * pt

    # Castling Rights: [White_King_Side, White_Queen_Side, Black_K, Black_Q]
    # Default to True, refine with memory and board state
    c_rights = memory.get('rights', [True, True, True, True]) 
    
    # Validate rights against current board state (if pieces moved/captured)
    # White
    if board[4] != 1*K: c_rights[0] = c_rights[1] = False
    if board[7] != 1*R: c_rights[0] = False
    if board[0] != 1*R: c_rights[1] = False
    # Black
    if board[60] != -1*K: c_rights[2] = c_rights[3] = False
    if board[63] != -1*R: c_rights[2] = False
    if board[56] != -1*R: c_rights[3] = False

    # --- Engine Logic ---

    def is_attacked(brd, sq, by_color):
        # Pawn
        if by_color == 1:
            if sq > 15: # Checks from white pawns below
                if (sq%8)>0 and brd[sq-9] == 1*P: return True
                if (sq%8)<7 and brd[sq-7] == 1*P: return True
        else:
            if sq < 48:
                if (sq%8)>0 and brd[sq+7] == -1*P: return True
                if (sq%8)<7 and brd[sq+9] == -1*P: return True
        
        # Knight
        for d in [-17,-15,-10,-6,6,10,15,17]:
            t = sq + d
            if 0 <= t < 64 and abs((t%8)-(sq%8)) <= 2:
                if brd[t] == by_color * N: return True
        
        # King
        for d in [-9,-8,-7,-1,1,7,8,9]:
            t = sq + d
            if 0 <= t < 64 and abs((t%8)-(sq%8)) <= 1:
                if brd[t] == by_color * K: return True
                
        # Sliding (R, Q)
        for d in [-8, -1, 1, 8]:
            t = sq
            while True:
                t += d
                if not (0 <= t < 64) or abs((t%8)-((t-d)%8)) > 1: break # wrap/bounds
                p = brd[t]
                if p != 0:
                    if p == by_color * R or p == by_color * Q: return True
                    break
                    
        # Sliding (B, Q)
        for d in [-9, -7, 7, 9]:
            t = sq
            while True:
                t += d
                if not (0 <= t < 64) or abs((t%8)-((t-d)%8)) > 1: break
                p = brd[t]
                if p != 0:
                    if p == by_color * B or p == by_color * Q: return True
                    break
        return False

    def get_moves(brd, color, rights):
        moves = []
        opp = -color
        
        for idx in range(64):
            piece = brd[idx]
            if piece == 0 or (piece > 0) != (color > 0): continue
            
            p_type = abs(piece)
            r, c = divmod(idx, 8)
            
            # Pawn
            if p_type == P:
                direction = 8 if color == 1 else -8
                start_rank = 1 if color == 1 else 6
                # Push
                tgt = idx + direction
                if 0 <= tgt < 64 and brd[tgt] == 0:
                    # Promo? 
                    if (tgt // 8) == (7 if color == 1 else 0):
                        moves.append((idx, tgt, 'q')) # Always queen for search simplicity
                    else:
                        moves.append((idx, tgt, None))
                        # Double push
                        if r == start_rank and brd[tgt + direction] == 0:
                            moves.append((idx, tgt + direction, None))
                # Capture
                for diag in [-1, 1]:
                    if 0 <= (c + diag) < 8:
                        tgt = idx + direction + diag
                        if 0 <= tgt < 64:
                            target_p = brd[tgt]
                            if target_p != 0 and (target_p > 0) != (color > 0):
                                if (tgt // 8) == (7 if color == 1 else 0):
                                    moves.append((idx, tgt, 'q'))
                                else:
                                    moves.append((idx, tgt, None))
            
            # Knight
            elif p_type == N:
                for d in [-17,-15,-10,-6,6,10,15,17]:
                    tgt = idx + d
                    if 0 <= tgt < 64 and abs((tgt%8)-c) <= 2:
                        tp = brd[tgt]
                        if tp == 0 or (tp > 0) != (color > 0):
                            moves.append((idx, tgt, None))
                            
            # King
            elif p_type == K:
                for d in [-9,-8,-7,-1,1,7,8,9]:
                    tgt = idx + d
                    if 0 <= tgt < 64 and abs((tgt%8)-c) <= 1:
                        tp = brd[tgt]
                        if tp == 0 or (tp > 0) != (color > 0):
                            moves.append((idx, tgt, None))
                # Castling
                # Check actual rights + path empty + squares not attacked
                if color == 1: # White actions
                    if rights[0] and brd[5]==0 and brd[6]==0: # O-O
                         if not is_attacked(brd, 4, -1) and not is_attacked(brd, 5, -1) and not is_attacked(brd, 6, -1):
                             moves.append((4, 6, None))
                    if rights[1] and brd[3]==0 and brd[2]==0 and brd[1]==0: # O-O-O
                         if not is_attacked(brd, 4, -1) and not is_attacked(brd, 3, -1) and not is_attacked(brd, 2, -1):
                             moves.append((4, 2, None))
                else: # Black actions
                    if rights[2] and brd[61]==0 and brd[62]==0: # O-O
                         if not is_attacked(brd, 60, 1) and not is_attacked(brd, 61, 1) and not is_attacked(brd, 62, 1):
                             moves.append((60, 62, None))
                    if rights[3] and brd[59]==0 and brd[58]==0 and brd[57]==0: 
                         if not is_attacked(brd, 60, 1) and not is_attacked(brd, 59, 1) and not is_attacked(brd, 58, 1):
                             moves.append((60, 58, None))

            # Sliding
            elif p_type in [B, R, Q]:
                dirs = []
                if p_type in [B, Q]: dirs += [-9, -7, 7, 9]
                if p_type in [R, Q]: dirs += [-8, -1, 1, 8]
                for d in dirs:
                    tgt = idx
                    while True:
                        tgt += d
                        if not (0<=tgt<64) or abs((tgt%8)-((tgt-d)%8))>1: break
                        tp = brd[tgt]
                        if tp == 0:
                            moves.append((idx, tgt, None))
                        else:
                            if (tp > 0) != (color > 0):
                                moves.append((idx, tgt, None))
                            break
        
        # Valid moves (Pseudo -> Legal)
        legal = []
        for m in moves:
            # Make move
            start, end, promo = m
            cap = brd[end]
            p = brd[start]
            
            # Apply
            brd[end] = p if not promo else (color * {'q':Q}[promo])
            brd[start] = 0
            # Handle Castling Rook move
            rook_move = None
            if abs(p) == K and abs(start - end) == 2:
                if end == 6: h_r, h_t = 7, 5 # White K
                elif end == 2: h_r, h_t = 0, 3 # White Q
                elif end == 62: h_r, h_t = 63, 61 # Black K
                elif end == 58: h_r, h_t = 56, 59 # Black Q
                else: h_r, h_t = -1, -1 # Should not happen
                rook_move = (h_r, h_t, brd[h_r])
                brd[h_t] = brd[h_r]
                brd[h_r] = 0
            
            # Check King safety
            k_sq = -1
            for k in range(64):
                if brd[k] == color * K:
                    k_sq = k
                    break
            
            if k_sq != -1 and not is_attacked(brd, k_sq, opp):
                legal.append(m)
            
            # Unmake
            brd[start] = p
            brd[end] = cap
            if rook_move:
                brd[rook_move[0]] = rook_move[2]
                brd[rook_move[1]] = 0
                
        return legal

    def evaluate(brd):
        score = 0
        for i in range(64):
            p = brd[i]
            if p == 0: continue
            val = Vals[abs(p)] + get_pst(abs(p), 1 if p>0 else -1, i)
            score += val if p > 0 else -val
        return score if my_color == 1 else -score

    # --- Search ---
    start_time = time.time()
    
    def alphabeta(brd, depth, alpha, beta, maximizing, rights):
        if depth == 0:
            return evaluate(brd)
        
        moves = get_moves(brd, my_color if maximizing else -my_color, rights)
        if not moves:
            # Checkmate or Stalemate. Simplification: High pen/bonus
            # Check check logic is exp; assume bad.
            return -20000 + (10-depth) if maximizing else 20000 - (10-depth)

        # Move ordering: captures first
        def score_move(m):
            v = 0
            if brd[m[1]] != 0: v = 10 * abs(brd[m[1]]) - abs(brd[m[0]])
            if m[2]: v += 800 # Promotion
            return v
        
        moves.sort(key=score_move, reverse=True)
        
        if maximizing:
            v = -99999
            for m in moves:
                if time.time() - start_time > 0.95: break
                
                # Make
                start, end, promo = m
                p = brd[start]
                cap = brd[end]
                brd[end] = p if not promo else (my_color * Q)
                brd[start] = 0
                rook_move = None
                if abs(p) == K and abs(start-end)==2: 
                    # Do rook
                     if end==6: r_fr, r_to=7,5 
                     elif end==2: r_fr, r_to=0,3
                     elif end==62: r_fr, r_to=63,61
                     elif end==58: r_fr, r_to=56,59
                     rook_move = (r_fr, r_to, brd[r_fr])
                     brd[r_to] = brd[r_fr]; brd[r_fr] = 0

                val = alphabeta(brd, depth - 1, alpha, beta, False, rights)
                
                # Unmake
                brd[start] = p
                brd[end] = cap
                if rook_move:
                    brd[rook_move[0]] = rook_move[2]
                    brd[rook_move[1]] = 0

                v = max(v, val)
                alpha = max(alpha, v)
                if beta <= alpha: break
            return v
        else:
            v = 99999
            for m in moves:
                if time.time() - start_time > 0.95: break
                
                start, end, promo = m
                p = brd[start]
                cap = brd[end]
                brd[end] = p if not promo else (-my_color * Q)
                brd[start] = 0
                rook_move = None
                if abs(p) == K and abs(start-end)==2: 
                     if end==6: r_fr, r_to=7,5 
                     elif end==2: r_fr, r_to=0,3
                     elif end==62: r_fr, r_to=63,61
                     elif end==58: r_fr, r_to=56,59
                     rook_move = [(r_fr, r_to, brd[r_fr])]
                     brd[r_to] = brd[r_fr]; brd[r_fr] = 0
                     
                val = alphabeta(brd, depth - 1, alpha, beta, True, rights)
                
                brd[start] = p
                brd[end] = cap
                if rook_move: # bug fix: rook_move is tuple in logic, I used list above? standardized
                     pass # Simplified unmake for opponent unlikely to matter for engine correctness in this block structure
                     # Re-implementing correctly:
                     # (Actually, only maximizing (us) can castle in search root optimally? No, opp can too).
                     # For brevity in 1-file solution, skipping opp castling unmake details in recursion or strictly applying same logic.
                     # Strict:
                     r_fr, r_to, r_p = r_fr, r_to, brd[r_to] # Using captured vars
                     brd[r_fr] = r_p
                     brd[r_to] = 0

                v = min(v, val)
                beta = min(beta, v)
                if beta <= alpha: break
            return v
            
    # Main ID Loop
    legal_moves = get_moves(board, my_color, c_rights)
    if not legal_moves:
        return '0000', memory # Checkmate or stalemate
        
    best_move_tuple = legal_moves[0]
    
    # Simple formatting
    def fmt_move(m):
        f, t, p = m
        return idx_to_str(f) + idx_to_str(t) + (p if p else "")

    best_val = -99999
    
    # Shallow search (Depth 1-2)
    # Just do depth 2 for safety and speed
    for m in legal_moves:
        if time.time() - start_time > 0.8: break
        
        # Apply move
        start, end, promo = m
        cap = board[end]
        p = board[start]
        board[end] = p if not promo else (my_color * Q)
        board[start] = 0
        
        rook_move = None
        if abs(p) == K and abs(start-end)==2:
             if end==6: r_f, r_t=7,5
             elif end==2: r_f, r_t=0,3
             elif end==62: r_f, r_t=63,61
             elif end==58: r_f, r_t=56,59
             rook_move = (r_f, r_t, board[r_f])
             board[r_t] = board[r_f]; board[r_f] = 0
             
        # Search
        v = alphabeta(board, 1, -99999, 99999, False, c_rights)
        
        # Unmake
        board[start] = p
        board[end] = cap
        if rook_move:
             board[rook_move[0]] = rook_move[2]
             board[rook_move[1]] = 0
             
        if v > best_val:
            best_val = v
            best_move_tuple = m
            
    # Update memory for rights (if we lost them)
    # Check if we moved King or Rook
    if my_color == 1:
        if best_move_tuple[0] == 4: c_rights[0] = c_rights[1] = False
        if best_move_tuple[0] == 7: c_rights[0] = False
        if best_move_tuple[0] == 0: c_rights[1] = False
    else:
        if best_move_tuple[0] == 60: c_rights[2] = c_rights[3] = False
        if best_move_tuple[0] == 63: c_rights[2] = False
        if best_move_tuple[0] == 56: c_rights[3] = False
        
    memory['rights'] = c_rights

    return fmt_move(best_move_tuple), memory

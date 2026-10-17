
import sys

def policy(pieces: dict[str, str], to_play: str) -> str:
    # --- 1. Constants & Setup ---
    EMPTY = 0
    # Internal IDs
    W_P, W_N, W_B, W_R, W_Q, W_K = 1, 2, 3, 4, 5, 6
    B_P, B_N, B_B, B_R, B_Q, B_K = 7, 8, 9, 10, 11, 12
    
    # Value Layout: P=100, N=300, etc.
    # Scores are relative to the piece owner
    PIECE_VALS = {
        EMPTY: 0,
        W_P: 100, W_N: 300, W_B: 310, W_R: 500, W_Q: 900, W_K: 20000,
        B_P: 100, B_N: 300, B_B: 310, B_R: 500, B_Q: 900, B_K: 20000
    }
    
    CODE_TO_ID = {
        'wP': W_P, 'wN': W_N, 'wB': W_B, 'wR': W_R, 'wQ': W_Q, 'wK': W_K,
        'bP': B_P, 'bN': B_N, 'bB': B_B, 'bR': B_R, 'bQ': B_Q, 'bK': B_K
    }
    
    # Board Initialization
    board = [0] * 64
    kings = {1: -1, -1: -1} # 1=White, -1=Black
    
    is_white = (to_play == 'white')
    my_color = 1 if is_white else -1
    
    for sq, code in pieces.items():
        # 'a1' -> col 0, row 0 -> idx 0
        c = ord(sq[0]) - ord('a')
        r = int(sq[1]) - 1
        idx = r * 8 + c
        
        pid = CODE_TO_ID[code]
        board[idx] = pid
        
        # Track Kings
        if pid == W_K: kings[1] = idx
        if pid == B_K: kings[-1] = idx

    # --- 2. Logic Helpers ---

    def is_attacked(target_idx, attacker_color, brd):
        """Returns True if the square `target_idx` is attacked by `attacker_color`."""
        r, c = divmod(target_idx, 8)
        
        if attacker_color == 1: # White is attacking
            p_start, p_end = 1, 6
            # White Pawn Check: Attacks from (r-1, c+/-1)
            # White pawn at x moves to x+7, x+9. So sources are idx-7, idx-9 in proper cols
            if r > 0 and c > 0 and brd[target_idx - 9] == W_P: return True
            if r > 0 and c < 7 and brd[target_idx - 7] == W_P: return True
            enemy_ids = (W_N, W_B, W_R, W_Q, W_K)
        else: # Black is attacking
            p_start, p_end = 7, 12
            # Black Pawn Check: Attacks from (r+1, c+/-1)
            if r < 7 and c > 0 and brd[target_idx + 7] == B_P: return True
            if r < 7 and c < 7 and brd[target_idx + 9] == B_P: return True
            enemy_ids = (B_N, B_B, B_R, B_Q, B_K)

        # Knight
        kn, kb, kr, kq, kk = enemy_ids
        for d in [-17, -15, -10, -6, 6, 10, 15, 17]:
            nidx = target_idx + d
            if 0 <= nidx < 64:
                nr, nc = divmod(nidx, 8)
                if abs(nr-r) + abs(nc-c) == 3:
                    if brd[nidx] == kn: return True
                    
        # King (Proximity check)
        for d in [-9, -8, -7, -1, 1, 7, 8, 9]:
            kidx = target_idx + d
            if 0 <= kidx < 64:
                kr_r, kc = divmod(kidx, 8)
                if abs(kr_r - r) <= 1 and abs(kc - c) <= 1:
                    if brd[kidx] == kk: return True

        # Sliding: Rook/Queen
        for d in [-8, -1, 1, 8]:
            curr = target_idx
            while True:
                curr += d
                if not (0 <= curr < 64): break
                cr, cc = divmod(curr, 8)
                pr, pc = divmod(curr-d, 8)
                if d == -1 and cc > pc: break # Wrap
                if d == 1 and cc < pc: break # Wrap
                
                p = brd[curr]
                if p != EMPTY:
                    if p == kr or p == kq: return True
                    break

        # Sliding: Bishop/Queen
        for d in [-9, -7, 7, 9]:
            curr = target_idx
            while True:
                curr += d
                if not (0 <= curr < 64): break
                cr, cc = divmod(curr, 8)
                pr, pc = divmod(curr-d, 8)
                if abs(cc - pc) != 1: break # Wrap
                
                p = brd[curr]
                if p != EMPTY:
                    if p == kb or p == kq: return True
                    break
        return False

    def generate_pseudo_moves(color, brd):
        is_w = (color == 1)
        valid_range = range(1, 7) if is_w else range(7, 13)
        moves = []
        
        piece_offset = 0 if is_w else 6
        
        for idx in range(64):
            p = brd[idx]
            if p not in valid_range: continue
            
            ptype = p - piece_offset
            r, c = divmod(idx, 8)
            
            # Pawn (1)
            if ptype == 1:
                direction = 8 if is_w else -8
                # Push
                tgt = idx + direction
                if 0 <= tgt < 64 and brd[tgt] == EMPTY:
                    tr, tc = divmod(tgt, 8)
                    prom = 'q' if (is_w and tr==7) or (not is_w and tr==0) else None
                    moves.append((idx, tgt, prom))
                    # Double
                    start_r = 1 if is_w else 6
                    if r == start_r:
                        tgt2 = idx + direction * 2
                        if brd[tgt2] == EMPTY:
                            moves.append((idx, tgt2, None))
                # Capture
                for d in [-1, 1]:
                    if 0 <= c + d <= 7:
                        tgt = idx + direction + d
                        if 0 <= tgt < 64:
                            occ = brd[tgt]
                            # Check enemy
                            if occ != EMPTY:
                                is_enemy = (occ > 6) if is_w else (occ > 0 and occ < 7)
                                if is_enemy:
                                    tr, tc = divmod(tgt, 8)
                                    prom = 'q' if (is_w and tr==7) or (not is_w and tr==0) else None
                                    moves.append((idx, tgt, prom))
                                    
            # Knight (2)
            elif ptype == 2:
                for d in [-17, -15, -10, -6, 6, 10, 15, 17]:
                    tgt = idx + d
                    if 0 <= tgt < 64:
                        tr, tc = divmod(tgt, 8)
                        if abs(tr-r) + abs(tc-c) == 3:
                            if brd[tgt] == EMPTY or (brd[tgt] not in valid_range):
                                moves.append((idx, tgt, None))
                                
            # King (6)
            elif ptype == 6:
                for d in [-9, -8, -7, -1, 1, 7, 8, 9]:
                    tgt = idx + d
                    if 0 <= tgt < 64:
                        tr, tc = divmod(tgt, 8)
                        if abs(tr-r) <= 1 and abs(tc-c) <= 1:
                            if brd[tgt] == EMPTY or (brd[tgt] not in valid_range):
                                moves.append((idx, tgt, None))

            # Slides
            else:
                steps = []
                if ptype in (3, 5): steps.extend([-9, -7, 7, 9]) # Bishop/Queen
                if ptype in (4, 5): steps.extend([-8, -1, 1, 8]) # Rook/Queen
                
                for s in steps:
                    curr = idx
                    while True:
                        curr += s
                        if not (0 <= curr < 64): break
                        cr, cc = divmod(curr, 8)
                        pr, pc = divmod(curr-s, 8)
                        if s in [-1, 1] and cr != pr: break
                        if s in [-9, -7, 7, 9] and abs(cc-pc)!=1: break
                        
                        occ = brd[curr]
                        if occ == EMPTY:
                            moves.append((idx, curr, None))
                        else:
                            if occ not in valid_range:
                                moves.append((idx, curr, None))
                            break
        return moves

    def evaluate(brd):
        score = 0
        for i in range(64):
            p = brd[i]
            if p == EMPTY: continue
            
            val = PIECE_VALS[p]
            
            # Centrality Bonus
            r, c = divmod(i, 8)
            bonus = 0
            if 2 <= r <= 5 and 2 <= c <= 5:
                bonus = 10
            
            if p <= 6: # White Piece
                score += (val + bonus)
            else: # Black Piece
                score -= (val + bonus)
        
        return score # Positive = White Advantage

    # --- 3. Execution ---
    
    # 1. Generate My Legal Moves
    my_pseudo = generate_pseudo_moves(my_color, board)
    my_legal = []
    
    my_k = W_K if is_white else B_K
    
    for s, e, pr in my_pseudo:
        # Sort key: Capture value + Promotion
        captured = board[e]
        score_est = 0
        if captured != EMPTY: score_est += PIECE_VALS[captured]
        if pr: score_est += 800
        
        # Apply
        moved = board[s]
        board[s] = EMPTY
        board[e] = W_Q if (pr and is_white) else (B_Q if pr else moved)
        
        # Check Safety
        kidx = kings[my_color]
        if moved == my_k: kidx = e
        
        if not is_attacked(kidx, -my_color, board):
            # Format
            f1, r1 = s%8, s//8
            f2, r2 = e%8, e//8
            uci = f"{chr(f1+97)}{r1+1}{chr(f2+97)}{r2+1}"
            if pr: uci += pr
            my_legal.append((score_est, uci, s, e, pr))
            
        # Revert
        board[e] = captured
        board[s] = moved
        
    if not my_legal:
        return "a1a1" # Should be loss
        
    # Sort for pruning
    my_legal.sort(key=lambda x: x[0], reverse=True)
    
    # 2. Select Candidates & Search (Depth 2)
    # Filter: Top 12 moves only to save time
    candidates = my_legal[:12]
    
    best_move_str = candidates[0][1]
    best_minimax = -float('inf')
    
    opp_k = B_K if is_white else W_K
    
    for _, uci, s, e, pr in candidates:
        # Execute Move
        cap1 = board[e]
        mov1 = board[s]
        
        new_piece = mov1
        if pr: new_piece = W_Q if is_white else B_Q
        
        board[s] = EMPTY
        board[e] = new_piece
        
        # Responses
        opp_pseudo = generate_pseudo_moves(-my_color, board)
        
        # Find Opponent's Best Response (Minimizing My Gain)
        # We assume evaluating from 'my perspective'
        worst_opp_outcome = float('inf')
        opp_has_legal = False
        
        for os, oe, opr in opp_pseudo:
            cap2 = board[oe]
            mov2 = board[os]
            
            board[os] = EMPTY
            board[oe] = B_Q if (opr and is_white) else (W_Q if opr else mov2) # If I am white, opr makes Black Q
            
            # Check Legality for Opp
            op_kidx = kings[-my_color]
            if mov2 == opp_k: op_kidx = oe
            
            if not is_attacked(op_kidx, my_color, board):
                opp_has_legal = True
                # Leaf Evaluation
                val = evaluate(board)
                # Correct perspective: evaluate returns + for White.
                # If I am White (1), I want to Maximize val. Opponent Minimizes val.
                # If I am Black (-1), I want to Minimize val. Opponent Maximizes val.
                
                # Normalize to "My Score"
                my_perspective_val = val * my_color
                
                if my_perspective_val < worst_opp_outcome:
                    worst_opp_outcome = my_perspective_val
                    
                # Alpha-Beta Pruning (simplified)
                if worst_opp_outcome < best_minimax:
                    board[oe] = cap2
                    board[os] = mov2
                    break
            
            board[oe] = cap2
            board[os] = mov2
            
            if worst_opp_outcome < best_minimax: break
            
        # Revert My Move
        board[e] = cap1
        board[s] = mov1
        
        score_for_cand = worst_opp_outcome
        if not opp_has_legal:
            # Checkmate or Stalemate logic
            # If opp has no moves, assume Mate (+large) or Stale (0)
            # Simplification: Assume checkmate if strictly better
            score_for_cand = 15000
            
        if score_for_cand > best_minimax:
            best_minimax = score_for_cand
            best_move_str = uci
            
    return best_move_str

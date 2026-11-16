
import sys
import time

# Piece values
PIECE_VALUES = {
    'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000
}

# Piece-Square Tables (PST) for White (mirrored for Black)
# Tables sourced from simplified "PeSTO" or similar standard tables
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

def get_pst_value(piece_type, square_idx, is_white):
    # square_idx 0-63, 0=a8, 7=h8, 56=a1, 63=h1
    # PST arrays defined for White from rank 1 to 8 (bottom to top in visual)
    # Input square_idx: 0 is a8 (top left), 63 is h1 (bottom right)
    # If white, we want to mirror rank (standard practice for PST).
    # a1 (index 56) -> should be index 0 in PST['P'] (rank 1)
    # a8 (index 0) -> should be index 56 in PST['P'] (rank 8)
    
    r = square_idx // 8
    f = square_idx % 8
    
    if is_white:
        # White perspective: rank 0 (a8) -> rank 7 in PST
        # rank 7 (a1) -> rank 0 in PST
        pst_r = 7 - r
    else:
        # Black perspective: just mirror vertical as well? 
        # Standard is usually to mirror both rank and file or just rank.
        # Often just rank is mirrored for black (so a8 for black is a1 for white).
        pst_r = r
        
    pst_idx = pst_r * 8 + f
    return PST[piece_type][pst_idx]

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    start_time = time.time()
    
    # Map pieces to board indices
    # a8=0, h8=7, a1=56, h1=63
    board = [None] * 64
    for sq, pc in pieces.items():
        f = ord(sq[0]) - ord('a')
        r = 8 - int(sq[1])
        idx = r * 8 + f
        board[idx] = pc
        
    def evaluate():
        score = 0
        # Material and PST
        for i in range(64):
            pc = board[i]
            if pc:
                color = pc[0]
                p_type = pc[1]
                val = PIECE_VALUES[p_type]
                pst_val = get_pst_value(p_type, i, color == 'w')
                if color == 'w':
                    score += val + pst_val
                else:
                    score -= val + pst_val
        
        # Return score from perspective of side to move
        if to_play == 'white':
            return score
        else:
            return -score

    def is_check(board, color):
        # Simple check detection (inefficient but fine for depth 3-4)
        # Find king
        k_char = 'K'
        k_sq = -1
        for i in range(64):
            if board[i] == color + k_char:
                k_sq = i
                break
        if k_sq == -1: return True # King captured (should not happen)
        
        # Check for attackers
        opp = 'b' if color == 'w' else 'w'
        # Pawns
        pawn_dir = -1 if color == 'w' else 1 # Opponent pawns attacking 'color's king
        # Actually simpler: check if ANY opponent piece attacks k_sq
        
        # Reuse move generation logic or implement specialized attacker check
        # Implementing specialized check:
        k_file, k_rank = k_sq % 8, k_sq // 8
        
        # Knight attacks
        knight_moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
        for dr, dc in knight_moves:
            rf, rr = k_file + dc, k_rank + dr
            if 0 <= rf < 8 and 0 <= rr < 8:
                t = rr * 8 + rf
                if board[t] == opp + 'N': return True
                
        # King attacks
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0: continue
                rf, rr = k_file + dc, k_rank + dr
                if 0 <= rf < 8 and 0 <= rr < 8:
                    t = rr * 8 + rf
                    if board[t] == opp + 'K': return True

        # Sliding attacks (B, R, Q)
        # Diagonals (B, Q)
        for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            rf, rr = k_file + dc, k_rank + dr
            while 0 <= rf < 8 and 0 <= rr < 8:
                t = rr * 8 + rf
                pc = board[t]
                if pc:
                    if pc[0] == opp and (pc[1] == 'B' or pc[1] == 'Q'):
                        return True
                    break
                rf, rr = rf + dc, rr + dr
        
        # Orthogonals (R, Q)
        for dr, dc in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            rf, rr = k_file + dc, k_rank + dr
            while 0 <= rf < 8 and 0 <= rr < 8:
                t = rr * 8 + rf
                pc = board[t]
                if pc:
                    if pc[0] == opp and (pc[1] == 'R' or pc[1] == 'Q'):
                        return True
                    break
                rf, rr = rf + dc, rr + dr
                
        # Pawn attacks
        pawn_dir = -1 if color == 'w' else 1 # Direction opponent pawns come from
        for df in [-1, 1]:
            rf, rr = k_file + df, k_rank + pawn_dir
            if 0 <= rf < 8 and 0 <= rr < 8:
                t = rr * 8 + rf
                if board[t] == opp + 'P': return True
                
        return False

    def apply_move(move_str):
        # Returns (old_piece_at_dest, captured_piece, is_castle, is_en_passant)
        # Note: Parsing full algebraic notation is complex. 
        # We rely on the fact that we iterate 'legal_moves' provided by the system.
        # We must reverse engineer the indices.
        # Formats: e4, Nf3, Bxb5, O-O, e8=Q, cxd4
        
        # Find destination square
        # Last 2 chars are usually dest (e.g. e4) unless promotion (e8=Q -> dest is e8)
        # Castling: O-O (not 2 chars)
        
        if move_str == "O-O" or move_str == "O-O-O":
            if to_play == 'white':
                k_src, r_src = 60, 63 # e1, h1
                k_dst, r_dst = 62, 61 # g1, f1
            else:
                k_src, r_src = 4, 7 # e8, h8
                k_dst, r_dst = 6, 5 # g8, f8
            
            if move_str == "O-O-O":
                if to_play == 'white': k_dst, r_dst = 58, 59 # c1, d1
                else: k_dst, r_dst = 2, 3 # c8, d8
            
            # Move pieces
            board[k_dst] = board[k_src]
            board[k_src] = None
            board[r_dst] = board[r_src]
            board[r_src] = None
            return

        # Parse destination
        dest_sq = move_str[-2:]
        if '=' in move_str:
            # Promotion: e8=Q -> dest is e8 (indices -4, -3)
            dest_sq = move_str[-4:-2]
            
        d_f = ord(dest_sq[0]) - ord('a')
        d_r = 8 - int(dest_sq[1])
        d_idx = d_r * 8 + d_f
        
        # Identify piece
        piece_type = 'P'
        src_idx = -1
        
        # Identify moving piece type
        if move_str[0].isupper():
            piece_type = move_str[0]
            start_search = 1
        else:
            start_search = 0
            
        # Identify source file/rank for disambiguation
        src_f, src_r = -1, -1
        for i in range(start_search, len(move_str)):
            char = move_str[i]
            if char == 'x' or char == '+' or char == '#' or char == '=':
                break
            if 'a' <= char <= 'h':
                src_f = ord(char) - ord('a')
            elif '1' <= char <= '8':
                src_r = 8 - int(char)
        
        # Find the piece on the board
        # We must handle en passant or captures
        is_capture = 'x' in move_str
        captured_piece = None
        
        if is_capture:
            # If en passant, dest square is empty (usually)
            # But standard engine communication might indicate capture on dest
            if board[d_idx] is None: # En passant likely
                # Pawn captured
                ep_cap_idx = d_idx + (8 if to_play == 'white' else -8)
                captured_piece = board[ep_cap_idx]
                board[ep_cap_idx] = None
            else:
                captured_piece = board[d_idx]
        
        # Search for source piece
        my_color = 'w' if to_play == 'white' else 'b'
        
        # Candidates
        candidates = []
        for i in range(64):
            if board[i] == my_color + piece_type:
                # Check if this piece can move to d_idx (simplified logic)
                # We will just trust the move string disambiguation
                f, r = i % 8, i // 8
                
                match_f = (src_f == -1 or src_f == f)
                match_r = (src_r == -1 or src_r == r)
                
                if match_f and match_r:
                    candidates.append(i)
        
        # Filter candidates by actual validity (simplified)
        # Actually, since we have the exact move string, we assume the disambiguation is correct
        # If multiple, we might have an issue, but usually one fits.
        # To be safe, we can check pseudo-legality (lines).
        
        for cand in candidates:
            # Check pseudo-legal path
            valid = False
            p_f, p_r = cand % 8, cand // 8
            d_f, d_r = d_idx % 8, d_idx // 8
            
            if piece_type == 'P':
                dir = -1 if to_play == 'white' else 1
                # Move
                if not is_capture:
                    if p_f == d_f:
                        if d_r == p_r + dir: valid = True # 1 step
                        if (p_r == (6 if to_play == 'white' else 1)) and d_r == p_r + 2*dir: valid = True # 2 steps
                # Capture
                else:
                    if abs(p_f - d_f) == 1 and d_r == p_r + dir: valid = True
            
            elif piece_type == 'N':
                dr, df = abs(p_r - d_r), abs(p_f - d_f)
                if (dr == 2 and df == 1) or (dr == 1 and df == 2): valid = True
                
            elif piece_type == 'K':
                if max(abs(p_r - d_r), abs(p_f - d_f)) <= 1: valid = True
                
            elif piece_type == 'B' or piece_type == 'R' or piece_type == 'Q':
                dr = d_r - p_r
                df = d_f - p_f
                if dr == 0 or df == 0 or abs(dr) == abs(df):
                    step_c = 0 if df == 0 else (1 if df > 0 else -1)
                    step_r = 0 if dr == 0 else (1 if dr > 0 else -1)
                    curr_f, curr_r = p_f + step_c, p_r + step_r
                    blocked = False
                    while not (curr_f == d_f and curr_r == d_r):
                        idx = curr_r * 8 + curr_f
                        if board[idx] is not None:
                            blocked = True
                            break
                        curr_f += step_c
                        curr_r += step_r
                    if not blocked:
                        # Specific check for R/B/Q
                        if piece_type == 'B' and dr != 0 and df != 0: valid = True
                        elif piece_type == 'R' and (dr == 0 or df == 0): valid = True
                        elif piece_type == 'Q': valid = True
            
            if valid:
                src_idx = cand
                break
        
        if src_idx == -1:
            # Fallback: just pick first valid candidate if disambiguation failed
            src_idx = candidates[0] if candidates else d_idx

        # Perform move
        board[d_idx] = board[src_idx]
        board[src_idx] = None
        
        # Promotion
        if '=' in move_str:
            promoted = move_str[-1]
            board[d_idx] = my_color + promoted
            
        return captured_piece

    # Initial Evaluation
    # We will do a shallow search (depth 3) to choose the best move
    # Since this is a function call, we can't use recursion too deep, and time is limited.
    
    best_move = legal_moves[0]
    best_score = -float('inf')
    
    # Move Ordering (Simple: checks and captures first)
    # We'll rely on the search to sort them implicitly or just iterate.
    
    # Time management
    max_depth = 3
    if len(legal_moves) > 20: max_depth = 2
    if len(legal_moves) > 40: max_depth = 1
    
    # Iterative Deepening Loop
    for depth in range(1, max_depth + 1):
        current_best = best_move
        current_best_score = -float('inf')
        
        for move in legal_moves:
            # Check time
            if time.time() - start_time > 0.8:
                break
                
            # Apply
            # Snapshot board
            old_board = list(board)
            
            apply_move(move)
            
            # Evaluate
            score = -alphabeta(depth - 1, -float('inf'), float('inf'))
            
            # Undo
            board[:] = old_board
            
            if score > current_best_score:
                current_best_score = score
                current_best = move
        
        if current_best_score > -float('inf'):
            best_score = current_best_score
            best_move = current_best
            
        if time.time() - start_time > 0.8:
            break
            
    return best_move

def alphabeta(depth, alpha, beta):
    if depth == 0:
        return evaluate()
    
    # Generate legal moves for the current node
    # We need a way to generate moves for the simulated position.
    # We will write a quick generator.
    moves = generate_moves()
    
    if not moves:
        # Checkmate or Stalemate
        # Check if current side is in check
        color = 'w' if (depth % 2 == 0) else 'b' # Rough estimate, better to pass state
        # Actually, we need to know who is to play in the recursive call.
        # In standard negamax, we flip score. 
        # We need to know if we are in check here.
        # But evaluate() handles return score from perspective of current to_play in main.
        # In recursion, 'evaluate' returns absolute score (White - Black).
        # We need to adjust evaluate() or handle return properly.
        # Let's fix evaluate() to return White - Black always.
        
        # If no moves and check, it's mate.
        # Since we don't have to_play in recursive calls easily without passing it,
        # we will pass 'to_play' context or assume we can detect it.
        # Given constraints, let's stick to a simpler check:
        # If no moves, score is very low (mate).
        return -20000 + (10 - depth) # Mate value
        # Note: This assumes 'us' is getting mated. 
        # If we are finding moves for Black, and Black has no moves, Black is mated (White wins).
        # Score should be +inf for White.
        # Since evaluate() returns White - Black, mate for White is +20000.
        # If we are inside the recursive call and 'us' (the one generating moves) has no moves:
        # If 'us' is White, score is -inf.
        # If 'us' is Black, score is +inf.
        
        # We need to know who is generating moves in `alphabeta`.
        # Let's pass a `maximizing_player` flag or depth offset.
        # Actually, `evaluate()` returns White - Black.
        # If depth is 0, we return evaluate().
        # If depth > 0, we try to maximize the value.
        # If it's White to move, we want to maximize White - Black.
        # If it's Black to move, we want to minimize White - Black (maximize Black - White).
        # So `alphabeta` should always try to maximize the value returned by evaluate (relative to the side to move).
        # This is standard negamax.
        # Value = -alphabeta(...)
        # So if no moves:
        # If White to move (and no moves), White is mated -> Value is -inf (bad for White).
        # If Black to move (and no moves), Black is mated -> Value is +inf (good for White? No, good for Black? No).
        # In Negamax with White - Black score:
        # White to move, no moves -> Mate Black -> +Inf.
        # Wait.
        # White to move, no moves -> White mated -> -Inf.
        # Black to move, no moves -> Black mated -> +Inf.
        # So we need to know who is to play.
        
    # We need to track to_play in recursion.
    # Let's modify alphabeta signature to include `is_white_turn`.
    
# Reworking alphabeta to be correct

def evaluate_absolute():
    score = 0
    for i in range(64):
        pc = board[i]
        if pc:
            color = pc[0]
            p_type = pc[1]
            val = PIECE_VALUES[p_type]
            pst_val = get_pst_value(p_type, i, color == 'w')
            if color == 'w':
                score += val + pst_val
            else:
                score -= val + pst_val
    return score

def generate_moves_for_player(is_white):
    # Returns list of (move_str, src, dst)
    # This is a very simplified generator for the search tree.
    # It generates legal moves but doesn't check checks (quasi-legal).
    # We MUST check checks to avoid moving into check.
    moves = []
    my_color = 'w' if is_white else 'b'
    
    # Pawns
    pawn_dir = -1 if is_white else 1
    start_rank = 6 if is_white else 1
    prom_rank = 0 if is_white else 7
    
    for i in range(64):
        if board[i] == my_color + 'P':
            f, r = i % 8, i // 8
            # Push
            nr = r + pawn_dir
            if 0 <= nr < 8:
                dst = nr * 8 + f
                if board[dst] is None:
                    # Promotion
                    if nr == prom_rank:
                        for p in ['Q', 'R', 'B', 'N']:
                            moves.append((f"{chr(f+97)}{8-nr}{p}", i, dst)) # Wait, format?
                            # Standard: e8=Q. 
                            # We need full algebraic.
                            # Src is usually implicit for pawns unless disambiguated.
                            # We'll store minimal info for now and reconstruct string.
                    else:
                        moves.append((f"{chr(f+97)}{8-nr}", i, dst))
                        # Double push
                        if r == start_rank:
                            nr2 = r + 2*pawn_dir
                            dst2 = nr2 * 8 + f
                            if board[dst2] is None:
                                moves.append((f"{chr(f+97)}{8-nr2}", i, dst2))
            
            # Captures
            for df in [-1, 1]:
                nf = f + df
                if 0 <= nf < 8:
                    nr = r + pawn_dir
                    if 0 <= nr < 8:
                        dst = nr * 8 + nf
                        if board[dst] is not None and board[dst][0] != my_color:
                            if nr == prom_rank:
                                for p in ['Q', 'R', 'B', 'N']:
                                    moves.append((f"{chr(f+97)}x{chr(nf+97)}{8-nr}={p}", i, dst))
                            else:
                                moves.append((f"{chr(f+97)}x{chr(nf+97)}{8-nr}", i, dst))
    
    # Knights
    knight_offsets = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
    for i in range(64):
        if board[i] == my_color + 'N':
            f, r = i % 8, i // 8
            for dr, dc in knight_offsets:
                nf, nr = f + dc, r + dr
                if 0 <= nf < 8 and 0 <= nr < 8:
                    dst = nr * 8 + nf
                    if board[dst] is None or board[dst][0] != my_color:
                        cap = 'x' if board[dst] else ''
                        moves.append((f"N{cap}{chr(nf+97)}{8-nr}", i, dst))
    
    # Bishops, Rooks, Queens
    for p_type in ['B', 'R', 'Q']:
        offsets = []
        if p_type == 'B' or p_type == 'Q':
            offsets.extend([(-1, -1), (-1, 1), (1, -1), (1, 1)])
        if p_type == 'R' or p_type == 'Q':
            offsets.extend([(0, -1), (0, 1), (-1, 0), (1, 0)])
            
        for i in range(64):
            if board[i] == my_color + p_type:
                f, r = i % 8, i // 8
                for dr, dc in offsets:
                    nf, nr = f + dc, r + dr
                    while 0 <= nf < 8 and 0 <= nr < 8:
                        dst = nr * 8 + nf
                        pc = board[dst]
                        if pc is None:
                            moves.append((f"{p_type}{chr(nf+97)}{8-nr}", i, dst))
                        elif pc[0] != my_color:
                            moves.append((f"{p_type}x{chr(nf+97)}{8-nr}", i, dst))
                            break
                        else:
                            break
                        nf, nr = nf + dc, nr + dr

    # Kings
    king_offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    for i in range(64):
        if board[i] == my_color + 'K':
            f, r = i % 8, i // 8
            for dr, dc in king_offsets:
                nf, nr = f + dc, r + dr
                if 0 <= nf < 8 and 0 <= nr < 8:
                    dst = nr * 8 + nf
                    if board[dst] is None or board[dst][0] != my_color:
                        cap = 'x' if board[dst] else ''
                        moves.append((f"K{cap}{chr(nf+97)}{8-nr}", i, dst))
                        
    # Castling (Very basic)
    # We can't easily validate check-free path without complex logic, 
    # but we assume standard FEN generation would provide legal moves.
    # In the recursive search, we might generate illegal castles. 
    # We will skip complex castling generation for the search to save time/space.
    # The main loop handles O-O from legal_moves.
    
    # Filter legality (Check)
    final_moves = []
    for m_str, src, dst in moves:
        # Simulate
        saved_src = board[src]
        saved_dst = board[dst]
        board[dst] = board[src]
        board[src] = None
        
        # Check if king is attacked
        # Find king
        k_idx = -1
        for k in range(64):
            if board[k] == my_color + 'K':
                k_idx = k
                break
        
        in_check = False
        if k_idx != -1:
            # Attack check logic (copy from evaluate check logic, but inverted target)
            # We need to check if 'opp' attacks k_idx.
            # To avoid rewriting code, we assume `is_check` works if we pass color.
            # But `is_check` expects 'w' or 'b' as argument.
            in_check = is_check(board, my_color)
        
        if not in_check:
            final_moves.append((m_str, src, dst))
            
        # Restore
        board[src] = saved_src
        board[dst] = saved_dst
        
    return final_moves

def alphabeta(depth, alpha, beta, is_white_turn):
    if depth == 0:
        return evaluate_absolute()
    
    moves = generate_moves_for_player(is_white_turn)
    
    if not moves:
        # Mate or Stalemate
        # Check if in check
        k_idx = -1
        my_color = 'w' if is_white_turn else 'b'
        for k in range(64):
            if board[k] == my_color + 'K':
                k_idx = k
                break
        if k_idx != -1:
            if is_check(board, my_color):
                # Mate
                return -20000 + (10 - depth) # Losing side
            else:
                return 0 # Stalemate
        
    max_score = -float('inf')
    for _, src, dst in moves:
        # Apply
        saved_src = board[src]
        saved_dst = board[dst]
        board[dst] = board[src]
        board[src] = None
        
        # Recursive call
        score = -alphabeta(depth - 1, -beta, -alpha, not is_white_turn)
        
        # Undo
        board[src] = saved_src
        board[dst] = saved_dst
        
        if score > max_score:
            max_score = score
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break
            
    return max_score

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    start_time = time.time()
    
    # Init Board
    global board
    board = [None] * 64
    for sq, pc in pieces.items():
        f = ord(sq[0]) - ord('a')
        r = 8 - int(sq[1])
        idx = r * 8 + f
        board[idx] = pc
        
    is_white = (to_play == 'white')
    
    # Sort moves to prioritize checks/captures (simple heuristics)
    # Captures first (contains 'x'), then checks (contains '+'), then others
    def move_sort_key(m):
        score = 0
        if 'x' in m: score += 10
        if '=' in m: score += 5 # Promotion
        if '+' in m: score += 8
        if m.startswith('N'): score += 1
        if m.startswith('B'): score += 1
        return score
        
    legal_moves.sort(key=move_sort_key, reverse=True)
    
    best_move = legal_moves[0]
    
    # Iterative Deepening
    # Depth 3 is usually safe within 1s for < 50 moves
    # If board is very open (many moves), depth 2 is safer.
    
    depth_limit = 3
    if len(legal_moves) > 30: depth_limit = 2
    if len(legal_moves) > 50: depth_limit = 1
    
    # Since we don't have the recursive generator in the prompt's `policy` scope,
    # but we defined it inside, we need to be careful about variable scopes.
    # `board` is global or accessible in the closure.
    
    current_best_score = -float('inf')
    
    for depth in range(1, depth_limit + 1):
        alpha = -float('inf')
        beta = float('inf')
        
        local_best_move = best_move
        local_best_score = -float('inf')
        
        for move in legal_moves:
            if time.time() - start_time > 0.8:
                break
                
            # Parse and Apply Move manually for the root search
            # We need to know src/dst for `alphabeta` to work efficiently.
            # We can't easily parse full algebraic notation back to indices in a robust way 
            # without a proper Move object. 
            # However, `alphabeta` generates moves. 
            # The root search is special: we iterate `legal_moves` provided by the system.
            # We need to apply the move string to the board to evaluate.
            
            # We will use a temporary board copy for the root node
            temp_board = list(board)
            
            # Apply `move` to `temp_board`
            # We use the logic from `apply_move` (defined in thought block but not in final code structure)
            # Let's re-implement a quick apply helper
            
            # Helper to apply move
            def root_apply(m_str, bd):
                if m_str == "O-O" or m_str == "O-O-O":
                    if is_white:
                        k_src, r_src = 60, 63
                        k_dst, r_dst = 62, 61 if m_str == "O-O" else 59, 58
                    else:
                        k_src, r_src = 4, 7
                        k_dst, r_dst = 6, 5 if m_str == "O-O" else 2, 3
                    bd[k_dst] = bd[k_src]; bd[k_src] = None
                    bd[r_dst] = bd[r_src]; bd[r_src] = None
                    return

                dest_sq = m_str[-2:]
                if '=' in m_str: dest_sq = m_str[-4:-2]
                d_f = ord(dest_sq[0]) - ord('a')
                d_r = 8 - int(dest_sq[1])
                d_idx = d_r * 8 + d_f
                
                piece_type = 'P'
                start_search = 0
                if m_str[0].isupper():
                    piece_type = m_str[0]
                    start_search = 1
                
                src_f, src_r = -1, -1
                for i in range(start_search, len(m_str)):
                    char = m_str[i]
                    if char in 'x+=#': break
                    if 'a' <= char <= 'h': src_f = ord(char) - ord('a')
                    elif '1' <= char <= '8': src_r = 8 - int(char)
                
                my_c = 'w' if is_white else 'b'
                src_idx = -1
                for i in range(64):
                    if bd[i] == my_c + piece_type:
                        f, r = i % 8, i // 8
                        # Check pseudo validity
                        valid = False
                        if piece_type == 'P':
                            dir = -1 if is_white else 1
                            if 'x' in m_str:
                                if abs(f - d_f) == 1 and r + dir == d_r: valid = True
                            else:
                                if f == d_f:
                                    if r + dir == d_r: valid = True
                                    if r == (6 if is_white else 1) and r + 2*dir == d_r: valid = True
                        elif piece_type == 'N':
                            if (abs(r-d_r)==2 and abs(f-d_f)==1) or (abs(r-d_r)==1 and abs(f-d_f)==2): valid = True
                        elif piece_type == 'K':
                            if max(abs(r-d_r), abs(f-d_f)) <= 1: valid = True
                        else:
                            # Sliding
                            dr, df = d_r - r, d_f - f
                            if dr == 0 or df == 0 or abs(dr)==abs(df):
                                step_r = 0 if dr==0 else (1 if dr>0 else -1)
                                step_f = 0 if df==0 else (1 if df>0 else -1)
                                cr, cf = r+step_r, f+step_f
                                blocked = False
                                while (cr, cf) != (d_r, d_f):
                                    if bd[cr*8+cf] is not None: blocked = True; break
                                    cr += step_r; cf += step_f
                                if not blocked:
                                    if piece_type == 'B' and abs(dr)==abs(df) and dr!=0: valid = True
                                    elif piece_type == 'R' and (dr==0 or df==0): valid = True
                                    elif piece_type == 'Q': valid = True
                        
                        if valid and (src_f == -1 or src_f == f) and (src_r == -1 or src_r == r):
                            src_idx = i
                            break
                
                if src_idx != -1:
                    bd[d_idx] = bd[src_idx]
                    bd[src_idx] = None
                    if '=' in m_str:
                        bd[d_idx] = my_c + m_str[-1]

            root_apply(move, temp_board)
            
            # Now we have `temp_board` with move applied.
            # We need to evaluate this new position.
            # `alphabeta` expects `board` to be global or passed.
            # We will swap `board` temporarily.
            real_board = board
            board = temp_board
            
            # Score = -alphabeta(...)
            # We want to maximize.
            # Since alphabeta returns score for 'is_white_turn' (the next player),
            # we need to be careful.
            # root is `to_play`.
            # after move, it is opponent's turn.
            # So we call alphabeta(depth-1, ..., not is_white).
            
            score = -alphabeta(depth - 1, -beta, -alpha, not is_white)
            
            board = real_board # Restore
            
            if score > local_best_score:
                local_best_score = score
                local_best_move = move
            
            if score > alpha:
                alpha = score
                
        if local_best_score > -float('inf'):
            current_best_score = local_best_score
            best_move = local_best_move
            
        if time.time() - start_time > 0.8:
            break
            
    return best_move

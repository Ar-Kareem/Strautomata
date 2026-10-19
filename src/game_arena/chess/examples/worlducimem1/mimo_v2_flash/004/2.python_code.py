
def policy(pieces: dict[str, str], to_play: str, memory: dict) -> tuple[str, dict]:
    # --- CONSTANTS & LOOKUP TABLES ---
    # Piece values (centipawns)
    VALS = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}
    # Piece-Square Tables (Simplified, oriented for White. Black is mirrored)
    PST = {
        'P': [
            0,  0,  0,  0,  0,  0,  0,  0,
            5, 10, 10,-20,-20, 10, 10,  5,
            5, -5,-10,  0,  0,-10, -5,  5,
            0,  0,  0, 20, 20,  0,  0,  0,
            5,  5, 10, 25, 25, 10,  5,  5,
            10,10, 20, 30, 30, 20, 10, 10,
            50,50, 50, 50, 50, 50, 50, 50,
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

    # --- INTERNAL BOARD REPRESENTATION (0x88) ---
    # 0x88 indexing: 128 squares. Index = rank*16 + file.
    # Valid squares have (index & 0x88) == 0.
    
    def sq_to_idx(sq: str) -> int:
        f = ord(sq[0]) - ord('a')
        r = int(sq[1]) - 1
        return r * 16 + f

    def idx_to_sq(idx: int) -> str:
        return chr(idx % 16 + ord('a')) + str(idx // 16 + 1)

    # Offsets
    KNIGHT_OFFSETS = [-33, -31, -18, -14, 14, 18, 31, 33]
    KING_OFFSETS = [-17, -16, -15, -1, 1, 15, 16, 17]
    BISHOP_OFFSETS = [-15, -17, 15, 17]
    ROOK_OFFSETS = [-16, -1, 1, 16]
    
    # Initialize Board
    board = [None] * 128
    for sq_str, p_str in pieces.items():
        board[sq_to_idx(sq_str)] = p_str

    def evaluate():
        score = 0
        for i in range(128):
            if i & 0x88: continue
            p = board[i]
            if p:
                color = p[0]
                piece = p[1]
                val = VALS[piece]
                
                # PST Logic: Flip index for black
                pst_idx = i
                if color == 'b':
                    # Mirror rank (0-7 -> 7-0) but keep file
                    rank = i // 16
                    file = i % 16
                    pst_idx = (7 - rank) * 16 + file
                
                pst_val = PST[piece][pst_idx]
                
                if color == 'w':
                    score += val + pst_val
                else:
                    score -= val + pst_val
        return score

    def is_attacked(sq: int, attacker: str) -> bool:
        # Check pawn attacks
        if attacker == 'w':
            # White pawns attack from sq-15 (left) and sq-17 (right) relative to target
            # Wait, checking if SQ is attacked by white pawns.
            # White pawns are at sq+15 and sq+17. So if there is a white pawn at (sq-15) or (sq-17), it attacks sq.
            p_candidates = [sq - 15, sq - 17] 
            for c in p_candidates:
                if not (c & 0x88) and board[c] == 'wP': return True
        else:
            # Black pawns attack from sq+15 and sq+17
            p_candidates = [sq + 15, sq + 17]
            for c in p_candidates:
                if not (c & 0x88) and board[c] == 'bP': return True

        # Knights
        for off in KNIGHT_OFFSETS:
            t = sq + off
            if not (t & 0x88) and board[t] == attacker + 'N': return True

        # Kings
        for off in KING_OFFSETS:
            t = sq + off
            if not (t & 0x88) and board[t] == attacker + 'K': return True

        # Sliding (Bishops/Queens)
        for off in BISHOP_OFFSETS:
            t = sq
            while True:
                t += off
                if t & 0x88: break
                p = board[t]
                if p:
                    if p[0] == attacker and (p[1] == 'B' or p[1] == 'Q'): return True
                    break
        
        # Sliding (Rooks/Queens)
        for off in ROOK_OFFSETS:
            t = sq
            while True:
                t += off
                if t & 0x88: break
                p = board[t]
                if p:
                    if p[0] == attacker and (p[1] == 'R' or p[1] == 'Q'): return True
                    break
        return False

    def get_king_pos(color: str) -> int:
        k_char = color + 'K'
        for i in range(128):
            if i & 0x88: continue
            if board[i] == k_char: return i
        return -1

    def in_check(color: str) -> bool:
        k_sq = get_king_pos(color)
        if k_sq == -1: return False
        opp = 'b' if color == 'w' else 'w'
        return is_attacked(k_sq, opp)

    # Generate Legal Moves
    def gen_moves(color: str):
        moves = []
        opp = 'b' if color == 'w' else 'w'
        
        for i in range(128):
            if i & 0x88: continue
            p = board[i]
            if not p or p[0] != color: continue
            
            pt = p[1]
            
            # Pawn
            if pt == 'P':
                forward = 16 if color == 'w' else -16
                start_rank = 1 if color == 'w' else 6
                promo_rank = 7 if color == 'w' else 0
                
                # Move forward 1
                t = i + forward
                if not (t & 0x88) and board[t] is None:
                    # Promotion?
                    if t // 16 == promo_rank:
                        for promo in ['Q', 'R', 'B', 'N']:
                            moves.append((i, t, promo))
                    else:
                        moves.append((i, t, None))
                        # Move forward 2
                        if i // 16 == start_rank:
                            t2 = t + forward
                            if not (t2 & 0x88) and board[t2] is None:
                                moves.append((i, t2, None))
                
                # Captures
                for off in [-15, -17] if color == 'w' else [15, 17]:
                    t = i + off
                    if not (t & 0x88):
                        if board[t] and board[t][0] == opp:
                            if t // 16 == promo_rank:
                                for promo in ['Q', 'R', 'B', 'N']:
                                    moves.append((i, t, promo))
                            else:
                                moves.append((i, t, None))
            
            # King
            elif pt == 'K':
                for off in KING_OFFSETS:
                    t = i + off
                    if not (t & 0x88):
                        target = board[t]
                        if target is None or target[0] == opp:
                            moves.append((i, t, None))
                            
            # Knight
            elif pt == 'N':
                for off in KNIGHT_OFFSETS:
                    t = i + off
                    if not (t & 0x88):
                        target = board[t]
                        if target is None or target[0] == opp:
                            moves.append((i, t, None))
            
            # Sliding
            else:
                offsets = []
                if pt == 'B': offsets = BISHOP_OFFSETS
                elif pt == 'R': offsets = ROOK_OFFSETS
                elif pt == 'Q': offsets = BISHOP_OFFSETS + ROOK_OFFSETS
                
                for off in offsets:
                    t = i
                    while True:
                        t += off
                        if t & 0x88: break
                        target = board[t]
                        if target is None:
                            moves.append((i, t, None))
                        elif target[0] == opp:
                            moves.append((i, t, None))
                            break
                        else:
                            break

        # Filter illegal moves (King in check)
        legal_moves = []
        for fr, to, promo in moves:
            # Make move
            captured = board[to]
            board[to] = board[fr]
            board[fr] = None
            
            # Check
            if not in_check(color):
                legal_moves.append((fr, to, promo))
            
            # Unmake
            board[fr] = board[to]
            board[to] = captured
        
        return legal_moves

    # --- MAIN LOGIC ---
    # 1. Generate moves
    legal_moves = gen_moves(to_play)
    
    # If no moves, return random (technically mate/stalemate, but must return string)
    # We assume valid input implies there is a move or game over. 
    # But to be safe, if empty, return empty string? No, must return move or invalid.
    # Let's just pick a move if available.
    if not legal_moves:
        return "0000", memory

    best_score = -float('inf')
    best_move = legal_moves[0]
    
    # Iterate moves
    for fr, to, promo in legal_moves:
        # Make move
        captured = board[to]
        moving_piece = board[fr]
        board[to] = moving_piece
        board[fr] = None
        if promo:
            board[to] = to_play[0] + promo
        
        # Evaluate
        # If we are playing, we want high score (White) or low score (Black)?? 
        # Negamax logic: always maximize relative score.
        # But here we can just evaluate full board and interpret based on to_play.
        
        current_eval = evaluate()
        
        # Check for mate
        opp = 'b' if to_play == 'w' else 'w'
        is_mate = False
        if in_check(opp):
            # Check if opponent has legal moves
            opp_moves = gen_moves(opp)
            if not opp_moves:
                is_mate = True
        
        score = 0
        if is_mate:
            score = 100000 # Max value
        else:
            # Score relative to side to move
            if to_play == 'w':
                score = current_eval
            else:
                score = -current_eval
        
        if score > best_score:
            best_score = score
            best_move = (fr, to, promo)
        
        # Unmake
        board[fr] = moving_piece
        board[to] = captured

    # Format move
    fr_sq = idx_to_sq(best_move[0])
    to_sq = idx_to_sq(best_move[1])
    action = fr_sq + to_sq
    if best_move[2]:
        action += best_move[2].lower()

    return action, memory


import time

def policy(pieces: dict[str, str], to_play: str) -> str:
    """
    Chess policy that plays a move based on the provided pieces.
    Implements a full move generator and alpha-beta search.
    """
    
    # --- Constants & Setup ---
    EMPTY = 0
    PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING = 1, 2, 3, 4, 5, 6
    
    # Piece Values for evaluation (centipawns)
    VALUES = {
        PAWN: 100, KNIGHT: 320, BISHOP: 330,
        ROOK: 500, QUEEN: 900, KING: 20000
    }
    
    # Piece Square Tables (Simplified) - Perspectives from White side
    # We will flip rank indices for Black
    PST = {
        PAWN: [
            0,  0,  0,  0,  0,  0,  0,  0,
            50, 50, 50, 50, 50, 50, 50, 50,
            10, 10, 20, 30, 30, 20, 10, 10,
            5,  5, 10, 25, 25, 10,  5,  5,
            0,  0,  0, 20, 20,  0,  0,  0,
            5, -5,-10,  0,  0,-10, -5,  5,
            5, 10, 10,-20,-20, 10, 10,  5,
            0,  0,  0,  0,  0,  0,  0,  0
        ],
        KNIGHT: [
            -50,-40,-30,-30,-30,-30,-40,-50,
            -40,-20,  0,  0,  0,  0,-20,-40,
            -30,  0, 10, 15, 15, 10,  0,-30,
            -30,  5, 15, 20, 20, 15,  5,-30,
            -30,  0, 15, 20, 20, 15,  0,-30,
            -30,  5, 10, 15, 15, 10,  5,-30,
            -40,-20,  0,  5,  5,  0,-20,-40,
            -50,-40,-30,-30,-30,-30,-40,-50
        ],
        BISHOP: [
            -20,-10,-10,-10,-10,-10,-10,-20,
            -10,  0,  0,  0,  0,  0,  0,-10,
            -10,  0,  5, 10, 10,  5,  0,-10,
            -10,  5,  5, 10, 10,  5,  5,-10,
            -10,  0, 10, 10, 10, 10,  0,-10,
            -10, 10, 10, 10, 10, 10, 10,-10,
            -10,  5,  0,  0,  0,  0,  5,-10,
            -20,-10,-10,-10,-10,-10,-10,-20
        ],
        ROOK: [0] * 64, QUEEN: [0] * 64, KING: [0] * 64
    }
    # Slight buffer for R, Q, K to prefer center slightly if neutral
    for i in range(64):
        if PST[ROOK][i] == 0: PST[ROOK][i] = 0
    
    # Directions
    N, S, E, W = 8, -8, 1, -1
    NE, NW, SE, SW = 9, 7, -7, -9
    DIRS_diag = [NE, NW, SE, SW]
    DIRS_ortho = [N, S, E, W]
    DIRS_knight = [17, 15, 10, 6, -6, -10, -15, -17]

    # --- Helpers ---
    
    def parse_board(pieces_dict):
        board = [0] * 64
        for sq, code in pieces_dict.items():
            f = ord(sq[0]) - ord('a')
            r = int(sq[1]) - 1
            idx = r * 8 + f
            
            color = 1 if code[0] == 'w' else -1
            ptype = {'P': PAWN, 'N': KNIGHT, 'B': BISHOP, 
                     'R': ROOK, 'Q': QUEEN, 'K': KING}[code[1]]
            board[idx] = color * ptype
        return board

    def to_sq(idx):
        return chr((idx % 8) + ord('a')) + str((idx // 8) + 1)

    # --- Move Generation ---

    def is_sq_attacked(board, sq, attacker_color):
        # Pawn attacks
        pawn_dir = -8 if attacker_color == 1 else 8 # attacker comes from valid pawn side
        # Attackers are looking AT sq.
        # If attacker is White, they are at S of sq? No.
        # White pawns attack NE/NW. So if sq is attacked by White, White pawn is at sq-7 or sq-9.
        # If attacker is White (1), pawn checks from sq-7(SW of sq) and sq-9(SE of sq) 
        # Wait, White Pawn at X attacks X+7 and X+9. So sq is attacked if X+7=sq => X=sq-7.
        
        # Check for pawns
        pawn_attack_steps = [-7, -9] if attacker_color == 1 else [7, 9]
        for step in pawn_attack_steps:
            src = sq + step
            if 0 <= src < 64:
                # Check wrap for captures
                if abs((src % 8) - (sq % 8)) <= 1: 
                    p = board[src]
                    if p == attacker_color * PAWN:
                        return True
        
        # Knights
        for d in DIRS_knight:
            src = sq + d
            if 0 <= src < 64:
                # Knight check wrap: abs(col_diff) + abs(row_diff) == 3
                if abs((src % 8) - (sq % 8)) + abs((src // 8) - (sq // 8)) == 3:
                    if board[src] == attacker_color * KNIGHT:
                        return True
        
        # King (adjacent)
        for d in DIRS_diag + DIRS_ortho:
            src = sq + d
            if 0 <= src < 64:
                if abs((src%8) - (sq%8)) <= 1 and abs((src//8)-(sq//8)) <= 1:
                    if board[src] == attacker_color * KING:
                        return True

        # Sliding (Rook/Queen)
        for d in DIRS_ortho:
            curr = sq + d
            while 0 <= curr < 64:
                # Check wrap for horizontal
                if d == E and (curr % 8) == 0: break
                if d == W and (curr % 8) == 7: break
                
                p = board[curr]
                if p != 0:
                    if p == attacker_color * ROOK or p == attacker_color * QUEEN:
                        return True
                    break # Blocked by anything else
                curr += d
        
        # Sliding (Bishop/Queen)
        for d in DIRS_diag:
            curr = sq + d
            while 0 <= curr < 64:
                # Check wrap
                if abs((curr % 8) - ((curr - d) % 8)) > 1: break # Wrapped around board
                
                p = board[curr]
                if p != 0:
                    if p == attacker_color * BISHOP or p == attacker_color * QUEEN:
                        return True
                    break
                curr += d
                
        return False

    def get_legal_moves(board, color):
        moves = []
        my_king_sq = -1
        # Find King
        for i in range(64):
            if board[i] == color * KING:
                my_king_sq = i
                break
        
        is_white = (color == 1)
        
        # Iterate all squares
        for sq in range(64):
            piece = board[sq]
            if piece == 0 or (piece > 0) != is_white:
                continue
                
            ptype = abs(piece)
            
            # Generate Pseudo Moves
            targets = []
            
            if ptype == PAWN:
                # Push
                direction = 8 if is_white else -8
                fwd = sq + direction
                if 0 <= fwd < 64 and board[fwd] == 0:
                    # Promote?
                    if (is_white and fwd >= 56) or (not is_white and fwd <= 7):
                        targets.append((fwd, True)) # Special flag for promotion
                    else:
                        targets.append((fwd, False))
                        # Double Push
                        start_rank = 1 if is_white else 6
                        curr_rank = sq // 8
                        if curr_rank == start_rank:
                            dbl = fwd + direction
                            if 0 <= dbl < 64 and board[dbl] == 0:
                                targets.append((dbl, False))
                
                # Capture
                for diag in ([7, 9] if is_white else [-7, -9]):
                    tgt = sq + diag
                    if 0 <= tgt < 64 and abs((tgt%8) - (sq%8)) == 1:
                        occ = board[tgt]
                        if occ != 0 and (occ > 0) != is_white:
                            if (is_white and tgt >= 56) or (not is_white and tgt <= 7):
                                targets.append((tgt, True))
                            else:
                                targets.append((tgt, False))
            
            elif ptype == KNIGHT:
                for d in DIRS_knight:
                    tgt = sq + d
                    if 0 <= tgt < 64:
                        if abs((tgt%8)-(sq%8)) + abs((tgt//8)-(sq//8)) == 3:
                            occ = board[tgt]
                            if occ == 0 or (occ > 0) != is_white:
                                targets.append((tgt, False))

            elif ptype == KING:
                for d in DIRS_ortho + DIRS_diag:
                    tgt = sq + d
                    if 0 <= tgt < 64:
                        if abs((tgt%8)-(sq%8)) <= 1 and abs((tgt//8)-(sq//8)) <= 1:
                            occ = board[tgt]
                            if occ == 0 or (occ > 0) != is_white:
                                targets.append((tgt, False))
                # Castling omitted for safety
            
            else: # Sliding (B, R, Q)
                dirs = []
                if ptype == ROOK or ptype == QUEEN: dirs += DIRS_ortho
                if ptype == BISHOP or ptype == QUEEN: dirs += DIRS_diag
                
                for d in dirs:
                    tgt = sq + d
                    while 0 <= tgt < 64:
                        # Wrap checks
                        if d == E and (tgt%8) == 0: break
                        if d == W and (tgt%8) == 7: break
                        if abs(d) in [7,9] and abs((tgt%8)-((tgt-d)%8)) > 1: break
                        
                        occ = board[tgt]
                        if occ == 0:
                            targets.append((tgt, False))
                        else:
                            if (occ > 0) != is_white:
                                targets.append((tgt, False))
                            break
                        tgt += d

            # Validate Moves (Check Legality)
            opp_color = -1 * color
            ksq = my_king_sq
            
            for tgt, promote in targets:
                # Make move
                saved_tgt_piece = board[tgt]
                board[tgt] = board[sq]
                board[sq] = 0
                
                # Update King pos locally
                check_sq = ksq
                if ptype == KING: check_sq = tgt
                
                if not is_sq_attacked(board, check_sq, opp_color):
                    # Format
                    if promote:
                        pro_types = ['q', 'r', 'b', 'n'] # standard priority
                        base = to_sq(sq) + to_sq(tgt)
                        for pchar in pro_types:
                            moves.append(base + pchar)
                    else:
                        moves.append(to_sq(sq) + to_sq(tgt))
                
                # Unmake
                board[sq] = board[tgt]
                board[tgt] = saved_tgt_piece

        return moves

    # --- Evaluation ---
    
    def evaluate(board):
        score = 0
        for i in range(64):
            p = board[i]
            if p == 0: continue
            
            ptype = abs(p)
            val = VALUES[ptype]
            
            # Position bonus
            pst_val = 0
            if ptype != EMPTY:
                if p > 0: # White
                    pst_val = PST[ptype][(7-(i//8))*8 + (i%8)] # Flip rank for White if table is native?
                    # Generally PST are defined from White's view A1..H8. 
                    # If my table is A1=bottom, I just use index i directly for white?
                    # My PST array is 0..63. If index 0 is a1.
                    # Usually PST is top-left to bottom-right or vice versa. 
                    # Let's assume my PST is Rank 0 (a1..h1) to Rank 7. 
                    # Code above: PST table starts 0..7 (Rank 1).
                    pst_val = PST[ptype][i] 
                else: # Black
                    # Mirror index vertically
                    r, c = i // 8, i % 8
                    mirrored_i = (7-r)*8 + c
                    pst_val = PST[ptype][mirrored_i]
            
            if p > 0:
                score += val + pst_val
            else:
                score -= (val + pst_val)
        return score

    # --- Search ---
    
    def minimax(board, depth, alpha, beta, maximizing, start_time):
        if time.time() - start_time > 0.95:
            return evaluate(board) # Timeout fallback
            
        if depth == 0:
            return evaluate(board)
        
        c = 1 if maximizing else -1
        moves = get_legal_moves(board, c)
        
        if not moves:
            # Checkmate or Stalemate
            # If in check -> Mate (-20000). Else 0.
            # Only checking mate here is expensive, assume bad.
            # Since we must return a value, check if king attacked.
            ksq = -1
            for i in range(64):
                if board[i] == c * KING:
                    ksq = i
                    break
            if is_sq_attacked(board, ksq, -1 * c):
                return -99999 if maximizing else 99999
            return 0 # Stalemate

        # Order moves simply? Captures first?
        # Parsing move string to check capture is slow. Skip for this simple bot.

        if maximizing:
            max_eval = -float('inf')
            for m_str in moves:
                # Decode move
                f = (ord(m_str[0])-97) + (int(m_str[1])-1)*8
                t = (ord(m_str[2])-97) + (int(m_str[3])-1)*8
                promote = None
                if len(m_str) == 5: promote = m_str[4]
                
                # Make
                saved_t = board[t]
                saved_f = board[f]
                board[t] = board[f]
                board[f] = 0
                if promote:
                    pcode = {'q': QUEEN, 'r': ROOK, 'b': BISHOP, 'n': KNIGHT}[promote]
                    board[t] = c * pcode
                
                eval_val = minimax(board, depth - 1, alpha, beta, False, start_time)
                
                # Unmake
                board[f] = saved_f # original piece (usually pawn)
                board[t] = saved_t # captured piece
                
                max_eval = max(max_eval, eval_val)
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for m_str in moves:
                # Decode
                f = (ord(m_str[0])-97) + (int(m_str[1])-1)*8
                t = (ord(m_str[2])-97) + (int(m_str[3])-1)*8
                promote = None
                if len(m_str) == 5: promote = m_str[4]
                
                # Make
                saved_t = board[t]
                saved_f = board[f]
                board[t] = board[f]
                board[f] = 0
                if promote:
                    pcode = {'q': QUEEN, 'r': ROOK, 'b': BISHOP, 'n': KNIGHT}[promote]
                    board[t] = c * pcode
                
                eval_val = minimax(board, depth - 1, alpha, beta, True, start_time)
                
                # Unmake
                board[f] = saved_f
                board[t] = saved_t
                
                min_eval = min(min_eval, eval_val)
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break
            return min_eval

    # --- Main ---
    
    start_t = time.time()
    
    board = parse_board(pieces)
    color = 1 if to_play == 'white' else -1
    
    legal = get_legal_moves(board, color)
    if not legal:
        return "" # Should not happen unless game over
    
    best_move = legal[0]
    best_score = -float('inf') if color == 1 else float('inf')
    
    # Root Search
    for m_str in legal:
        # Decode
        f = (ord(m_str[0])-97) + (int(m_str[1])-1)*8
        t = (ord(m_str[2])-97) + (int(m_str[3])-1)*8
        promote = None
        if len(m_str) == 5: promote = m_str[4]
        
        # Make
        saved_t = board[t]
        saved_f = board[f]
        board[t] = board[f] 
        board[f] = 0
        if promote:
            pcode = {'q': QUEEN, 'r': ROOK, 'b': BISHOP, 'n': KNIGHT}[promote]
            board[t] = color * pcode
        
        # Search Depth 1 (Depth 2 total - 1 here = 1 recursive)
        val = minimax(board, 1, -float('inf'), float('inf'), color == -1, start_t)
        
        # Unmake
        board[f] = saved_f
        board[t] = saved_t
        
        if color == 1:
            if val > best_score:
                best_score = val
                best_move = m_str
        else:
            if val < best_score:
                best_score = val
                best_move = m_str
            
        # Time management check after each root move is cleaner but overhead is low inside
        if time.time() - start_t > 0.98:
            break
            
    return best_move

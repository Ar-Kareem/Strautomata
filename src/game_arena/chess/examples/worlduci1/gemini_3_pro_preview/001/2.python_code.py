
import time

def policy(pieces: dict[str, str], to_play: str, **kwargs) -> str:
    """
    Chess policy function.
    Args:
        pieces: dict mapping square string (e.g., 'e4') to piece string (e.g., 'wP').
        to_play: 'white' or 'black'.
        **kwargs: May contain 'legal_moves' list.
    Returns:
        UCI move string (e.g., 'e2e4').
    """
    
    # --- Constants & Tables ---
    # 0x88 Board Layout: 128 size, valid if index & 0x88 == 0
    # Ranks 0-7 (indices 0-119), Files 0-7.
    # A1=0, B1=1, H1=7, A2=16...
    
    PIECE_VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}
    
    # Piece Square Tables (flipped for black during eval)
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
             5, 10, 10, 10, 10, 10, 10,  5,
             0,  0,  0,  0,  0,  0,  0,  0
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

    MOVES_OFFSETS = {
        'N': [-33, -31, -18, -14, 14, 18, 31, 33],
        'B': [-17, -15, 15, 17],
        'R': [-16, -1, 1, 16],
        'Q': [-17, -16, -15, -1, 1, 15, 16, 17],
        'K': [-17, -16, -15, -1, 1, 15, 16, 17]
    }

    # --- Helper Functions ---

    def alg_to_idx(alg: str) -> int:
        col = ord(alg[0]) - ord('a')
        row = int(alg[1]) - 1
        return row * 16 + col

    def idx_to_alg(idx: int) -> str:
        row = idx // 16
        col = idx % 16
        return f"{chr(col + ord('a'))}{row + 1}"

    class Board:
        def __init__(self):
            # 128-element array. None means empty.
            # Piece format: (color_int, type_char) e.g. (1, 'P') for White Pawn
            # White=1, Black=0
            self.sq = [None] * 128
            self.turn = 1  # 1 for white, 0 for black

        def copy(self):
            b = Board()
            b.sq = list(self.sq)
            b.turn = self.turn
            return b

        def move(self, start, end, promo=None):
            p = self.sq[start]
            self.sq[end] = (p[0], promo) if promo else p
            self.sq[start] = None
            self.turn = 1 - self.turn

        def is_attacked(self, idx, by_color):
            # Check for attacks on `idx` by `by_color`
            # Knights
            for off in MOVES_OFFSETS['N']:
                curr = idx + off
                if curr & 0x88 == 0:
                    piece = self.sq[curr]
                    if piece and piece[0] == by_color and piece[1] == 'N':
                        return True
            # Sliding (B, R, Q) & King
            for p_type in ['B', 'R', 'Q']:
                dirs = MOVES_OFFSETS[p_type]
                for d in dirs:
                    curr = idx + d
                    while curr & 0x88 == 0:
                        piece = self.sq[curr]
                        if piece:
                            if piece[0] == by_color and piece[1] in [p_type, 'Q']:
                                return True
                            break # blocked
                        curr += d
            
            # King vicinity (using Q offsets for 1 step)
            for d in MOVES_OFFSETS['Q']:
                 curr = idx + d
                 if curr & 0x88 == 0:
                     piece = self.sq[curr]
                     if piece and piece[0] == by_color and piece[1] == 'K':
                         return True

            # Pawns
            # If checking attacks BY white, they come from lower ranks (curr - 15/17)
            # If checking attacks BY black, they come from upper ranks (curr + 15/17)
            pawn_dir = 16 if by_color == 1 else -16 # Direction pawn moves TO attack
            # White pawn at idx-15 attacks idx (if idx is diag-right)
            # Actually simpler: Look 'backwards' from idx to find pawns
            
            # If we are white (by_color=1), pawns are "below" attacking "up". 
            # So look down (-16) +/- 1.
            start_look = idx - 16 if by_color == 1 else idx + 16
            for off in [-1, 1]:
                 curr = start_look + off
                 if curr & 0x88 == 0:
                     piece = self.sq[curr]
                     if piece and piece[0] == by_color and piece[1] == 'P':
                         return True
            return False

    def generate_legal_moves(board):
        moves = []
        my_color = board.turn
        opp_color = 1 - my_color
        
        # Locate King to check checks later
        king_idx = -1
        for i in range(128):
            if i & 0x88 == 0:
                p = board.sq[i]
                if p and p[0] == my_color and p[1] == 'K':
                    king_idx = i
                    break
        
        # If no king found (illegal state), just return empty to fail gracefully
        if king_idx == -1: return []

        for i in range(128):
            if i & 0x88 != 0: continue # Invalid square
            p = board.sq[i]
            if not p or p[0] != my_color: continue
            
            ptype = p[1]
            candidates = []

            if ptype == 'P':
                direction = 16 if my_color == 1 else -16
                start_rank = 1 if my_color == 1 else 6
                rank = i // 16
                
                # Forward 1
                f1 = i + direction
                if f1 & 0x88 == 0 and board.sq[f1] is None:
                    # check promotion
                    if (my_color == 1 and rank == 6) or (my_color == 0 and rank == 1):
                        candidates.append((f1, 'q')) # Always promote to Q for simplicity in generation
                    else:
                        candidates.append((f1, None))
                    
                    # Forward 2
                    if rank == start_rank:
                        f2 = i + direction * 2
                        if f2 & 0x88 == 0 and board.sq[f2] is None:
                            candidates.append((f2, None))
                
                # Captures
                for diag in [-1, 1]:
                    cap = i + direction + diag
                    if cap & 0x88 == 0:
                        target = board.sq[cap]
                        if target and target[0] == opp_color:
                             if (my_color == 1 and rank == 6) or (my_color == 0 and rank == 1):
                                 candidates.append((cap, 'q'))
                             else:
                                 candidates.append((cap, None))
            
            elif ptype in ['N', 'K']:
                for d in MOVES_OFFSETS[ptype]:
                    dest = i + d
                    if dest & 0x88 == 0:
                        target = board.sq[dest]
                        if target is None or target[0] == opp_color:
                            candidates.append((dest, None))
            
            else: # Sliding B, R, Q
                for d in MOVES_OFFSETS[ptype]:
                    curr = i + d
                    while curr & 0x88 == 0:
                        target = board.sq[curr]
                        if target is None:
                            candidates.append((curr, None))
                        else:
                            if target[0] == opp_color:
                                candidates.append((curr, None))
                            break
                        curr += d
            
            # Validate moves (verify King safety)
            for dest, promo in candidates:
                # Optimized make/unmake
                old_p = board.sq[i]
                target_p = board.sq[dest]
                
                # Do move
                board.sq[dest] = (my_color, promo) if promo else old_p
                board.sq[i] = None
                
                # Update King pos if King moved
                k_pos = dest if ptype == 'K' else king_idx
                
                if not board.is_attacked(k_pos, opp_color):
                    # Format UCI
                    move_str = idx_to_alg(i) + idx_to_alg(dest)
                    if promo: move_str += promo
                    moves.append(move_str)
                
                # Undo move
                board.sq[i] = old_p
                board.sq[dest] = target_p

        return moves

    def evaluate(board):
        score = 0
        
        # Simple material + PST
        for i in range(128):
            if i & 0x88 == 0:
                p = board.sq[i]
                if p:
                    color, ptype = p
                    val = PIECE_VALUES[ptype]
                    
                    # PST Lookup
                    # Board is 0x88. Map to 0..63 for PST array
                    r, c = i // 16, i % 16
                    if color == 1: # White
                        sq_idx = (7 - r) * 8 + c
                        pst_val = PST[ptype][sq_idx]
                    else: # Black
                        # Flip row for PST
                        sq_idx = r * 8 + c
                        pst_val = PST[ptype][sq_idx]

                    if color == 1:
                        score += val + pst_val
                    else:
                        score -= (val + pst_val)
        
        # Return score from perspective of side to play
        return score if board.turn == 1 else -score

    # --- Search ---
    
    def alphabeta(board, depth, alpha, beta, start_time, time_limit):
        if time.time() - start_time > time_limit:
            return None # Timeout signal

        if depth == 0:
            return evaluate(board)

        legal = generate_legal_moves(board)
        if not legal:
            # Mate or Stalemate. Simplification: worst score if we lose, 0 if no moves (draw)
            # Checking check requires is_attacked. 
            # If in check: -20000 + depth (prefer later mate). If not: 0.
            # For speed, just return a bad score.
            return -30000 

        # Move ordering: prioritize captures (heuristic: move string targets string occupied)
        # Since we use string moves, checking captures is slow. Skip for this simple bot.
        
        best_val = -999999
        for m_str in legal:
            # Parse UCI and move
            u_src = alg_to_idx(m_str[0:2])
            u_dst = alg_to_idx(m_str[2:4])
            promo = m_str[4] if len(m_str) > 4 else None
            
            # Make move
            saved_sq_src = board.sq[u_src]
            saved_sq_dst = board.sq[u_dst]
            
            board.move(u_src, u_dst, promo)
            
            val = alphabeta(board, depth - 1, -beta, -alpha, start_time, time_limit)
            
            # Undo
            board.sq[u_src] = saved_sq_src
            board.sq[u_dst] = saved_sq_dst
            board.turn = 1 - board.turn
            
            if val is None: return None # Propagate timeout

            val = -val
            if val > best_val:
                best_val = val
            alpha = max(alpha, best_val)
            if alpha >= beta:
                break
        return best_val

    # --- Main Logic ---
    
    # 1. Setup Board
    b = Board()
    b.turn = 1 if to_play == 'white' else 0
    for sq, p_code in pieces.items():
        idx = alg_to_idx(sq)
        # Parse 'wK' -> (1, 'K')
        c_code = 1 if p_code[0] == 'w' else 0
        b.sq[idx] = (c_code, p_code[1])
        
    # 2. Get Candidates
    # If legal_moves is provided in kwargs, use it to strict-filter or choose from.
    # Otherwise generate internal moves.
    # Note: If provided list contains castling, my generator won't match it (missing castling logic).
    # To be safe: generate own moves. If provided list exists, intersection or fallback?
    # Safest constraint approach: purely use internal logic to pick a move, but ensure it is in `legal_moves` if `legal_moves` is authoritative.
    # However, since I cannot generate castling accurately, if the best move IS castling, I will miss it.
    # If I just evaluate the moves in `legal_moves`, I rely on external correctness (which is mandated by "one move string that is an element of legal_moves").
    
    provided_legal = kwargs.get('legal_moves', [])
    
    if provided_legal and isinstance(provided_legal, list) and len(provided_legal) > 0:
        candidates = provided_legal
    else:
        candidates = generate_legal_moves(b)
        
    if not candidates:
        return '0000' # Should not happen unless mate

    # 3. Search Loop
    start_ts = time.time()
    best_move = candidates[0]
    
    # Iterative Deepening
    # Depth 1 first
    best_score = -999999
    
    # Simple sort to improve alpha-beta (captures first?)
    # Without board context for external strings, hard to sort. Just shuffle?
    
    for depth in [1, 2]: # Depth 2 usually fits in 1s for Python < 1000 nodes/sec
        current_best_move = best_move
        current_best_score = -999999
        alpha = -999999
        beta = 999999
        
        timed_out = False
        
        for m_str in candidates:
            # Parse & Make
            u_src = alg_to_idx(m_str[0:2])
            u_dst = alg_to_idx(m_str[2:4])
            promo = m_str[4] if len(m_str) > 4 else None
            
            # Backups
            saved_sq_src = b.sq[u_src]
            saved_sq_dst = b.sq[u_dst]
            
            # Hypothetical check: is this move actually pseudo-legal on my board?
            # If using provided_legal, it might contain castling which I handle poorly if I try to validate.
            # Trust the string, just update board blindly (assuming external legality).
            # But wait, castling logic for board update (moving rook) is needed for accurate search tree.
            # If move is e1g1 (White Castle), I must move Rook h1->f1.
            # Detection: K move > 1 step.
            is_castling = False
            if b.sq[u_src] and b.sq[u_src][1] == 'K' and abs(u_dst - u_src) == 2:
                is_castling = True
            
            b.move(u_src, u_dst, promo)
            
            # Handle Castling Rook move manually for evaluation accuracy
            # (Only needed if provided_legal had castling)
            rook_src, rook_dst = None, None
            saved_rook = None
            if is_castling:
                if u_dst > u_src: # KS
                    rook_src = u_dst + 1 # e.g. g1+1 = h1? No, e1(4)->g1(6). h1(7).
                    rook_dst = u_dst - 1
                else: # QS
                    rook_src = u_dst - 2
                    rook_dst = u_dst + 1
                
                # Check valid rook src (sometimes 0x88 issues if incorrect math)
                if rook_src & 0x88 == 0 and rook_dst & 0x88 == 0:
                    saved_rook = b.sq[rook_src]
                    b.sq[rook_dst] = saved_rook
                    b.sq[rook_src] = None

            val = alphabeta(b, depth - 1, -beta, -alpha, start_ts, 0.95) # 0.95s buf
            
            # Undo Rook
            if is_castling and saved_rook:
                b.sq[rook_src] = saved_rook
                b.sq[rook_dst] = None
                
            # Undo Move
            b.sq[u_src] = saved_sq_src
            b.sq[u_dst] = saved_sq_dst
            b.turn = 1 - b.turn
            
            if val is None:
                timed_out = True
                break
            
            val = -val
            if val > current_best_score:
                current_best_score = val
                current_best_move = m_str
            
            alpha = max(alpha, current_best_score)
        
        if not timed_out:
            best_move = current_best_move
            # If we found a mate, stop
            if best_score > 15000: break
        else:
            break
            
    return best_move

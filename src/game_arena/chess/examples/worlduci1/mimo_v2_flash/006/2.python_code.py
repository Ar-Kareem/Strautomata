
import random

def policy(pieces: dict[str, str], to_play: str) -> str:
    # Piece constants
    EMPTY = 0
    PAWN = 1
    KNIGHT = 3
    BISHOP = 4
    ROOK = 5
    QUEEN = 7
    KING = 9
    
    # Color constants
    WHITE = 1
    BLACK = -1
    
    # Map piece codes to internal representation
    code_map = {
        'P': PAWN, 'N': KNIGHT, 'B': BISHOP, 'R': ROOK, 'Q': QUEEN, 'K': KING
    }
    
    # Helper to map coordinates
    files = 'abcdefgh'
    
    def parse_square(sq):
        f = files.index(sq[0])
        r = 8 - int(sq[1])
        return r, f
        
    def to_uci(r, f):
        return files[f] + str(8 - r)

    # Initialize board
    board = [[EMPTY]*8 for _ in range(8)]
    for sq, pc in pieces.items():
        r, c = parse_square(sq)
        val = code_map[pc[1]]
        if pc[0] == 'b': val = -val
        board[r][c] = val

    # Determine turn color
    my_color = WHITE if to_play == 'white' else BLACK
    
    # --- Move Generation ---
    
    def get_all_moves(bd, turn):
        moves = []
        en_passant_target = None # Simplified: Doesn't track full EP state, relies on position
        
        # Scan board
        for r in range(8):
            for c in range(8):
                p = bd[r][c]
                if p == EMPTY: continue
                if (turn == WHITE and p > 0) or (turn == BLACK and p < 0):
                    p_type = abs(p)
                    
                    # Pawn
                    if p_type == PAWN:
                        dir = -1 if turn == WHITE else 1
                        start_row = 6 if turn == WHITE else 1
                        # Move forward
                        if 0 <= r+dir < 8 and bd[r+dir][c] == EMPTY:
                            # Promotion check
                            if (turn == WHITE and r+dir == 0) or (turn == BLACK and r+dir == 7):
                                for prom in ['q', 'r', 'b', 'n']:
                                    moves.append(((r,c), (r+dir, c), prom))
                            else:
                                moves.append(((r,c), (r+dir, c), None))
                            # Double move
                            if r == start_row and bd[r+2*dir][c] == EMPTY:
                                moves.append(((r,c), (r+2*dir, c), None))
                        # Captures
                        for dc in [-1, 1]:
                            if 0 <= c+dc < 8 and 0 <= r+dir < 8:
                                target = bd[r+dir][c+dc]
                                # Normal capture
                                if target != EMPTY and ((target > 0 and turn == BLACK) or (target < 0 and turn == WHITE)):
                                    if (turn == WHITE and r+dir == 0) or (turn == BLACK and r+dir == 7):
                                        for prom in ['q', 'r', 'b', 'n']:
                                            moves.append(((r,c), (r+dir, c+dc), prom))
                                    else:
                                        moves.append(((r,c), (r+dir, c+dc), None))
                                # Simplified En Passant
                                # To be strictly correct, we need EP history. 
                                # We will treat double pawn pushes adjacent to our pawn as potential EP targets for the next move.
                                # But since we don't have history here, we skip EP logic to save complexity and stay safe.
                                
                    # Knight
                    elif p_type == KNIGHT:
                        offsets = [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]
                        for dr, dc in offsets:
                            nr, nc = r+dr, c+dc
                            if 0 <= nr < 8 and 0 <= nc < 8:
                                target = bd[nr][nc]
                                if target == EMPTY or (target > 0 and turn == BLACK) or (target < 0 and turn == WHITE):
                                    moves.append(((r,c), (nr, nc), None))
                    
                    # King (including Castling - simplified logic)
                    elif p_type == KING:
                        offsets = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
                        for dr, dc in offsets:
                            nr, nc = r+dr, c+dc
                            if 0 <= nr < 8 and 0 <= nc < 8:
                                target = bd[nr][nc]
                                if target == EMPTY or (target > 0 and turn == BLACK) or (target < 0 and turn == WHITE):
                                    moves.append(((r,c), (nr, nc), None))
                        # Castling (Basic: Check if rows 6/7 (white) or 0/1 (black) are mostly empty)
                        # This is a heuristic approximation. Strict castling rights require game history (castling flags).
                        # If we are in the corner and it's empty, try castling.
                        if turn == WHITE and r == 7 and c == 4:
                            # Kingside
                            if bd[7][5] == EMPTY and bd[7][6] == EMPTY and bd[7][7] == ROOK:
                                moves.append(((7,4), (7,6), None))
                            # Queenside
                            if bd[7][3] == EMPTY and bd[7][2] == EMPTY and bd[7][1] == EMPTY and bd[7][0] == ROOK:
                                moves.append(((7,4), (7,2), None))
                        elif turn == BLACK and r == 0 and c == 4:
                            # Kingside
                            if bd[0][5] == EMPTY and bd[0][6] == EMPTY and bd[0][7] == -ROOK:
                                moves.append(((0,4), (0,6), None))
                            # Queenside
                            if bd[0][3] == EMPTY and bd[0][2] == EMPTY and bd[0][1] == EMPTY and bd[0][0] == -ROOK:
                                moves.append(((0,4), (0,2), None))

                    # Sliding Pieces (Bishop, Rook, Queen)
                    if p_type == BISHOP or p_type == ROOK or p_type == QUEEN:
                        directions = []
                        if p_type in [BISHOP, QUEEN]:
                            directions.extend([(-1,-1),(-1,1),(1,-1),(1,1)])
                        if p_type in [ROOK, QUEEN]:
                            directions.extend([(-1,0),(1,0),(0,-1),(0,1)])
                        
                        for dr, dc in directions:
                            nr, nc = r+dr, c+dc
                            while 0 <= nr < 8 and 0 <= nc < 8:
                                target = bd[nr][nc]
                                if target == EMPTY:
                                    moves.append(((r,c), (nr, nc), None))
                                elif (target > 0 and turn == BLACK) or (target < 0 and turn == WHITE):
                                    moves.append(((r,c), (nr, nc), None))
                                    break
                                else:
                                    break
                                nr += dr
                                nc += dc
        
        # Validate moves (ensure King is not left in check)
        valid_moves = []
        for m in moves:
            fr, to = m[0], m[1]
            fr_r, fr_c = fr
            to_r, to_c = to
            
            # Simulate
            old_piece = bd[to_r][to_c]
            moved_piece = bd[fr_r][fr_c]
            bd[fr_r][fr_c] = EMPTY
            bd[to_r][to_c] = moved_piece
            
            # Promotion handling for simulation (visual only, doesn't change value much for check logic)
            if m[2]:
                # If we promote, assume Queen for check simulation
                bd[to_r][to_c] = (QUEEN if turn == WHITE else -QUEEN)
            
            # Check King Safety
            if not is_in_check(bd, turn):
                valid_moves.append(m)
            
            # Revert
            bd[fr_r][fr_c] = moved_piece
            bd[to_r][to_c] = old_piece

        return valid_moves

    def is_in_check(bd, turn):
        # Find King
        kr, kc = -1, -1
        for r in range(8):
            for c in range(8):
                if bd[r][c] == (KING if turn == WHITE else -KING):
                    kr, kc = r, c
                    break
        if kr == -1: return True # Should not happen unless king captured (invalid state)
        
        # Check if any enemy piece attacks (r, c)
        enemy = -turn
        
        # Pawn attacks
        attack_dir = 1 if enemy == WHITE else -1
        for dc in [-1, 1]:
            if 0 <= kr+attack_dir < 8 and 0 <= kc+dc < 8:
                if bd[kr+attack_dir][kc+dc] == enemy * PAWN:
                    return True
        
        # Knight attacks
        offsets = [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]
        for dr, dc in offsets:
            nr, nc = kr+dr, kc+dc
            if 0 <= nr < 8 and 0 <= nc < 8 and bd[nr][nc] == enemy * KNIGHT:
                return True
                
        # King attacks
        offsets = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
        for dr, dc in offsets:
            nr, nc = kr+dr, kc+dc
            if 0 <= nr < 8 and 0 <= nc < 8 and bd[nr][nc] == enemy * KING:
                return True
                
        # Sliding attacks
        directions = [(-1,-1),(-1,1),(1,-1),(1,1), (-1,0),(1,0),(0,-1),(0,1)]
        for dr, dc in directions:
            nr, nc = kr+dr, kc+dc
            dist = 0
            while 0 <= nr < 8 and 0 <= nc < 8:
                dist += 1
                p = bd[nr][nc]
                if p != EMPTY:
                    if (p == enemy * ROOK and abs(dr)+abs(dc) != 1 and abs(dr)!=abs(dc)) or \
                       (p == enemy * BISHOP and abs(dr)==abs(dc)) or \
                       (p == enemy * QUEEN) or \
                       (p == enemy * PAWN and dist == 1 and ((enemy==WHITE and dr==1) or (enemy==BLACK and dr==-1)) and dc != 0):
                        return True
                    break
                nr += dr
                nc += dc
        return False

    # --- Evaluation ---

    piece_vals = {PAWN: 100, KNIGHT: 320, BISHOP: 330, ROOK: 500, QUEEN: 900, KING: 20000}
    
    # Bonus for centralization (e4, d4, e5, d5)
    center_bonus = [
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 5, 10, 10, 5, 0, 0],
        [0, 0, 10, 20, 20, 10, 0, 0],
        [0, 0, 10, 20, 20, 10, 0, 0],
        [0, 0, 5, 10, 10, 5, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0]
    ]

    def evaluate(bd, turn):
        score = 0
        material_count = 0
        
        for r in range(8):
            for c in range(8):
                p = bd[r][c]
                if p == EMPTY: continue
                
                p_abs = abs(p)
                p_val = piece_vals[p_abs]
                p_color = 1 if p > 0 else -1
                
                # Material
                if p > 0: 
                    score += p_val
                    material_count += p_val
                else: 
                    score -= p_val
                    material_count += p_val
                
                # Positional (Centralization)
                # Flip row for black
                r_eff = r if p > 0 else 7-r
                c_eff = c if p > 0 else 7-c
                bonus = center_bonus[r_eff][c_eff]
                if p > 0: score += bonus
                else: score -= bonus
                
                # Bishop Pair Bonus (Simple heuristic)
                if p_abs == BISHOP:
                    if p > 0: score += 5
                    else: score -= 5

        # Mobility (Tapered: more important in endgame)
        # Estimate mobility by counting own legal moves
        # Note: Doing full move gen for eval is slow, but depth 2 is acceptable.
        # We will count moves for current turn and subtract moves for opponent.
        # This is expensive, so we only do it if the state isn't terminal.
        
        # Heuristic: Mobility weight based on material on board
        # Less material = Endgame = Higher mobility weight
        avg_material = material_count / 32.0 # Normalized roughly
        mobility_weight = 5 * (1.2 - avg_material) # Increases as material drops
        
        if mobility_weight > 0:
            my_moves = len(get_all_moves(bd, turn))
            opp_moves = len(get_all_moves(bd, -turn))
            score += (my_moves - opp_moves) * mobility_weight

        # Perspective
        if turn == BLACK:
            score = -score
            
        return score

    # --- Minimax Search (Depth 2) ---
    
    def minimax(bd, depth, alpha, beta, turn):
        if depth == 0:
            return evaluate(bd, turn)
            
        moves = get_all_moves(bd, turn)
        
        if not moves:
            # Checkmate or Stalemate
            if is_in_check(bd, turn):
                return -99999 if turn == my_color else 99999 # Huge loss if we are mated
            return 0 # Stalemate
        
        # Move Ordering: Simple capture ordering
        def move_score(m):
            fr, to = m[0], m[1]
            target = bd[to[0]][to[1]]
            if target != EMPTY:
                return 10000 + abs(target) # Prioritize captures
            return 0
        moves.sort(key=move_score, reverse=True)
        
        if turn == my_color:
            max_eval = -float('inf')
            for move in moves:
                # Apply Move
                fr, to, prom = move
                fr_r, fr_c = fr
                to_r, to_c = to
                old_p = bd[to_r][to_c]
                p = bd[fr_r][fr_c]
                bd[fr_r][fr_c] = EMPTY
                bd[to_r][to_c] = p
                if prom:
                    bd[to_r][to_c] = (QUEEN if my_color == WHITE else -QUEEN)
                
                eval = minimax(bd, depth-1, alpha, beta, -turn)
                
                # Undo Move
                bd[fr_r][fr_c] = p
                bd[to_r][to_c] = old_p
                
                if eval > max_eval: max_eval = eval
                alpha = max(alpha, eval)
                if beta <= alpha: break
            return max_eval
        else:
            min_eval = float('inf')
            for move in moves:
                fr, to, prom = move
                fr_r, fr_c = fr
                to_r, to_c = to
                old_p = bd[to_r][to_c]
                p = bd[fr_r][fr_c]
                bd[fr_r][fr_c] = EMPTY
                bd[to_r][to_c] = p
                if prom:
                    bd[to_r][to_c] = (QUEEN if -turn == WHITE else -QUEEN)
                    
                eval = minimax(bd, depth-1, alpha, beta, -turn)
                
                bd[fr_r][fr_c] = p
                bd[to_r][to_c] = old_p
                
                if eval < min_eval: min_eval = eval
                beta = min(beta, eval)
                if beta <= alpha: break
            return min_eval

    # --- Main Logic ---
    
    legal_moves_raw = get_all_moves(board, my_color)
    
    # Format moves for return (UCI)
    def format_move(m):
        fr, to, prom = m
        s = to_uci(fr[0], fr[1]) + to_uci(to[0], to[1])
        if prom: s += prom
        return s
        
    legal_moves = [format_move(m) for m in legal_moves_raw]
    
    if not legal_moves:
        # Should not happen if game state is valid, but safety net
        return "a1a1" 
        
    best_score = -float('inf')
    best_move = legal_moves[0]
    best_move_raw = legal_moves_raw[0]
    
    # First pass: Look for immediate checkmates or depth 1 tactical blunders
    # Sort by captures for better pruning
    # We perform the depth 2 search on all moves to find the best one
    for i, move in enumerate(legal_moves_raw):
        fr, to, prom = move
        fr_r, fr_c = fr
        to_r, to_c = to
        
        # Apply Move
        old_p = board[to_r][to_c]
        p = board[fr_r][fr_c]
        board[fr_r][fr_c] = EMPTY
        board[to_r][to_c] = p
        if prom:
            board[to_r][to_c] = (QUEEN if my_color == WHITE else -QUEEN)
            
        # Depth 1 search (Opponent response)
        score = minimax(board, 1, -float('inf'), float('inf'), -my_color)
        
        # Undo
        board[fr_r][fr_c] = p
        board[to_r][to_c] = old_p
        
        # Add a small random jitter to prefer captures over quiet moves if scores are equal
        # This makes the bot look more active
        if score == best_score:
            if old_p != EMPTY:
                score += 1
            
        if score > best_score:
            best_score = score
            best_move = format_move(move)
            best_move_raw = move
            
    return best_move

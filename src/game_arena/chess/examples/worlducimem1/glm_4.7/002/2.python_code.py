
import random
import copy

# --- Constants ---
PIECE_VALUES = {
    'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000
}

# Simplified Piece-Square Tables (PST) for positional evaluation
# Positive values are good for White, negative for Black
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
    # Generic others for brevity, primarily controlling center
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

# --- Helpers ---
def sq_to_idx(sq):
    return (ord(sq[0]) - 97) + (int(sq[1]) - 1) * 8

def idx_to_sq(idx):
    return chr(idx % 8 + 97) + str(idx // 8 + 1)

def get_piece_info(board, idx):
    pc = board[idx]
    if pc == '.': return None
    return pc[0], pc[1] # color, type

def is_enemy(p_color, my_color):
    return p_color and p_color != my_color

def is_ally(p_color, my_color):
    return p_color and p_color == my_color

# --- Move Logic ---

def get_legal_moves(board, to_play_color, castling, ep_sq):
    """
    Generate legal moves for the current position.
    board: list of 64 chars
    to_play_color: 'w' or 'b'
    castling: dict of bools
    ep_sq: index of en passant target or None
    """
    moves = []
    
    # Identify King pos early for check validation
    my_king_idx = -1
    for i in range(64):
        if board[i] == to_play_color + 'K':
            my_king_idx = i
            break
    
    # 1. Generate Pseudo-Legal Moves
    for i in range(64):
        pc = board[i]
        if pc == '.': continue
        p_color, p_type = pc[0], pc[1]
        if p_color != to_play_color: continue

        r, f = i // 8, i % 8
        
        if p_type == 'P':
            direction = -1 if p_color == 'w' else 1
            start_rank = 6 if p_color == 'w' else 1
            promotion_rank = 0 if p_color == 'w' else 7
            
            # Quiet push
            target = i + direction * 8
            if 0 <= target < 64 and board[target] == '.':
                if r // 8 == promotion_rank: # Logic check: is target on promotion rank?
                    # Actually, if I'm on rank 2 (white), target is rank 1. Wait.
                    # White pawns move -1 (7->0). Start rank 6. Target 5. 
                    # If r (6) + dir(-1) = 5.
                    # Promotion rank for White is 0. Black is 7.
                    is_promo = (target // 8 == promotion_rank) 
                    if is_promo:
                        for prom in ['q', 'r', 'b', 'n']:
                            moves.append((i, target, prom))
                    else:
                        moves.append((i, target, None))
                        
                        # Double push
                        if r == start_rank:
                            target2 = target + direction * 8
                            if board[target2] == '.':
                                moves.append((i, target2, None))

            # Captures
            for df in [-1, 1]:
                target = i + direction * 8 + df
                # Check bounds (wrap around)
                tr, tf = target // 8, target % 8
                if 0 <= target < 64 and abs(tf - f) == 1:
                    if board[target] != '.' and is_enemy(board[target][0], to_play_color):
                        is_promo = (tr == promotion_rank)
                        if is_promo:
                            for prom in ['q', 'r', 'b', 'n']:
                                moves.append((i, target, prom))
                        else:
                            moves.append((i, target, None))
                    # En Passant
                    elif target == ep_sq:
                        moves.append((i, target, None))

        elif p_type == 'N':
            jumps = [-17, -15, -10, -6, 6, 10, 15, 17]
            for offset in jumps:
                target = i + offset
                if 0 <= target < 64:
                    tr, tf = target // 8, target % 8
                    # Check for board wrap (knight jumping from a-file to h-file)
                    if abs(tf - f) <= 2:
                        if board[target] == '.' or is_enemy(board[target][0], to_play_color):
                            moves.append((i, target, None))

        elif p_type == 'B':
            dirs = [-9, -7, 7, 9]
            for d in dirs:
                target = i + d
                while 0 <= target < 64:
                    tr, tf = target // 8, target % 8
                    if abs(tf - f) > 1: break # Wrap check
                    
                    if board[target] == '.':
                        moves.append((i, target, None))
                    elif is_enemy(board[target][0], to_play_color):
                        moves.append((i, target, None))
                        break
                    else: # Ally
                        break
                    target += d

        elif p_type == 'R':
            dirs = [-8, -1, 1, 8]
            for d in dirs:
                target = i + d
                while 0 <= target < 64:
                    tr, tf = target // 8, target % 8
                    if abs(tf - f) > 1 and abs(d) in [-1, 1]: break # Wrap check for file moves
                    
                    if board[target] == '.':
                        moves.append((i, target, None))
                    elif is_enemy(board[target][0], to_play_color):
                        moves.append((i, target, None))
                        break
                    else:
                        break
                    target += d

        elif p_type == 'Q':
            dirs = [-9, -7, -8, -1, 1, 8, 7, 9]
            for d in dirs:
                target = i + d
                while 0 <= target < 64:
                    tr, tf = target // 8, target % 8
                    if abs(tf - f) > 1 and abs(d) in [-1, 1, 7, 9]: break
                    
                    if board[target] == '.':
                        moves.append((i, target, None))
                    elif is_enemy(board[target][0], to_play_color):
                        moves.append((i, target, None))
                        break
                    else:
                        break
                    target += d

        elif p_type == 'K':
            dirs = [-9, -7, -8, -1, 1, 8, 7, 9]
            for d in dirs:
                target = i + d
                if 0 <= target < 64:
                    tr, tf = target // 8, target % 8
                    if abs(tf - f) <= 1:
                        if board[target] == '.' or is_enemy(board[target][0], to_play_color):
                            moves.append((i, target, None))
            
            # Castling
            if to_play_color == 'w' and i == 60: # e1
                if castling['K'] and board[61] == '.' and board[62] == '.':
                    if not is_square_attacked(board, 60, 'b') and \
                       not is_square_attacked(board, 61, 'b') and \
                       not is_square_attacked(board, 62, 'b'):
                        moves.append((i, 62, None)) # e1g1
                if castling['Q'] and board[59] == '.' and board[58] == '.' and board[57] == '.':
                    if not is_square_attacked(board, 60, 'b') and \
                       not is_square_attacked(board, 59, 'b') and \
                       not is_square_attacked(board, 58, 'b'):
                        moves.append((i, 58, None)) # e1c1
            elif to_play_color == 'b' and i == 4: # e8
                if castling['k'] and board[5] == '.' and board[6] == '.':
                    if not is_square_attacked(board, 4, 'w') and \
                       not is_square_attacked(board, 5, 'w') and \
                       not is_square_attacked(board, 6, 'w'):
                        moves.append((i, 6, None)) # e8g8
                if castling['q'] and board[3] == '.' and board[2] == '.' and board[1] == '.':
                    if not is_square_attacked(board, 4, 'w') and \
                       not is_square_attacked(board, 3, 'w') and \
                       not is_square_attacked(board, 2, 'w'):
                        moves.append((i, 2, None)) # e8c8

    # 2. Filter Illegal Moves (Checks)
    legal_moves = []
    for start, end, prom in moves:
        # Apply move temporarily
        saved_board = list(board)
        captured = board[end]
        
        # Handle en passant capture removal
        if board[start][1] == 'P' and end != start + (8 if to_play_color == 'b' else -8) and \
           end != start + (16 if to_play_color == 'b' else -16) and captured == '.':
             # En passant capture square
             ep_capture_idx = end - (8 if to_play_color == 'b' else -8)
             board[ep_capture_idx] = '.'
        
        board[end] = board[start]
        board[start] = '.'
        if prom: board[end] = to_play_color + prom.upper()

        # Find King (might have moved)
        k_pos = my_king_idx
        if board[my_king_idx][1] != 'K':
            for k in range(64):
                if board[k] == to_play_color + 'K':
                    k_pos = k
                    break
        
        if not is_square_attacked(board, k_pos, 'b' if to_play_color == 'w' else 'w'):
            legal_moves.append((start, end, prom))

        # Restore
        board[ep_capture_idx] = saved_board[ep_capture_idx] if 'ep_capture_idx' in locals() else saved_board[ep_capture_idx] 
        # The above line is tricky in Python scope, simpler to just copy back
        board[start] = saved_board[start]
        board[end] = saved_board[end]
        if 'ep_capture_idx' in locals():
            board[ep_capture_idx] = saved_board[ep_capture_idx]

    return legal_moves

def is_square_attacked(board, sq_idx, attacker_color):
    # Check if any attacker_color piece can hit sq_idx
    # Pawn attacks
    p_dir = -1 if attacker_color == 'w' else 1
    # Pawns attack "forward" relative to themselves.
    # A white pawn at X attacks X-8 + (-1, 1).
    # Wait, if attacker is White, they are below (rank 2). They attack Rank 3.
    # sq_idx is target. 
    # If attacker is White, check sq_idx - 8 +/- 1 for White Pawns.
    
    # Reverse logic: from target, where would attackers come from?
    # Pawn: 
    check_dir = 1 if attacker_color == 'w' else -1 # White attacks from rank-1 to rank. So look at rank - check_dir
    for df in [-1, 1]:
        source = sq_idx + check_dir * 8 + df
        r, f = source // 8, source % 8
        tr, tf = sq_idx // 8, sq_idx % 8
        if 0 <= source < 64 and abs(tf - f) == 1:
            if board[source] == attacker_color + 'P': return True
            
    # Knight
    jumps = [-17, -15, -10, -6, 6, 10, 15, 17]
    for offset in jumps:
        source = sq_idx + offset
        if 0 <= source < 64:
            sr, sf = source // 8, source % 8
            tr, tf = sq_idx // 8, sq_idx % 8
            if abs(sf - tf) <= 2:
                if board[source] == attacker_color + 'N': return True

    # King
    for d in [-9, -7, -8, -1, 1, 8, 7, 9]:
        source = sq_idx + d
        if 0 <= source < 64:
            sr, sf = source // 8, source % 8
            tr, tf = sq_idx // 8, sq_idx % 8
            if abs(sf - tf) <= 1:
                if board[source] == attacker_color + 'K': return True

    # Sliding (R, B, Q)
    dirs = [-9, -7, 7, 9] # Bishop
    for d in dirs:
        source = sq_idx + d
        while 0 <= source < 64:
            sr, sf = source // 8, source % 8
            tr, tf = sq_idx // 8, sq_idx % 8
            if abs(sf - tf) > 1: break
            pc = board[source]
            if pc != '.':
                if pc[0] == attacker_color and pc[1] in ['B', 'Q']: return True
                break
            source += d
            
    dirs = [-8, -1, 1, 8] # Rook
    for d in dirs:
        source = sq_idx + d
        while 0 <= source < 64:
            sr, sf = source // 8, source % 8
            tr, tf = sq_idx // 8, sq_idx % 8
            if abs(sf - tf) > 1 and abs(d) in [-1, 1]: break
            pc = board[source]
            if pc != '.':
                if pc[0] == attacker_color and pc[1] in ['R', 'Q']: return True
                break
            source += d
            
    return False

# --- Search ---

def evaluate(board, color):
    score = 0
    for i in range(64):
        pc = board[i]
        if pc == '.': continue
        p_color, p_type = pc[0], pc[1]
        val = PIECE_VALUES[p_type]
        
        # PST handling
        # If White, use table as is. If Black, reverse table (mirror rank).
        pst_idx = i if p_color == 'w' else 63 - i
        pst_val = PST[p_type][pst_idx]
        
        if p_color == color:
            score += val + pst_val
        else:
            score -= (val + pst_val)
            
    return score

def make_move(board, move):
    # Returns new board and info (ep_possible, capture)
    new_board = list(board)
    start, end, prom = move
    p_color = new_board[start][0]
    p_type = new_board[start][1]
    
    # Capture?
    captured = new_board[end]
    
    # Move
    new_board[end] = new_board[start]
    new_board[start] = '.'
    
    # Promotion
    if prom:
        new_board[end] = p_color + prom.upper()
        
    # Castling Move (Rook move)
    if p_type == 'K':
        if abs(end - start) == 2:
            if end > start: # King side
                new_board[start+1] = new_board[start+3] # Move Rook
                new_board[start+3] = '.'
            else: # Queen side
                new_board[start-1] = new_board[start-4]
                new_board[start-4] = '.'
                
    # En Passant Capture (remove pawn)
    if p_type == 'P' and end != start + (8 if p_color == 'b' else -8) and \
       end != start + (16 if p_color == 'b' else -16) and captured == '.':
        # Remove the captured pawn
        cap_idx = end - (8 if p_color == 'b' else -8)
        new_board[cap_idx] = '.'
        
    return new_board

def get_move_score(move, board):
    # MVV-LVA
    start, end, prom = move
    target = board[end]
    if target == '.':
        if prom: return 800 # Promote
        return 0
    
    victim_val = PIECE_VALUES[target[1]]
    attacker_val = PIECE_VALUES[board[start][1]]
    return victim_val * 10 - attacker_val

def alphabeta(board, depth, alpha, beta, color, castling, ep_sq):
    if depth == 0:
        return evaluate(board, color)
    
    moves = get_legal_moves(board, color, castling, ep_sq)
    if not moves:
        if is_square_attacked(board, 
                               next((i for i, x in enumerate(board) if x == color+'K'), -1), 
                               'b' if color == 'w' else 'w'):
            return -100000 + depth # Checkmate
        return 0 # Stalemate
        
    # Sort moves: Captures first
    moves.sort(key=lambda m: get_move_score(m, board), reverse=True)
    
    for move in moves:
        new_board = make_move(board, move)
        
        # Update castling/EP for next node? 
        # Simplified: Castling/EP propagation in recursion is hard without full undo stack.
        # For depth 3, the effect of losing castling rights or EP is minimal.
        # We just pass the current state's rights. This is a "light" engine approximation.
        val = -alphabeta(new_board, depth-1, -beta, -alpha, 'b' if color == 'w' else 'w', castling, None)
        if val >= beta:
            return beta
        if val > alpha:
            alpha = val
    return alpha

# --- Main API ---

def policy(pieces: dict[str, str], to_play: str, memory: dict) -> tuple[str, dict]:
    
    # 1. Convert pieces to internal board array
    board = ['.'] * 64
    for sq, pc in pieces.items():
        board[sq_to_idx(sq)] = pc
        
    color = 'w' if to_play == 'white' else 'b'
    
    # 2. Update Castling and EP from memory
    # Initialize memory if needed
    if 'castling' not in memory:
        memory['castling'] = {
            'K': 'e1' in pieces and 'h1' in pieces, 
            'Q': 'e1' in pieces and 'a1' in pieces,
            'k': 'e8' in pieces and 'h8' in pieces, 
            'q': 'e8' in pieces and 'a8' in pieces
        }
        # If kings/rooks aren't home, rights are lost
        if 'K' in pieces['e1']: # Standard start check logic
            pass # Assuming start position
        else:
             # If not standard start, assume no castling unless history proves otherwise (which we don't have on turn 1)
             pass
        memory['ep'] = None
        memory['last_board'] = pieces.copy()
    else:
        # Detect changes to update rights
        prev_board = memory['last_board']
        curr_board = pieces
        
        # If King moved, lose rights
        if prev_board.get('e1') == 'wK' and 'e1' not in curr_board: memory['castling']['K'] = False; memory['castling']['Q'] = False
        if prev_board.get('e8') == 'bK' and 'e8' not in curr_board: memory['castling']['k'] = False; memory['castling']['q'] = False
        
        # If Rooks moved or captured
        if prev_board.get('h1') == 'wR' and 'h1' not in curr_board: memory['castling']['K'] = False
        if prev_board.get('a1') == 'wR' and 'a1' not in curr_board: memory['castling']['Q'] = False
        if prev_board.get('h8') == 'bR' and 'h8' not in curr_board: memory['castling']['k'] = False
        if prev_board.get('a8') == 'bR' and 'a8' not in curr_board: memory['castling']['q'] = False
        
        # En Passant Detection
        # Look for a pawn that moved 2 squares
        # This is complex to robustly detect without move logs, but we can try:
        # If a pawn is now on rank 4 (white) or 5 (black), and prev_board had it on rank 2 or 7...
        memory['ep'] = None # Reset EP by default (EP lasts 1 move)
        
        # Simple check: Did a white pawn move from rank 2 to rank 4 in one turn?
        # Since we only see snapshots, we assume if opponent moved, they might have enabled EP.
        # However, we only need to know EP for *our* turn.
        # If opponent moved, EP is set. If we moved, we consumed it.
        # Since we calculate moves for `to_play`, and `to_play` is the one moving NOW:
        # If `to_play` is White, and Black just moved, we need to check if Black's last move was double pawn.
        # But we only have `pieces`.
        # We will approximate: ignore complex EP generation logic unless obvious from position.
        # Actually, let's just skip dynamic EP detection from snapshots to avoid bugs, 
        # relying on standard EP logic inside the generator if provided.
        # But `memory['ep']` is None. 
        # To be strong, we should try to detect it.
        # Iterate squares. If white pawn on rank 4 (idx 24-31), check rank 2 (8-15) in prev.
        # Opponent color: 'b' if to_play='white'.
        opponent = 'b' if color == 'w' else 'w'
        pawn_rank_start = 1 if opponent == 'b' else 6 # 0-indexed
        pawn_rank_end = 3 if opponent == 'b' else 4 # 0-indexed
        
        for f in range(8):
            sq_end = pawn_rank_end * 8 + f
            sq_start = pawn_rank_start * 8 + f
            if board[sq_end] == opponent + 'P' and prev_board.get(idx_to_sq(sq_start)) == opponent + 'P':
                 # Opponent pawn moved 2 squares
                 memory['ep'] = sq_end - (8 if opponent == 'b' else -8)

        memory['last_board'] = pieces.copy()

    # 3. Get Legal Moves
    legal_moves = get_legal_moves(board, color, memory['castling'], memory['ep'])
    
    if not legal_moves:
        # Should not happen in game flow unless mate/stalemate
        return "a1a1", memory # Fallback fail-safe

    # 4. Search for best move
    # Depth 3 is safe for Python in 1s. Depth 4 if branching is low.
    # Use Iterative Deepening or just fixed depth? Fixed depth 3.
    
    best_move = None
    best_score = -float('inf')
    
    # Shuffle to add variety in equal positions
    random.shuffle(legal_moves)
    
    # Sort moves for efficiency (capturers first)
    legal_moves.sort(key=lambda m: get_move_score(m, board), reverse=True)

    for move in legal_moves:
        new_board = make_move(board, move)
        
        # Note: Passing memory['castling'] and None for EP to child is imperfect 
        # because the child state might change rights, but it's a standard simplification.
        score = -alphabeta(new_board, 2, -float('inf'), float('inf'), 
                           'b' if color == 'w' else 'w', memory['castling'], None)
        
        if score > best_score:
            best_score = score
            best_move = move

    # 5. Format Output
    start, end, prom = best_move
    move_str = idx_to_sq(start) + idx_to_sq(end)
    if prom:
        move_str += prom
        
    return move_str, memory

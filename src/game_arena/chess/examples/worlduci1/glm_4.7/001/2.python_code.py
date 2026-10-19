
import random
import math

# --- Configuration ---

# Piece values for evaluation
PIECE_VALUES = {
    'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000
}

# Piece-Square Tables (PST) for positional evaluation
# Defined for White (0..63), will be mirrored for Black
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
    'R': [0]*64, # Simplified
    'Q': [-20,-10,-10, -5, -5,-10,-10,-20] + [0]*8 + [-5]*4 + [0]*4 + [0]*8 + [5]*8 + [5]*8 + [10]*4 + [-20,-10,-10, -5, -5,-10,-10,-20],
    'K': [0]*64  # Simplified King safety
}

# --- Helper Functions ---

def sq_to_idx(sq):
    """Convert algebraic notation (e.g., 'e4') to board index (0-63)."""
    return (8 - int(sq[1])) * 8 + (ord(sq[0]) - ord('a'))

def idx_to_sq(idx):
    """Convert board index (0-63) to algebraic notation."""
    return chr(ord('a') + (idx % 8)) + str(8 - idx // 8)

def get_pst_score(piece_type, idx, color):
    """Get positional score from PST, mirroring for Black."""
    if color == 'w':
        return PST.get(piece_type, [0]*64)[idx]
    else:
        return PST.get(piece_type, [0]*64)[63 - idx]

# --- Move Generation & Logic ---

def get_legal_moves(board, to_play):
    """Generate all legal moves for the current position."""
    color = 'w' if to_play == 'white' else 'b'
    opp = 'b' if color == 'w' else 'w'
    moves = []
    
    # 1. Generate Pseudo-Legal Moves
    for i in range(64):
        p = board[i]
        if not p or p[0] != color:
            continue
        
        p_type = p[1]
        r, c = i // 8, i % 8
        
        # Pawn
        if p_type == 'P':
            direction = -1 if color == 'w' else 1
            start_rank = 6 if color == 'w' else 1
            promo_rank = 0 if color == 'w' else 7
            
            # Move forward 1
            nr, nc = r + direction, c
            if 0 <= nr < 8:
                ni = nr * 8 + nc
                if board[ni] == '':
                    moves.append((i, ni, 'q' if nr == promo_rank else ''))
                    # Move forward 2
                    if r == start_rank:
                        nnr = r + 2 * direction
                        nni = nnr * 8 + nc
                        if board[nni] == '':
                            moves.append((i, nni, ''))
            
            # Captures
            for dc in [-1, 1]:
                nr, nc = r + direction, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    ni = nr * 8 + nc
                    target = board[ni]
                    if target and target[0] == opp:
                        moves.append((i, ni, 'q' if nr == promo_rank else ''))

        # Knight
        elif p_type == 'N':
            for dr, dc in [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    ni = nr * 8 + nc
                    target = board[ni]
                    if not target or target[0] == opp:
                        moves.append((i, ni, ''))

        # King
        elif p_type == 'K':
            for dr, dc in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    ni = nr * 8 + nc
                    target = board[ni]
                    if not target or target[0] == opp:
                        moves.append((i, ni, ''))
            
            # Castling (Heuristic: allowed if pieces on home squares, path clear)
            home_rank = 7 if color == 'w' else 0
            if r == home_rank and c == 4:
                # Kingside
                if board[home_rank * 8 + 7] == color + 'R':
                    if board[home_rank * 8 + 5] == '' and board[home_rank * 8 + 6] == '':
                        moves.append((i, home_rank * 8 + 6, ''))
                # Queenside
                if board[home_rank * 8 + 0] == color + 'R':
                    if board[home_rank * 8 + 1] == '' and board[home_rank * 8 + 2] == '' and board[home_rank * 8 + 3] == '':
                        moves.append((i, home_rank * 8 + 2, ''))

        # Sliding Pieces (B, R, Q)
        elif p_type in ['B', 'R', 'Q']:
            dirs = []
            if p_type in ['B', 'Q']: dirs += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
            if p_type in ['R', 'Q']: dirs += [(-1, 0), (1, 0), (0, -1), (0, 1)]
            
            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                while 0 <= nr < 8 and 0 <= nc < 8:
                    ni = nr * 8 + nc
                    target = board[ni]
                    if not target:
                        moves.append((i, ni, ''))
                    else:
                        if target[0] == opp:
                            moves.append((i, ni, ''))
                        break
                    nr += dr
                    nc += dc

    # 2. Filter for Legality (King Safety)
    legal_moves = []
    
    # Find current King position
    king_pos = -1
    for i in range(64):
        if board[i] == color + 'K':
            king_pos = i
            break
            
    for start, end, prom in moves:
        p_moved = board[start]
        p_captured = board[end]
        
        # Simulate move
        board[end] = p_moved[0] + prom if prom else p_moved
        board[start] = ''
        
        # Determine King position after move
        kp = end if p_moved[1] == 'K' else king_pos
        
        # Check safety
        is_safe = not is_square_attacked(board, kp, opp)
        
        # Castling specific checks (path must be clear of attack)
        if is_safe and p_moved[1] == 'K' and abs(start - end) == 2:
            # Cannot castle out of check, through check, or into check
            # 'is_safe' checks into check. 
            # Check current position (start) and path
            if is_square_attacked(board, start, opp):
                is_safe = False
            else:
                direction = 1 if end > start else -1
                mid_sq = start + direction
                if is_square_attacked(board, mid_sq, opp):
                    is_safe = False

        # Undo move
        board[start] = p_moved
        board[end] = p_captured
        
        if is_safe:
            legal_moves.append((start, end, prom))
            
    return legal_moves

def is_square_attacked(board, sq_idx, attacker_color):
    """Check if a square is attacked by any piece of attacker_color."""
    r, c = sq_idx // 8, sq_idx % 8
    
    # Pawn attacks
    p_dir = -1 if attacker_color == 'w' else 1
    for dc in [-1, 1]:
        nr, nc = r + p_dir, c + dc
        if 0 <= nr < 8 and 0 <= nc < 8:
            if board[nr*8 + nc] == attacker_color + 'P':
                return True
                
    # Knight attacks
    for dr, dc in [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 8 and 0 <= nc < 8:
            if board[nr*8 + nc] == attacker_color + 'N':
                return True
                
    # King attacks (adjacency)
    for dr, dc in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 8 and 0 <= nc < 8:
            if board[nr*8 + nc] == attacker_color + 'K':
                return True

    # Sliding attacks (R, B, Q)
    # Indices 0-3 are diagonals (B/Q), 4-7 are straights (R/Q)
    all_dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)]
    for i, (dr, dc) in enumerate(all_dirs):
        nr, nc = r + dr, c + dc
        while 0 <= nr < 8 and 0 <= nc < 8:
            ni = nr * 8 + nc
            p = board[ni]
            if p:
                if p[0] == attacker_color:
                    pt = p[1]
                    if i < 4 and pt in ['B', 'Q']: return True
                    if i >= 4 and pt in ['R', 'Q']: return True
                break
            nr += dr
            nc += dc
            
    return False

def evaluate(board):
    """Static board evaluation."""
    score = 0
    for i in range(64):
        p = board[i]
        if p:
            color = p[0]
            p_type = p[1]
            val = PIECE_VALUES[p_type]
            pst = get_pst_score(p_type, i, color)
            if color == 'w':
                score += val + pst
            else:
                score -= (val + pst)
    return score

# --- Search ---

def minimax(board, depth, alpha, beta, to_play):
    """Minimax with Alpha-Beta pruning."""
    moves = get_legal_moves(board, to_play)
    
    if depth == 0:
        return evaluate(board), None
        
    if not moves:
        color = 'w' if to_play == 'white' else 'b'
        opp = 'b' if color == 'w' else 'w'
        # Find King
        kp = -1
        for i in range(64):
            if board[i] == color + 'K': kp = i
        if is_square_attacked(board, kp, opp):
            return -100000 + (3 - depth), None # Checkmate (prefer sooner)
        return 0, None # Stalemate

    # Move ordering: Captures first
    def move_score(m):
        _, end, _ = m
        target = board[end]
        if target:
            return PIECE_VALUES.get(target[1], 0)
        return 0
    moves.sort(key=move_score, reverse=True)

    best_move = moves[0] # Default
    
    if to_play == 'white':
        max_eval = -float('inf')
        for start, end, prom in moves:
            p_cap = board[end]
            p_mov = board[start]
            board[end] = p_mov[0] + prom if prom else p_mov
            board[start] = ''
            
            eval_val, _ = minimax(board, depth - 1, alpha, beta, 'black')
            
            board[start] = p_mov
            board[end] = p_cap
            
            if eval_val > max_eval:
                max_eval = eval_val
                best_move = (start, end, prom)
            alpha = max(alpha, eval_val)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for start, end, prom in moves:
            p_cap = board[end]
            p_mov = board[start]
            board[end] = p_mov[0] + prom if prom else p_mov
            board[start] = ''
            
            eval_val, _ = minimax(board, depth - 1, alpha, beta, 'white')
            
            board[start] = p_mov
            board[end] = p_cap
            
            if eval_val < min_eval:
                min_eval = eval_val
                best_move = (start, end, prom)
            beta = min(beta, eval_val)
            if beta <= alpha:
                break
        return min_eval, best_move

# --- Main Policy ---

def policy(pieces: dict[str, str], to_play: str) -> str:
    # Initialize board
    board = [''] * 64
    for sq, pc in pieces.items():
        board[sq_to_idx(sq)] = pc
        
    # Search
    _, best_move = minimax(board, 3, -float('inf'), float('inf'), to_play)
    
    # Construct UCI string
    if best_move:
        start, end, prom = best_move
        return idx_to_sq(start) + idx_to_sq(end) + prom
        
    # Fallback if search fails (should not happen in valid non-terminal states)
    legal_moves = get_legal_moves(board, to_play)
    if legal_moves:
        m = random.choice(legal_moves)
        return idx_to_sq(m[0]) + idx_to_sq(m[1]) + m[2]
    
    return "a1a1" # Absolute fail-safe

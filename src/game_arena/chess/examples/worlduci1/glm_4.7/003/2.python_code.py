
import random

# --- Constants ---
# Map algebraic notation to grid indices
# Grid: [rank][file] where rank 0 is '8' (top), rank 7 is '1' (bottom).
FILES = {c: i for i, c in enumerate("abcdefgh")}
RANKS = {c: 7 - i for i, c in enumerate("12345678")}  # '1' -> 7, '8' -> 0

# Inverse map for output
FILES_INV = {i: c for i, c in enumerate("abcdefgh")}
RANKS_INV = {i: c for i, c in enumerate("87654321")}  # 0 -> '8', 7 -> '1'

# Piece Values (Material)
PIECE_VALS = {
    'P': 10, 'N': 30, 'B': 30, 'R': 50, 'Q': 90, 'K': 900,
}

# Simplified Piece-Square Tables (Encourage center control, development)
# Values are added to White, subtracted for Black.
PST = {
    'P': [
        [0,  0,  0,  0,  0,  0,  0,  0],
        [5,  5,  5,  5,  5,  5,  5,  5],
        [1,  1,  2,  3,  3,  2,  1,  1],
        [0.5, 0.5, 1, 2.5, 2.5, 1, 0.5, 0.5],
        [0,  0,  0,  2,  2,  0,  0,  0],
        [0.5, -0.5, -1, 0, 0, -1, -0.5, 0.5],
        [0.5, 1, 1, -2, -2, 1, 1, 0.5],
        [0,  0,  0,  0,  0,  0,  0,  0]
    ],
    'N': [
        [-5, -4, -3, -3, -3, -3, -4, -5],
        [-4, -2,  0,  0,  0,  0, -2, -4],
        [-3,  0,  1,  1.5, 1.5, 1,  0, -3],
        [-3,  0.5, 1.5, 2, 2, 1.5, 0.5, -3],
        [-3,  0,  1.5, 2, 2, 1.5, 0, -3],
        [-3,  0.5, 1, 1.5, 1.5, 1, 0.5, -3],
        [-4, -2,  0,  0.5, 0.5, 0, -2, -4],
        [-5, -4, -3, -3, -3, -3, -4, -5]
    ],
    'B': [
        [-2, -1, -1, -1, -1, -1, -1, -2],
        [-1,  0,  0,  0,  0,  0,  0, -1],
        [-1,  0,  0.5, 1, 1, 0.5,  0, -1],
        [-1,  0.5, 0.5, 1, 1, 0.5, 0.5, -1],
        [-1,  0,  1, 1, 1, 1, 0, -1],
        [-1,  1, 1, 1, 1, 1, 1, -1],
        [-1,  0.5, 0, 0, 0, 0, 0.5, -1],
        [-2, -1, -1, -1, -1, -1, -1, -2]
    ],
    'R': [
        [0,  0,  0,  0,  0,  0,  0,  0],
        [0.5, 1, 1, 1, 1, 1, 1, 0.5],
        [-0.5, 0,  0,  0,  0,  0,  0, -0.5],
        [-0.5, 0,  0,  0,  0,  0,  0, -0.5],
        [-0.5, 0,  0,  0,  0,  0,  0, -0.5],
        [-0.5, 0,  0,  0,  0,  0,  0, -0.5],
        [-0.5, 0,  0,  0,  0,  0,  0, -0.5],
        [0,  0,  0,  0.5, 0.5, 0,  0,  0]
    ],
    'Q': [
        [-2, -1, -1, -0.5, -0.5, -1, -1, -2],
        [-1,  0,  0,  0,  0,  0,  0, -1],
        [-1,  0,  0.5, 0.5, 0.5, 0.5,  0, -1],
        [-0.5, 0,  0.5, 0.5, 0.5, 0.5, 0, -0.5],
        [0,  0,  0.5, 0.5, 0.5, 0.5, 0, -0.5],
        [-1,  0.5, 0.5, 0.5, 0.5, 0.5, 0, -1],
        [-1,  0,  0.5, 0,  0,  0,  0, -1],
        [-2, -1, -1, -0.5, -0.5, -1, -1, -2]
    ],
    'K': [
        [-3, -4, -4, -5, -5, -4, -4, -3],
        [-3, -4, -4, -5, -5, -4, -4, -3],
        [-3, -4, -4, -5, -5, -4, -4, -3],
        [-3, -4, -4, -5, -5, -4, -4, -3],
        [-2, -3, -3, -4, -4, -3, -3, -2],
        [-1, -2, -2, -2, -2, -2, -2, -1],
        [2,  2,  0,  0,  0,  0,  2,  2],
        [2,  3,  1,  0,  0,  1,  3,  2]
    ]
}

# --- Helper Functions ---

def to_board(pieces):
    board = [[None for _ in range(8)] for _ in range(8)]
    for sq, p in pieces.items():
        f = FILES[sq[0]]
        r = RANKS[sq[1]]
        board[r][f] = p
    return board

def to_uci(r1, f1, r2, f2, promo=None):
    s = FILES_INV[f1] + RANKS_INV[r1] + FILES_INV[f2] + RANKS_INV[r2]
    if promo:
        s += promo
    return s

def on_board(r, c):
    return 0 <= r < 8 and 0 <= c < 8

def get_color(p):
    return p[0] if p else None

def get_type(p):
    return p[1] if p else None

# --- Core Engine ---

def find_king(board, color):
    for r in range(8):
        for c in range(8):
            if board[r][c] == color + 'K':
                return (r, c)
    return None

def is_attacked(board, r, c, attacker_color):
    # Pawn attacks
    p_dir = -1 if attacker_color == 'w' else 1
    # White pawns are at higher rank index (7) attacking "up" (lower index)
    # Actually standard: White moves 7->0. Attacks 7->6.
    # My grid: 0 is 8, 7 is 1.
    # White pawn at r=7 attacks r=6.
    
    pawns_dirs = []
    if attacker_color == 'w':
        pawns_dirs = [(-1, -1), (-1, 1)]
    else:
        pawns_dirs = [(1, -1), (1, 1)]
        
    for dr, dc in pawns_dirs:
        nr, nc = r + dr, c + dc
        if on_board(nr, nc):
            if board[nr][nc] == attacker_color + 'P':
                return True

    # Knight
    knight_dirs = [(-2,-1), (-2,1), (-1,-2), (-1,2), (1,-2), (1,2), (2,-1), (2,1)]
    for dr, dc in knight_dirs:
        nr, nc = r + dr, c + dc
        if on_board(nr, nc) and board[nr][nc] == attacker_color + 'N':
            return True
            
    # King (for adjacent kings)
    king_dirs = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
    for dr, dc in king_dirs:
        nr, nc = r + dr, c + dc
        if on_board(nr, nc) and board[nr][nc] == attacker_color + 'K':
            return True
            
    # Sliding (R, B, Q)
    dirs = [(-1,-1), (-1,1), (1,-1), (1,1), (-1,0), (1,0), (0,-1), (0,1)]
    for dr, dc in dirs:
        nr, nc = r + dr, c + dc
        while on_board(nr, nc):
            p = board[nr][nc]
            if p:
                if get_color(p) == attacker_color:
                    pt = get_type(p)
                    is_diag = (dr != 0 and dc != 0)
                    if pt == 'Q': return True
                    if is_diag and pt == 'B': return True
                    if not is_diag and pt == 'R': return True
                break
            nr += dr
            nc += dc
    return False

def get_moves(board, color):
    moves = []
    # Find King for Castling
    k_pos = None
    for r in range(8):
        for c in range(8):
            if board[r][c] == color + 'K':
                k_pos = (r, c)
                break

    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if not p or get_color(p) != color:
                continue
            
            pt = get_type(p)
            
            if pt == 'P':
                fwd = -1 if color == 'w' else 1
                start_row = 6 if color == 'w' else 1
                
                # Move 1
                nr, nc = r + fwd, c
                if on_board(nr, nc) and board[nr][nc] is None:
                    if (color == 'w' and nr == 0) or (color == 'b' and nr == 7):
                        moves.append(to_uci(r, c, nr, nc, 'q')) # Always promote Queen
                    else:
                        moves.append(to_uci(r, c, nr, nc))
                        # Move 2
                        if r == start_row and on_board(r + 2*fwd, c) and board[r + 2*fwd][c] is None:
                            moves.append(to_uci(r, c, r + 2*fwd, c))
                
                # Captures
                for dc in [-1, 1]:
                    nr, nc = r + fwd, c + dc
                    if on_board(nr, nc):
                        tgt = board[nr][nc]
                        if tgt and get_color(tgt) != color:
                            if (color == 'w' and nr == 0) or (color == 'b' and nr == 7):
                                moves.append(to_uci(r, c, nr, nc, 'q'))
                            else:
                                moves.append(to_uci(r, c, nr, nc))
                                
            elif pt == 'N':
                for dr, dc in [(-2,-1), (-2,1), (-1,-2), (-1,2), (1,-2), (1,2), (2,-1), (2,1)]:
                    nr, nc = r + dr, c + dc
                    if on_board(nr, nc):
                        tgt = board[nr][nc]
                        if tgt is None or get_color(tgt) != color:
                            moves.append(to_uci(r, c, nr, nc))
                            
            elif pt == 'B':
                for dr, dc in [(-1,-1), (-1,1), (1,-1), (1,1)]:
                    nr, nc = r + dr, c + dc
                    while on_board(nr, nc):
                        tgt = board[nr][nc]
                        if tgt is None:
                            moves.append(to_uci(r, c, nr, nc))
                        else:
                            if get_color(tgt) != color:
                                moves.append(to_uci(r, c, nr, nc))
                            break
                        nr += dr
                        nc += dc
                        
            elif pt == 'R':
                for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                    nr, nc = r + dr, c + dc
                    while on_board(nr, nc):
                        tgt = board[nr][nc]
                        if tgt is None:
                            moves.append(to_uci(r, c, nr, nc))
                        else:
                            if get_color(tgt) != color:
                                moves.append(to_uci(r, c, nr, nc))
                            break
                        nr += dr
                        nc += dc
                        
            elif pt == 'Q':
                for dr, dc in [(-1,-1), (-1,1), (1,-1), (1,1), (-1,0), (1,0), (0,-1), (0,1)]:
                    nr, nc = r + dr, c + dc
                    while on_board(nr, nc):
                        tgt = board[nr][nc]
                        if tgt is None:
                            moves.append(to_uci(r, c, nr, nc))
                        else:
                            if get_color(tgt) != color:
                                moves.append(to_uci(r, c, nr, nc))
                            break
                        nr += dr
                        nc += dc

            elif pt == 'K':
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0: continue
                        nr, nc = r + dr, c + dc
                        if on_board(nr, nc):
                            tgt = board[nr][nc]
                            if tgt is None or get_color(tgt) != color:
                                moves.append(to_uci(r, c, nr, nc))
                
                # Castling (Simplified)
                if k_pos == (r, c):
                    # Kingside
                    if board[r][c+1] is None and board[r][c+2] is None:
                        if board[r][c+3] == color + 'R':
                            moves.append(to_uci(r, c, r, c+2))
                    # Queenside
                    if board[r][c-1] is None and board[r][c-2] is None and board[r][c-3] is None:
                        if board[r][c-4] == color + 'R':
                            moves.append(to_uci(r, c, r, c-2))
    return moves

def get_legal_moves(board, color):
    pseudo = get_moves(board, color)
    legal = []
    k_pos = find_king(board, color)
    
    for move in pseudo:
        f1 = FILES[move[0]]
        r1 = RANKS[move[1]]
        f2 = FILES[move[2]]
        r2 = RANKS[move[3]]
        
        saved_tgt = board[r2][f2]
        saved_src = board[r1][f1]
        board[r2][f2] = saved_src
        board[r1][f1] = None
        
        is_castle = False
        if saved_src[1] == 'K' and abs(f2 - f1) > 1:
            is_castle = True
            # Move Rook
            if f2 > f1: # Kingside
                board[r1][f2-1] = board[r1][7]
                board[r1][7] = None
            else:
                board[r1][f2+1] = board[r1][0]
                board[r1][0] = None
        
        # Check validity
        opp = 'b' if color == 'w' else 'w'
        valid = not is_attacked(board, k_pos[0], k_pos[1], opp)
        
        # Castling specific checks (path squares)
        if valid and is_castle:
            # Check start square (implicit by k_pos check above? No, King moved in sim)
            # We need to check the path in the current state
            # Re-sim path checks on original board logic is cleaner, but here we just check
            # the squares the king passed.
            if is_attacked(board, r1, f1, opp): valid = False
            if valid:
                step = 1 if f2 > f1 else -1
                for cf in range(f1 + step, f2, step):
                    if is_attacked(board, r1, cf, opp):
                        valid = False
                        break
        
        if valid:
            legal.append(move)
            
        # Undo
        board[r1][f1] = saved_src
        board[r2][f2] = saved_tgt
        if is_castle:
            if f2 > f1:
                board[r1][7] = board[r1][f2-1]
                board[r1][f2-1] = None
            else:
                board[r1][0] = board[r1][f2+1]
                board[r1][f2+1] = None
                
    return legal

def evaluate(board):
    score = 0
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if not p: continue
            color = get_color(p)
            pt = get_type(p)
            
            val = PIECE_VALS[pt]
            
            # PST
            pst_row = 7 - r if color == 'b' else r
            pst_val = PST[pt][pst_row][c]
            
            if color == 'w':
                score += (val + pst_val)
            else:
                score -= (val + pst_val)
    return score

def minimax(board, depth, alpha, beta, is_maximizing, color):
    if depth == 0:
        return evaluate(board)
    
    legal_moves = get_legal_moves(board, color)
    if not legal_moves:
        k_pos = find_king(board, color)
        if is_attacked(board, k_pos[0], k_pos[1], 'b' if color == 'w' else 'w'):
            return -10000 if is_maximizing else 10000
        return 0 # Stalemate
    
    if is_maximizing:
        max_eval = -float('inf')
        for move in legal_moves:
            f1 = FILES[move[0]]
            r1 = RANKS[move[1]]
            f2 = FILES[move[2]]
            r2 = RANKS[move[3]]
            
            saved_tgt = board[r2][f2]
            saved_src = board[r1][f1]
            board[r2][f2] = saved_src
            board[r1][f1] = None
            
            is_castle = False
            if saved_src[1] == 'K' and abs(f2 - f1) > 1:
                is_castle = True
                if f2 > f1: board[r1][5] = board[r1][7]; board[r1][7] = None
                else: board[r1][3] = board[r1][0]; board[r1][0] = None
            
            eval_val = minimax(board, depth-1, alpha, beta, False, 'b')
            
            board[r1][f1] = saved_src
            board[r2][f2] = saved_tgt
            if is_castle:
                if f2 > f1: board[r1][7] = board[r1][5]; board[r1][5] = None
                else: board[r1][0] = board[r1][3]; board[r1][3] = None
                
            max_eval = max(max_eval, eval_val)
            alpha = max(alpha, eval_val)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for move in legal_moves:
            f1 = FILES[move[0]]
            r1 = RANKS[move[1]]
            f2 = FILES[move[2]]
            r2 = RANKS[move[3]]
            
            saved_tgt = board[r2][f2]
            saved_src = board[r1][f1]
            board[r2][f2] = saved_src
            board[r1][f1] = None
            
            is_castle = False
            if saved_src[1] == 'K' and abs(f2 - f1) > 1:
                is_castle = True
                if f2 > f1: board[r1][5] = board[r1][7]; board[r1][7] = None
                else: board[r1][3] = board[r1][0]; board[r1][0] = None
            
            eval_val = minimax(board, depth-1, alpha, beta, True, 'w')
            
            board[r1][f1] = saved_src
            board[r2][f2] = saved_tgt
            if is_castle:
                if f2 > f1: board[r1][7] = board[r1][5]; board[r1][5] = None
                else: board[r1][0] = board[r1][3]; board[r1][3] = None
                
            min_eval = min(min_eval, eval_val)
            beta = min(beta, eval_val)
            if beta <= alpha:
                break
        return min_eval

def policy(pieces: dict[str, str], to_play: str) -> str:
    board = to_board(pieces)
    color = 'w' if to_play == 'white' else 'b'
    
    legal_moves = get_legal_moves(board, color)
    
    if not legal_moves:
        # Game over, return a dummy move to satisfy API signature constraints
        return "a1a1"
        
    best_move = None
    best_val = -float('inf')
    depth = 3 # Fixed depth for 1s limit
    
    # Sort moves to improve pruning (captures first)
    legal_moves.sort(key=lambda m: 1 if board[RANKS[m[3]]][FILES[m[2]]] else 0, reverse=True)
    
    for move in legal_moves:
        f1 = FILES[move[0]]
        r1 = RANKS[move[1]]
        f2 = FILES[move[2]]
        r2 = RANKS[move[3]]
        
        saved_tgt = board[r2][f2]
        saved_src = board[r1][f1]
        board[r2][f2] = saved_src
        board[r1][f1] = None
        
        is_castle = False
        if saved_src[1] == 'K' and abs(f2 - f1) > 1:
            is_castle = True
            if f2 > f1: board[r1][5] = board[r1][7]; board[r1][7] = None
            else: board[r1][3] = board[r1][0]; board[r1][0] = None
        
        val = minimax(board, depth - 1, -float('inf'), float('inf'), False, 'b' if color == 'w' else 'w')
        
        board[r1][f1] = saved_src
        board[r2][f2] = saved_tgt
        if is_castle:
            if f2 > f1: board[r1][7] = board[r1][5]; board[r1][5] = None
            else: board[r1][0] = board[r1][3]; board[r1][3] = None
            
        if val > best_val:
            best_val = val
            best_move = move
            
    return best_move if best_move else legal_moves[0]

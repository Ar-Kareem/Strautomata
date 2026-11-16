
import copy

# Piece Values
PIECE_VALUES = {
    'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000
}

# Piece Square Tables (PST) for positional play
# Indexed by [row][col] where row 0 is Rank 8 and col 0 is File A
PST_PAWN = [
    [0,  0,  0,  0,  0,  0,  0,  0],
    [50, 50, 50, 50, 50, 50, 50, 50],
    [10, 10, 20, 30, 30, 20, 10, 10],
    [5,  5, 10, 25, 25, 10,  5,  5],
    [0,  0,  0, 20, 20,  0,  0,  0],
    [5, -5,-10,  0,  0,-10, -5,  5],
    [5, 10, 10,-20,-20, 10, 10,  5],
    [0,  0,  0,  0,  0,  0,  0,  0]
]

PST_KNIGHT = [
    [-50,-40,-30,-30,-30,-30,-40,-50],
    [-40,-20,  0,  0,  0,  0,-20,-40],
    [-30,  0, 10, 15, 15, 10,  0,-30],
    [-30,  5, 15, 20, 20, 15,  5,-30],
    [-30,  0, 15, 20, 20, 15,  0,-30],
    [-30,  5, 10, 15, 15, 10,  5,-30],
    [-40,-20,  0,  5,  5,  0,-20,-40],
    [-50,-40,-30,-30,-30,-30,-40,-50]
]

PST_BISHOP = [
    [-20,-10,-10,-10,-10,-10,-10,-20],
    [-10,  0,  0,  0,  0,  0,  0,-10],
    [-10,  0,  5, 10, 10,  5,  0,-10],
    [-10,  5,  5, 10, 10,  5,  5,-10],
    [-10,  0, 10, 10, 10, 10,  0,-10],
    [-10, 10, 10, 10, 10, 10, 10,-10],
    [-10,  5,  0,  0,  0,  0,  5,-10],
    [-20,-10,-10,-10,-10,-10,-10,-20]
]

PST_ROOK = [
    [0,  0,  0,  0,  0,  0,  0,  0],
    [5, 10, 10, 10, 10, 10, 10,  5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [0,  0,  0,  5,  5,  0,  0,  0]
]

PST_QUEEN = [
    [-20,-10,-10, -5, -5,-10,-10,-20],
    [-10,  0,  0,  0,  0,  0,  0,-10],
    [-10,  0,  5,  5,  5,  5,  0,-10],
    [-5,  0,  5,  5,  5,  5,  0, -5],
    [0,  0,  5,  5,  5,  5,  0, -5],
    [-10,  5,  5,  5,  5,  5,  0,-10],
    [-10,  0,  5,  0,  0,  0,  0,-10],
    [-20,-10,-10, -5, -5,-10,-10,-20]
]

PST_KING_MID = [
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-20,-30,-30,-40,-40,-30,-30,-20],
    [-10,-20,-20,-20,-20,-20,-20,-10],
    [20, 20,  0,  0,  0,  0, 20, 20],
    [20, 30, 10,  0,  0, 10, 30, 20]
]

PIECE_PSTS = {
    'P': PST_PAWN, 'N': PST_KNIGHT, 'B': PST_BISHOP,
    'R': PST_ROOK, 'Q': PST_QUEEN, 'K': PST_KING_MID
}

def sq_to_idx(sq):
    return 8 - int(sq[1]), ord(sq[0]) - ord('a')

def get_pst_value(piece_code, sq):
    color = piece_code[0]
    ptype = piece_code[1]
    table = PIECE_PSTS[ptype]
    r, c = sq_to_idx(sq)
    val = table[r][c]
    return val if color == 'w' else -val

def is_attacked(board, sq, attacker_color):
    for from_sq, p in board.items():
        if p[0] != attacker_color: continue
        if can_attack(p, from_sq, sq, board):
            return True
    return False

def can_attack(piece, from_sq, to_sq, board):
    # Simplified attack logic (geometry only, path check for sliders)
    ptype = piece[1]
    fr, fc = sq_to_idx(from_sq)
    tr, tc = sq_to_idx(to_sq)
    dr, dc = tr - fr, tc - fc
    
    if ptype == 'P':
        direction = -1 if piece[0] == 'w' else 1
        return (dr == direction and abs(dc) == 1)
    
    if ptype == 'N':
        return (abs(dr) * abs(dc) == 2)
        
    if ptype == 'K':
        return max(abs(dr), abs(dc)) == 1
        
    step_r = 0 if dr == 0 else (1 if dr > 0 else -1)
    step_c = 0 if dc == 0 else (1 if dc > 0 else -1)
    
    if ptype == 'R':
        if dr != 0 and dc != 0: return False
    elif ptype == 'B':
        if abs(dr) != abs(dc): return False
    elif ptype == 'Q':
        if (dr != 0 and dc != 0) and (abs(dr) != abs(dc)): return False
        
    curr_r, curr_c = fr + step_r, fc + step_c
    while (curr_r, curr_c) != (tr, tc):
        if (8 - curr_r, chr(curr_c + ord('a'))) in board:
            return False
        curr_r += step_r
        curr_c += step_c
        
    return True

def apply_move(board, move, color):
    new_board = board.copy()
    
    if move == 'O-O':
        if color == 'w':
            new_board['g1'] = 'wK'; new_board['f1'] = 'wR'
            del new_board['e1']; del new_board['h1']
        else:
            new_board['g8'] = 'bK'; new_board['f8'] = 'bR'
            del new_board['e8']; del new_board['h8']
        return new_board, 0, PIECE_VALUES['K'], 'g1' if color=='w' else 'g8'

    if move == 'O-O-O':
        if color == 'w':
            new_board['c1'] = 'wK'; new_board['d1'] = 'wR'
            del new_board['e1']; del new_board['a1']
        else:
            new_board['c8'] = 'bK'; new_board['d8'] = 'bR'
            del new_board['e8']; del new_board['a8']
        return new_board, 0, PIECE_VALUES['K'], 'c1' if color=='w' else 'c8'

    clean_move = move.replace('+', '').replace('#', '')
    promotion = None
    if '=' in clean_move:
        clean_move, promo_piece = clean_move.split('=')
        promotion = color + promo_piece
        
    is_capture = 'x' in clean_move
    if is_capture:
        clean_move = clean_move.replace('x', '')
        
    dest = clean_move[-2:]
    
    if clean_move[0].isupper():
        ptype = clean_move[0]
        disamb = clean_move[1:-2]
    else:
        ptype = 'P'
        disamb = clean_move[:-2]
        
    src_candidates = []
    for sq, p in board.items():
        if p == color + ptype:
            if len(disamb) > 0:
                if disamb[0].isalpha():
                    if sq[0] != disamb[0]: continue
                if disamb[-1].isdigit():
                    if sq[1] != disamb[-1]: continue
            
            # Use can_move logic for pseudo-legal move generation
            if can_reach(board, p, sq, dest, is_capture):
                src_candidates.append(sq)
                
    if not src_candidates:
        # Fallback: try to find by ignoring capture status if ambiguous (e.g. moving to empty square that was technically a capture target in logic)
        # This handles cases where my simple parser fails, but legal_moves is correct
        for sq, p in board.items():
            if p == color + ptype:
                if len(disamb) > 0:
                    if disamb[0].isalpha() and sq[0] != disamb[0]: continue
                    if disamb[-1].isdigit() and sq[1] != disamb[-1]: continue
                if can_reach(board, p, sq, dest, False): src_candidates.append(sq)
                if can_reach(board, p, sq, dest, True): src_candidates.append(sq)
                
    src = src_candidates[0] if src_candidates else None
    if not src: 
        raise ValueError(f"Could not find source for move {move}")

    moved_piece = board[src]
    captured_piece = board.get(dest, None)
    captured_val = 0
    if captured_piece:
        captured_val = PIECE_VALUES[captured_piece[1]]
        del new_board[dest]
    
    if ptype == 'P' and is_capture and not captured_piece:
        # En Passant
        ep_sq = dest[0] + src[1]
        if ep_sq in board:
            captured_val = PIECE_VALUES['P']
            del new_board[ep_sq]
            
    del new_board[src]
    
    final_piece = promotion if promotion else moved_piece
    new_board[dest] = final_piece
    moved_val = PIECE_VALUES[final_piece[1]]
        
    return new_board, captured_val, moved_val, dest

def can_reach(board, piece, from_sq, to_sq, is_capture):
    # Check if a piece can move from from_sq to to_sq
    ptype = piece[1]
    color = piece[0]
    fr, fc = sq_to_idx(from_sq)
    tr, tc = sq_to_idx(to_sq)
    dr, dc = tr - fr, tc - fc
    
    if ptype == 'P':
        direction = -1 if color == 'w' else 1
        # Push
        if dc == 0 and dr == direction and to_sq not in board: return True
        if dc == 0 and dr == direction * 2 and fr in (6 if color=='w' else 1) and to_sq not in board:
            # Check path
            mid_sq = (8 - (fr - direction), chr(fc + ord('a')))
            if mid_sq not in board: return True
        # Capture
        if abs(dc) == 1 and dr == direction:
            if is_capture: return True # Standard capture
            # Check En Passant-like logic for reachability (dest empty but valid capture square)
            if not is_capture and to_sq not in board: return False
            return True
        return False

    # Reuse attack logic for other pieces (Knights, King, Sliders)
    if can_attack(piece, from_sq, to_sq, board):
        # For non-pawns, can_attack covers geometry and path.
        # We don't check 'is_capture' validation here strictly, assuming legal_moves handles it.
        return True
        
    return False

def evaluate(board, color):
    score = 0
    for sq, p in board.items():
        val = PIECE_VALUES[p[1]] + get_pst_value(p, sq)
        if p[0] == color:
            score += val
        else:
            score -= val
    return score

def policy(pieces, to_play, legal_moves):
    my_color = 'w' if to_play == 'white' else 'b'
    opp_color = 'b' if my_color == 'w' else 'w'
    
    best_move = legal_moves[0]
    best_score = -float('inf')
    
    for move in legal_moves:
        try:
            new_board, captured_val, moved_val, dest_sq = apply_move(pieces, move, my_color)
            score = evaluate(new_board, my_color)
            
            # Blunder detection: if moved piece is hanging
            if is_attacked(new_board, dest_sq, opp_color):
                if not is_attacked(new_board, dest_sq, my_color):
                    if moved_val > captured_val:
                        score -= moved_val # Bad trade / blunder
                    elif moved_val == captured_val:
                        score -= moved_val * 0.1 # Unnecessary risk
            
            if '#' in move: score += 100000
            elif '+' in move: score += 50
            
            if score > best_score:
                best_score = score
                best_move = move
        except Exception:
            continue
            
    return best_move

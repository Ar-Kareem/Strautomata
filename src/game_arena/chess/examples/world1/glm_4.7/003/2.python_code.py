
import random
import math

# --- Constants and Weights ---
PIECE_VALUES = {
    'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000
}

# Simplified Piece-Square Tables (PST) for positional evaluation.
# Values are from perspective of White. Black's perspective is mirrored (rank 7-r).
PST = {
    'P': [
        [0,  0,  0,  0,  0,  0,  0,  0],
        [50, 50, 50, 50, 50, 50, 50, 50],
        [10, 10, 20, 30, 30, 20, 10, 10],
        [5,  5, 10, 25, 25, 10,  5,  5],
        [0,  0,  0, 20, 20,  0,  0,  0],
        [5, -5,-10,  0,  0,-10, -5,  5],
        [5, 10, 10,-20,-20, 10, 10,  5],
        [0,  0,  0,  0,  0,  0,  0,  0]
    ],
    'N': [
        [-50,-40,-30,-30,-30,-30,-40,-50],
        [-40,-20,  0,  0,  0,  0,-20,-40],
        [-30,  0, 10, 15, 15, 10,  0,-30],
        [-30,  5, 15, 20, 20, 15,  5,-30],
        [-30,  0, 15, 20, 20, 15,  0,-30],
        [-30,  5, 10, 15, 15, 10,  5,-30],
        [-40,-20,  0,  5,  5,  0,-20,-40],
        [-50,-40,-30,-30,-30,-30,-40,-50]
    ],
    'B': [
        [-20,-10,-10,-10,-10,-10,-10,-20],
        [-10,  0,  0,  0,  0,  0,  0,-10],
        [-10,  0,  5, 10, 10,  5,  0,-10],
        [-10,  5,  5, 10, 10,  5,  5,-10],
        [-10,  0, 10, 10, 10, 10,  0,-10],
        [-10, 10, 10, 10, 10, 10, 10,-10],
        [-10,  5,  0,  0,  0,  0,  5,-10],
        [-20,-10,-10,-10,-10,-10,-10,-20]
    ],
    'R': [
        [0,  0,  0,  0,  0,  0,  0,  0],
        [5, 10, 10, 10, 10, 10, 10,  5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [-5,  0,  0,  0,  0,  0,  0, -5],
        [0,  0,  0,  5,  5,  0,  0,  0]
    ],
    'Q': [
        [-20,-10,-10, -5, -5,-10,-10,-20],
        [-10,  0,  0,  0,  0,  0,  0,-10],
        [-10,  0,  5,  5,  5,  5,  0,-10],
        [-5,  0,  5,  5,  5,  5,  0, -5],
        [0,  0,  5,  5,  5,  5,  0, -5],
        [-10,  5,  5,  5,  5,  5,  0,-10],
        [-10,  0,  5,  0,  0,  0,  0,-10],
        [-20,-10,-10, -5, -5,-10,-10,-20]
    ],
    'K': [
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-20,-30,-30,-40,-40,-30,-30,-20],
        [-10,-20,-20,-20,-20,-20,-20,-10],
        [20, 20,  0,  0,  0,  0, 20, 20],
        [20, 30, 10,  0,  0, 10, 30, 20]
    ]
}

def sq_to_idx(sq):
    return ord(sq[0]) - ord('a'), int(sq[1]) - 1

def idx_to_sq(c, r):
    return chr(ord('a') + c) + str(r + 1)

def evaluate_board(board_pieces, to_play_color):
    score = 0
    for sq, p_code in board_pieces.items():
        p_type = p_code[1]
        color = p_code[0]
        c, r = sq_to_idx(sq)
        
        val = PIECE_VALUES[p_type]
        pos_val = 0
        
        # Handle PST mirroring for Black
        if color == 'w':
            pos_val = PST[p_type][r][c]
        else:
            pos_val = PST[p_type][7-r][c]
            
        piece_score = val + pos_val
        
        if color == to_play_color:
            score += piece_score
        else:
            score -= piece_score
    return score

def is_attacked(sq_idx, attacker_color, board_pieces):
    sx, sy = sq_idx
    # Check all opponent pieces
    for sq, p_code in board_pieces.items():
        if p_code[0] != attacker_color:
            continue
            
        p_type = p_code[1]
        ox, oy = sq_to_idx(sq)
        dx, dy = sx - ox, sy - oy
        adx, ady = abs(dx), abs(dy)
        
        if p_type == 'P':
            # Pawn attacks (diagonally)
            direction = -1 if attacker_color == 'w' else 1
            if dy == direction and adx == 1:
                return True
        elif p_type == 'N':
            if (adx == 1 and ady == 2) or (adx == 2 and ady == 1):
                return True
        elif p_type == 'K':
            if adx <= 1 and ady <= 1:
                return True
        elif p_type == 'R':
            if dx == 0 or dy == 0:
                if not is_blocked(ox, oy, sx, sy, board_pieces):
                    return True
        elif p_type == 'B':
            if adx == ady:
                if not is_blocked(ox, oy, sx, sy, board_pieces):
                    return True
        elif p_type == 'Q':
            if (dx == 0 or dy == 0) or (adx == ady):
                if not is_blocked(ox, oy, sx, sy, board_pieces):
                    return True
    return False

def is_blocked(x1, y1, x2, y2, board_pieces):
    dx = 0 if x1 == x2 else (1 if x2 > x1 else -1)
    dy = 0 if y1 == y2 else (1 if y2 > y1 else -1)
    
    cx, cy = x1 + dx, y1 + dy
    while (cx, cy) != (x2, y2):
        if idx_to_sq(cx, cy) in board_pieces:
            return True
        cx += dx
        cy += dy
    return False

def find_source(board, move, color):
    # Parse move string to find source square
    # 1. Check Castling
    if move == 'O-O':
        if color == 'w': return 'e1'
        else: return 'e8'
    if move == 'O-O-O':
        if color == 'w': return 'e1'
        else: return 'e8'
        
    # 2. Parse structure
    # Piece, disambiguation, capture flag, dest, promotion
    m_clean = move.replace('+', '').replace('#', '')
    promo_piece = None
    if '=' in m_clean:
        m_clean, promo_piece = m_clean.split('=')
    
    target = m_clean[-2:]
    prefix = m_clean[:-2]
    
    is_capture = 'x' in prefix
    if is_capture:
        prefix = prefix.replace('x', '')
        
    piece_type = 'P'
    if prefix and prefix[0] in 'KQRBN':
        piece_type = prefix[0]
        disamb = prefix[1:]
    else:
        disamb = prefix # For pawns, e.g. 'e' in 'exd5'
        
    # 3. Find candidates
    candidates = []
    for sq, p in board.items():
        if p == color + piece_type:
            candidates.append(sq)
            
    # 4. Filter by disambiguation
    filtered = []
    for sq in candidates:
        if disamb:
            if len(disamb) == 1:
                if disamb.isdigit(): # Rank disambiguation (e.g. R1a3)
                    if sq[1] != disamb: continue
                else: # File disambiguation (e.g. Nec3)
                    if sq[0] != disamb: continue
            else: # Full square disambiguation (rare)
                if sq != disamb: continue
        filtered.append(sq)
        
    # 5. Filter by geometry
    tx, ty = sq_to_idx(target)
    for sq in filtered:
        ox, oy = sq_to_idx(sq)
        dx, dy = tx - ox, ty - oy
        adx, ady = abs(dx), abs(dy)
        
        valid = False
        if piece_type == 'P':
            if is_capture:
                if adx == 1 and ((color=='w' and dy==1) or (color=='b' and dy==-1)):
                    valid = True
            else:
                if dx == 0:
                    if (color=='w' and dy==1) or (color=='b' and dy==-1): valid = True
                    if (color=='w' and dy==2 and oy==1) or (color=='b' and dy==-2 and oy==6): valid = True
        elif piece_type == 'N':
            if (adx==1 and ady==2) or (adx==2 and ady==1): valid = True
        elif piece_type == 'B':
            if adx == ady: valid = True
        elif piece_type == 'R':
            if dx==0 or dy==0: valid = True
        elif piece_type == 'Q':
            if (adx==ady) or (dx==0 or dy==0): valid = True
        elif piece_type == 'K':
            if adx<=1 and ady<=1: valid = True
            
        if valid:
            return sq
            
    return None # Should not happen with legal moves

def simulate_move(board, move, color):
    new_board = board.copy()
    
    if move == 'O-O':
        if color == 'w':
            del new_board['e1']; del new_board['h1']
            new_board['g1'] = 'wK'; new_board['f1'] = 'wR'
        else:
            del new_board['e8']; del new_board['h8']
            new_board['g8'] = 'bK'; new_board['f8'] = 'bR'
        return new_board
        
    if move == 'O-O-O':
        if color == 'w':
            del new_board['e1']; del new_board['a1']
            new_board['c1'] = 'wK'; new_board['d1'] = 'wR'
        else:
            del new_board['e8']; del new_board['a8']
            new_board['c8'] = 'bK'; new_board['d8'] = 'bR'
        return new_board

    source = find_source(board, move, color)
    piece = board[source]
    p_type = piece[1]
    
    # Parse target and promotion
    m_clean = move.replace('+', '').replace('#', '').split('=')[0]
    target = m_clean[-2:]
    is_capture = 'x' in move
    
    # Remove from source
    del new_board[source]
    
    # Handle En Passant (Pawn capture where target is empty)
    if p_type == 'P' and is_capture and target not in board:
        # Capturing pawn is on file of target, rank of source
        tx, ty = sq_to_idx(target)
        sx, sy = sq_to_idx(source)
        capture_sq = idx_to_sq(tx, sy)
        del new_board[capture_sq]
    
    # Place piece
    promo = None
    if '=' in move:
        promo = move.split('=')[1]
        
    new_board[target] = color + (promo if promo else p_type)
    
    return new_board

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    color = 'w' if to_play == 'white' else 'b'
    opp_color = 'b' if to_play == 'white' else 'w'
    
    best_move = None
    best_score = -float('inf')
    
    # Prioritize Checkmate (detected by '#' in move string)
    # If a move guarantees mate, take it immediately (simplified heuristic)
    for move in legal_moves:
        if '#' in move:
            return move
            
    for move in legal_moves:
        # 1. Simulate
        next_board = simulate_move(pieces, move, color)
        
        # 2. Evaluate Base Score (Material + Position)
        score = evaluate_board(next_board, color)
        
        # 3. Safety Check (Tactical)
        # Identify the destination square of the move we just made
        target_sq = None
        m_clean = move.replace('+', '').replace('#', '').split('=')[0]
        if move in ['O-O', 'O-O-O']:
            target_sq = 'g1' if color == 'w' and move == 'O-O' else \
                        'c1' if color == 'w' and move == 'O-O-O' else \
                        'g8' if color == 'b' and move == 'O-O' else 'c8'
        else:
            target_sq = m_clean[-2:]
            
        # Get the piece we moved
        moved_piece = next_board[target_sq]
        moved_val = PIECE_VALUES[moved_piece[1]]
        
        # Check if this piece is now attacked by opponent
        if is_attacked(sq_to_idx(target_sq), opp_color, next_board):
            # Penalty: Losing the piece is bad. 
            # We assign a penalty proportional to value to discourage hanging pieces.
            # A simple penalty is (Value of piece) / 2.
            # If attacked by a pawn or minor piece, very dangerous. 
            # By checking "is attacked", we just assume it can be taken next turn.
            score -= (moved_val * 0.5) 
        
        # Small random factor to break ties and vary play
        score += random.uniform(0, 1)
        
        if score > best_score:
            best_score = score
            best_move = move
            
    return best_move

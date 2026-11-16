
import re
import copy

# --- Constants and Tables ---

# Piece values for evaluation
PIECE_VALUES = {
    'P': 100, 'N': 320, 'B': 330, 
    'R': 500, 'Q': 900, 'K': 20000
}

# Simplified Piece Square Tables (PST) for positional evaluation
# Indexed by rank (0-7) and file (0-7). 0,0 is a8.
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

OFFSETS = {
    'N': [(-2,-1), (-2,1), (-1,-2), (-1,2), (1,-2), (1,2), (2,-1), (2,1)],
    'K': [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)],
    'B_DIRS': [(-1,-1), (-1,1), (1,-1), (1,1)],
    'R_DIRS': [(-1,0), (1,0), (0,-1), (0,1)],
    'Q_DIRS': [(-1,-1), (-1,1), (1,-1), (1,1), (-1,0), (1,0), (0,-1), (0,1)]
}

# --- Helper Functions ---

def parse_sq(s):
    """Converts algebraic notation (e.g., 'e4') to 0-indexed tuple (row, col)."""
    return 8 - int(s[1]), ord(s[0]) - 97

def to_sq(r, c):
    """Converts (row, col) to algebraic notation."""
    return chr(c + 97) + str(8 - r)

def get_attackers(r, c, color, board):
    """Returns a list of (value, row, col) for pieces of 'color' attacking (r,c)."""
    attackers = []
    for (pr, pc), (p_color, p_type) in board.items():
        if p_color != color:
            continue
        
        # Logic for each piece type to see if it attacks (r,c)
        if p_type == 'P':
            dr = r - pr
            dc = c - pc
            # White pawns attack up (-1), Black pawns attack down (+1)
            if color == 'w':
                if dr == -1 and abs(dc) == 1:
                    attackers.append((PIECE_VALUES['P'], pr, pc))
            else:
                if dr == 1 and abs(dc) == 1:
                    attackers.append((PIECE_VALUES['P'], pr, pc))
                    
        elif p_type == 'N':
            if (r - pr, c - pc) in OFFSETS['N']:
                attackers.append((PIECE_VALUES['N'], pr, pc))
                
        elif p_type in ['B', 'R', 'Q']:
            directions = []
            if p_type in ['B', 'Q']: directions.extend(OFFSETS['B_DIRS'])
            if p_type in ['R', 'Q']: directions.extend(OFFSETS['R_DIRS'])
            
            for dr, dc in directions:
                tr, tc = pr + dr, pc + dc
                while 0 <= tr < 8 and 0 <= tc < 8:
                    if tr == r and tc == c:
                        attackers.append((PIECE_VALUES[p_type], pr, pc))
                        break
                    if (tr, tc) in board:
                        break
                    tr += dr
                    tc += dc
                    
        elif p_type == 'K':
            if (r - pr, c - pc) in OFFSETS['K']:
                attackers.append((PIECE_VALUES['K'], pr, pc))
                
    return attackers

# --- Main Policy ---

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    # 1. Setup Board State
    # board: dict[(r,c)] = (color, type)
    board = {}
    for sq, code in pieces.items():
        r, c = parse_sq(sq)
        board[(r, c)] = (code[0], code[1])

    my_color = 'w' if to_play == 'white' else 'b'
    opp_color = 'b' if my_color == 'w' else 'w'

    # 2. Check for immediate Checkmate (in move string)
    for move in legal_moves:
        if '#' in move:
            return move, memory

    # 3. Evaluate Legal Moves
    best_move = legal_moves[0]
    best_score = -float('inf')

    # Sort captures first to prune or find good moves early
    legal_moves.sort(key=lambda m: 1 if 'x' in m else 0, reverse=True)

    for move_str in legal_moves:
        # --- Parse Move String ---
        # Castling
        if move_str == 'O-O':
            src, dest = ('e1', 'g1') if my_color == 'w' else ('e8', 'g8')
            r_src, r_dest = ('h1', 'f1') if my_color == 'w' else ('h8', 'f8')
            p_type = 'K'
            is_castle = True
            promo = None
        elif move_str == 'O-O-O':
            src, dest = ('e1', 'c1') if my_color == 'w' else ('e8', 'c8')
            r_src, r_dest = ('a1', 'd1') if my_color == 'w' else ('a8', 'd8')
            p_type = 'K'
            is_castle = True
            promo = None
        else:
            # Regex: (Piece)(File)(Rank)(x)(Dest)(=Promo)
            m = re.match(r"^([KQRBN])?([a-h])?([1-8])?(x)?([a-h][1-8])(=([KQRBN]))?$", move_str)
            if not m: continue # Should not happen
            
            p_char = m.group(1)
            p_type = p_char if p_char else 'P'
            dest = m.group(5)
            promo = m.group(7)
            is_castle = False
            
            # Determine source square
            dest_r, dest_c = parse_sq(dest)
            file_char = m.group(2)
            rank_char = m.group(3)
            
            # Find piece matching move
            src = None
            for sq, (col, typ) in board.items():
                if col != my_color or typ != p_type: continue
                if file_char and sq[0] != file_char: continue
                if rank_char and sq[1] != rank_char: continue
                
                # Geometric validation
                sr, sc = parse_sq(sq)
                valid = False
                if p_type == 'P':
                    dr, dc = dest_r - sr, dest_c - sc
                    is_capture = 'x' in move_str
                    if is_capture:
                        if abs(dc) == 1 and ((my_color == 'w' and dr == -1) or (my_color == 'b' and dr == 1)):
                            valid = True
                    else:
                        if dc == 0 and ((my_color == 'w' and dr == -1) or (my_color == 'b' and dr == 1)):
                            valid = True
                        if dc == 0 and ((my_color == 'w' and dr == -2) or (my_color == 'b' and dr == 2)):
                            # Check if path clear for double pawn
                            mid_r = sr + (-1 if my_color == 'w' else 1)
                            if (mid_r, sc) not in board:
                                valid = True
                elif p_type == 'N':
                    if (dest_r - sr, dest_c - sc) in OFFSETS['N']: valid = True
                elif p_type == 'K':
                    if (dest_r - sr, dest_c - sc) in OFFSETS['K']: valid = True
                elif p_type in ['B', 'R', 'Q']:
                    dr, dc = dest_r - sr, dest_c - sc
                    if (dr == 0 or dc == 0 or abs(dr) == abs(dc)):
                        # Check obstruction
                        step_r = 0 if dr == 0 else (1 if dr > 0 else -1)
                        step_c = 0 if dc == 0 else (1 if dc > 0 else -1)
                        tr, tc = sr + step_r, sc + step_c
                        blocked = False
                        while (tr, tc) != (dest_r, dest_c):
                            if (tr, tc) in board:
                                blocked = True
                                break
                            tr += step_r
                            tc += step_c
                        if not blocked: valid = True
                
                if valid:
                    src = sq
                    break
        
        if not src: continue # Failed to parse source
        src_r, src_c = parse_sq(src)
        dest_r, dest_c = parse_sq(dest)
        
        # --- Simulate Move ---
        sim_board = copy.deepcopy(board)
        
        # Handle capture
        captured = sim_board.pop((dest_r, dest_c), None)
        
        # Move piece
        piece_color, piece_type = sim_board.pop((src_r, src_c))
        if promo:
            piece_type = promo
        sim_board[(dest_r, dest_c)] = (piece_color, piece_type)
        
        # Handle Castling Rook
        if is_castle:
            rr, rc = parse_sq(r_src)
            rd, cd = parse_sq(r_dest)
            sim_board.pop((rr, rc))
            sim_board[(rd, cd)] = (piece_color, 'R')
            
        # Handle En Passant (pawn captured not on dest square)
        if 'x' in move_str and not captured and piece_type == 'P':
            cap_r = dest_r + (1 if my_color == 'w' else -1)
            sim_board.pop((cap_r, dest_c), None)
            
        # --- Evaluate Position ---
        score = 0
        
        # 1. Material Gain
        if captured:
            score += PIECE_VALUES[captured[1]] * 10
            
        # 2. Positional Score (PST)
        # Mirror rank for black
        r_idx = dest_r if my_color == 'w' else 7 - dest_r
        old_r_idx = src_r if my_color == 'w' else 7 - src_r
        
        score += PST[piece_type][r_idx * 8 + dest_c]
        score -= PST[p_type if not promo else piece_type][old_r_idx * 8 + src_c]
        
        # 3. Safety: Am I hanging?
        opp_attackers = get_attackers(dest_r, dest_c, opp_color, sim_board)
        my_defenders = get_attackers(dest_r, dest_c, my_color, sim_board)
        
        my_val = PIECE_VALUES[piece_type]
        
        if opp_attackers:
            min_opp_val = min(v for v, _, _ in opp_attackers)
            
            # If undefended, definitely bad
            if not my_defenders:
                score -= my_val * 1.5
            # If attacked by smaller piece, might lose material
            elif min_opp_val < my_val:
                # Crude SEE approximation
                score -= (my_val - min_opp_val)
            else:
                score -= 5 # Slight penalty for being under fire
        
        # 4. Check Bonus (Is opponent king attacked?)
        opp_king_sq = None
        for sq, (col, typ) in sim_board.items():
            if col == opp_color and typ == 'K':
                opp_king_sq = sq
                break
        
        if opp_king_sq:
            kr, kc = parse_sq(opp_king_sq)
            if get_attackers(kr, kc, my_color, sim_board):
                score += 50 # Check is good
        
        # 5. Random jitter to vary play
        score += 0.1
        
        if score > best_score:
            best_score = score
            best_move = move_str

    return best_move, memory

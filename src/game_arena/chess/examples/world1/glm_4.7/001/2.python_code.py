
import random
import math

# --- Constants & Configuration ---
# Piece values for evaluation
PIECE_VALUES = {
    'P': 100,
    'N': 320,
    'B': 330,
    'R': 500,
    'Q': 900,
    'K': 20000
}

# Piece-Square Tables (PST) for positional evaluation.
# Values represent desirability of a square for the piece.
# Tables are from White's perspective. Black's perspective is mirrored.
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

# --- Helper Functions ---

def square_to_index(sq):
    """Converts algebraic notation (e.g., 'e4') to (row, col) indices."""
    file = sq[0]
    rank = sq[1]
    col = ord(file) - ord('a')
    row = 8 - int(rank)
    return row, col

def index_to_square(row, col):
    """Converts (row, col) indices to algebraic notation."""
    return chr(col + ord('a')) + str(8 - row)

def get_position_value(piece, sq, color):
    """Returns the Piece-Square Table value for a piece on a square."""
    if piece not in PST:
        return 0
    row, col = square_to_index(sq)
    
    # Mirror for black
    if color == 'b':
        row = 7 - row
        
    return PST[piece][row][col]

def is_attacked(sq, attacker_color, pieces):
    """
    Checks if a square is attacked by any piece of the attacker_color.
    Note: This is a simplified check based on the current board state.
    It checks rays and jumps.
    """
    row, col = square_to_index(sq)
    
    # Helper to check bounds
    def on_board(r, c):
        return 0 <= r < 8 and 0 <= c < 8

    # 1. Pawn Attacks
    # White attacks (r-1, c-1), (r-1, c+1)
    # Black attacks (r+1, c-1), (r+1, c+1)
    pawn_dirs = [(-1, -1), (-1, 1)] if attacker_color == 'w' else [(1, -1), (1, 1)]
    for dr, dc in pawn_dirs:
        pr, pc = row + dr, col + dc
        if on_board(pr, pc):
            target_sq = index_to_square(pr, pc)
            target_p = pieces.get(target_sq)
            if target_p and target_p == attacker_color + 'P':
                return True

    # 2. Knight Attacks
    knight_offsets = [
        (-2, -1), (-2, 1), (-1, -2), (-1, 2),
        (1, -2), (1, 2), (2, -1), (2, 1)
    ]
    for dr, dc in knight_offsets:
        kr, kc = row + dr, col + dc
        if on_board(kr, kc):
            target_sq = index_to_square(kr, kc)
            target_p = pieces.get(target_sq)
            if target_p and target_p == attacker_color + 'N':
                return True

    # 3. King Attacks (for adjacency)
    king_offsets = [
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)
    ]
    for dr, dc in king_offsets:
        kr, kc = row + dr, col + dc
        if on_board(kr, kc):
            target_sq = index_to_square(kr, kc)
            target_p = pieces.get(target_sq)
            if target_p and target_p == attacker_color + 'K':
                return True

    # 4. Sliding Pieces (Rook, Bishop, Queen)
    # Orthogonal (Rook, Queen)
    ortho_dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    for dr, dc in ortho_dirs:
        r, c = row + dr, col + dc
        while on_board(r, c):
            target_sq = index_to_square(r, c)
            target_p = pieces.get(target_sq)
            if target_p:
                if target_p[0] == attacker_color:
                    if target_p[1] in ['R', 'Q']:
                        return True
                    # If blocked by own piece, stop
                break 
            r += dr
            c += dc

    # Diagonal (Bishop, Queen)
    diag_dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    for dr, dc in diag_dirs:
        r, c = row + dr, col + dc
        while on_board(r, c):
            target_sq = index_to_square(r, c)
            target_p = pieces.get(target_sq)
            if target_p:
                if target_p[0] == attacker_color:
                    if target_p[1] in ['B', 'Q']:
                        return True
                break
            r += dr
            c += dc

    return False

# --- Main Policy ---

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    """
    Selects the best move based on heuristics.
    """
    my_color = 'w' if to_play == 'white' else 'b'
    opp_color = 'b' if my_color == 'w' else 'w'
    
    best_move = legal_moves[0]
    best_score = -float('inf')
    
    # Small random noise to break ties and add variety
    random.seed() 

    for move in legal_moves:
        score = 0.0
        
        # --- Parse Move ---
        # Remove check/mate symbols for parsing
        clean_move = move.replace('+', '').replace('#', '')
        
        # 1. Determine Piece Type and Destination
        # Examples: "Nf3", "exd5", "O-O", "e8=Q", "Raxb1"
        piece_type = 'P' # Default pawn
        dest_sq = ''
        
        if clean_move == 'O-O':
            piece_type = 'K'
            dest_sq = 'g1' if my_color == 'w' else 'g8'
            score += 50 # Castling bonus
        elif clean_move == 'O-O-O':
            piece_type = 'K'
            dest_sq = 'c1' if my_color == 'w' else 'c8'
            score += 50 # Castling bonus
        else:
            # Promotions: "e8=Q" -> split by '='
            if '=' in clean_move:
                base, promo = clean_move.split('=')
                piece_type = promo # Evaluate as the promoted piece
                # But the capturing logic needs to know it's a pawn arriving
                moving_p_base = base[-1]
                if moving_p_base in ['K', 'Q', 'R', 'B', 'N']:
                    # Logic for non-pawn promotion (impossible in standard chess but handle generically)
                    pass 
                # Destination is the part before =
                dest_sq = base[-2:]
                
                # Promotion Bonus: Value difference
                # Note: The move string implies a pawn moved there.
                score += PIECE_VALUES[promo] - PIECE_VALUES['P']
            else:
                # Normal moves
                # The last two chars are the destination (unless it's just a file like 'e4'? No, standard is rank+file)
                # Handle 'Nbd7' vs 'Nf3'
                # If first char is K, Q, R, B, N, it's that piece. Else Pawn.
                if clean_move[0] in ['K', 'Q', 'R', 'B', 'N']:
                    piece_type = clean_move[0]
                else:
                    piece_type = 'P'
                
                # Handle disambiguation e.g. "Rad1". Dest is "d1". "a" is file.
                # Dest is always last 2 chars if not castle/promotion.
                dest_sq = clean_move[-2:]

        # --- Evaluation ---

        # 2. Capture Bonus
        # Check if 'x' is in the original move string
        is_capture = 'x' in move
        
        if is_capture:
            # Check what is currently on the destination square
            # Note: For En Passant, the destination square is empty in `pieces`
            captured_piece_code = pieces.get(dest_sq)
            
            if captured_piece_code:
                # Standard capture
                victim_type = captured_piece_code[1]
                score += PIECE_VALUES[victim_type]
            else:
                # Likely En Passant (Pawn capture on empty square)
                # En Passant captures a pawn
                score += PIECE_VALUES['P']

        # 3. Positional Bonus (PST)
        # Evaluate the value of placing `piece_type` on `dest_sq`
        if dest_sq:
            score += get_position_value(piece_type, dest_sq, my_color)

        # 4. Check Bonus
        if '+' in move or '#' in move:
            score += 20 # Giving check is generally good
        
        if '#' in move:
            score += 10000 # Mate is highest priority

        # 5. Safety / Blunder Prevention
        # If the destination square is attacked by the opponent, penalize the move.
        # Penalty approximates the value of the piece we are moving there.
        # We don't know exactly which piece moved (e.g. Nbd7 vs Nfd7), but we know the type.
        # Also, if we captured, we already gained that material.
        
        if is_sq_attacked(dest_sq, opp_color, pieces):
            # The piece moving here is under fire.
            # If it's a trade (we captured X, they take Y), we need X > Y to be good.
            # If we didn't capture, we are just losing material.
            
            # Approximate value of the piece we moved
            # If promotion, value is already high.
            val_moved = PIECE_VALUES[piece_type]
            
            # Risk penalty.
            # If we captured, we might have taken the defender.
            # But safe heuristic: assume we lose the piece if it's attacked.
            score -= (val_moved * 0.9)
            
            # Exception: If we are capturing a higher value piece, it might be worth it.
            # The score accumulation handles:
            # score = (VictimVal) - (MyVal * 0.9) + PST.
            # If VictimVal > MyVal * 0.9, it's positive.

        # Add tiny random jitter for variety
        score += random.random()

        # Update Best
        if score > best_score:
            best_score = score
            best_move = move

    return best_move

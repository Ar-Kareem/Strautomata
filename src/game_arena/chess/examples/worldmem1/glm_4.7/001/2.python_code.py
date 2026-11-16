
import random

# --- Piece-Square Tables ---
# These tables encourage piece development and center control.
# Values are in centipawns (approx). Tables are from white's perspective.
# For black, we mirror the table (rank 1 <-> 8).

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

PIECE_VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}

def get_piece_pos_value(piece, square, is_white):
    """
    Returns the positional value from PST for a given piece and square.
    """
    p_type = piece[1]
    # Convert square 'a1' to (0,0) indices. 'a' is file 0, '1' is rank 0.
    file_idx = ord(square[0]) - ord('a')
    rank_idx = int(square[1]) - 1
    
    if not is_white:
        # Mirror the rank index for black
        rank_idx = 7 - rank_idx
        
    table = None
    if p_type == 'P': table = PST_PAWN
    elif p_type == 'N': table = PST_KNIGHT
    elif p_type == 'B': table = PST_BISHOP
    elif p_type == 'R': table = PST_ROOK
    elif p_type == 'Q': table = PST_QUEEN
    elif p_type == 'K': table = PST_KING_MID
    
    if table:
        return table[rank_idx][file_idx]
    return 0

def evaluate_board(pieces: dict, color_to_play: str) -> int:
    """
    Evaluates the board state. Positive is good for the color_to_play.
    """
    score = 0
    is_white = (color_to_play == 'white')
    
    for sq, p_code in pieces.items():
        p_color = p_code[0]
        p_type = p_code[1]
        
        # Material value
        val = PIECE_VALUES.get(p_type, 0)
        
        # Positional value
        val += get_piece_pos_value(p_code, sq, p_color == 'white')
        
        if (p_color == 'w' and is_white) or (p_color == 'b' and not is_white):
            score += val
        else:
            score -= val
            
    return score

def find_move_origin(move_str: str, pieces: dict, color: str) -> str:
    """
    Parses the SAN move string to find the origin square.
    """
    # Handle Castling
    if move_str == "O-O" or move_str == "O-O+":
        rank = "1" if color == 'white' else "8"
        return "e1" if color == 'white' else "e8" # King is always on e-file here
    if move_str == "O-O-O" or move_str == "O-O-O+":
        rank = "1" if color == 'white' else "8"
        return "e1" if color == 'white' else "e8"

    # Parse destination square (last 2 chars before =, +, #)
    # Simplified regex logic
    clean_move = move_str.replace('+', '').replace('#', '')
    if '=' in clean_move:
        clean_move = clean_move.split('=')[0]
    
    dest_sq = clean_move[-2:]
    
    # Determine Piece Type
    pt = 'P'
    if clean_move[0].isupper():
        pt = clean_move[0]
    
    # Collect candidates
    candidates = []
    my_color_code = 'w' if color == 'white' else 'b'
    
    for sq, p in pieces.items():
        if p[0] == my_color_code and p[1] == pt:
            candidates.append(sq)
            
    # Filter candidates based on geometry and SAN disambiguation
    
    # 1. Disambiguation (File or Rank)
    disambig_file = None
    disambig_rank = None
    
    # Extract file/rank from the middle of the string
    # e.g. "Rad1" -> file 'a'. "R1a3" -> rank '1'. "Rba3" -> file 'b', dest 'a3'? No, usually file.
    
    # Strip piece type and dest to see what's left
    temp = clean_move[1:] if len(clean_move) > 2 else "" # 'e4' -> "", 'Nf3' -> 'f3', 'Rac1' -> 'ac1'
    # Remove dest from temp
    if dest_sq in temp:
        temp = temp.replace(dest_sq, "")
    
    # If temp is not empty, it contains disambiguation
    if temp:
        if 'x' in temp:
            temp = temp.replace('x', '')
        if temp:
            if temp[0].isalpha():
                disambig_file = temp[0]
            if temp[0].isdigit():
                disambig_rank = temp[0]
            # Handle long notation like "a1a2" - though usually not standard SAN, just in case
            if len(temp) == 2:
                disambig_file = temp[0]
                disambig_rank = temp[1]
                
    # Filter by disambiguation
    if disambig_file:
        candidates = [c for c in candidates if c[0] == disambig_file]
    if disambig_rank:
        candidates = [c for c in candidates if c[1] == disambig_rank]
        
    # 2. Geometry Filter
    valid_candidates = []
    
    dx = ord(dest_sq[0]) - ord('a')
    dy = int(dest_sq[1]) - 1
    
    is_capture = 'x' in clean_move
    
    for c in candidates:
        cx = ord(c[0]) - ord('a')
        cy = int(c[1]) - 1
        
        diff_x = dx - cx
        diff_y = dy - cy
        
        valid_move = False
        
        if pt == 'N':
            if (abs(diff_x) == 2 and abs(diff_y) == 1) or (abs(diff_x) == 1 and abs(diff_y) == 2):
                valid_move = True
                
        elif pt == 'K':
            if abs(diff_x) <= 1 and abs(diff_y) <= 1:
                valid_move = True
                
        elif pt == 'P':
            direction = -1 if my_color_code == 'w' else 1
            # Pawn capture
            if is_capture:
                if abs(diff_x) == 1 and diff_y == direction:
                    valid_move = True
            else:
                # Pawn push
                if diff_x == 0:
                    if diff_y == direction:
                        valid_move = True
                    elif (diff_y == 2 * direction) and ((my_color_code == 'w' and cy == 6) or (my_color_code == 'b' and cy == 1)):
                        # Double push check (simplified: assume path clear for finding origin, logic is robust enough with candidates)
                        valid_move = True
                        
        else: # Sliding pieces (B, R, Q)
            # Check alignment
            if pt == 'B' or pt == 'Q':
                if abs(diff_x) == abs(diff_y) and diff_x != 0:
                    # Diagonal
                    valid_move = True
            if pt == 'R' or pt == 'Q':
                if (diff_x == 0) != (diff_y == 0): # XOR
                    # Orthogonal
                    valid_move = True
            
            if valid_move:
                # Check path clear
                if pt == 'B' or pt == 'R' or pt == 'Q':
                    step_x = 0 if diff_x == 0 else (1 if diff_x > 0 else -1)
                    step_y = 0 if diff_y == 0 else (1 if diff_y > 0 else -1)
                    
                    curr_x, curr_y = cx + step_x, cy + step_y
                    blocked = False
                    while (curr_x, curr_y) != (dx, dy):
                        if f"{chr(curr_x+97)}{curr_y+1}" in pieces:
                            blocked = True
                            break
                        curr_x += step_x
                        curr_y += step_y
                    
                    if blocked:
                        valid_move = False

        if valid_move:
            valid_candidates.append(c)
            
    # Should be exactly 1
    return valid_candidates[0] if valid_candidates else None

def simulate_move(pieces: dict, move_str: str, color: str) -> dict:
    """
    Returns a new pieces dictionary representing the state after the move.
    """
    new_pieces = pieces.copy()
    my_color = 'w' if color == 'white' else 'b'
    
    # 1. Identify origin and destination
    if move_str in ["O-O", "O-O+", "O-O-O", "O-O-O+"]:
        king_src = "e1" if color == 'white' else "e8"
        king_piece = new_pieces.pop(king_src)
        
        if move_str in ["O-O", "O-O+"]: # King side
            dest = "g1" if color == 'white' else "g8"
            rook_src = "h1" if color == 'white' else "h8"
            rook_dest = "f1" if color == 'white' else "f8"
        else: # Queen side
            dest = "c1" if color == 'white' else "c8"
            rook_src = "a1" if color == 'white' else "a8"
            rook_dest = "d1" if color == 'white' else "d8"
            
        new_pieces[dest] = king_piece
        rook_p = new_pieces.pop(rook_src)
        new_pieces[rook_dest] = rook_p
        return new_pieces

    # Normal move
    src = find_move_origin(move_str, pieces, color)
    
    # Parse dest
    clean_move = move_str.replace('+', '').replace('#', '')
    if '=' in clean_move:
        dest = clean_move.split('=')[0][-2:]
        promotion_char = clean_move.split('=')[1][0]
    else:
        dest = clean_move[-2:]
        promotion_char = None

    # Handle Capture
    if dest in new_pieces:
        del new_pieces[dest]
        
    # Handle En Passant (special capture case where dest is empty)
    # 'exd5' logic: pawn moves to d5, removes pawn on d6 (if white) or d4 (if black)
    # Since 'dest' in pieces is false for en passant, we detect by piece type and move pattern
    moving_p = new_pieces[src]
    if moving_p[1] == 'P' and 'x' in move_str and dest not in pieces:
        # En passant capture
        # Remove the pawn being captured
        direction = -1 if color == 'white' else 1
        captured_sq = f"{dest[0]}{int(dest[1]) - direction}"
        if captured_sq in new_pieces:
            del new_pieces[captured_sq]

    # Move piece
    p_code = new_pieces.pop(src)
    
    # Handle Promotion
    if promotion_char:
        p_code = my_color + promotion_char
        
    new_pieces[dest] = p_code
    
    return new_pieces

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    # Initialize random seed based on memory or time to vary play
    if 'seed' not in memory:
        memory['seed'] = random.randint(0, 1000000)
    random.seed(memory['seed'] + len(legal_moves) + sum(ord(c) for c in to_play))

    best_move = None
    best_score = -float('inf')
    
    # 1. Check for immediate mate
    for move in legal_moves:
        if '#' in move:
            return move, memory
            
    # 2. Evaluate moves
    # Shuffle moves to randomize equal scores
    temp_moves = legal_moves[:]
    random.shuffle(temp_moves)
    
    for move in temp_moves:
        # Prioritize checks
        check_bonus = 50 if '+' in move else 0
        
        # Create next board state
        next_board = simulate_move(pieces, move, to_play)
        
        # Evaluate
        # Note: evaluate_board returns score relative to the side to play.
        # Here, to_play is the current player making the move.
        # After the move, it is the opponent's turn.
        # We want the score from the perspective of the CURRENT player (to_play).
        
        # evaluate_board returns (MyScore - OpponentScore). 
        # If we pass 'to_play' to evaluate_board on 'next_board', 
        # it will calculate (NextState_Opponent_Mat - NextState_My_Mat).
        # So we should negate the result to get the perspective of the current player.
        
        score_from_next_pov = evaluate_board(next_board, to_play)
        current_player_score = -score_from_next_pov
        
        current_player_score += check_bonus
        
        if current_player_score > best_score:
            best_score = current_player_score
            best_move = move
            
    # Fallback: Should not happen if legal_moves is non-empty
    if best_move is None and legal_moves:
        best_move = legal_moves[0]
        
    return best_move, memory


import random
import copy

# Piece Values for evaluation
PIECE_VALUES = {
    'P': 10, 'N': 30, 'B': 30, 'R': 50, 'Q': 90, 'K': 900
}

# Center squares for positional bonus
CENTER_SQUARES = ['c3', 'c4', 'c5', 'c6', 'd3', 'd4', 'd5', 'd6', 
                  'e3', 'e4', 'e5', 'e6', 'f3', 'f4', 'f5', 'f6']

def get_coords(square):
    """Convert algebraic square (e.g., 'e4') to 0-indexed (row, col)."""
    return 8 - int(square[1]), ord(square[0]) - ord('a')

def get_square(row, col):
    """Convert 0-indexed (row, col) to algebraic square."""
    return chr(ord('a') + col) + str(8 - row)

def is_attacked(board, row, col, attacker_color):
    """
    Check if the square (row, col) is attacked by any piece of attacker_color.
    board is 8x8 list of strings or None.
    """
    # Check Pawn attacks
    pawn_dir = -1 if attacker_color == 'w' else 1
    start_row = row - pawn_dir
    if 0 <= start_row < 8:
        for dc in [-1, 1]:
            c = col + dc
            if 0 <= c < 8:
                p = board[start_row][c]
                if p and p[0] == attacker_color and p[1] == 'P':
                    return True

    # Check Knight attacks
    knight_moves = [(r, c) for r in [-2, -1, 1, 2] for c in [-2, -1, 1, 2] if abs(r) != abs(c)]
    for dr, dc in knight_moves:
        r, c = row + dr, col + dc
        if 0 <= r < 8 and 0 <= c < 8:
            p = board[r][c]
            if p and p[0] == attacker_color and p[1] == 'N':
                return True

    # Check King attacks (adjacent)
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            if dr == 0 and dc == 0: continue
            r, c = row + dr, col + dc
            if 0 <= r < 8 and 0 <= c < 8:
                p = board[r][c]
                if p and p[0] == attacker_color and p[1] == 'K':
                    return True

    # Check Sliding pieces (Rook/Queen - straight, Bishop/Queen - diagonal)
    directions = [
        ([('R', 'Q')], [(-1, 0), (1, 0), (0, -1), (0, 1)]),
        ([('B', 'Q')], [(-1, -1), (-1, 1), (1, -1), (1, 1)])
    ]
    
    for types, dirs in directions:
        for dr, dc in dirs:
            r, c = row + dr, col + dc
            while 0 <= r < 8 and 0 <= c < 8:
                p = board[r][c]
                if p:
                    if p[0] == attacker_color and p[1] in types[0]:
                        return True
                    break # Blocked
                r += dr
                c += dc
    return False

def simulate_move(board, move, my_color):
    """
    Executes a move on a copy of the board.
    Returns: new_board, captured_piece_value
    """
    new_board = [row[:] for row in board]
    move_str = move
    
    # Handle Castling
    if move_str == 'O-O':
        row = 0 if my_color == 'w' else 7
        # King e -> g
        new_board[row][4] = None
        new_board[row][6] = my_color + 'K'
        # Rook h -> f
        new_board[row][7] = None
        new_board[row][5] = my_color + 'R'
        return new_board, 0
    if move_str == 'O-O-O':
        row = 0 if my_color == 'w' else 7
        # King e -> c
        new_board[row][4] = None
        new_board[row][2] = my_color + 'K'
        # Rook a -> d
        new_board[row][0] = None
        new_board[row][3] = my_color + 'R'
        return new_board, 0

    # Parse Move String
    # Strip check/mate symbols
    clean_move = move_str.replace('+', '').replace('#', '')
    
    # Parse promotion
    promotion = None
    if '=' in clean_move:
        clean_move, promo_piece = clean_move.split('=')
        promotion = my_color + promo_piece

    # Parse capture
    is_capture = 'x' in clean_move
    clean_move = clean_move.replace('x', '')

    # Destination is always last 2 chars
    dest_sq_str = clean_move[-2:]
    tr, tc = get_coords(dest_sq_str)
    
    # Piece type
    piece_char = 'P'
    rest = clean_move[:-2]
    if rest and rest[0] in ['K', 'Q', 'R', 'B', 'N']:
        piece_char = rest[0]
        rest = rest[1:] # Remove piece type, leaving disambiguation (file/rank)

    target_piece = new_board[tr][tc]
    captured_val = 0
    if target_piece:
        captured_val = PIECE_VALUES.get(target_piece[1], 0)

    # Find Source
    # Find all pieces of my type
    candidates = []
    for r in range(8):
        for c in range(8):
            p = new_board[r][c]
            if p and p == my_color + piece_char:
                # Check disambiguation
                if rest:
                    if len(rest) == 1:
                        if rest.isdigit() and (8 - int(rest)) != r: continue
                        if rest.isalpha() and (ord(rest) - ord('a')) != c: continue
                    # Very rare full disambiguation 'a1', ignore for simplicity or assume standard SAN
                
                # Check pseudo-legal move geometry to confirm source
                dr, dc = tr - r, tc - c
                
                valid_geom = False
                if piece_char == 'N':
                    if (abs(dr), abs(dc)) in [(1, 2), (2, 1)]: valid_geom = True
                elif piece_char == 'K':
                    if max(abs(dr), abs(dc)) == 1: valid_geom = True
                elif piece_char == 'P':
                    direction = -1 if my_color == 'w' else 1
                    # Move forward 1
                    if dc == 0 and dr == direction and not is_capture: valid_geom = True
                    # Move forward 2
                    if dc == 0 and dr == 2 * direction and not is_capture and ((my_color=='w' and r==6) or (my_color=='b' and r==1)): valid_geom = True
                    # Capture
                    if abs(dc) == 1 and dr == direction and is_capture: valid_geom = True
                
                elif piece_char in ['R', 'B', 'Q']:
                    # Sliding check
                    step_r, step_c = 0, 0
                    if dr == 0: step_c = 1 if dc > 0 else -1
                    elif dc == 0: step_r = 1 if dr > 0 else -1
                    elif abs(dr) == abs(dc): 
                        step_r = 1 if dr > 0 else -1
                        step_c = 1 if dc > 0 else -1
                    
                    if step_r != 0 or step_c != 0:
                        # Check path clear
                        curr_r, curr_c = r + step_r, c + step_c
                        blocked = False
                        while curr_r != tr or curr_c != tc:
                            if new_board[curr_r][curr_c]:
                                blocked = True
                                break
                            curr_r += step_r
                            curr_c += step_c
                        if not blocked:
                            if piece_char == 'R' and (dr == 0 or dc == 0): valid_geom = True
                            elif piece_char == 'B' and (dr != 0 and dc != 0): valid_geom = True
                            elif piece_char == 'Q': valid_geom = True
                
                if valid_geom:
                    candidates.append((r, c))
    
    # If ambiguity remains (rare with legal_moves), pick first
    sr, sc = candidates[0] if candidates else (None, None)

    # Execute move on board
    if sr is not None:
        new_board[sr][sc] = None
        
        # Handle En Passant Capture
        if piece_char == 'P' and is_capture and not target_piece:
            # Captured pawn is behind dest
            ep_r = tr - (-1 if my_color == 'w' else 1)
            target_piece = new_board[ep_r][tc] # The pawn being captured
            captured_val = PIECE_VALUES.get('P', 0)
            new_board[ep_r][tc] = None
        
        new_board[tr][tc] = promotion if promotion else my_color + piece_char

    return new_board, captured_val

def evaluate(board, color):
    score = 0
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if p:
                p_type = p[1]
                val = PIECE_VALUES.get(p_type, 0)
                
                # Positional bonus
                sq = get_square(r, c)
                if sq in CENTER_SQUARES:
                    if p_type in ['N', 'B', 'P']:
                        val += 2
                    elif p_type == 'K':
                        val -= 2 # King in center is bad usually
                
                # Material
                if p[0] == color:
                    score += val
                else:
                    score -= val
    return score

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    # Convert dict to 8x8 board
    board = [[None for _ in range(8)] for _ in range(8)]
    for sq, p in pieces.items():
        r, c = get_coords(sq)
        board[r][c] = p
    
    my_color = 'w' if to_play == 'white' else 'b'
    opp_color = 'b' if to_play == 'white' else 'w'
    
    best_move = None
    best_score = -float('inf')
    
    # Shuffle moves for variety if scores are equal
    random.shuffle(legal_moves)
    
    # Sort moves: Promotions > Captures > Castles > Checks > Normal
    def sort_key(m):
        if '=' in m: return 1000 # Promotion
        if 'x' in m: return 500 # Capture
        if 'O' in m: return 100 # Castle
        if '+' in m or '#' in m: return 50 # Check
        return 0
    
    legal_moves.sort(key=sort_key, reverse=True)
    
    for move in legal_moves:
        new_board, captured_val = simulate_move(board, move, my_color)
        if new_board is None: continue # Should not happen with legal moves
        
        # Safety check for captures: is the moving piece now attacked?
        # and is it worth it?
        penalty = 0
        
        # Find where we moved to
        # Note: simulate_move already updated new_board, but we need coords
        # Re-parsing quickly or relying on move logic:
        # We need the destination square from move string again
        clean_m = move.replace('+', '').replace('#', '').replace('=', '').replace('x', '')
        if len(clean_m) >= 2:
            dest_sq = clean_m[-2:]
            tr, tc = get_coords(dest_sq)
            
            # Check if destination is under attack
            if is_attacked(new_board, tr, tc, opp_color):
                # If we captured something, but the piece we moved with is now hanging
                # and we didn't get enough value, penalize.
                # Identify the piece we moved
                moved_piece = new_board[tr][tc]
                moved_val = PIECE_VALUES.get(moved_piece[1], 0)
                
                if captured_val < moved_val:
                    # Bad trade: Gave pawn for queen, or queen for nothing
                    penalty = -50 - (moved_val - captured_val)
                elif captured_val == moved_val:
                    penalty = -10 # Slight preference not to trade even material immediately if under attack

        score = evaluate(new_board, my_color) + penalty
        
        if score > best_score:
            best_score = score
            best_move = move
            
            # Hard stop if we find a Queen capture that is safe
            if captured_val >= 90 and penalty >= 0:
                break

    if best_move is None and legal_moves:
        best_move = legal_moves[0]
        
    return (best_move, memory)

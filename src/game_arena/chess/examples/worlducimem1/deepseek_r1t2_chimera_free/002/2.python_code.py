
import copy

PIECE_VALUES = {'Q': 900, 'R': 500, 'B': 300, 'N': 300, 'P': 100, 'K': 0}

def square_to_coords(square):
    file = square[0]
    rank = int(square[1:])
    return (8 - rank, ord(file) - ord('a'))

def coords_to_square(row, col):
    return f"{chr(col + ord('a'))}{8 - row}"

def is_in_bounds(row, col):
    return 0 <= row < 8 and 0 <= col < 8

def make_board(pieces):
    board = [[None]*8 for _ in range(8)]
    for square, piece in pieces.items():
        row, col = square_to_coords(square)
        board[row][col] = piece
    return board

def get_king_position(board, color_code):
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece and piece[0] == color_code and piece[1] == 'K':
                return (r, c)
    return None

def is_square_attacked(board, row, col, attacker_color):
    # Knights
    for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
        nr, nc = row+dr, col+dc
        if is_in_bounds(nr, nc) and board[nr][nc] == f"{attacker_color}N":
            return True

    # Pawns
    pawn_dir = -1 if attacker_color == 'b' else 1
    for dc in (-1,1):
        nr, nc = row + pawn_dir, col + dc
        if is_in_bounds(nr, nc) and board[nr][nc] == f"{attacker_color}P":
            return True

    # Sliding pieces
    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]:
        nr, nc = row+dr, col+dc
        while is_in_bounds(nr, nc):
            piece = board[nr][nc]
            if piece:
                pcolor, ptype = piece[0], piece[1]
                if pcolor == attacker_color:
                    if (dr == 0 or dc == 0) and ptype in ['Q','R']:
                        return True
                    if (dr != 0 and dc != 0) and ptype in ['Q','B']:
                        return True
                break
            nr += dr
            nc += dc

    # King
    for dr in (-1,0,1):
        for dc in (-1,0,1):
            if dr == dc == 0: continue
            nr, nc = row+dr, col+dc
            if is_in_bounds(nr, nc) and board[nr][nc] == f"{attacker_color}K":
                return True

    return False

def generate_pawn_moves(board, row, col, color_code):
    moves = []
    direction = -1 if color_code == 'w' else 1
    start_row = 6 if color_code == 'w' else 1

    # Single move
    if is_in_bounds(row+direction, col) and not board[row+direction][col]:
        if (row+direction == 0 and color_code == 'w') or (row+direction == 7 and color_code == 'b'):
            for promo in ['q','r','b','n']:
                moves.append((row+direction, col, promo))
        else:
            moves.append((row+direction, col, None))
            # Double move
            if row == start_row and not board[row+2*direction][col]:
                moves.append((row+2*direction, col, None))

    # Captures
    for dc in (-1,1):
        nr, nc = row+direction, col+dc
        if is_in_bounds(nr, nc):
            target = board[nr][nc]
            promo_row = (nr == 0 and color_code == 'w') or (nr == 7 and color_code == 'b')
            if target and target[0] != color_code:
                if promo_row:
                    for promo in ['q','r','b','n']:
                        moves.append((nr, nc, promo))
                else:
                    moves.append((nr, nc, None))

    return moves

def generate_piece_moves(board, row, col):
    color_code = board[row][col][0]
    piece_type = board[row][col][1]
    moves = []

    if piece_type == 'P':
        return generate_pawn_moves(board, row, col, color_code)

    vectors = []
    if piece_type in ['N', 'K']:
        vectors = [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)] if piece_type == 'N' else [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
    elif piece_type == 'B':
        vectors = [(-1,-1),(-1,1),(1,-1),(1,1)]
    elif piece_type == 'R':
        vectors = [(-1,0),(1,0),(0,-1),(0,1)]
    elif piece_type == 'Q':
        vectors = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
    
    for dr, dc in vectors:
        nr, nc = row+dr, col+dc
        while is_in_bounds(nr, nc):
            target = board[nr][nc]
            if target and target[0] == color_code:
                break
            if piece_type in ['N','K']:
                moves.append((nr, nc, None))
                break
            moves.append((nr, nc, None))
            if target and target[0] != color_code:
                break
            nr += dr
            nc += dc
    
    return moves

def is_move_safe(board, move, color_code):
    temp_board = copy.deepcopy(board)
    (fr, fc), (tr, tc), promo = move
    piece = temp_board[fr][fc]
    captured = temp_board[tr][tc]
    
    # Execute move
    temp_board[fr][fc] = None
    temp_board[tr][tc] = f"{color_code}{promo[0].upper()}" if promo else piece
    
    king_pos = (tr, tc) if piece[1] == 'K' else get_king_position(temp_board, color_code)
    return not is_square_attacked(temp_board, king_pos[0], king_pos[1], 'b' if color_code == 'w' else 'w')

def get_legal_moves(board, to_play):
    color_code = 'w' if to_play == 'white' else 'b'
    legal_moves = []
    
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece and piece[0] == color_code:
                for move in generate_piece_moves(board, r, c):
                    tr, tc, promo = move
                    move_obj = ((r, c), (tr, tc), promo)
                    if is_move_safe(board, move_obj, color_code):
                        legal_moves.append(move_obj)
    return legal_moves

def evaluate_move(board, move):
    (fr, fc), (tr, tc), promo = move
    piece = board[fr][fc][1]
    captured = board[tr][tc]
    score = 0
    
    # Base material gain
    if captured:
        score += PIECE_VALUES.get(captured[1], 0)
    
    # Promotion bonus
    if promo:
        score += PIECE_VALUES[promo[0].upper()] - PIECE_VALUES['P']
    
    # Center control bonus for minor pieces
    center = {(3,3),(3,4),(4,3),(4,4)}
    if piece in ['N','B'] and (tr, tc) in center:
        score += 50
        
    # Check opponent king after move
    temp_board = copy.deepcopy(board)
    temp_board[fr][fc] = None
    temp_board[tr][tc] = f"{board[fr][fc][0]}{promo[0].upper()}" if promo else board[fr][fc]
    opp_color = 'b' if board[fr][fc][0] == 'w' else 'w'
    king_pos = get_king_position(temp_board, opp_color)
    if king_pos and is_square_attacked(temp_board, king_pos[0], king_pos[1], board[fr][fc][0]):
        score += 100  # Check bonus
    
    # Penalize moving kings near edges early
    if piece == 'K' and (tr in [0,7] or tc in [0,7]):
        score -= 30
        
    return score

def policy(pieces, to_play, memory):
    board = make_board(pieces)
    legal_moves = get_legal_moves(board, to_play)
    
    if not legal_moves:
        return "a1a1", memory  # Fallback if no moves found
    
    best_move = None
    best_score = -99999
    for move in legal_moves:
        score = evaluate_move(board, move)
        if score > best_score:
            best_score = score
            best_move = move
    
    (fr, fc), (tr, tc), promo = best_move
    move_str = coords_to_square(fr, fc).lower() + coords_to_square(tr, tc).lower()
    if promo:
        move_str += promo
    
    return (move_str[:4] if not promo else move_str, memory)

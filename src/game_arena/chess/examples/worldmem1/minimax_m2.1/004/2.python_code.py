
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    """
    Chess move selection policy using tactical and positional evaluation.
    """
    color_prefix = 'w' if to_play == 'white' else 'b'
    opponent_prefix = 'b' if to_play == 'white' else 'w'
    
    # Piece values for material evaluation
    piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
    
    # Build board mapping
    board = {}
    for square, piece in pieces.items():
        board[square] = piece
    
    # Parse square to coordinates
    file_idx = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
    rank_idx = {'1': 0, '2': 1, '3': 2, '4': 3, '5': 4, '6': 5, '7': 6, '8': 7}
    
    def parse_square(sq):
        return file_idx[sq[0]], rank_idx[sq[1]]
    
    def on_board(x, y):
        return 0 <= x < 8 and 0 <= y < 8
    
    def get_piece_at(x, y):
        if not on_board(x, y):
            return None
        for square, piece in board.items():
            fx, fy = parse_square(square)
            if fx == x and fy == y:
                return piece
        return None
    
    def is_opponent_piece(piece):
        return piece and piece[0] == opponent_prefix
    
    def is_own_piece(piece):
        return piece and piece[0] == color_prefix
    
    # Check if a square is attacked by opponent
    def is_attacked(x, y, by_color_prefix):
        opponent = by_color_prefix
        
        # Check knight attacks
        knight_moves = [(2,1), (2,-1), (-2,1), (-2,-1), (1,2), (1,-2), (-1,2), (-1,-2)]
        for dx, dy in knight_moves:
            nx, ny = x + dx, y + dy
            if on_board(nx, ny):
                piece = get_piece_at(nx, ny)
                if piece and piece[0] == opponent and piece[1] == 'N':
                    return True
        
        # Check pawn attacks (pawns attack diagonally forward)
        pawn_dir = 1 if opponent == 'w' else -1
        for dx in [-1, 1]:
            nx, ny = x + dx, y + pawn_dir
            if on_board(nx, ny):
                piece = get_piece_at(nx, ny)
                if piece and piece[0] == opponent and piece[1] == 'P':
                    return True
        
        # Check bishop/queen diagonal attacks
        for dx, dy in [(1,1), (1,-1), (-1,1), (-1,-1)]:
            nx, ny = x + dx, y + dy
            while on_board(nx, ny):
                piece = get_piece_at(nx, ny)
                if piece:
                    if piece[0] == opponent and piece[1] in ['B', 'Q']:
                        return True
                    break
                nx, ny = nx + dx, dy + dy
        
        # Check rook/queen straight attacks
        for dx, dy in [(1,0), (-1,0), (0,1), (0,-1)]:
            nx, ny = x + dx, y + dy
            while on_board(nx, ny):
                piece = get_piece_at(nx, ny)
                if piece:
                    if piece[0] == opponent and piece[1] in ['R', 'Q']:
                        return True
                    break
                nx, ny = nx + dx, dy + dy
        
        # Check king attacks
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if on_board(nx, ny):
                    piece = get_piece_at(nx, ny)
                    if piece and piece[0] == opponent and piece[1] == 'K':
                        return True
        
        return False
    
    # Count attacks on a square
    def count_attacks(x, y, by_color_prefix):
        count = 0
        opponent = by_color_prefix
        
        # Knight attacks
        knight_moves = [(2,1), (2,-1), (-2,1), (-2,-1), (1,2), (1,-2), (-1,2), (-1,-2)]
        for dx, dy in knight_moves:
            nx, ny = x + dx, y + dy
            if on_board(nx, ny):
                piece = get_piece_at(nx, ny)
                if piece and piece[0] == opponent and piece[1] == 'N':
                    count += 1
        
        # Pawn attacks
        pawn_dir = 1 if opponent == 'w' else -1
        for dx in [-1, 1]:
            nx, ny = x + dx, y + pawn_dir
            if on_board(nx, ny):
                piece = get_piece_at(nx, ny)
                if piece and piece[0] == opponent and piece[1] == 'P':
                    count += 1
        
        # Diagonal attacks (bishop/queen)
        for dx, dy in [(1,1), (1,-1), (-1,1), (-1,-1)]:
            nx, ny = x + dx, y + dy
            while on_board(nx, ny):
                piece = get_piece_at(nx, ny)
                if piece:
                    if piece[0] == opponent and piece[1] in ['B', 'Q']:
                        count += 1
                    break
                nx, ny = nx + dx, dy + dy
        
        # Straight attacks (rook/queen)
        for dx, dy in [(1,0), (-1,0), (0,1), (0,-1)]:
            nx, ny = x + dx, y + dy
            while on_board(nx, ny):
                piece = get_piece_at(nx, ny)
                if piece:
                    if piece[0] == opponent and piece[1] in ['R', 'Q']:
                        count += 1
                    break
                nx, ny = nx + dx, dy + dy
        
        return count
    
    # Find king position
    def find_king(color):
        prefix = 'w' if color == 'white' else 'b'
        for square, piece in board.items():
            if piece[0] == prefix and piece[1] == 'K':
                return parse_square(square)
        return None
    
    # Parse move to get source and destination
    def parse_move_notation(move, board, color_prefix):
        # Handle castling
        if move.startswith('O-O'):
            king_square = {'white': 'e1', 'black': 'e8'}[to_play]
            return king_square, {'white': 'g1', 'black': 'g8'}[to_play]
        elif move.startswith('O-O-O'):
            king_square = {'white': 'e1', 'black': 'e8'}[to_play]
            return king_square, {'white': 'c1', 'black': 'c8'}[to_play]
        
        # Remove any check/mate symbols
        clean_move = move
        for symbol in ['+', '#', '=', 'ep']:
            if symbol in clean_move:
                clean_move = clean_move.split(symbol)[0]
        
        # Determine piece type
        piece_type = clean_move[0] if clean_move[0] in 'KQRBNP' else 'P'
        
        # Extract disambiguation
        disambig_file = ''
        disambig_rank = ''
        remaining = clean_move
        
        if piece_type in 'KQRBN':
            remaining = remaining[1:]
        else:
            piece_type = 'P'
        
        # Check for disambiguation
        if len(remaining) >= 2 and remaining[0] in 'abcdefgh':
            if remaining[1] in 'abcdefgh':
                # File disambiguation
                disambig_file = remaining[0]
                remaining = remaining[1:]
            elif remaining[1] in '12345678':
                # Rank disambiguation
                disambig_rank = remaining[0]
                remaining = remaining[1:]
        
        # Destination square
        dest_square = remaining[-2:]
        
        # Find source square
        dest_x, dest_y = parse_square(dest_square)
        
        for square, piece in board.items():
            if not piece.startswith(color_prefix):
                continue
            
            sq_piece_type = piece[1] if len(piece) == 2 else piece[1:]
            if sq_piece_type != piece_type:
                continue
            
            src_x, src_y = parse_square(square)
            
            # Check file/rank disambiguation
            if disambig_file and file_idx_inv[src_x] != disambig_file:
                continue
            if disambig_rank and rank_idx_inv[src_y] != disambig_rank:
                continue
            
            # Verify move is legal (basic check)
            if can_piece_move(piece_type, src_x, src_y, dest_x, dest_y, board, color_prefix):
                return square, dest_square
        
        return None, None
    
    file_idx_inv = {v: k for k, v in file_idx.items()}
    rank_idx_inv = {v: k for k, v in rank_idx.items()}
    
    def can_piece_move(piece_type, src_x, src_y, dest_x, dest_y, board, color):
        dest_piece = get_piece_at(dest_x, dest_y)
        if dest_piece and dest_piece[0] == color:
            return False
        
        dx = dest_x - src_x
        dy = dest_y - src_y
        abs_dx = abs(dx)
        abs_dy = abs(dy)
        
        if piece_type == 'P':
            direction = 1 if color == 'w' else -1
            start_rank = 1 if color == 'w' else 6
            
            # Forward move
            if src_x == dest_x:
                if dy == direction:
                    return dest_piece is None
                elif dy == 2 * direction and src_y == start_rank:
                    return dest_piece is None and get_piece_at(src_x, src_y + direction) is None
                return False
            
            # Capture
            if abs_dx == 1 and dy == direction:
                return dest_piece is not None and dest_piece[0] != color
            
            return False
        
        elif piece_type == 'N':
            return (abs_dx == 2 and abs_dy == 1) or (abs_dx == 1 and abs_dy == 2)
        
        elif piece_type == 'B':
            if abs_dx != abs_dy:
                return False
            step_x = 1 if dx > 0 else -1
            step_y = 1 if dy > 0 else -1
            cx, cy = src_x + step_x, src_y + step_y
            while (cx, cy) != (dest_x, dest_y):
                if get_piece_at(cx, cy) is not None:
                    return False
                cx, cy = cx + step_x, cy + step_y
            return True
        
        elif piece_type == 'R':
            if src_x != dest_x and src_y != dest_y:
                return False
            step_x = 0 if dx == 0 else (1 if dx > 0 else -1)
            step_y = 0 if dy == 0 else (1 if dy > 0 else -1)
            cx, cy = src_x + step_x, src_y + step_y
            while (cx, cy) != (dest_x, dest_y):
                if get_piece_at(cx, cy) is not None:
                    return False
                cx, cy = cx + step_x, cy + step_y
            return True
        
        elif piece_type == 'Q':
            if src_x != dest_x and src_y != dest_y and abs_dx != abs_dy:
                return False
            if src_x == dest_x or src_y == dest_y:
                step_x = 0 if dx == 0 else (1 if dx > 0 else -1)
                step_y = 0 if dy == 0 else (1 if dy > 0 else -1)
            else:
                step_x = 1 if dx > 0 else -1
                step_y = 1 if dy > 0 else -1
            cx, cy = src_x + step_x, src_y + step_y
            while (cx, cy) != (dest_x, dest_y):
                if get_piece_at(cx, cy) is not None:
                    return False
                cx, cy = cx + step_x, cy + step_y
            return True
        
        elif piece_type == 'K':
            return max(abs_dx, abs_dy) == 1
        
        return False
    
    # Piece-square tables for positional evaluation
    # Higher values = better for the side to move
    pawn_table = [
        0,  0,  0,  0,  0,  0,  0,  0,
        5, 10, 10, -20, -20, 10, 10,  5,
        5, -5, -10,  0,  0, -10, -5,  5,
        0,  0,  0, 20, 20,  0,  0,  0,
        5,  5, 10, 25, 25, 10,  5,  5,
        10, 10, 20, 30, 30, 20, 10, 10,
        50, 50, 50, 50, 50, 50, 50, 50,
        0,  0,  0,  0,  0,  0,  0,  0
    ]
    
    knight_table = [
        -50, -40, -30, -30, -30, -30, -40, -50,
        -40, -20,  0,  5,  5,  0, -20, -40,
        -30,  0, 10, 15, 15, 10,  0, -30,
        -30,  5, 15, 20, 20, 15,  5, -30,
        -30,  0, 15, 20, 20, 15,  0, -30,
        -30,  5, 10, 15, 15, 10,  5, -30,
        -40, -20,  0,  0,  0,  0, -20, -40,
        -50, -40, -30, -30, -30, -30, -40, -50
    ]
    
    bishop_table = [
        -20, -10, -10, -10, -10, -10, -10, -20,
        -10,  5,  0,  0,  0,  0,  5, -10,
        -10, 10, 10, 10, 10, 10, 10, -10,
        -10,  0, 10, 10, 10, 10,  0, -10,
        -10,  5,  5, 10, 10,  5,  5, -10,
        -10,  0,  5, 10, 10,  5,  0, -10,
        -10,  0,  0,  0,  0,  0,  0, -10,
        -20, -10, -10, -10, -10, -10, -10, -20
    ]
    
    rook_table = [
        0,  0,  0,  5,  5,  0,  0,  0,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        5, 10, 10, 10, 10, 10, 10,  5,
        0,  0,  0,  0,  0,  0,  0,  0
    ]
    
    queen_table = [
        -20, -10, -10, -5, -5, -10, -10, -20,
        -10,  0,  0,  0,  0,  0,  0, -10,
        -10,  5,  5,  5,  5,  5,  0, -10,
        0,  0,  5,  5,  5,  5,  0, -5,
        -5,  0,  5,  5,  5,  5,  0, -5,
        -10,  0,  5,  5,  5,  5,  0, -10,
        -10,  0,  0,  0,  0,  0,  0, -10,
        -20, -10, -10, -5, -5, -10, -10, -20
    ]
    
    king_middle_table = [
        20, 30, 10,  0,  0, 10, 30, 20,
        20, 20,  0,  0,  0,  0, 20, 20,
        -10, -20, -20, -20, -20, -20, -20, -10,
        -20, -30, -30, -40, -40, -30, -30, -20,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30
    ]
    
    king_endgame_table = [
        -50, -30, -30, -30, -30, -30, -30, -50,
        -30, -30,  0,  0,  0,  0, -30, -30,
        -30, -10, 20, 30, 30, 20, -10, -30,
        -30, -10, 30, 40, 40, 30, -10, -30,
        -30, -10, 30, 40, 40, 30, -10, -30,
        -30, -10, 20, 30, 30, 20, -10, -30,
        -30, -20, -10,  0,  0, -10, -20, -30,
        -50, -30, -30, -30, -30, -30, -30, -50
    ]
    
    def get_positional_value(piece, x, y):
        piece_type = piece[1]
        table = pawn_table if piece_type == 'P' else \
                knight_table if piece_type == 'N' else \
                bishop_table if piece_type == 'B' else \
                rook_table if piece_type == 'R' else \
                queen_table if piece_type == 'Q' else \
                king_middle_table if piece_type == 'K' else None
        
        if table is None:
            return 0
        
        # Flip table for black pieces
        if piece[0] == 'b':
            idx = (7 - y) * 8 + x
        else:
            idx = y * 8 + x
        
        return table[idx]
    
    # Count material
    def count_material(board_state, color):
        prefix = 'w' if color == 'white' else 'b'
        value = 0
        for piece in board_state.values():
            if piece.startswith(prefix):
                piece_type = piece[1]
                value += piece_values.get(piece_type, 0)
        return value
    
    # Simple endgame detection
    def is_endgame(board_state):
        queen_count = sum(1 for p in board_state.values() if p[1] == 'Q')
        rook_count = sum(1 for p in board_state.values() if p[1] == 'R')
        minor_pieces = sum(1 for p in board_state.values() if p[1] in ['N', 'B'])
        
        total_material = sum(piece_values.get(p[1], 0) for p in board_state.values())
        
        # Endgame: low material or both queens off
        return total_material < 25 or (queen_count == 0 and rook_count == 0)
    
    # Evaluate a move
    def evaluate_move(move):
        score = 0
        
        # Check for checkmate (moves ending with #)
        if move.endswith('#'):
            return 100000
        
        # Check for check (moves ending with +)
        if move.endswith('+'):
            score += 50
        
        # Parse move
        src, dst = parse_move_notation(move, board, color_prefix)
        if src is None:
            return -100000  # Invalid move
        
        src_x, src_y = parse_square(src)
        dst_x, dst_y = parse_square(dst)
        
        piece = board.get(src, '')
        captured_piece = board.get(dst, '')
        
        # Material gain
        if captured_piece:
            cap_type = captured_piece[1] if len(captured_piece) == 2 else captured_piece[1:]
            score += piece_values.get(cap_type, 0) * 100
        
        # Positional improvement
        score += get_positional_value(piece, dst_x, dst_y) - get_positional_value(piece, src_x, src_y)
        
        # Center control bonus
        center_squares = [(3,3), (3,4), (4,3), (4,4)]
        if (dst_x, dst_y) in center_squares:
            score += 10
        
        # Development bonus (moving pieces from starting rank)
        piece_type = piece[1] if len(piece) == 2 else piece[1:]
        if piece_type in ['N', 'B']:
            start_rank = 7 if color_prefix == 'w' else 0
            if src_y == start_rank:
                score += 15
        
        # King safety - check if move protects king
        king_pos = find_king(to_play)
        if king_pos:
            kx, ky = king_pos
            # Check if destination square protects king
            if max(abs(dst_x - kx), abs(dst_y - ky)) <= 1:
                score += 20
        
        # King attack bonus
        opponent_king_pos = find_king('black' if to_play == 'white' else 'white')
        if opponent_king_pos:
            okx, oky = opponent_king_pos
            if max(abs(dst_x - okx), abs(dst_y - oky)) <= 2:
                score += 15
        
        # Penalty if moving piece away from protecting something
        if piece_type == 'K':
            score -= 10  # Generally avoid moving king unless necessary
        
        # Pawn promotion bonus
        if '=Q' in move or '=R' in move or '=B' in move or '=N' in move:
            score += 800
        
        # Castling bonus
        if move.startswith('O-O'):
            score += 50
        
        return score
    
    # Evaluate all moves and select the best one
    best_move = None
    best_score = -float('inf')
    
    for move in legal_moves:
        score = evaluate_move(move)
        if score > best_score:
            best_score = score
            best_move = move
    
    # Fallback: return first legal move if evaluation fails
    if best_move is None and legal_moves:
        best_move = legal_moves[0]
    
    return best_move, memory

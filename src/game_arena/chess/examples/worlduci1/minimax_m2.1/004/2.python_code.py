
def policy(pieces: dict[str, str], to_play: str) -> str:
    """
    Chess move selection policy that evaluates positions and selects the best move.
    
    Args:
        pieces: Dictionary mapping squares to piece codes (e.g., {'e1': 'bK'})
        to_play: Current player to move ('white' or 'black')
    
    Returns:
        Best move in UCI notation
    """
    import itertools
    
    # Piece values and definitions
    PIECE_VALUES = {
        'P': 100, 'N': 300, 'B': 330, 'R': 500, 'Q': 900, 'K': 0
    }
    
    FILE_ORDER = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
    
    def parse_square(square):
        """Convert square like 'e4' to (file, rank)"""
        return FILE_ORDER[square[0]], int(square[1])
    
    def make_square(file_rank):
        """Convert (file, rank) back to square string"""
        file_char = list(FILE_ORDER.keys())[list(FILE_ORDER.values()).index(file_rank[0])]
        return f"{file_char}{file_rank[1]}"
    
    def get_piece_at(square):
        """Get piece at a square, return (color, type) or None"""
        if square in pieces:
            code = pieces[square]
            return code[0], code[1]  # color, type
        return None
    
    def is_own_piece(color, square):
        """Check if square contains own piece"""
        piece = get_piece_at(square)
        return piece and piece[0] == color
    
    def is_enemy_piece(color, square):
        """Check if square contains enemy piece"""
        piece = get_piece_at(square)
        return piece and piece[0] != color
    
    def is_empty(square):
        """Check if square is empty"""
        return square not in pieces
    
    def is_on_board(square):
        """Check if square is on the chessboard"""
        if len(square) != 2:
            return False
        file_char, rank_char = square[0], square[1]
        return file_char in FILE_ORDER and '1' <= rank_char <= '8'
    
    def get_king_pos(color):
        """Find king position for given color"""
        target_piece = color + 'K'
        for square, code in pieces.items():
            if code == target_piece:
                return square
        return None
    
    # Positional tables (from white's perspective)
    # We'll adjust for black by flipping
    PAWN_TABLE = [
        0,  0,  0,  0,  0,  0,  0,  0,
        50, 50, 50, 50, 50, 50, 50, 50,
        10, 10, 20, 30, 30, 20, 10, 10,
        5,  5, 10, 25, 25, 10,  5,  5,
        0,  0,  0, 20, 20,  0,  0,  0,
        5, -5,-10,  0,  0,-10, -5,  5,
        5, 10, 10,-20,-20, 10, 10,  5,
        0,  0,  0,  0,  0,  0,  0,  0
    ]
    
    KNIGHT_TABLE = [
        -50,-40,-30,-30,-30,-30,-40,-50,
        -40,-20,  0,  0,  0,  0,-20,-40,
        -30,  0, 10, 15, 15, 10,  0,-30,
        -30,  5, 15, 20, 20, 15,  5,-30,
        -30,  0, 15, 20, 20, 15,  0,-30,
        -30,  5, 10, 15, 15, 10,  5,-30,
        -40,-20,  0,  5,  5,  0,-20,-40,
        -50,-40,-30,-30,-30,-30,-40,-50
    ]
    
    BISHOP_TABLE = [
        -20,-10,-10,-10,-10,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5, 10, 10,  5,  0,-10,
        -10,  5,  5, 10, 10,  5,  5,-10,
        -10,  0, 10, 10, 10, 10,  0,-10,
        -10, 10, 10, 10, 10, 10, 10,-10,
        -10,  5,  0,  0,  0,  0,  5,-10,
        -20,-10,-10,-10,-10,-10,-10,-20
    ]
    
    ROOK_TABLE = [
        0,  0,  0,  0,  0,  0,  0,  0,
        5, 10, 10, 10, 10, 10, 10,  5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        0,  0,  0,  5,  5,  0,  0,  0
    ]
    
    QUEEN_TABLE = [
        -20,-10,-10, -5, -5,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5,  5,  5,  5,  0,-10,
        -5,  0,  5,  5,  5,  5,  0, -5,
        0,  0,  5,  5,  5,  5,  0, -5,
        -10,  5,  5,  5,  5,  5,  0,-10,
        -10,  0,  5,  0,  0,  0,  0,-10,
        -20,-10,-10, -5, -5,-10,-10,-20
    ]
    
    KING_MIDDLE = [
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -20,-30,-30,-40,-40,-30,-30,-20,
        -10,-20,-20,-20,-20,-20,-20,-10,
        20, 20,  0,  0,  0,  0, 20, 20,
        20, 30, 10,  0,  0, 10, 30, 20
    ]
    
    def get_positional_value(piece_code, square):
        """Get positional value for a piece on a square"""
        color, piece_type = piece_code[0], piece_code[1]
        file_idx, rank_idx = parse_square(square)
        
        # Adjust for black (flip vertically)
        if color == 'b':
            rank_idx = 7 - rank_idx
        
        table_index = rank_idx * 8 + file_idx
        
        if piece_type == 'P':
            return PAWN_TABLE[table_index]
        elif piece_type == 'N':
            return KNIGHT_TABLE[table_index]
        elif piece_type == 'B':
            return BISHOP_TABLE[table_index]
        elif piece_type == 'R':
            return ROOK_TABLE[table_index]
        elif piece_type == 'Q':
            return QUEEN_TABLE[table_index]
        elif piece_type == 'K':
            return KING_MIDDLE[table_index]
        return 0
    
    def generate_pawn_moves(color, square):
        """Generate pawn moves for a given piece"""
        moves = []
        file_idx, rank_idx = parse_square(square)
        direction = 1 if color == 'w' else -1
        start_rank = 2 if color == 'w' else 7
        
        # Forward move
        new_rank = rank_idx + direction
        new_square = make_square((file_idx, new_rank))
        if is_on_board(new_square) and is_empty(new_square):
            moves.append(square + new_square)
            
            # Double move from start
            if rank_idx == start_rank:
                double_rank = rank_idx + 2 * direction
                double_square = make_square((file_idx, double_rank))
                if is_on_board(double_square) and is_empty(double_square):
                    moves.append(square + double_square)
        
        # Captures
        for df in [-1, 1]:
            new_file = file_idx + df
            if 0 <= new_file <= 7:
                capture_square = make_square((new_file, new_rank))
                if is_on_board(capture_square) and is_enemy_piece(color, capture_square):
                    moves.append(square + capture_square)
        
        return moves
    
    def generate_sliding_moves(color, square, directions):
        """Generate sliding moves (bishop, rook, queen)"""
        moves = []
        file_idx, rank_idx = parse_square(square)
        
        for df, dr in directions:
            curr_file, curr_rank = file_idx + df, rank_idx + dr
            while 0 <= curr_file <= 7 and 1 <= curr_rank <= 8:
                curr_square = make_square((curr_file, curr_rank))
                
                if is_empty(curr_square):
                    moves.append(square + curr_square)
                elif is_enemy_piece(color, curr_square):
                    moves.append(square + curr_square)
                    break
                else:  # own piece
                    break
                
                curr_file += df
                curr_rank += dr
        
        return moves
    
    def generate_knight_moves(color, square):
        """Generate knight moves"""
        moves = []
        file_idx, rank_idx = parse_square(square)
        knight_moves = [(-2,-1), (-2,1), (-1,-2), (-1,2), (1,-2), (1,2), (2,-1), (2,1)]
        
        for df, dr in knight_moves:
            new_file, new_rank = file_idx + df, rank_idx + dr
            if 0 <= new_file <= 7 and 1 <= new_rank <= 8:
                new_square = make_square((new_file, new_rank))
                if is_empty(new_square) or is_enemy_piece(color, new_square):
                    moves.append(square + new_square)
        
        return moves
    
    def generate_king_moves(color, square):
        """Generate king moves"""
        moves = []
        file_idx, rank_idx = parse_square(square)
        
        for df in [-1, 0, 1]:
            for dr in [-1, 0, 1]:
                if df == 0 and dr == 0:
                    continue
                new_file, new_rank = file_idx + df, rank_idx + dr
                if 0 <= new_file <= 7 and 1 <= new_rank <= 8:
                    new_square = make_square((new_file, new_rank))
                    if is_empty(new_square) or is_enemy_piece(color, new_square):
                        moves.append(square + new_square)
        
        # Castling
        king_pos = get_king_pos(color)
        if square == king_pos:
            # Check castling rules (simplified - would need more state in real engine)
            rank = '1' if color == 'w' else '8'
            if is_empty('f' + rank) and is_empty('g' + rank):
                if is_empty('h' + rank) and get_piece_at('h' + rank) == (color, 'R'):
                    moves.append(square + 'g' + rank)  # Kingside
            if is_empty('d' + rank) and is_empty('c' + rank) and is_empty('b' + rank):
                if is_empty('a' + rank) and get_piece_at('a' + rank) == (color, 'R'):
                    moves.append(square + 'c' + rank)  # Queenside
        
        return moves
    
    def generate_moves(color):
        """Generate all legal moves for a color"""
        moves = []
        
        for square, piece_code in pieces.items():
            if piece_code[0] != color:
                continue
            
            piece_type = piece_code[1]
            
            if piece_type == 'P':
                moves.extend(generate_pawn_moves(color, square))
            elif piece_type == 'N':
                moves.extend(generate_knight_moves(color, square))
            elif piece_type == 'B':
                moves.extend(generate_sliding_moves(color, square, [(-1,-1), (-1,1), (1,-1), (1,1)]))
            elif piece_type == 'R':
                moves.extend(generate_sliding_moves(color, square, [(-1,0), (1,0), (0,-1), (0,1)]))
            elif piece_type == 'Q':
                moves.extend(generate_sliding_moves(color, square, [(-1,-1), (-1,1), (1,-1), (1,1), (-1,0), (1,0), (0,-1), (0,1)]))
            elif piece_type == 'K':
                moves.extend(generate_king_moves(color, square))
        
        return moves
    
    def apply_move(pieces_dict, move):
        """Apply a move and return new pieces dict"""
        new_pieces = pieces_dict.copy()
        from_square = move[:2]
        to_square = move[2:4]
        
        piece = new_pieces.pop(from_square)
        new_pieces[to_square] = piece
        
        # Handle promotion
        if len(move) > 4:
            promotion_piece = move[4]
            new_pieces[to_square] = piece[0] + promotion_piece
        
        return new_pieces
    
    def evaluate_position(pieces_dict, color):
        """Evaluate position from perspective of given color"""
        score = 0
        
        for square, piece_code in pieces_dict.items():
            piece_color, piece_type = piece_code[0], piece_code[1]
            value = PIECE_VALUES[piece_type]
            
            # Add positional value
            value += get_positional_value(piece_code, square)
            
            if piece_color == color:
                score += value
            else:
                score -= value
        
        return score
    
    def is_check(pieces_dict, color):
        """Check if king of given color is in check"""
        enemy_color = 'b' if color == 'w' else 'w'
        king_pos = get_king_pos(color)
        
        if not king_pos:
            return False
        
        # Generate all enemy moves and see if any attack the king
        for square, piece_code in pieces_dict.items():
            if piece_code[0] != enemy_color:
                continue
            
            piece_type = piece_code[1]
            enemy_moves = []
            
            if piece_type == 'P':
                # Pawn attacks
                file_idx, rank_idx = parse_square(square)
                direction = 1 if enemy_color == 'w' else -1
                for df in [-1, 1]:
                    new_file = file_idx + df
                    new_rank = rank_idx + direction
                    if 0 <= new_file <= 7 and 1 <= new_rank <= 8:
                        attack_square = make_square((new_file, new_rank))
                        enemy_moves.append(square + attack_square)
            elif piece_type == 'N':
                enemy_moves = generate_knight_moves(enemy_color, square)
            elif piece_type == 'B':
                enemy_moves = generate_sliding_moves(enemy_color, square, [(-1,-1), (-1,1), (1,-1), (1,1)])
            elif piece_type == 'R':
                enemy_moves = generate_sliding_moves(enemy_color, square, [(-1,0), (1,0), (0,-1), (0,1)])
            elif piece_type == 'Q':
                enemy_moves = generate_sliding_moves(enemy_color, square, [(-1,-1), (-1,1), (1,-1), (1,1), (-1,0), (1,0), (0,-1), (0,1)])
            elif piece_type == 'K':
                enemy_moves = generate_king_moves(enemy_color, square)
            
            for move in enemy_moves:
                if move[2:4] == king_pos:
                    return True
        
        return False
    
    def is_checkmate(pieces_dict, color):
        """Check if position is checkmate"""
        if not is_check(pieces_dict, color):
            return False
        
        # No legal moves means checkmate
        legal_moves = generate_moves(color)
        return len(legal_moves) == 0
    
    # Generate all legal moves
    legal_moves = generate_moves(to_play)
    
    if not legal_moves:
        # No legal moves - return empty string or handle stalemate
        return ''
    
    # Evaluate each move
    best_move = legal_moves[0]
    best_score = float('-inf')
    
    for move in legal_moves:
        # Apply move
        new_pieces = apply_move(pieces, move)
        
        # Check for checkmate (immediate win)
        enemy_color = 'b' if to_play == 'w' else 'w'
        if is_checkmate(new_pieces, enemy_color):
            return move  # Immediate checkmate!
        
        # Check if we're delivering check
        if is_check(new_pieces, enemy_color):
            score = 1000  # Bonus for delivering check
        else:
            score = 0
        
        # Evaluate the resulting position
        score += evaluate_position(new_pieces, to_play)
        
        # Add small randomness to break ties
        score += 0.01
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move

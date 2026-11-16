
def policy(pieces: dict[str, str], to_play: str, memory: dict) -> tuple[str, dict]:
    import random
    
    # Piece values
    piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
    
    # Center squares bonus
    center_squares = {'d4', 'd5', 'e4', 'e5'}
    extended_center = {'c3', 'c4', 'c5', 'c6', 'd3', 'd6', 'e3', 'e6', 'f3', 'f4', 'f5', 'f6'}
    
    def get_legal_moves(board, color):
        """Generate all legal moves for the given color"""
        moves = []
        my_color = 'w' if color == 'white' else 'b'
        
        for square, piece in board.items():
            if piece[0] == my_color:
                moves.extend(get_piece_moves(board, square, piece, color))
        
        # Filter out moves that leave king in check
        legal = []
        for move in moves:
            new_board = apply_move(board.copy(), move)
            if not is_in_check(new_board, color):
                legal.append(move)
        
        return legal
    
    def get_piece_moves(board, square, piece, color):
        """Get possible moves for a piece at a square"""
        moves = []
        piece_type = piece[1]
        my_color = piece[0]
        
        if piece_type == 'P':
            moves.extend(get_pawn_moves(board, square, my_color))
        elif piece_type == 'N':
            moves.extend(get_knight_moves(board, square, my_color))
        elif piece_type == 'B':
            moves.extend(get_bishop_moves(board, square, my_color))
        elif piece_type == 'R':
            moves.extend(get_rook_moves(board, square, my_color))
        elif piece_type == 'Q':
            moves.extend(get_queen_moves(board, square, my_color))
        elif piece_type == 'K':
            moves.extend(get_king_moves(board, square, my_color))
        
        return moves
    
    def get_pawn_moves(board, square, color):
        moves = []
        file, rank = square[0], int(square[1])
        direction = 1 if color == 'w' else -1
        start_rank = 2 if color == 'w' else 7
        promo_rank = 8 if color == 'w' else 1
        
        # Forward move
        new_rank = rank + direction
        if 1 <= new_rank <= 8:
            new_sq = file + str(new_rank)
            if new_sq not in board:
                if new_rank == promo_rank:
                    for promo in ['q', 'r', 'b', 'n']:
                        moves.append(square + new_sq + promo)
                else:
                    moves.append(square + new_sq)
                
                # Double move from start
                if rank == start_rank:
                    new_rank2 = rank + 2 * direction
                    new_sq2 = file + str(new_rank2)
                    if new_sq2 not in board:
                        moves.append(square + new_sq2)
        
        # Captures
        for df in [-1, 1]:
            new_file = chr(ord(file) + df)
            if 'a' <= new_file <= 'h':
                new_rank = rank + direction
                if 1 <= new_rank <= 8:
                    new_sq = new_file + str(new_rank)
                    if new_sq in board and board[new_sq][0] != color:
                        if new_rank == promo_rank:
                            for promo in ['q', 'r', 'b', 'n']:
                                moves.append(square + new_sq + promo)
                        else:
                            moves.append(square + new_sq)
        
        return moves
    
    def get_knight_moves(board, square, color):
        moves = []
        file, rank = ord(square[0]), int(square[1])
        deltas = [(2,1), (2,-1), (-2,1), (-2,-1), (1,2), (1,-2), (-1,2), (-1,-2)]
        
        for df, dr in deltas:
            new_file, new_rank = file + df, rank + dr
            if ord('a') <= new_file <= ord('h') and 1 <= new_rank <= 8:
                new_sq = chr(new_file) + str(new_rank)
                if new_sq not in board or board[new_sq][0] != color:
                    moves.append(square + new_sq)
        
        return moves
    
    def get_sliding_moves(board, square, color, directions):
        moves = []
        file, rank = ord(square[0]), int(square[1])
        
        for df, dr in directions:
            for dist in range(1, 8):
                new_file, new_rank = file + df * dist, rank + dr * dist
                if not (ord('a') <= new_file <= ord('h') and 1 <= new_rank <= 8):
                    break
                new_sq = chr(new_file) + str(new_rank)
                if new_sq in board:
                    if board[new_sq][0] != color:
                        moves.append(square + new_sq)
                    break
                moves.append(square + new_sq)
        
        return moves
    
    def get_bishop_moves(board, square, color):
        return get_sliding_moves(board, square, color, [(1,1), (1,-1), (-1,1), (-1,-1)])
    
    def get_rook_moves(board, square, color):
        return get_sliding_moves(board, square, color, [(1,0), (-1,0), (0,1), (0,-1)])
    
    def get_queen_moves(board, square, color):
        return get_sliding_moves(board, square, color, [(1,1), (1,-1), (-1,1), (-1,-1), (1,0), (-1,0), (0,1), (0,-1)])
    
    def get_king_moves(board, square, color):
        moves = []
        file, rank = ord(square[0]), int(square[1])
        
        for df in [-1, 0, 1]:
            for dr in [-1, 0, 1]:
                if df == 0 and dr == 0:
                    continue
                new_file, new_rank = file + df, rank + dr
                if ord('a') <= new_file <= ord('h') and 1 <= new_rank <= 8:
                    new_sq = chr(new_file) + str(new_rank)
                    if new_sq not in board or board[new_sq][0] != color:
                        moves.append(square + new_sq)
        
        return moves
    
    def apply_move(board, move):
        """Apply a move to the board"""
        new_board = board.copy()
        from_sq = move[:2]
        to_sq = move[2:4]
        
        piece = new_board[from_sq]
        del new_board[from_sq]
        
        if len(move) == 5:  # Promotion
            promo_piece = move[4].upper()
            new_board[to_sq] = piece[0] + promo_piece
        else:
            new_board[to_sq] = piece
        
        return new_board
    
    def is_in_check(board, color):
        """Check if the king of the given color is in check"""
        my_color = 'w' if color == 'white' else 'b'
        opp_color = 'b' if color == 'white' else 'w'
        
        # Find king
        king_sq = None
        for sq, piece in board.items():
            if piece == my_color + 'K':
                king_sq = sq
                break
        
        if not king_sq:
            return False
        
        # Check if any opponent piece attacks the king
        for sq, piece in board.items():
            if piece[0] == opp_color:
                attacks = get_piece_attacks(board, sq, piece)
                if king_sq in attacks:
                    return True
        
        return False
    
    def get_piece_attacks(board, square, piece):
        """Get all squares attacked by a piece"""
        attacks = set()
        piece_type = piece[1]
        color = piece[0]
        
        if piece_type == 'P':
            file, rank = square[0], int(square[1])
            direction = 1 if color == 'w' else -1
            for df in [-1, 1]:
                new_file = chr(ord(file) + df)
                new_rank = rank + direction
                if 'a' <= new_file <= 'h' and 1 <= new_rank <= 8:
                    attacks.add(new_file + str(new_rank))
        else:
            # For other pieces, just get their moves (simplified)
            moves = get_piece_moves(board, square, piece, 'white' if color == 'w' else 'black')
            for move in moves:
                attacks.add(move[2:4])
        
        return attacks
    
    def evaluate_position(board, color):
        """Evaluate the board position"""
        my_color = 'w' if color == 'white' else 'b'
        opp_color = 'b' if color == 'white' else 'w'
        
        score = 0
        
        # Material count
        for piece in board.values():
            value = piece_values[piece[1]]
            if piece[0] == my_color:
                score += value
            else:
                score -= value
        
        # Positional bonuses
        for sq, piece in board.items():
            bonus = 0
            if sq in center_squares:
                bonus = 0.3
            elif sq in extended_center:
                bonus = 0.15
            
            if piece[0] == my_color:
                score += bonus
            else:
                score -= bonus
        
        return score
    
    def is_checkmate(board, color):
        """Check if the position is checkmate for the given color"""
        if not is_in_check(board, color):
            return False
        return len(get_legal_moves(board, color)) == 0
    
    def evaluate_move(board, move, color):
        """Evaluate a single move"""
        new_board = apply_move(board.copy(), move)
        to_sq = move[2:4]
        
        score = 0
        
        # Check for checkmate
        opp_color = 'black' if color == 'white' else 'white'
        if is_checkmate(new_board, opp_color):
            return 10000
        
        # Capture value
        if to_sq in board:
            captured_piece = board[to_sq][1]
            score += piece_values[captured_piece] * 10
        
        # Check bonus
        if is_in_check(new_board, opp_color):
            score += 3
        
        # Position evaluation
        score += evaluate_position(new_board, color)
        
        # Center control
        if to_sq in center_squares:
            score += 0.5
        
        # Promotion bonus
        if len(move) == 5:
            promo_piece = move[4]
            if promo_piece == 'q':
                score += 8
            else:
                score += 2
        
        return score
    
    # Main logic
    legal_moves = get_legal_moves(pieces, to_play)
    
    if not legal_moves:
        # Should not happen, but return a dummy move
        return ('e2e4', memory)
    
    # Evaluate all moves
    best_move = legal_moves[0]
    best_score = float('-inf')
    
    for move in legal_moves:
        score = evaluate_move(pieces, move, to_play)
        if score > best_score:
            best_score = score
            best_move = move
    
    return (best_move, memory)

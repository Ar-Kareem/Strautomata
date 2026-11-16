
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    """
    Select the best chess move using minimax search with alpha-beta pruning.
    """
    # Parse board into more usable format
    board = {}
    for square, piece in pieces.items():
        board[square] = piece
    
    # Get color abbreviation
    color = 'w' if to_play == 'white' else 'b'
    opponent = 'b' if color == 'w' else 'w'
    
    # Check for forced mate first
    for move in legal_moves:
        if '#' in move or 'mate' in move.lower():
            return move
    
    # Piece values for evaluation
    piece_values = {
        'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000
    }
    
    # Piece-square tables (positive values = better for white)
    pawn_table = [
        0,  0,  0,  0,  0,  0,  0,  0,
        50, 50, 50, 50, 50, 50, 50, 50,
        10, 10, 20, 30, 30, 20, 10, 10,
        5,  5, 10, 25, 25, 10,  5,  5,
        0,  0,  0, 20, 20,  0,  0,  0,
        5, -5,-10,  0,  0,-10, -5,  5,
        5, 10, 10,-20,-20, 10, 10,  5,
        0,  0,  0,  0,  0,  0,  0,  0
    ]
    
    knight_table = [
        -50,-40,-30,-30,-30,-30,-40,-50,
        -40,-20,  0,  0,  0,  0,-20,-40,
        -30,  0, 10, 15, 15, 10,  0,-30,
        -30,  5, 15, 20, 20, 15,  5,-30,
        -30,  0, 15, 20, 20, 15,  0,-30,
        -30,  5, 10, 15, 15, 10,  5,-30,
        -40,-20,  0,  5,  5,  0,-20,-40,
        -50,-40,-30,-30,-30,-30,-40,-50
    ]
    
    bishop_table = [
        -20,-10,-10,-10,-10,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5, 10, 10,  5,  0,-10,
        -10,  5,  5, 10, 10,  5,  5,-10,
        -10,  0, 10, 10, 10, 10,  0,-10,
        -10, 10, 10, 10, 10, 10, 10,-10,
        -10,  5,  0,  0,  0,  0,  5,-10,
        -20,-10,-10,-10,-10,-10,-10,-20
    ]
    
    rook_table = [
        0,  0,  0,  0,  0,  0,  0,  0,
        5, 10, 10, 10, 10, 10, 10,  5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        0,  0,  0,  5,  5,  0,  0,  0
    ]
    
    queen_table = [
        -20,-10,-10, -5, -5,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5,  5,  5,  5,  0,-10,
        -5,  0,  5,  5,  5,  5,  0, -5,
        0,  0,  5,  5,  5,  5,  0, -5,
        -10,  5,  5,  5,  5,  5,  0,-10,
        -10,  0,  5,  0,  0,  0,  0,-10,
        -20,-10,-10, -5, -5,-10,-10,-20
    ]
    
    king_table = [
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -20,-30,-30,-40,-40,-30,-30,-20,
        -10,-20,-20,-20,-20,-20,-20,-10,
        20, 20,  0,  0,  0,  0, 20, 20,
        20, 30, 10,  0,  0, 10, 30, 20
    ]
    
    def square_to_index(square):
        file = ord(square[0]) - ord('a')
        rank = int(square[1]) - 1
        return rank * 8 + file
    
    def index_to_square(idx):
        rank = idx // 8
        file = idx % 8
        return chr(ord('a') + file) + str(rank + 1)
    
    def evaluate_board(board_state):
        """Evaluate position from white's perspective."""
        score = 0
        white_material = 0
        black_material = 0
        white_pawns = []
        black_pawns = []
        white_king_sq = None
        black_king_sq = None
        
        for square, piece in board_state.items():
            idx = square_to_index(square)
            piece_type = piece[1]
            piece_color = piece[0]
            
            # Material
            if piece_color == 'w':
                white_material += piece_values.get(piece_type, 0)
                if piece_type == 'P':
                    white_pawns.append(idx)
                elif piece_type == 'K':
                    white_king_sq = idx
            else:
                black_material += piece_values.get(piece_type, 0)
                if piece_type == 'P':
                    black_pawns.append(idx)
                elif piece_type == 'K':
                    black_king_sq = idx
            
            # Position values
            if piece_type == 'P':
                table = pawn_table
            elif piece_type == 'N':
                table = knight_table
            elif piece_type == 'B':
                table = bishop_table
            elif piece_type == 'R':
                table = rook_table
            elif piece_type == 'Q':
                table = queen_table
            elif piece_type == 'K':
                table = king_table
            else:
                continue
            
            if piece_color == 'w':
                score += table[idx]
            else:
                # Flip table for black
                flipped_idx = (7 - (idx // 8)) * 8 + (7 - (idx % 8))
                score -= table[flipped_idx]
        
        # Material difference
        score += white_material - black_material
        
        # Pawn structure
        white_passed = 0
        white_doubled = 0
        white_isolated = 0
        for p in white_pawns:
            file = p % 8
            rank = p // 8
            
            # Passed pawn bonus
            passed = True
            for r in range(rank + 1, 8):
                if (r * 8 + file) in board_state:
                    if board_state[r * 8 + file][0] == 'w' and board_state[r * 8 + file][1] == 'P':
                        passed = False
                        break
            if passed:
                white_passed += 30 * (rank + 1)
            
            # Doubled pawn penalty
            for other in white_pawns:
                if other != p and other % 8 == file and other > p:
                    white_doubled -= 10
                    break
            
            # Isolated pawn penalty
            isolated = True
            for df in [-1, 1]:
                if 0 <= file + df < 8:
                    for r in range(8):
                        if r != rank:
                            sq = r * 8 + file + df
                            if sq in board_state and board_state[sq][0] == 'w' and board_state[sq][1] == 'P':
                                isolated = False
                                break
                if not isolated:
                    break
            if isolated:
                white_isolated -= 15
        
        black_passed = 0
        black_doubled = 0
        black_isolated = 0
        for p in black_pawns:
            file = p % 8
            rank = p // 8
            
            passed = True
            for r in range(rank - 1, -1, -1):
                if (r * 8 + file) in board_state:
                    if board_state[r * 8 + file][0] == 'b' and board_state[r * 8 + file][1] == 'P':
                        passed = False
                        break
            if passed:
                black_passed += 30 * (7 - rank)
            
            for other in black_pawns:
                if other != p and other % 8 == file and other < p:
                    black_doubled -= 10
                    break
            
            isolated = True
            for df in [-1, 1]:
                if 0 <= file + df < 8:
                    for r in range(8):
                        if r != rank:
                            sq = r * 8 + file + df
                            if sq in board_state and board_state[sq][0] == 'b' and board_state[sq][1] == 'P':
                                isolated = False
                                break
                if not isolated:
                    break
            if isolated:
                black_isolated -= 15
        
        score += white_passed + white_doubled + white_isolated
        score -= black_passed + black_doubled + black_isolated
        
        # King safety
        if white_king_sq is not None:
            wkf = white_king_sq % 8
            wkr = white_king_sq // 8
            white_defenders = 0
            for dfile in [-1, 0, 1]:
                for drank in [-1, 0, 1]:
                    if dfile == 0 and drank == 0:
                        continue
                    nf, nr = wkf + dfile, wkr + drank
                    if 0 <= nf < 8 and 0 <= nr < 8:
                        sq = nr * 8 + nf
                        if sq in board_state and board_state[sq][0] == 'w':
                            if board_state[sq][1] in ['P', 'N', 'B', 'R', 'Q']:
                                white_defenders += 10
            score += white_defenders
        
        if black_king_sq is not None:
            bkf = black_king_sq % 8
            bkr = black_king_sq // 8
            black_defenders = 0
            for dfile in [-1, 0, 1]:
                for drank in [-1, 0, 1]:
                    if dfile == 0 and drank == 0:
                        continue
                    nf, nr = bkf + dfile, bkr + drank
                    if 0 <= nf < 8 and 0 <= nr < 8:
                        sq = nr * 8 + nf
                        if sq in board_state and board_state[sq][0] == 'b':
                            if board_state[sq][1] in ['P', 'N', 'B', 'R', 'Q']:
                                black_defenders += 10
            score -= black_defenders
        
        # Center control
        center_squares = [27, 28, 35, 36]  # d4, e4, d5, e5
        for sq in center_squares:
            if sq in board_state:
                if board_state[sq][0] == 'w':
                    score += 10
                else:
                    score -= 10
        
        return score
    
    def make_move(board_state, move):
        """Apply a move to the board and return new board state."""
        new_board = board_state.copy()
        
        # Handle castling
        if move == 'O-O':
            if color == 'w':
                new_board['e1'] = None
                new_board['h1'] = None
                new_board['g1'] = 'wK'
                new_board['f1'] = 'wR'
            else:
                new_board['e8'] = None
                new_board['h8'] = None
                new_board['g8'] = 'bK'
                new_board['f8'] = 'bR'
            return {k: v for k, v in new_board.items() if v is not None}
        elif move == 'O-O-O':
            if color == 'w':
                new_board['e1'] = None
                new_board['a1'] = None
                new_board['c1'] = 'wK'
                new_board['d1'] = 'wR'
            else:
                new_board['e8'] = None
                new_board['a8'] = None
                new_board['c8'] = 'bK'
                new_board['d8'] = 'bR'
            return {k: v for k, v in new_board.items() if v is not None}
        
        # Parse the move
        # Handle disambiguation like 'Nbd7'
        if move[0] in 'RNBQK' and len(move) >= 4 and move[2] in 'abcdefgh':
            # Disambiguation like 'Nbd7'
            piece_type = move[0]
            from_file = move[1]
            to_square = move[2:4]
        elif move[0] in 'abcdefgh' and len(move) >= 4 and move[1] in 'abcdefgh':
            # Pawn move
            from_square = move[0:2]
            to_square = move[2:4]
        elif move[0] in 'RNBQK':
            piece_type = move[0]
            to_square = move[-2:]
        else:
            # King or special move
            to_square = move[-2:]
        
        # Find source square
        if piece_type == 'P':
            from_square = None
            for sq, p in board_state.items():
                if p == color + 'P':
                    file_match = sq[0] == move[0]
                    to_match = sq == to_square or (len(move) > 4 and sq == move[2:4])
                    if file_match and to_match:
                        from_square = sq
                        break
        else:
            from_square = None
            for sq, p in board_state.items():
                if p == color + piece_type:
                    # Simple check - in real chess we'd verify move legality
                    if to_square in generate_pseudo_legal_moves(sq, p, board_state):
                        from_square = sq
                        break
        
        if from_square is None:
            return board_state
        
        # Handle captures and promotions
        new_piece = color + piece_type if piece_type != 'P' else color + 'P'
        if '=Q' in move:
            new_piece = color + 'Q'
        elif '=R' in move:
            new_piece = color + 'R'
        elif '=B' in move:
            new_piece = color + 'B'
        elif '=N' in move:
            new_piece = color + 'N'
        
        new_board[from_square] = None
        new_board[to_square] = new_piece
        
        return {k: v for k, v in new_board.items() if v is not None}
    
    def generate_pseudo_legal_moves(square, piece, board_state):
        """Generate pseudo-legal moves for a piece."""
        moves = []
        file = ord(square[0]) - ord('a')
        rank = int(square[1]) - 1
        piece_type = piece[1]
        piece_color = piece[0]
        
        def is_valid(f, r):
            return 0 <= f < 8 and 0 <= r < 8
        
        def is_empty(f, r):
            sq = chr(ord('a') + f) + str(r + 1)
            return sq not in board_state
        
        def is_enemy(f, r):
            sq = chr(ord('a') + f) + str(r + 1)
            if sq in board_state:
                return board_state[sq][0] != piece_color
            return False
        
        if piece_type == 'P':
            direction = -1 if piece_color == 'w' else 1
            # Forward move
            if is_valid(file, rank + direction) and is_empty(file, rank + direction):
                moves.append(chr(ord('a') + file) + str(rank + direction + 1))
                # Double move from start
                start_rank = 1 if piece_color == 'w' else 6
                if rank == start_rank and is_empty(file, rank + 2 * direction):
                    moves.append(chr(ord('a') + file) + str(rank + 2 * direction + 1))
            # Captures
            for df in [-1, 1]:
                if is_valid(file + df, rank + direction):
                    if is_enemy(file + df, rank + direction):
                        moves.append(chr(ord('a') + file) + str(rank + direction + 1))
        
        elif piece_type == 'N':
            offsets = [(-2,-1), (-2,1), (-1,-2), (-1,2), (1,-2), (1,2), (2,-1), (2,1)]
            for df, dr in offsets:
                if is_valid(file + df, rank + dr):
                    if is_empty(file + df, rank + dr) or is_enemy(file + df, rank + dr):
                        moves.append(chr(ord('a') + file + df) + str(rank + dr + 1))
        
        elif piece_type in ['B', 'R', 'Q']:
            directions = []
            if piece_type in ['B', 'Q']:
                directions.extend([(-1,-1), (-1,1), (1,-1), (1,1)])
            if piece_type in ['R', 'Q']:
                directions.extend([(-1,0), (1,0), (0,-1), (0,1)])
            
            for df, dr in directions:
                for i in range(1, 8):
                    nf, nr = file + df * i, rank + dr * i
                    if not is_valid(nf, nr):
                        break
                    if is_empty(nf, nr):
                        moves.append(chr(ord('a') + nf) + str(nr + 1))
                    else:
                        if is_enemy(nf, nr):
                            moves.append(chr(ord('a') + nf) + str(nr + 1))
                        break
        
        elif piece_type == 'K':
            for df in [-1, 0, 1]:
                for dr in [-1, 0, 1]:
                    if df == 0 and dr == 0:
                        continue
                    if is_valid(file + df, rank + dr):
                        if is_empty(file + df, rank + dr) or is_enemy(file + df, rank + dr):
                            moves.append(chr(ord('a') + file + df) + str(rank + dr + 1))
        
        return moves
    
    def order_moves(moves, board_state):
        """Order moves for better alpha-beta pruning."""
        scored = []
        for move in moves:
            score = 0
            # Prioritize captures
            if 'x' in move or move[0] in 'abcdefgh' and len(move) > 4 and move[2] in 'abcdefgh':
                # Find captured piece
                if len(move) >= 4:
                    if move[0] in 'abcdefgh':
                        to_sq = move[2:4]
                    else:
                        to_sq = move[-2:]
                    if to_sq in board_state:
                        captured = board_state[to_sq][1]
                        score += piece_values.get(captured, 0) * 10
            
            # Prioritize checks
            if '+' in move or '#' in move:
                score += 500
            
            # Prioritize promotions
            if '=' in move:
                score += 400
            
            scored.append((score, move))
        
        scored.sort(reverse=True)
        return [m for s, m in scored]
    
    def minimax(board_state, depth, alpha, beta, maximizing):
        """Minimax with alpha-beta pruning."""
        if depth == 0:
            return evaluate_board(board_state)
        
        # Generate legal moves (simplified - use provided legal_moves)
        moves = legal_moves
        if not moves:
            # Check for checkmate or stalemate
            return -100000 if maximizing else 100000
        
        moves = order_moves(moves, board_state)
        
        if maximizing:
            max_eval = -float('inf')
            for move in moves:
                new_board = make_move(board_state, move)
                eval_score = minimax(new_board, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in moves:
                new_board = make_move(board_state, move)
                eval_score = minimax(new_board, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    # Try deeper searches if time permits
    best_move = legal_moves[0] if legal_moves else None
    best_value = -float('inf') if to_play == 'white' else float('inf')
    
    # Simple move ordering
    ordered = order_moves(legal_moves, board)
    
    for move in ordered:
        new_board = make_move(board, move)
        # Use depth 2 search
        score = minimax(new_board, 2, -float('inf'), float('inf'), to_play == 'black')
        
        if to_play == 'white':
            if score > best_value:
                best_value = score
                best_move = move
        else:
            if score < best_value:
                best_value = score
                best_move = move
    
    return best_move if best_move else legal_moves[0]


def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    """
    Select the best chess move using material and positional evaluation.
    Prioritizes checkmates, then captures, checks, and promotions.
    Evaluates resulting positions with simple heuristics.
    """
    # Quick check for immediate checkmate
    for move in legal_moves:
        if move.endswith('#'):
            return move, memory
    
    # Parse board into 8x8 grid
    board = _parse_board(pieces)
    is_white = to_play == 'white'
    
    # Evaluate each legal move
    best_move = None
    best_score = float('-inf')
    
    for move in legal_moves:
        # Apply move to get resulting board
        new_board = _apply_move(board, move, is_white)
        
        # Evaluate position from White's perspective
        score = _evaluate_board(new_board)
        
        # Flip perspective if we're Black
        if not is_white:
            score = -score
        
        # Update best move
        if score > best_score:
            best_score = score
            best_move = move
    
    # Fallback to first move if something went wrong
    if best_move is None:
        best_move = legal_moves[0]
    
    return best_move, memory


def _parse_board(pieces: dict[str, str]) -> None:
    """Convert pieces dictionary to 8x8 board representation."""
    board = [[None] * 8 for _ in range(8)]
    for square, piece in pieces.items():
        file = ord(square[0]) - ord('a')
        rank = int(square[1]) - 1
        board[rank][file] = piece
    return board


def _apply_move(board: list[list[str | None]], move: str, is_white: bool) -> None:
    """Apply a SAN-style move to the board and return new board state."""
    new_board = [row[:] for row in board]
    clean_move = move.replace('+', '').replace('#', '')
    
    # Handle castling
    if clean_move == 'O-O':
        rank = 0 if is_white else 7
        # Move king
        new_board[rank][4] = None
        new_board[rank][6] = ('w' if is_white else 'b') + 'K'
        # Move rook
        new_board[rank][7] = None
        new_board[rank][5] = ('w' if is_white else 'b') + 'R'
        return new_board
    elif clean_move == 'O-O-O':
        rank = 0 if is_white else 7
        # Move king
        new_board[rank][4] = None
        new_board[rank][2] = ('w' if is_white else 'b') + 'K'
        # Move rook
        new_board[rank][0] = None
        new_board[rank][3] = ('w' if is_white else 'b') + 'R'
        return new_board
    
    # Handle promotion
    promotion = None
    if '=' in clean_move:
        parts = clean_move.split('=')
        clean_move = parts[0]
        promotion = parts[1]
    
    # Extract destination square (last two characters)
    dest_sq = clean_move[-2:]
    dest_file = ord(dest_sq[0]) - ord('a')
    dest_rank = int(dest_sq[1]) - 1
    
    # Determine piece type
    if clean_move[0].isupper() and clean_move[0] not in 'O':
        piece_type = clean_move[0]
    else:
        piece_type = 'P'
    
    # Find and move the piece (brute-force search for source)
    prefix = 'w' if is_white else 'b'
    for rank in range(8):
        for file in range(8):
            piece = new_board[rank][file]
            if piece and piece[0] == prefix and piece[1] == piece_type:
                # Simple validation: check if this piece could move to dest
                # In practice, we trust the move is legal
                new_board[rank][file] = None
                if promotion:
                    new_board[dest_rank][dest_file] = prefix + promotion
                else:
                    new_board[dest_rank][dest_file] = prefix + piece_type
                return new_board
    
    return new_board


def _evaluate_board(board: list[list[str | None]]) -> float:
    """
    Evaluate board position from White's perspective.
    Returns material balance plus simple positional bonuses.
    """
    # Piece values
    piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
    
    material = 0
    center_control = 0
    king_safety = 0
    
    for rank in range(8):
        for file in range(8):
            piece = board[rank][file]
            if not piece:
                continue
            
            value = piece_values[piece[1]]
            
            # Material count
            if piece[0] == 'w':
                material += value
            else:
                material -= value
            
            # Center control bonus
            if piece[1] != 'K':
                if (2 <= file <= 5) and (2 <= rank <= 5):
                    center_bonus = 0.1 if piece[1] == 'P' else 0.05
                    if piece[0] == 'w':
                        center_control += center_bonus
                    else:
                        center_control -= center_bonus
            
            # King safety (penalty for central king)
            if piece[1] == 'K':
                king_dist = max(abs(rank - 0 if piece[0] == 'w' else rank - 7),
                               abs(file - 4))
                safety = -0.1 * king_dist if king_dist > 1 else 0.1
                if piece[0] == 'w':
                    king_safety += safety
                else:
                    king_safety -= safety
    
    return material + center_control + king_safety


def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    # Create the board from the given piece lists
    board = create_board(my_men, my_kings, opp_men, opp_kings, color)
    
    # Generate all legal moves for the current player
    all_moves = generate_all_moves(board, color)
    
    # Separate capture moves and simple moves
    capture_moves = [move for move in all_moves if is_capture_move(move)]
    simple_moves = [move for move in all_moves if not is_capture_move(move)]
    
    # If capture moves are available, use them; otherwise, use simple moves
    legal_moves = capture_moves if capture_moves else simple_moves
    
    # If no legal moves are available, return a default move (should not happen in valid games)
    if not legal_moves:
        return ((0, 0), (0, 1))  # fallback, but games should always have moves
    
    best_move = None
    best_score = float('inf')  # We want to minimize the opponent's score
    
    # Evaluate each legal move
    for move in legal_moves:
        new_board = apply_move(board, move)
        # After the move, it is the opponent's turn
        opponent_color = 'b' if color == 'w' else 'w'
        score = evaluate_board(new_board, opponent_color)
        if score < best_score:
            best_score = score
            best_move = move
    
    return best_move

def create_board(my_men, my_kings, opp_men, opp_kings, color):
    """Create an 8x8 board from the piece lists."""
    board = [[None for _ in range(8)] for _ in range(8)]
    # Define piece symbols based on color
    if color == 'b':
        my_man_symbol = 'bm'
        my_king_symbol = 'bk'
        opp_man_symbol = 'wm'
        opp_king_symbol = 'wk'
    else:  # color == 'w'
        my_man_symbol = 'wm'
        my_king_symbol = 'wk'
        opp_man_symbol = 'bm'
        opp_king_symbol = 'bk'
    
    # Place my pieces
    for (r, c) in my_men:
        board[r][c] = my_man_symbol
    for (r, c) in my_kings:
        board[r][c] = my_king_symbol
    
    # Place opponent pieces
    for (r, c) in opp_men:
        board[r][c] = opp_man_symbol
    for (r, c) in opp_kings:
        board[r][c] = opp_king_symbol
    
    return board

def generate_all_moves(board, color):
    """Generate all possible moves for the current player."""
    moves = []
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece is None:
                continue
            if is_my_piece(piece, color):
                piece_moves = generate_moves_for_piece(board, r, c, piece, color)
                moves.extend(piece_moves)
    return moves

def generate_moves_for_piece(board, r, c, piece, color):
    """Generate all legal moves for a single piece."""
    capture_moves = get_capture_moves_for_piece(board, r, c, piece, color)
    if capture_moves:
        return capture_moves  # Only capture moves are legal if available
    else:
        return get_simple_moves_for_piece(board, r, c, piece, color)

def get_capture_moves_for_piece(board, r, c, piece, color):
    """Generate all capture moves for a piece."""
    moves = []
    if piece in ['bm', 'wm']:  # men
        if color == 'b':
            capture_dirs = [(-1, -1), (-1, 1)]
        else:
            capture_dirs = [(1, -1), (1, 1)]
    else:  # kings
        capture_dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    
    for dr, dc in capture_dirs:
        intermediate_r = r + dr
        intermediate_c = c + dc
        dest_r = r + 2 * dr
        dest_c = c + 2 * dc
        
        # Check if intermediate and destination are on the board
        if 0 <= intermediate_r < 8 and 0 <= intermediate_c < 8 and 0 <= dest_r < 8 and 0 <= dest_c < 8:
            intermediate_piece = board[intermediate_r][intermediate_c]
            if intermediate_piece is not None and is_opponent_piece(intermediate_piece, color):
                if board[dest_r][dest_c] is None:
                    moves.append(((r, c), (dest_r, dest_c)))
    return moves

def get_simple_moves_for_piece(board, r, c, piece, color):
    """Generate all simple moves for a piece."""
    moves = []
    if piece in ['bm', 'wm']:  # men
        if color == 'b':
            simple_dirs = [(-1, -1), (-1, 1)]
        else:
            simple_dirs = [(1, -1), (1, 1)]
    else:  # kings
        simple_dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    
    for dr, dc in simple_dirs:
        new_r = r + dr
        new_c = c + dc
        if 0 <= new_r < 8 and 0 <= new_c < 8 and board[new_r][new_c] is None:
            moves.append(((r, c), (new_r, new_c)))
    return moves

def is_my_piece(piece, color):
    """Check if a piece belongs to the current player."""
    if color == 'b':
        return piece in ['bm', 'bk']
    else:
        return piece in ['wm', 'wk']

def is_opponent_piece(piece, color):
    """Check if a piece belongs to the opponent."""
    if color == 'b':
        return piece in ['wm', 'wk']
    else:
        return piece in ['bm', 'bk']

def is_capture_move(move):
    """Determine if a move is a capture move."""
    from_r, from_c = move[0]
    to_r, to_c = move[1]
    return abs(to_r - from_r) == 2  # Capture moves have a row difference of 2

def apply_move(board, move):
    """Apply a move to the board and return a new board state."""
    from_r, from_c = move[0]
    to_r, to_c = move[1]
    piece = board[from_r][from_c]
    if piece is None:
        raise ValueError("Invalid move: from square is empty")
    
    # Create a copy of the board
    new_board = [row[:] for row in board]
    
    # If capture move, remove the captured piece
    if is_capture_move(move):
        intermediate_r = (from_r + to_r) // 2
        intermediate_c = (from_c + to_c) // 2
        new_board[intermediate_r][intermediate_c] = None
    
    # Move the piece
    new_board[from_r][from_c] = None
    new_board[to_r][to_c] = piece
    
    # Check for kinging
    if piece in ['bm', 'wm']:  # man
        if piece == 'bm' and to_r == 0:  # black man reached king row
            new_board[to_r][to_c] = 'bk'
        elif piece == 'wm' and to_r == 7:  # white man reached king row
            new_board[to_r][to_c] = 'wk'
    
    return new_board

def evaluate_board(board, player_color):
    """Evaluate the board state from the perspective of the player to move."""
    my_score = 0
    opp_score = 0
    
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece is None:
                continue
            if is_my_piece(piece, player_color):
                if piece in ['bm', 'wm']:  # man
                    my_score += 1
                else:  # king
                    my_score += 3
            else:
                if piece in ['bm', 'wm']:  # man
                    opp_score += 1
                else:  # king
                    opp_score += 3
    
    # Score is from the perspective of player_color: positive is good for player_color
    return my_score - opp_score

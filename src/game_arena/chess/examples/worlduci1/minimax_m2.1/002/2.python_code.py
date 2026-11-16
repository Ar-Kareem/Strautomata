
def policy(pieces: dict[str, str], to_play: str) -> str:
    # Define piece values for evaluation
    piece_values = {
        'P': 1,
        'N': 3,
        'B': 3,
        'R': 5,
        'Q': 9,
        'K': 0
    }
    
    # Convert pieces dictionary to 8x8 board
    board = [[None] * 8 for _ in range(8)]
    for square, piece in pieces.items():
        file = square[0]
        rank = int(square[1])
        row = 8 - rank
        col = ord(file) - ord('a')
        board[row][col] = piece
    
    # Generate all legal moves for the current player
    legal_moves = generate_legal_moves(board, to_play)
    
    if not legal_moves:
        return None  # Should not happen, but handle no moves case
    
    # Evaluate each move and select the best one
    best_move = None
    best_score = -float('inf')
    for move in legal_moves:
        score = evaluate_move(board, move, to_play, piece_values)
        if score > best_score:
            best_score = score
            best_move = move
    
    # Convert best_move to UCI string
    from_row, from_col, to_row, to_col, promo = best_move
    from_square = chr(ord('a') + from_col) + str(8 - from_row)
    to_square = chr(ord('a') + to_col) + str(8 - to_row)
    if promo is not None:
        return from_square + to_square + promo
    else:
        return from_square + to_square

def generate_legal_moves(board, player):
    pseudo_legal_moves = generate_pseudo_legal_moves(board, player)
    legal_moves = []
    for move in pseudo_legal_moves:
        if is_move_legal(board, move, player):
            legal_moves.append(move)
    return legal_moves

def generate_pseudo_legal_moves(board, player):
    moves = []
    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if piece is not None and piece[0] == player[0]:
                piece_moves = get_piece_moves(board, row, col)
                for move in piece_moves:
                    new_row, new_col, promo = move
                    moves.append((row, col, new_row, new_col, promo))
    return moves

def get_piece_moves(board, row, col):
    piece = board[row][col]
    piece_type = piece[1]
    
    if piece_type == 'P':
        return get_pawn_moves(board, row, col)
    elif piece_type == 'N':
        return get_knight_moves(board, row, col)
    elif piece_type == 'B':
        return get_bishop_moves(board, row, col)
    elif piece_type == 'R':
        return get_rook_moves(board, row, col)
    elif piece_type == 'Q':
        return get_queen_moves(board, row, col)
    elif piece_type == 'K':
        return get_king_moves(board, row, col)
    else:
        return []

def get_pawn_moves(board, row, col):
    piece = board[row][col]
    color = piece[0]
    moves = []
    
    if color == 'w':
        direction = -1
        start_row = 6
    else:
        direction = 1
        start_row = 1
    
    # Forward one square
    new_row = row + direction
    if 0 <= new_row < 8:
        if board[new_row][col] is None:
            if new_row == 0 or new_row == 7:
                for promo in ['q', 'r', 'b', 'n']:
                    moves.append((new_row, col, promo))
            else:
                moves.append((new_row, col, None))
            
            # Forward two squares from start
            if row == start_row:
                new_row2 = row + 2 * direction
                if 0 <= new_row2 < 8 and board[new_row2][col] is None:
                    moves.append((new_row2, col, None))
    
    # Captures
    for dc in [-1, 1]:
        new_col = col + dc
        new_row = row + direction
        if 0 <= new_row < 8 and 0 <= new_col < 8:
            target = board[new_row][new_col]
            if target is not None and target[0] != color:
                if new_row == 0 or new_row == 7:
                    for promo in ['q', 'r', 'b', 'n']:
                        moves.append((new_row, new_col, promo))
                else:
                    moves.append((new_row, new_col, None))
    
    return moves

def get_knight_moves(board, row, col):
    moves = []
    directions = [(2,1), (2,-1), (-2,1), (-2,-1), (1,2), (1,-2), (-1,2), (-1,-2)]
    piece = board[row][col]
    color = piece[0]
    
    for dr, dc in directions:
        new_row = row + dr
        new_col = col + dc
        if 0 <= new_row < 8 and 0 <= new_col < 8:
            target = board[new_row][new_col]
            if target is None or target[0] != color:
                moves.append((new_row, new_col, None))
    
    return moves

def get_bishop_moves(board, row, col):
    moves = []
    directions = [(1,1), (1,-1), (-1,1), (-1,-1)]
    piece = board[row][col]
    color = piece[0]
    
    for dr, dc in directions:
        new_row = row + dr
        new_col = col + dc
        while 0 <= new_row < 8 and 0 <= new_col < 8:
            target = board[new_row][new_col]
            if target is None:
                moves.append((new_row, new_col, None))
            else:
                if target[0] != color:
                    moves.append((new_row, new_col, None))
                break
            new_row += dr
            new_col += dc
    
    return moves

def get_rook_moves(board, row, col):
    moves = []
    directions = [(1,0), (-1,0), (0,1), (0,-1)]
    piece = board[row][col]
    color = piece[0]
    
    for dr, dc in directions:
        new_row = row + dr
        new_col = col + dc
        while 0 <= new_row < 8 and 0 <= new_col < 8:
            target = board[new_row][new_col]
            if target is None:
                moves.append((new_row, new_col, None))
            else:
                if target[0] != color:
                    moves.append((new_row, new_col, None))
                break
            new_row += dr
            new_col += dc
    
    return moves

def get_queen_moves(board, row, col):
    return get_bishop_moves(board, row, col) + get_rook_moves(board, row, col)

def get_king_moves(board, row, col):
    moves = []
    directions = [(1,0), (-1,0), (0,1), (0,-1), (1,1), (1,-1), (-1,1), (-1,-1)]
    piece = board[row][col]
    color = piece[0]
    
    for dr, dc in directions:
        new_row = row + dr
        new_col = col + dc
        if 0 <= new_row < 8 and 0 <= new_col < 8:
            target = board[new_row][new_col]
            if target is None or target[0] != color:
                moves.append((new_row, new_col, None))
    
    return moves

def is_move_legal(board, move, player):
    new_board = [row[:] for row in board]
    from_row, from_col, to_row, to_col, promo = move
    piece = new_board[from_row][from_col]
    new_board[to_row][to_col] = piece
    new_board[from_row][from_col] = None
    
    if promo is not None:
        color = piece[0]
        new_board[to_row][to_col] = color + promo.upper()
    
    return not is_king_in_check(new_board, player)

def is_king_in_check(board, player):
    king_piece = player[0] + 'K'
    king_row, king_col = None, None
    for row in range(8):
        for col in range(8):
            if board[row][col] == king_piece:
                king_row, king_col = row, col
                break
        if king_row is not None:
            break
    
    if king_row is None:
        return False
    
    opponent = 'black' if player == 'white' else 'white'
    opponent_moves = generate_pseudo_legal_moves(board, opponent)
    
    for move in opponent_moves:
        _, _, to_row, to_col, _ = move
        if to_row == king_row and to_col == king_col:
            return True
    
    return False

def is_checkmate(board, player):
    opponent = 'black' if player == 'white' else 'white'
    opponent_moves = generate_legal_moves(board, opponent)
    if len(opponent_moves) == 0:
        return is_king_in_check(board, opponent)
    return False

def evaluate_move(board, move, player, piece_values):
    new_board = [row[:] for row in board]
    from_row, from_col, to_row, to_col, promo = move
    piece = new_board[from_row][from_col]
    captured_piece = new_board[to_row][to_col]
    new_board[to_row][to_col] = piece
    new_board[from_row][from_col] = None
    
    if promo is not None:
        color = piece[0]
        new_board[to_row][to_col] = color + promo.upper()
    
    score = 0
    
    if is_checkmate(new_board, player):
        score += 1000
        return score
    
    if captured_piece is not None:
        score += piece_values[captured_piece[1]]
    
    if is_king_in_check(new_board, player):
        score -= 10
    
    center_squares = [(4,4), (4,3), (3,4), (3,3)]
    if (to_row, to_col) in center_squares:
        score += 0.5
    
    if player == 'white' and from_row == 7:
        score += 0.5
    elif player == 'black' and from_row == 0:
        score += 0.5
    
    return score

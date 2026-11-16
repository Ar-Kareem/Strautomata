
def policy(pieces: dict[str, str], to_play: str) -> str:
    import random
    
    # Generate legal moves
    legal_moves = generate_legal_moves(pieces, to_play)
    
    if not legal_moves:
        return "0000"  # Should never happen in a legal position
    
    # Evaluate each move and pick the best one
    best_score = float('-inf')
    best_moves = []
    
    for move in legal_moves:
        score = evaluate_move(pieces, move, to_play)
        if score > best_score:
            best_score = score
            best_moves = [move]
        elif score == best_score:
            best_moves.append(move)
    
    return random.choice(best_moves)


def generate_legal_moves(pieces: dict[str, str], to_play: str) -> list[str]:
    """Generate all legal moves for the current position."""
    color_prefix = 'w' if to_play == 'white' else 'b'
    moves = []
    
    for square, piece in pieces.items():
        if piece[0] == color_prefix[0]:
            piece_type = piece[1]
            moves.extend(get_piece_moves(square, piece_type, pieces, color_prefix[0]))
    
    # Filter out moves that leave king in check
    legal = []
    for move in moves:
        new_pieces = apply_move(pieces.copy(), move)
        if not is_in_check(new_pieces, color_prefix[0]):
            legal.append(move)
    
    return legal


def get_piece_moves(square, piece_type, pieces, color):
    """Get pseudo-legal moves for a piece."""
    moves = []
    file, rank = ord(square[0]) - ord('a'), int(square[1]) - 1
    
    if piece_type == 'P':
        moves.extend(get_pawn_moves(file, rank, pieces, color))
    elif piece_type == 'N':
        moves.extend(get_knight_moves(file, rank, pieces, color))
    elif piece_type == 'B':
        moves.extend(get_bishop_moves(file, rank, pieces, color))
    elif piece_type == 'R':
        moves.extend(get_rook_moves(file, rank, pieces, color))
    elif piece_type == 'Q':
        moves.extend(get_queen_moves(file, rank, pieces, color))
    elif piece_type == 'K':
        moves.extend(get_king_moves(file, rank, pieces, color))
    
    return moves


def get_pawn_moves(file, rank, pieces, color):
    moves = []
    square = chr(file + ord('a')) + str(rank + 1)
    direction = 1 if color == 'w' else -1
    start_rank = 1 if color == 'w' else 6
    promotion_rank = 7 if color == 'w' else 0
    
    # Forward move
    new_rank = rank + direction
    if 0 <= new_rank <= 7:
        target = chr(file + ord('a')) + str(new_rank + 1)
        if target not in pieces:
            if new_rank == promotion_rank:
                for promo in ['q', 'r', 'b', 'n']:
                    moves.append(square + target + promo)
            else:
                moves.append(square + target)
            
            # Double move from start
            if rank == start_rank:
                new_rank2 = rank + 2 * direction
                target2 = chr(file + ord('a')) + str(new_rank2 + 1)
                if target2 not in pieces:
                    moves.append(square + target2)
    
    # Captures
    for df in [-1, 1]:
        new_file, new_rank = file + df, rank + direction
        if 0 <= new_file <= 7 and 0 <= new_rank <= 7:
            target = chr(new_file + ord('a')) + str(new_rank + 1)
            if target in pieces and pieces[target][0] != color:
                if new_rank == promotion_rank:
                    for promo in ['q', 'r', 'b', 'n']:
                        moves.append(square + target + promo)
                else:
                    moves.append(square + target)
    
    return moves


def get_knight_moves(file, rank, pieces, color):
    moves = []
    square = chr(file + ord('a')) + str(rank + 1)
    deltas = [(-2,-1), (-2,1), (-1,-2), (-1,2), (1,-2), (1,2), (2,-1), (2,1)]
    
    for df, dr in deltas:
        new_file, new_rank = file + df, rank + dr
        if 0 <= new_file <= 7 and 0 <= new_rank <= 7:
            target = chr(new_file + ord('a')) + str(new_rank + 1)
            if target not in pieces or pieces[target][0] != color:
                moves.append(square + target)
    
    return moves


def get_sliding_moves(file, rank, pieces, color, directions):
    moves = []
    square = chr(file + ord('a')) + str(rank + 1)
    
    for df, dr in directions:
        for dist in range(1, 8):
            new_file, new_rank = file + df * dist, rank + dr * dist
            if not (0 <= new_file <= 7 and 0 <= new_rank <= 7):
                break
            target = chr(new_file + ord('a')) + str(new_rank + 1)
            if target in pieces:
                if pieces[target][0] != color:
                    moves.append(square + target)
                break
            moves.append(square + target)
    
    return moves


def get_bishop_moves(file, rank, pieces, color):
    return get_sliding_moves(file, rank, pieces, color, [(-1,-1), (-1,1), (1,-1), (1,1)])


def get_rook_moves(file, rank, pieces, color):
    return get_sliding_moves(file, rank, pieces, color, [(0,-1), (0,1), (-1,0), (1,0)])


def get_queen_moves(file, rank, pieces, color):
    return get_sliding_moves(file, rank, pieces, color, 
                            [(0,-1), (0,1), (-1,0), (1,0), (-1,-1), (-1,1), (1,-1), (1,1)])


def get_king_moves(file, rank, pieces, color):
    moves = []
    square = chr(file + ord('a')) + str(rank + 1)
    
    for df in [-1, 0, 1]:
        for dr in [-1, 0, 1]:
            if df == 0 and dr == 0:
                continue
            new_file, new_rank = file + df, rank + dr
            if 0 <= new_file <= 7 and 0 <= new_rank <= 7:
                target = chr(new_file + ord('a')) + str(new_rank + 1)
                if target not in pieces or pieces[target][0] != color:
                    moves.append(square + target)
    
    return moves


def apply_move(pieces, move):
    """Apply a move and return new position."""
    new_pieces = pieces.copy()
    from_sq = move[:2]
    to_sq = move[2:4]
    
    piece = new_pieces[from_sq]
    del new_pieces[from_sq]
    
    # Handle promotion
    if len(move) == 5:
        promo_piece = move[4].upper()
        new_pieces[to_sq] = piece[0] + promo_piece
    else:
        new_pieces[to_sq] = piece
    
    return new_pieces


def is_in_check(pieces, color):
    """Check if the given color's king is in check."""
    # Find king
    king_square = None
    for square, piece in pieces.items():
        if piece == color + 'K':
            king_square = square
            break
    
    if not king_square:
        return False
    
    # Check if any enemy piece attacks the king
    enemy_color = 'b' if color == 'w' else 'w'
    for square, piece in pieces.items():
        if piece[0] == enemy_color:
            enemy_moves = get_piece_moves(square, piece[1], pieces, enemy_color)
            for move in enemy_moves:
                if move[2:4] == king_square:
                    return True
    
    return False


def evaluate_move(pieces, move, to_play):
    """Evaluate how good a move is."""
    new_pieces = apply_move(pieces.copy(), move)
    color = 'w' if to_play == 'white' else 'b'
    enemy_color = 'b' if color == 'w' else 'w'
    
    score = 0
    
    # Check if this move delivers checkmate
    enemy_moves = generate_legal_moves(new_pieces, 'black' if to_play == 'white' else 'white')
    if not enemy_moves:
        if is_in_check(new_pieces, enemy_color):
            return 100000  # Checkmate!
    
    # Material evaluation
    piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
    
    # Capture value
    to_sq = move[2:4]
    if to_sq in pieces:
        captured = pieces[to_sq][1]
        score += piece_values.get(captured, 0) * 100
    
    # Material balance
    my_material = sum(piece_values.get(p[1], 0) for p in new_pieces.values() if p[0] == color)
    enemy_material = sum(piece_values.get(p[1], 0) for p in new_pieces.values() if p[0] == enemy_color)
    score += (my_material - enemy_material) * 10
    
    # Center control
    center_squares = ['d4', 'd5', 'e4', 'e5']
    if to_sq in center_squares:
        score += 5
    
    # King safety penalty if king moves early
    from_sq = move[:2]
    if pieces[from_sq][1] == 'K':
        score -= 10
    
    # Prefer developing pieces
    back_rank = '1' if color == 'w' else '8'
    if from_sq[1] == back_rank and to_sq[1] != back_rank:
        score += 3
    
    return score

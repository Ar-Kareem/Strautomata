
import sys
import math
from collections import defaultdict

# Piece values for material evaluation
PIECE_VALUES = {
    'P': 1,
    'N': 3,
    'B': 3,
    'R': 5,
    'Q': 9,
    'K': 0  # King cannot be captured
}

# Optimal promotion is always queen
PROMOTION_PIECE = 'q'

# Central squares bonus
CENTRAL_SQUARES = ['d4', 'e4', 'd5', 'e5']

def square_to_coords(square):
    """Convert algebraic square to (file, rank) indices."""
    file = ord(square[0]) - ord('a')
    rank = int(square[1]) - 1
    return (file, rank)

def coords_to_square(file, rank):
    """Convert (file, rank) indices to algebraic square."""
    return chr(file + ord('a')) + str(rank + 1)

def generate_pawn_moves(square, board, color):
    """Generate pawn moves including captures and promotions."""
    moves = []
    file, rank = square_to_coords(square)
    direction = 1 if color == 'w' else -1
    start_rank = 1 if color == 'w' else 6

    # Single push
    new_rank = rank + direction
    if 0 <= new_rank < 8:
        forward_sq = coords_to_square(file, new_rank)
        if forward_sq not in board:
            moves.append(forward_sq)

            # Double push from starting position
            if rank == start_rank:
                double_rank = rank + 2 * direction
                if 0 <= double_rank < 8:
                    double_sq = coords_to_square(file, double_rank)
                    if double_sq not in board:
                        moves.append(double_sq)

    # Captures
    for d_file in (-1, 1):
        cap_file = file + d_file
        cap_rank = rank + direction
        if 0 <= cap_file < 8 and 0 <= cap_rank < 8:
            cap_sq = coords_to_square(cap_file, cap_rank)
            if cap_sq in board and board[cap_sq][0] != color:
                moves.append(cap_sq)

    # Promotions
    promo_rank = 7 if color == 'w' else 0
    if rank + direction == promo_rank:
        promo_moves = []
        for move in moves:
            promo_moves.append(move + PROMOTION_PIECE)
        return promo_moves

    return moves

def generate_knight_moves(square, board, color):
    """Generate knight L-shaped moves."""
    moves = []
    file, rank = square_to_coords(square)
    knight_moves = [
        (2, 1), (1, 2), (-1, 2), (-2, 1),
        (-2, -1), (-1, -2), (1, -2), (2, -1)
    ]

    for df, dr in knight_moves:
        new_file = file + df
        new_rank = rank + dr
        if 0 <= new_file < 8 and 0 <= new_rank < 8:
            new_sq = coords_to_square(new_file, new_rank)
            if new_sq not in board or board[new_sq][0] != color:
                moves.append(new_sq)

    return moves

def generate_line_moves(square, board, color, directions):
    """Generate sliding moves (bishop/rook/queen)."""
    moves = []
    file, rank = square_to_coords(square)

    for dx, dy in directions:
        step = 1
        while True:
            new_file = file + dx * step
            new_rank = rank + dy * step
            if not (0 <= new_file < 8 and 0 <= new_rank < 8):
                break

            new_sq = coords_to_square(new_file, new_rank)
            if new_sq not in board:
                moves.append(new_sq)
            else:
                if board[new_sq][0] != color:
                    moves.append(new_sq)
                break
            step += 1

    return moves

def generate_king_moves(square, board, color):
    """Generate king moves (castling not implemented)."""
    moves = []
    file, rank = square_to_coords(square)

    for df in (-1, 0, 1):
        for dr in (-1, 0, 1):
            if df == 0 and dr == 0:
                continue
            new_file = file + df
            new_rank = rank + dr
            if 0 <= new_file < 8 and 0 <= new_rank < 8:
                new_sq = coords_to_square(new_file, new_rank)
                if new_sq not in board or board[new_sq][0] != color:
                    moves.append(new_sq)

    return moves

def evaluate_move(move, board, color):
    """Score move based on material, position, and promotions."""
    from_sq = move[:2]
    to_sq = move[2:4]

    # Capture evaluation
    captured_value = 0
    if to_sq in board:
        captured_piece = board[to_sq][1]
        captured_value = PIECE_VALUES.get(captured_piece, 0)

    # Promotion bonus
    promotion_bonus = 9 if len(move) == 5 else 0

    # Positional evaluation
    positional_bonus = 0.1 * (1 if to_sq in CENTRAL_SQUARES else 0)

    # King safety penalty
    moved_piece = board[from_sq][1]
    king_penalty = 0
    if moved_piece == 'K' and to_sq in CENTRAL_SQUARES:
        king_penalty = 0.5  # Prefer king safety in middlegame

    return captured_value + promotion_bonus + positional_bonus - king_penalty

def policy(pieces, to_play):
    color = 'w' if to_play == 'white' else 'b'
    board = pieces.copy()

    # Generate all pseudo-legal moves
    all_moves = []
    for square, piece_code in board.items():
        if piece_code[0] != color:
            continue

        piece_type = piece_code[1]
        if piece_type == 'P':
            moves = generate_pawn_moves(square, board, color)
        elif piece_type == 'N':
            moves = generate_knight_moves(square, board, color)
        elif piece_type == 'B':
            moves = generate_line_moves(square, board, color, [(1,1), (1,-1), (-1,1), (-1,-1)])
        elif piece_type == 'R':
            moves = generate_line_moves(square, board, color, [(0,1), (1,0), (0,-1), (-1,0)])
        elif piece_type == 'Q':
            directions = [(1,0), (0,1), (-1,0), (0,-1), (1,1), (1,-1), (-1,1), (-1,-1)]
            moves = generate_line_moves(square, board, color, directions)
        elif piece_type == 'K':
            moves = generate_king_moves(square, board, color)
        else:
            continue

        # Format moves as UCI strings
        for move in moves:
            # Skip promotions without piece suffix
            if len(move) == 2:
                all_moves.append(square + move)
            else:  # Promotions include piece suffix
                all_moves.append(square + move)

    # If no moves available (shouldn't happen), default to first square
    if not all_moves:
        return list(board.keys())[0] + list(board.keys())[0]  # Fallback

    # Evaluate and select best move
    best_move = all_moves[0]
    best_score = -math.inf

    for move in all_moves:
        score = evaluate_move(move, board, color)
        if score > best_score:
            best_score = score
            best_move = move

    return best_move

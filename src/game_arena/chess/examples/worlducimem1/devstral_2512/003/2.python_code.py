
import random
from collections import defaultdict

# Standard piece values
PIECE_VALUES = {
    'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0
}

# Square values (center control is more important)
SQUARE_VALUES = {
    'a1': 0, 'b1': 0, 'c1': 0, 'd1': 0, 'e1': 0, 'f1': 0, 'g1': 0, 'h1': 0,
    'a2': 1, 'b2': 1, 'c2': 1, 'd2': 1, 'e2': 1, 'f2': 1, 'g2': 1, 'h2': 1,
    'a3': 2, 'b3': 2, 'c3': 2, 'd3': 2, 'e3': 2, 'f3': 2, 'g3': 2, 'h3': 2,
    'a4': 3, 'b4': 3, 'c4': 3, 'd4': 3, 'e4': 3, 'f4': 3, 'g4': 3, 'h4': 3,
    'a5': 3, 'b5': 3, 'c5': 3, 'd5': 3, 'e5': 3, 'f5': 3, 'g5': 3, 'h5': 3,
    'a6': 2, 'b6': 2, 'c6': 2, 'd6': 2, 'e6': 2, 'f6': 2, 'g6': 2, 'h6': 2,
    'a7': 1, 'b7': 1, 'c7': 1, 'd7': 1, 'e7': 1, 'f7': 1, 'g7': 1, 'h7': 1,
    'a8': 0, 'b8': 0, 'c8': 0, 'd8': 0, 'e8': 0, 'f8': 0, 'g8': 0, 'h8': 0
}

# Center squares
CENTER_SQUARES = {'d4', 'e4', 'd5', 'e5'}

def evaluate_position(pieces, to_play):
    """Evaluate the current position from the perspective of the player to move."""
    score = 0
    white_material = 0
    black_material = 0
    white_pawns = set()
    black_pawns = set()

    for square, piece in pieces.items():
        color = piece[0]
        piece_type = piece[1]
        value = PIECE_VALUES[piece_type]

        if color == 'w':
            white_material += value
            if piece_type == 'P':
                white_pawns.add(square)
            # Bonus for piece activity
            score += SQUARE_VALUES[square] * 0.1
            # Bonus for center control
            if square in CENTER_SQUARES:
                score += 0.5
        else:
            black_material -= value
            if piece_type == 'P':
                black_pawns.add(square)
            # Penalty for opponent's piece activity
            score -= SQUARE_VALUES[square] * 0.1
            # Penalty for opponent's center control
            if square in CENTER_SQUARES:
                score -= 0.5

    # Material balance
    score += white_material - black_material

    # Pawn structure evaluation
    score += evaluate_pawn_structure(white_pawns, black_pawns)

    return score if to_play == 'white' else -score

def evaluate_pawn_structure(white_pawns, black_pawns):
    """Evaluate pawn structure."""
    score = 0

    # Bonus for connected pawns
    for pawn in white_pawns:
        file = pawn[0]
        rank = int(pawn[1])
        # Check adjacent files for pawns
        if rank > 1:
            if f"{chr(ord(file)-1)}{rank-1}" in white_pawns:
                score += 0.2
            if f"{chr(ord(file)+1)}{rank-1}" in white_pawns:
                score += 0.2

    for pawn in black_pawns:
        file = pawn[0]
        rank = int(pawn[1])
        # Check adjacent files for pawns
        if rank < 8:
            if f"{chr(ord(file)-1)}{rank+1}" in black_pawns:
                score -= 0.2
            if f"{chr(ord(file)+1)}{rank+1}" in black_pawns:
                score -= 0.2

    # Penalty for isolated pawns
    for pawn in white_pawns:
        file = pawn[0]
        has_neighbor = False
        for df in [-1, 1]:
            neighbor_file = chr(ord(file) + df)
            if neighbor_file >= 'a' and neighbor_file <= 'h':
                for rank in range(1, 9):
                    if f"{neighbor_file}{rank}" in white_pawns:
                        has_neighbor = True
                        break
        if not has_neighbor:
            score -= 0.3

    for pawn in black_pawns:
        file = pawn[0]
        has_neighbor = False
        for df in [-1, 1]:
            neighbor_file = chr(ord(file) + df)
            if neighbor_file >= 'a' and neighbor_file <= 'h':
                for rank in range(1, 9):
                    if f"{neighbor_file}{rank}" in black_pawns:
                        has_neighbor = True
                        break
        if not has_neighbor:
            score += 0.3

    return score

def is_capture(move, pieces):
    """Check if a move is a capture."""
    dest = move[2:4]
    return dest in pieces

def get_captured_piece(move, pieces):
    """Get the piece that would be captured by this move."""
    dest = move[2:4]
    return pieces.get(dest, None)

def get_piece_type(piece_code):
    """Get the piece type from a piece code."""
    return piece_code[1] if piece_code else None

def evaluate_move(move, pieces, to_play):
    """Evaluate a single move."""
    score = 0
    from_square = move[:2]
    to_square = move[2:4]
    piece = pieces.get(from_square, None)

    if not piece:
        return -float('inf')

    # Check if this is a capture
    captured = get_captured_piece(move, pieces)
    if captured:
        # Material gain
        captured_value = PIECE_VALUES.get(get_piece_type(captured), 0)
        moving_value = PIECE_VALUES.get(get_piece_type(piece), 0)
        score += captured_value - moving_value

        # Bonus for capturing a higher value piece
        if captured_value > moving_value:
            score += 0.5

    # Bonus for moving to a more valuable square
    score += (SQUARE_VALUES[to_square] - SQUARE_VALUES[from_square]) * 0.1

    # Bonus for moving to center
    if to_square in CENTER_SQUARES:
        score += 0.3

    # Penalty for moving king (unless castling)
    if get_piece_type(piece) == 'K' and abs(ord(from_square[0]) - ord(to_square[0])) <= 1:
        score -= 0.5

    # Bonus for pawn promotion
    if get_piece_type(piece) == 'P' and len(move) == 5:
        promo_piece = move[4]
        score += PIECE_VALUES[promo_piece] - 1  # -1 for the pawn value

    return score

def policy(pieces, to_play, memory):
    """
    Select the best move based on the current position.

    Args:
        pieces: Dictionary mapping squares to piece codes
        to_play: 'white' or 'black'
        memory: Dictionary to store state between calls

    Returns:
        tuple: (best_move, updated_memory)
    """
    # Initialize memory if empty
    if not memory:
        memory = {
            'move_history': [],
            'game_phase': 'opening',  # opening, middlegame, endgame
            'piece_counts': {'white': {'Q': 1, 'R': 2, 'B': 2, 'N': 2, 'P': 8},
                            'black': {'Q': 1, 'R': 2, 'B': 2, 'N': 2, 'P': 8}}
        }

    # Update piece counts
    white_pieces = {v[1] for k, v in pieces.items() if v[0] == 'w'}
    black_pieces = {v[1] for k, v in pieces.items() if v[0] == 'b'}

    for piece in ['Q', 'R', 'B', 'N', 'P']:
        memory['piece_counts']['white'][piece] = white_pieces.count(piece)
        memory['piece_counts']['black'][piece] = black_pieces.count(piece)

    # Determine game phase
    total_pieces = sum(memory['piece_counts']['white'].values()) + sum(memory['piece_counts']['black'].values())
    if total_pieces > 20:
        memory['game_phase'] = 'opening'
    elif total_pieces > 10:
        memory['game_phase'] = 'middlegame'
    else:
        memory['game_phase'] = 'endgame'

    # Get legal moves (in a real implementation, these would be provided)
    # For this example, we'll assume legal_moves is available
    legal_moves = get_legal_moves(pieces, to_play)

    if not legal_moves:
        return (None, memory)

    # Evaluate each move
    move_scores = []
    for move in legal_moves:
        # Make a copy of pieces to simulate the move
        new_pieces = pieces.copy()

        # Remove the piece from the source square
        from_square = move[:2]
        piece = new_pieces.pop(from_square, None)

        # Handle captures
        to_square = move[2:4]
        if to_square in new_pieces:
            del new_pieces[to_square]

        # Place the piece on the destination square
        # Handle pawn promotion
        if len(move) == 5 and get_piece_type(piece) == 'P':
            promo_piece = move[4]
            new_pieces[to_square] = piece[0] + promo_piece
        else:
            new_pieces[to_square] = piece

        # Evaluate the resulting position
        score = evaluate_move(move, pieces, to_play)

        # Add some randomness to avoid being too predictable
        score += random.uniform(-0.1, 0.1)

        move_scores.append((move, score))

    # Sort moves by score
    move_scores.sort(key=lambda x: x[1], reverse=True)

    # Select the best move
    best_move = move_scores[0][0]

    # Update move history
    memory['move_history'].append(best_move)
    if len(memory['move_history']) > 10:
        memory['move_history'] = memory['move_history'][-10:]

    return (best_move, memory)

def get_legal_moves(pieces, to_play):
    """
    Generate legal moves for the current position.
    Note: In a real implementation, this would be provided by the game engine.
    This is a simplified version for demonstration.
    """
    legal_moves = []
    color = 'w' if to_play == 'white' else 'b'

    for square, piece in pieces.items():
        if piece[0] == color:
            piece_type = piece[1]
            if piece_type == 'P':
                legal_moves.extend(get_pawn_moves(square, piece, pieces))
            elif piece_type == 'N':
                legal_moves.extend(get_knight_moves(square, piece, pieces))
            elif piece_type == 'B':
                legal_moves.extend(get_bishop_moves(square, piece, pieces))
            elif piece_type == 'R':
                legal_moves.extend(get_rook_moves(square, piece, pieces))
            elif piece_type == 'Q':
                legal_moves.extend(get_queen_moves(square, piece, pieces))
            elif piece_type == 'K':
                legal_moves.extend(get_king_moves(square, piece, pieces))

    return legal_moves

def get_pawn_moves(square, piece, pieces):
    """Generate legal pawn moves."""
    moves = []
    color = piece[0]
    file = square[0]
    rank = int(square[1])
    direction = 1 if color == 'w' else -1

    # Forward move
    new_rank = rank + direction
    if 1 <= new_rank <= 8:
        new_square = f"{file}{new_rank}"
        if new_square not in pieces:
            moves.append(f"{square}{new_square}")
            # Double move from starting position
            if ((color == 'w' and rank == 2) or (color == 'b' and rank == 7)) and f"{file}{new_rank + direction}" not in pieces:
                moves.append(f"{square}{file}{new_rank + direction}")

    # Captures
    for df in [-1, 1]:
        new_file = chr(ord(file) + df)
        if 'a' <= new_file <= 'h':
            new_square = f"{new_file}{rank + direction}"
            if new_square in pieces and pieces[new_square][0] != color:
                moves.append(f"{square}{new_square}")
                # Promotion
                if (color == 'w' and new_rank == 8) or (color == 'b' and new_rank == 1):
                    for promo in ['q', 'r', 'b', 'n']:
                        moves.append(f"{square}{new_square}{promo}")

    return moves

def get_knight_moves(square, piece, pieces):
    """Generate legal knight moves."""
    moves = []
    color = piece[0]
    file = square[0]
    rank = int(square[1])

    knight_moves = [
        (2, 1), (2, -1), (-2, 1), (-2, -1),
        (1, 2), (1, -2), (-1, 2), (-1, -2)
    ]

    for df, dr in knight_moves:
        new_file = chr(ord(file) + df)
        new_rank = rank + dr
        if 'a' <= new_file <= 'h' and 1 <= new_rank <= 8:
            new_square = f"{new_file}{new_rank}"
            if new_square not in pieces or pieces[new_square][0] != color:
                moves.append(f"{square}{new_square}")

    return moves

def get_bishop_moves(square, piece, pieces):
    """Generate legal bishop moves."""
    moves = []
    color = piece[0]
    file = square[0]
    rank = int(square[1])

    directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]

    for df, dr in directions:
        for i in range(1, 8):
            new_file = chr(ord(file) + df * i)
            new_rank = rank + dr * i
            if not ('a' <= new_file <= 'h' and 1 <= new_rank <= 8):
                break
            new_square = f"{new_file}{new_rank}"
            if new_square in pieces:
                if pieces[new_square][0] != color:
                    moves.append(f"{square}{new_square}")
                break
            moves.append(f"{square}{new_square}")

    return moves

def get_rook_moves(square, piece, pieces):
    """Generate legal rook moves."""
    moves = []
    color = piece[0]
    file = square[0]
    rank = int(square[1])

    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    for df, dr in directions:
        for i in range(1, 8):
            new_file = chr(ord(file) + df * i)
            new_rank = rank + dr * i
            if not ('a' <= new_file <= 'h' and 1 <= new_rank <= 8):
                break
            new_square = f"{new_file}{new_rank}"
            if new_square in pieces:
                if pieces[new_square][0] != color:
                    moves.append(f"{square}{new_square}")
                break
            moves.append(f"{square}{new_square}")

    return moves

def get_queen_moves(square, piece, pieces):
    """Generate legal queen moves (combination of bishop and rook)."""
    return get_bishop_moves(square, piece, pieces) + get_rook_moves(square, piece, pieces)

def get_king_moves(square, piece, pieces):
    """Generate legal king moves."""
    moves = []
    color = piece[0]
    file = square[0]
    rank = int(square[1])

    for df in [-1, 0, 1]:
        for dr in [-1, 0, 1]:
            if df == 0 and dr == 0:
                continue
            new_file = chr(ord(file) + df)
            new_rank = rank + dr
            if 'a' <= new_file <= 'h' and 1 <= new_rank <= 8:
                new_square = f"{new_file}{new_rank}"
                if new_square not in pieces or pieces[new_square][0] != color:
                    moves.append(f"{square}{new_square}")

    return moves

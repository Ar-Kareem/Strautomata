
import numpy as np
from typing import Dict, Tuple, List

# Piece values (material)
PIECE_VALUES = {
    'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0  # King has no material value
}

# Directions for sliding pieces (rook, bishop, queen)
SLIDING_DIRECTIONS = {
    'R': [(0, 1), (1, 0), (0, -1), (-1, 0)],
    'B': [(1, 1), (-1, 1), (1, -1), (-1, -1)],
    'Q': [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, 1), (1, -1), (-1, -1)]
}

# Knight moves (delta)
KNIGHT_MOVES = [(1, 2), (2, 1), (-1, 2), (2, -1), (1, -2), (-1, -2), (-2, 1), (-2, -1)]

def square_to_rank_file(square: str) -> Tuple[int, int]:
    """Convert algebraic square (e.g., 'e4') to (rank, file) tuple (e.g., (4, 4))."""
    file = ord(square[0]) - ord('a')
    rank = int(square[1]) - 1
    return rank, file

def rank_file_to_square(rank: int, file: int) -> str:
    """Convert (rank, file) tuple back to algebraic square."""
    return chr(file + ord('a')) + str(rank + 1)

def parse_piece(piece_code: str) -> Tuple[str, str]:
    """Split piece code into color and type."""
    return piece_code[0], piece_code[1]

def is_sliding_piece(piece_type: str) -> bool:
    """Check if piece is a sliding piece (rook, bishop, queen)."""
    return piece_type in ['R', 'B', 'Q']

def is_knight(piece_type: str) -> bool:
    """Check if piece is a knight."""
    return piece_type == 'N'

def is_pawn(piece_type: str) -> bool:
    """Check if piece is a pawn."""
    return piece_type == 'P'

def is_king(piece_type: str) -> bool:
    """Check if piece is a king."""
    return piece_type == 'K'

def get_piece_value(piece_code: str) -> int:
    """Get material value of a piece."""
    _, piece_type = parse_piece(piece_code)
    return PIECE_VALUES[piece_type]

def evaluate_board(pieces: Dict[str, str], to_play: str) -> float:
    """
    Evaluate the board position using:
    - Material balance
    - King safety (distance to opponent's pieces, pawn shield)
    - Pawn structure (center control, passed pawns)
    - Piece mobility (number of legal moves)
    """
    color = to_play[0]
    opponent_color = 'b' if color == 'w' else 'w'
    score = 0.0

    # 1. Material balance
    material = sum(get_piece_value(piece) for piece in pieces.values() if piece[0] == color)
    opponent_material = sum(get_piece_value(piece) for piece in pieces.values() if piece[0] == opponent_color)
    score += (material - opponent_material) * 0.5  # Normalize

    # 2. King safety
    king_square = None
    for square, piece in pieces.items():
        if is_king(piece) and piece[0] == color:
            king_square = square
            break
    if king_square:
        king_rank, king_file = square_to_rank_file(king_square)
        # Distance to opponent's pieces (avoid being near them)
        opponent_pieces = [square for square, piece in pieces.items() if piece[0] == opponent_color]
        for square in opponent_pieces:
            rank, file = square_to_rank_file(square)
            distance = abs(king_rank - rank) + abs(king_file - file)
            score -= 1.0 / (distance + 1)  # Penalize proximity
        # Pawn shield (prefer squares in front of king covered by own pawns)
        pawns = [square for square, piece in pieces.items() if is_pawn(piece) and piece[0] == color]
        for pawn in pawns:
            pawn_rank, pawn_file = square_to_rank_file(pawn)
            if pawn_rank == king_rank + 1 and abs(pawn_file - king_file) <= 1:
                score += 0.2  # Bonus for pawn shield

    # 3. Pawn structure (center control, passed pawns)
    center_squares = ['d4', 'd5', 'e4', 'e5']
    for square in pieces:
        piece = pieces[square]
        if is_pawn(piece) and piece[0] == color and square in center_squares:
            score += 0.3  # Bonus for controlling center
        elif is_pawn(piece) and piece[0] == color:
            # Passed pawn bonus (simplified: if no enemy pawns in front)
            rank, file = square_to_rank_file(square)
            passed = True
            for f in range(file - 1, file + 2):
                for r in range(rank + 1, 8):
                    if 0 <= f < 8 and rank_file_to_square(r, f) in pieces:
                        if is_pawn(pieces[rank_file_to_square(r, f)]) and pieces[rank_file_to_square(r, f)][0] == opponent_color:
                            passed = False
                            break
                if not passed:
                    break
            if passed:
                score += 0.5 * (8 - rank) / 8.0  # Bonus for passed pawns (higher for advanced pawns)

    # 4. Piece mobility (number of legal moves)
    for square in pieces:
        piece = pieces[square]
        if piece[0] == color:
            rank, file = square_to_rank_file(square)
            piece_type = piece[1]
            mobility = 0
            # Count possible moves (simplified, no actual legality check)
            if is_sliding_piece(piece_type):
                for dr, df in SLIDING_DIRECTIONS[piece_type]:
                    r, f = rank + dr, file + df
                    while 0 <= r < 8 and 0 <= f < 8:
                        mobility += 1
                        if rank_file_to_square(r, f) in pieces:
                            break
                        r += dr
                        f += df
            elif is_knight(piece_type):
                mobility = len(KNIGHT_MOVES)
            elif is_pawn(piece):
                # Pawn mobility: forward + captures
                mobility = 1  # forward
                for df in [-1, 1]:
                    if 0 <= file + df < 8 and rank_file_to_square(rank + 1, file + df) in pieces:
                        mobility += 1  # capture
            elif is_king(piece_type):
                mobility = 8  # all adjacent squares
            # Normalize mobility bonus (higher for pieces with fewer natural moves)
            if piece_type == 'N':
                score += mobility * 0.1
            elif piece_type == 'B':
                score += mobility * 0.05
            elif piece_type == 'R':
                score += mobility * 0.03
            elif piece_type == 'Q':
                score += mobility * 0.02
            elif piece_type == 'P':
                score += mobility * 0.01

    return score

def simulate_move(pieces: Dict[str, str], move: str, to_play: str) -> Dict[str, str]:
    """
    Simulate a move on the board and return the new pieces dict.
    Assumes the move is legal (no validation).
    """
    new_pieces = pieces.copy()
    color = to_play[0]
    from_square = move[:2]
    to_square = move[2:4]

    # Remove piece from from_square (or pawn if promotion)
    piece_code = new_pieces[from_square]
    if is_pawn(piece_code[1]) and len(move) == 5:  # Promotion
        new_piece = piece_code[0] + move[4]
        del new_pieces[from_square]
        new_pieces[to_square] = new_piece
    else:
        del new_pieces[from_square]
        new_pieces[to_square] = piece_code

    # Handle en passant (not implemented here, but legal_moves should exclude illegal ones)
    return new_pieces

def is_checkmate(pieces: Dict[str, str], to_play: str) -> bool:
    """
    Check if the current position is a checkmate (simplified).
    Assumes the move is legal and the opponent has no escape.
    """
    color = to_play[0]
    opponent_color = 'b' if color == 'w' else 'w'
    king_square = None
    for square, piece in pieces.items():
        if is_king(piece) and piece[0] == color:
            king_square = square
            break

    # Check if opponent's king is under attack (simplified: count attacking pieces)
    attacks = 0
    for square in pieces:
        piece = pieces[square]
        if piece[0] == opponent_color:
            continue
        rank, file = square_to_rank_file(square)
        piece_type = piece[1]
        if is_sliding_piece(piece_type):
            # Check if piece attacks king (simplified: same rank/file/diagonal)
            king_rank, king_file = square_to_rank_file(king_square)
            if (piece_type == 'R' or piece_type == 'Q') and (rank == king_rank or file == king_file):
                attacks += 1
            elif (piece_type == 'B' or piece_type == 'Q') and abs(rank - king_rank) == abs(file - king_file):
                attacks += 1
        elif is_knight(piece_type):
            # Check knight attacks
            if abs(rank - king_rank) in [1, 2] and abs(file - king_file) in [1, 2]:
                attacks += 1
        elif is_pawn(piece):
            # Check pawn attacks (simplified: forward diagonal)
            if piece[0] == color:  # Our pawn
                pawn_rank, pawn_file = square_to_rank_file(square)
                if pawn_rank == king_rank - 1 and abs(pawn_file - king_file) == 1:
                    attacks += 1
    # If attacks >= 2, it's likely checkmate (simplified)
    return attacks >= 2

def policy(pieces: Dict[str, str], to_play: str, memory: Dict) -> Tuple[str, Dict]:
    """
    Select the best move using a hybrid approach:
    1. Check for checkmate in one move.
    2. Evaluate all legal moves using minimax (1-ply lookahead).
    3. Choose the move with the highest score.
    """
    color = to_play[0]
    legal_moves = memory.get('legal_moves', [])

    if not legal_moves:
        return '', memory  # Should not happen per problem statement

    # Step 1: Check for immediate checkmate
    for move in legal_moves:
        new_pieces = simulate_move(pieces, move, to_play)
        if is_checkmate(new_pieces, to_play):
            return move, memory  # Return first checkmate move found

    # Step 2: Evaluate all legal moves using minimax (1-ply)
    best_move = None
    best_score = -float('inf')
    for move in legal_moves:
        new_pieces = simulate_move(pieces, move, to_play)
        # Simulate opponent's best response (1-ply minimax)
        opponent_best_score = -float('inf')
        for opponent_move in memory.get('opponent_legal_moves', []):
            opponent_pieces = simulate_move(new_pieces, opponent_move, to_play)
            score = evaluate_board(opponent_pieces, to_play)
            if score > opponent_best_score:
                opponent_best_score = score
        # Our score is the negative of opponent's best response (maximin)
        score = -opponent_best_score
        if score > best_score:
            best_score = score
            best_move = move

    # Step 3: If no clear winner, fall back to greedy material/capture moves
    if best_move is None:
        # Prefer captures or pawn pushes
        capture_moves = [move for move in legal_moves if move[2] in pieces and pieces[move[2]][0] != color]
        if capture_moves:
            # Choose capture with highest material gain
            best_capture = None
            best_gain = 0
            for move in capture_moves:
                from_piece = pieces[move[:2]]
                to_piece = pieces[move[2:4]]
                gain = get_piece_value(to_piece) - get_piece_value(from_piece)
                if gain > best_gain:
                    best_gain = gain
                    best_move = move
            return best_move, memory
        else:
            # No captures, prefer pawn moves or king safety
            pawn_moves = [move for move in legal_moves if is_pawn(pieces[move[:2]][1])]
            if pawn_moves:
                # Prefer center pawn moves or passed pawns
                center_pawn_moves = [move for move in pawn_moves if move[2] in ['d4', 'd5', 'e4', 'e5']]
                if center_pawn_moves:
                    return center_pawn_moves[0], memory  # Pick first center pawn move
                else:
                    return pawn_moves[0], memory  # Pick any pawn move
            else:
                # No pawn moves, pick any move (e.g., king safety)
                return legal_moves[0], memory

    return best_move, memory

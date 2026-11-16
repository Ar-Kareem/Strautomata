
import re
from collections import defaultdict

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    # Determine our color and opponent's color
    our_color = 'w' if to_play == 'white' else 'b'
    opponent_color = 'b' if to_play == 'white' else 'w'

    # Precompute piece values (material)
    piece_values = {
        'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0
    }

    # Precompute square values (center control)
    square_values = {
        'a1': 0.0, 'b1': 0.1, 'c1': 0.2, 'd1': 0.3, 'e1': 0.2, 'f1': 0.1, 'g1': 0.0, 'h1': 0.0,
        'a2': 0.1, 'b2': 0.2, 'c2': 0.3, 'd2': 0.4, 'e2': 0.3, 'f2': 0.2, 'g2': 0.1, 'h2': 0.0,
        'a3': 0.0, 'b3': 0.2, 'c3': 0.3, 'd3': 0.4, 'e3': 0.4, 'f3': 0.3, 'g3': 0.2, 'h3': 0.0,
        'a4': 0.0, 'b4': 0.2, 'c4': 0.3, 'd4': 0.4, 'e4': 0.4, 'f4': 0.3, 'g4': 0.2, 'h4': 0.0,
        'a5': 0.0, 'b5': 0.2, 'c5': 0.3, 'd5': 0.4, 'e5': 0.4, 'f5': 0.3, 'g5': 0.2, 'h5': 0.0,
        'a6': 0.1, 'b6': 0.2, 'c6': 0.3, 'd6': 0.4, 'e6': 0.3, 'f6': 0.2, 'g6': 0.1, 'h6': 0.0,
        'a7': 0.1, 'b7': 0.2, 'c7': 0.3, 'd7': 0.3, 'e7': 0.2, 'f7': 0.1, 'g7': 0.0, 'h7': 0.0,
        'a8': 0.0, 'b8': 0.1, 'c8': 0.2, 'd8': 0.2, 'e8': 0.1, 'f8': 0.0, 'g8': 0.0, 'h8': 0.0,
    }

    # Precompute king safety scores (distance to opponent's pieces)
    def king_safety_score(square):
        king_square = None
        for sq, piece in pieces.items():
            if piece[1] == 'K' and piece[0] == our_color:
                king_square = sq
                break
        if not king_square:
            return 0.0

        # Distance to opponent's pieces (higher is better)
        distance = 0
        for sq, piece in pieces.items():
            if piece[0] == opponent_color:
                distance += chess_distance(king_square, sq)
        return distance / (len(pieces) - 1) if (len(pieces) - 1) > 0 else 0.0

    # Helper: Chess distance between two squares (max of file and rank difference)
    def chess_distance(sq1, sq2):
        file1, rank1 = ord(sq1[0]) - ord('a'), int(sq1[1])
        file2, rank2 = ord(sq2[0]) - ord('a'), int(sq2[1])
        return max(abs(file1 - file2), abs(rank1 - rank2))

    # Helper: Parse move to get from/to squares and capture info
    def parse_move(move):
        if move == 'O-O' or move == 'O-O-O':
            return move, None, None, None
        # Handle promotions
        if '=' in move:
            parts = move.split('=')
            move_part = parts[0]
            promotion = parts[1]
            if 'x' in move_part:
                from_sq = move_part[:-2]
                to_sq = move_part[-2:]
                captured = move_part[-1]
            else:
                from_sq = move_part[:-2]
                to_sq = move_part[-2:]
                captured = None
            return move, from_sq, to_sq, promotion
        # Handle captures
        if 'x' in move:
            parts = move.split('x')
            from_sq = parts[0]
            to_sq = parts[1]
            captured = to_sq
            return move, from_sq, to_sq, None
        # Handle disambiguation (e.g., 'Nec3')
        if re.match(r'^[a-h][a-h][a-h][1-8]$', move):
            from_sq = move[:2]
            to_sq = move[2:]
            return move, from_sq, to_sq, None
        # Handle simple moves (e.g., 'e4')
        if len(move) == 2:
            from_sq = None
            to_sq = move
            return move, from_sq, to_sq, None
        # Handle other cases (e.g., 'Nf3')
        if len(move) == 3 and move[1] in 'NBRQ':
            from_sq = None
            to_sq = move[1:]
            return move, from_sq, to_sq, None
        # Default: assume move is 'from_to' or 'from_to+'
        if '+' in move:
            move_part = move[:-1]
            if 'x' in move_part:
                from_sq = move_part[:-2]
                to_sq = move_part[-2:]
                captured = to_sq
                return move, from_sq, to_sq, None
            else:
                from_sq = move_part[:-2]
                to_sq = move_part[-2:]
                return move, from_sq, to_sq, None
        else:
            if 'x' in move:
                from_sq = move[:-2]
                to_sq = move[-2:]
                captured = to_sq
                return move, from_sq, to_sq, None
            else:
                from_sq = move[:-2]
                to_sq = move[-2:]
                return move, from_sq, to_sq, None

    # Helper: Simulate move to get material change
    def simulate_move(move, from_sq, to_sq, captured):
        # Copy pieces
        new_pieces = pieces.copy()
        # Remove captured piece
        if captured and captured in new_pieces:
            del new_pieces[captured]
        # Move piece
        if from_sq in new_pieces:
            piece = new_pieces[from_sq]
            del new_pieces[from_sq]
            new_pieces[to_sq] = piece
        # Check for checkmate (simplified: if opponent has no legal moves after this move)
        # For simplicity, we assume the move is legal and checkmate is handled by the input
        return new_pieces

    # Helper: Evaluate material change
    def evaluate_material_change(new_pieces):
        material = 0
        for piece in new_pieces.values():
            color = piece[0]
            value = piece_values[piece[1]]
            material += value if color == our_color else -value
        return material

    # Helper: Evaluate king safety after move
    def evaluate_king_safety(new_pieces):
        king_square = None
        for sq, piece in new_pieces.items():
            if piece[1] == 'K' and piece[0] == our_color:
                king_square = sq
                break
        if not king_square:
            return 0.0
        # Distance to opponent's pieces (higher is better)
        distance = 0
        for sq, piece in new_pieces.items():
            if piece[0] == opponent_color:
                distance += chess_distance(king_square, sq)
        return distance / (len(new_pieces) - 1) if (len(new_pieces) - 1) > 0 else 0.0

    # Helper: Evaluate piece activity (mobility)
    def evaluate_piece_activity(new_pieces):
        activity = 0
        for sq, piece in new_pieces.items():
            if piece[0] == our_color:
                activity += square_values[sq]
        return activity

    # Helper: Check if move is a capture
    def is_capture(move):
        return 'x' in move or ('=' in move and 'x' in move.split('=')[0])

    # Helper: Check if move is a check
    def is_check(move):
        return move.endswith('+')

    # Helper: Check if move is a checkmate (simplified: assume input is correct)
    def is_checkmate(move):
        return any('+' in m and '#' in m for m in legal_moves)

    # Evaluate each move
    best_move = None
    best_score = -float('inf')

    for move in legal_moves:
        # Check for checkmate
        if is_checkmate(move):
            return move

        # Parse move
        parsed_move, from_sq, to_sq, promotion = parse_move(move)
        captured = None
        if 'x' in parsed_move:
            captured = parsed_move.split('x')[1][:2] if '=' not in parsed_move else parsed_move.split('x')[1][:2]

        # Simulate move
        new_pieces = simulate_move(parsed_move, from_sq, to_sq, captured)

        # Evaluate material change
        material_change = evaluate_material_change(new_pieces)

        # Evaluate king safety
        king_safety = evaluate_king_safety(new_pieces)

        # Evaluate piece activity
        piece_activity = evaluate_piece_activity(new_pieces)

        # Evaluate move score
        score = 0
        # Weight material change heavily
        score += material_change * 100
        # King safety is important
        score += king_safety * 10
        # Piece activity is good
        score += piece_activity * 5
        # Captures are good
        if is_capture(move):
            score += 20
        # Checks are good
        if is_check(move):
            score += 30

        # Update best move
        if score > best_score:
            best_score = score
            best_move = move

    # Default to first move if no clear best (shouldn't happen)
    return best_move if best_move is not None else legal_moves[0]

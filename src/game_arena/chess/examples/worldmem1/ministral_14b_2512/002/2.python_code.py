
import re
from collections import defaultdict

# Piece values (material)
PIECE_VALUES = {
    'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0
}

# Center control squares (for evaluation)
CENTER_SQUARES = {'d4', 'd5', 'e4', 'e5'}

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    color = 'w' if to_play == 'white' else 'b'
    opponent_color = 'b' if color == 'w' else 'w'

    # Check for checkmates first
    mate_moves = [move for move in legal_moves if '+' in move and '#' in move]
    if mate_moves:
        # Prefer shortest mate (simplistic; in practice, use depth)
        return (mate_moves[0], memory)

    # Evaluate all legal moves and pick the best
    best_move = None
    best_score = -float('inf')

    for move in legal_moves:
        score = evaluate_move(pieces, color, move, memory)
        if score > best_score:
            best_score = score
            best_move = move

    return (best_move, memory)

def evaluate_move(pieces: dict[str, str], color: str, move: str, memory: dict) -> float:
    # Parse the move to understand its effect
    from_sq, to_sq = parse_move(move)
    if not from_sq or not to_sq:
        return -float('inf')  # Invalid move (shouldn't happen per problem statement)

    # Check if the move is a capture
    is_capture = 'x' in move
    if is_capture:
        captured_piece = pieces.get(to_sq, None)
        if captured_piece:
            captured_value = PIECE_VALUES[captured_piece[1]]
            # Bonus for capturing high-value pieces
            material_gain = captured_value * 100
        else:
            material_gain = 0
    else:
        material_gain = 0

    # Check if the move gives check
    gives_check = '+' in move
    check_bonus = 1000 if gives_check else 0

    # Check if the move is a promotion
    is_promotion = '=' in move
    if is_promotion:
        promotion_bonus = 100  # Small bonus for promotions (could be adjusted)

    # Evaluate piece activity (mobility, center control)
    piece_activity = evaluate_piece_activity(pieces, color, from_sq, to_sq)

    # Evaluate king safety (avoid moving king into danger)
    king_safety = evaluate_king_safety(pieces, color, from_sq, to_sq)

    # Combine all factors
    score = (
        material_gain +
        check_bonus +
        promotion_bonus +
        piece_activity +
        king_safety
    )

    return score

def parse_move(move: str) -> tuple[str, str]:
    # Simplistic move parser (handles most cases)
    if move == 'O-O' or move == 'O-O-O':
        return ('e1', 'g1') if move == 'O-O' else ('e1', 'c1')  # White castling
    if move == 'O-O' or move == 'O-O-O':
        return ('e8', 'g8') if move == 'O-O' else ('e8', 'c8')  # Black castling

    # Handle disambiguation (e.g., 'Nec3' -> 'e3' to 'c3')
    if re.match(r'^[a-h][a-h][a-h][a-z]$', move):
        # Example: 'Nec3' -> from='e3', to='c3'
        from_sq = move[1:3]
        to_sq = move[3]
        if len(move) == 4 and move[0] in 'NBRQ':
            to_sq = move[2:4]
        else:
            to_sq = move[2:]
    else:
        # Standard move (e.g., 'e4', 'Bxf5')
        if 'x' in move:
            parts = move.split('x')
            from_sq = parts[0]
            to_sq = parts[1]
            if '=' in to_sq:
                to_sq = to_sq.split('=')[0]
        else:
            if '=' in move:
                from_sq = move[:-2]
                to_sq = move[-2]
            else:
                from_sq = move[:-2]
                to_sq = move[-2:]

    return (from_sq, to_sq)

def evaluate_piece_activity(pieces: dict[str, str], color: str, from_sq: str, to_sq: str) -> float:
    # Bonus for moving to center
    center_bonus = 5 if to_sq in CENTER_SQUARES else 0

    # Bonus for developing pieces (knights/bishops to center)
    piece = pieces.get(from_sq, None)
    if piece and piece[0] == color:
        if piece[1] in ['N', 'B'] and to_sq in CENTER_SQUARES:
            return center_bonus + 10
        elif piece[1] == 'P' and to_sq in CENTER_SQUARES:
            return center_bonus + 5

    return center_bonus

def evaluate_king_safety(pieces: dict[str, str], color: str, from_sq: str, to_sq: str) -> float:
    # Avoid moving king into check (simplistic)
    king_pos = None
    for sq, piece in pieces.items():
        if piece[1] == 'K' and piece[0] == color:
            king_pos = sq
            break

    if king_pos == from_sq:
        # Moving king: check if to_sq is safe (simplistic)
        # In practice, you'd need to simulate the move and check for checks
        return -50  # Penalty for moving king (unless necessary)

    return 0

# Example usage (not part of the policy, just for testing)
if __name__ == "__main__":
    # Mock data for testing
    pieces = {'e1': 'bK', 'f3': 'wR', 'e4': 'wP', 'd5': 'bP'}
    to_play = 'white'
    legal_moves = ['Rf1', 'Rf2', 'Rf4', 'Rf5', 'Rf6', 'Rf7', 'Rf8', 'Rg1', 'Rg2', 'Rg3', 'Rg4', 'Rg5', 'Rg6', 'Rg7', 'Rg8']
    memory = {}

    move, _ = policy(pieces, to_play, legal_moves, memory)
    print(f"Selected move: {move}")

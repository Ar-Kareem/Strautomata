
import random
from collections import defaultdict

# Piece values (material balance)
PIECE_VALUES = {
    'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0  # King has no material value
}

# Center control squares (for positional bonuses)
CENTER_SQUARES = {'d4', 'd5', 'e4', 'e5'}

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    # Determine our color and opponent's color
    our_color = to_play
    opponent_color = 'black' if our_color == 'white' else 'white'

    # Initialize best move and score
    best_move = None
    best_score = -float('inf')

    # Iterate through all legal moves
    for move in legal_moves:
        score = evaluate_move(pieces, our_color, opponent_color, move)
        if score > best_score:
            best_score = score
            best_move = move
        elif score == best_score:
            # Randomly choose among equally good moves
            if random.random() < 0.5:
                best_move = move

    # Return the best move and empty memory (or updated memory if needed)
    return (best_move, {})

def evaluate_move(pieces: dict[str, str], our_color: str, opponent_color: str, move: str) -> float:
    score = 0.0

    # Check if the move is a capture (e.g., 'Bxf5')
    if 'x' in move:
        # Extract the captured piece (last character before 'x' or '=')
        captured_piece = move.split('x')[1].split('=')[0][0] if 'x' in move else None
        if captured_piece:
            # Add value of captured piece
            score += PIECE_VALUES.get(captured_piece, 0)
            # Subtract value of our piece if we lose material
            our_piece = move[0]
            if our_piece in ['P', 'N', 'B', 'R', 'Q']:
                score -= PIECE_VALUES.get(our_piece, 0)

    # Check if the move delivers check (e.g., 'Bxf5+')
    if move.endswith('+'):
        score += 100.0  # High bonus for check

    # Check if the move is a promotion (e.g., 'b8=Q')
    if '=' in move:
        # Promote to queen is best for material
        promoted_piece = move.split('=')[1]
        if promoted_piece == 'Q':
            score += 9.0  # Queen promotion
        else:
            score += PIECE_VALUES.get(promoted_piece, 0)

    # Check if the move is castling (e.g., 'O-O')
    if move in ['O-O', 'O-O-O']:
        score += 0.5  # Small bonus for castling (king safety)

    # Check if the move improves king safety (avoid moves that leave king in check)
    # (This is simplified; in practice, you'd need to simulate the move and check)
    if not move.endswith('+'):
        # Penalize moves that leave the king in a weak position (simplified)
        king_pos = find_king(pieces, our_color)
        if king_pos:
            # Check if king is in center (bad for safety)
            if king_pos in CENTER_SQUARES:
                score -= 1.0

    # Check if the move develops a piece (e.g., knight to center)
    if len(move) == 2:  # Pawn move (e.g., 'e4')
        pass  # Pawn moves are handled separately
    elif move[0] in ['N', 'B', 'R', 'Q']:
        # Check if the move is a knight/bishop developing to center
        target_square = move[-2:] if len(move) > 2 else move[1:]
        if target_square in CENTER_SQUARES:
            score += 0.5  # Small bonus for developing to center

    # Check if the move supports a passed pawn (simplified)
    # (This would require tracking pawn structure, which is complex)

    # Randomness for unpredictability (small noise)
    score += random.uniform(-0.1, 0.1)

    return score

def find_king(pieces: dict[str, str], color: str) -> str:
    king_code = f"{color}K"
    for square, piece in pieces.items():
        if piece == king_code:
            return square
    return None

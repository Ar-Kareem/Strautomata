
import random
from collections import defaultdict

# Piece values (material)
PIECE_VALUES = {
    'wP': 1, 'bP': 1,
    'wN': 3, 'bN': 3,
    'wB': 3, 'bB': 3,
    'wR': 5, 'bR': 5,
    'wQ': 9, 'bQ': 9,
    'wK': 0, 'bK': 0  # King has infinite value but is not captured
}

# Center control squares (for positional bonuses)
CENTER_SQUARES = {'d4', 'd5', 'e4', 'e5'}

def evaluate_board(pieces, to_play):
    """Evaluate the board position from the perspective of the current player."""
    score = 0
    color = 'w' if to_play == 'white' else 'b'
    opponent_color = 'b' if color == 'w' else 'w'

    # Material score
    for square, piece in pieces.items():
        if piece.startswith(color):
            score += PIECE_VALUES[piece]
        elif piece.startswith(opponent_color):
            score -= PIECE_VALUES[piece]

    # Positional bonuses (simplified)
    for square, piece in pieces.items():
        if piece.startswith(color):
            # Center control bonus
            if square in CENTER_SQUARES:
                score += 0.5
            # Pawn structure (simplified)
            if piece == 'wP' or piece == 'bP':
                file = square[0]
                rank = int(square[1])
                # Avoid isolated pawns (simplified)
                adjacent_pawns = 0
                for f in [chr(ord(file) - 1), chr(ord(file) + 1)]:
                    if f in 'abcdefgh':
                        adj_square = f + str(rank)
                        if adj_square in pieces and pieces[adj_square].startswith(color) and pieces[adj_square][1] == 'P':
                            adjacent_pawns += 1
                if adjacent_pawns == 0:
                    score -= 0.3  # Penalty for isolated pawn

    return score

def is_checkmate(pieces, to_play, move):
    """Simulate the move and check if it results in checkmate (simplified)."""
    # This is a placeholder. In practice, you'd need to simulate the move and check for checkmate.
    # For simplicity, we assume the move is a checkmate if it's a king capture (invalid in real chess).
    # In a real implementation, you'd use a chess engine or simulate the board state.
    return False  # Simplified: assume no checkmate for now

def policy(pieces, to_play, legal_moves=None):
    """Select the best move from legal_moves using evaluation and tactical awareness."""
    if legal_moves is None:
        legal_moves = []  # Should not happen per problem statement

    # Step 1: Check for checkmates (highest priority)
    for move in legal_moves:
        if is_checkmate(pieces, to_play, move):
            return move

    # Step 2: Evaluate all legal moves and pick the best
    best_move = None
    best_score = -float('inf')

    for move in legal_moves:
        # Simulate the move (simplified: just evaluate the resulting board)
        # In practice, you'd need to simulate the move and evaluate the new board.
        # For now, we just evaluate the current board and pick the move that seems best.
        # This is a placeholder for a more sophisticated evaluation.
        score = evaluate_board(pieces, to_play)

        # Bonus for captures (material gain)
        from_square = move[:2]
        to_square = move[2:4]
        if from_square in pieces and to_square in pieces:
            from_piece = pieces[from_square]
            to_piece = pieces[to_square]
            if from_piece.startswith(to_play) and to_piece.startswith('w' if to_play == 'black' else 'b'):
                # Capture: add the value of the captured piece
                score += PIECE_VALUES[to_piece]

        # Bonus for developing pieces (simplified)
        if from_square in pieces and pieces[from_square][1] in ['N', 'B', 'R', 'Q']:
            if from_square not in ['a1', 'b1', 'c1', 'd1', 'e1', 'f1', 'g1', 'h1']:  # Not starting square
                score += 0.2

        # Bonus for controlling center
        if to_square in CENTER_SQUARES:
            score += 0.3

        if score > best_score:
            best_score = score
            best_move = move

    # If no clear best move, pick randomly (fallback)
    if best_move is None:
        best_move = random.choice(legal_moves)

    return best_move

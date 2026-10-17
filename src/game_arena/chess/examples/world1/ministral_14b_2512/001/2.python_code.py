
import re

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    # Precompute piece values for evaluation
    piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
    color = 'w' if to_play == 'white' else 'b'
    opponent_color = 'b' if color == 'w' else 'w'

    # Helper function to parse a move string into start, end, and promotion
    def parse_move(move):
        if move == 'O-O' or move == 'O-O-O':
            return (move, None, None)
        # Handle castling (not in legal_moves as per problem statement, but just in case)
        if 'x' in move:
            parts = re.split('x|=', move)
            start = parts[0]
            end = parts[1]
            promotion = parts[2] if len(parts) > 2 else None
        else:
            parts = re.split('=', move)
            start = parts[0]
            end = parts[1] if len(parts) > 1 else None
            promotion = parts[1] if len(parts) > 1 else None
        return (start, end, promotion)

    # Evaluate a move based on material gain, check, and king safety
    def evaluate_move(move):
        start, end, promotion = parse_move(move)
        if not start or not end:  # Castling
            return 0  # Neutral for now

        # Check if the move captures
        captures = 'x' in move
        if captures:
            captured_piece = pieces.get(end, None)
            if captured_piece and captured_piece[0] == opponent_color:
                captured_value = piece_values.get(captured_piece[1], 0)
                return captured_value * 100  # High priority for captures

        # Check if the move gives check (indicated by '+' in move)
        if '+' in move:
            return 1000  # Check is very valuable

        # Check if the move promotes
        if promotion:
            return 900  # Promotion is very valuable

        # Check if the move develops a piece (non-pawn moves)
        if start and end and pieces.get(start, None) and pieces.get(start, None)[1] != 'P':
            return 50  # Developing pieces is good

        # Check if the move controls the center (e4, d4, e5, d5)
        center_squares = {'d4', 'd5', 'e4', 'e5'}
        if end in center_squares:
            return 30  # Controlling center is good

        # Default: prefer non-pawn moves over pawn moves
        if pieces.get(start, None) and pieces.get(start, None)[1] == 'P':
            return 10
        else:
            return 20

    # Evaluate all legal moves and pick the best one
    best_move = None
    best_score = -float('inf')

    for move in legal_moves:
        score = evaluate_move(move)
        if score > best_score:
            best_score = score
            best_move = move

    # If no move gives check or captures, prefer moves that develop pieces or control center
    if best_score == -float('inf'):
        # Fallback: pick the first move (should not happen as legal_moves is non-empty)
        return legal_moves[0]

    return best_move

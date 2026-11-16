
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    """
    Chooses the best move from a list of legal moves based on a simple evaluation function.
    """

    piece_values = {'K': 1000, 'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'P': 1}
    color_multiplier = 1 if to_play == 'white' else -1  # White wants positive scores, black negative

    def evaluate_move(move: str, pieces: dict[str, str], to_play: str) -> float:
        """
        Evaluates a move based on simple heuristics.
        """
        score = 0.0

        # 1. Capture High-Value Pieces
        if 'x' in move:
            captured_piece = move.split('x')[-1][0].upper() if len(move.split('x')[-1]) > 0 and move.split('x')[-1][0].isalpha()  else 'P' # Default to pawn if ambiguous.
            score += color_multiplier * piece_values.get(captured_piece, 0.5)  # Added default value 0.5 to prevent error

        # 2. Promote pawns
        if '=' in move:
             promoted_piece = move.split('=')[-1][0].upper()
             score += color_multiplier * piece_values.get(promoted_piece, 0)

        return score

    best_move = None
    best_score = float('-inf') if to_play == 'white' else float('inf') # Initialize according to the player

    for move in legal_moves:
        score = evaluate_move(move, pieces, to_play)

        if to_play == 'white':
            if score > best_score:
                best_score = score
                best_move = move
        else:
            if score < best_score:
                best_score = score
                best_move = move

    if best_move is None:
        return legal_moves[0] if legal_moves else None #pick the first valid move if all moves return the same score
    return best_move

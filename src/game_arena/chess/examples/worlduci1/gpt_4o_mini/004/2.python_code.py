
def policy(pieces: dict[str, str], to_play: str) -> str:
    # Scores for evaluating the moves
    piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}

    def evaluate_move(move: str) -> int:
        start_square = move[:2]
        end_square = move[2:4]
        score = 0
        
        # Check if the move is a capture
        if end_square in pieces:
            piece_captured = pieces[end_square]
            score += piece_values[piece_captured[1]]  # Add value of the captured piece

        # Basic heuristic for piece positioning (advancing pawns, central control)
        if move[1] == '2' and move[3] == '4':  # Example: pawn moves
            score += 1  # Advance score for pawns

        return score

    legal_moves = ['e2e4', 'd2d4', 'g1f3']  # Example move list, this should come from the actual game state
    best_move = ''
    best_score = -1

    for move in legal_moves:
        score = evaluate_move(move)
        if score > best_score:
            best_score = score
            best_move = move

    return best_move

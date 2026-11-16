
def evaluate_move(pieces, move, to_play):
    # A simple evaluation based on material and positional aspects
    scores = {
        'wP': 1, 'wN': 3, 'wB': 3, 'wR': 5, 'wQ': 9, 'wK': 0,
        'bP': 1, 'bN': 3, 'bB': 3, 'bR': 5, 'bQ': 9, 'bK': 0,
    }

    from_square, to_square = move[:2], move[2:4]
    piece = pieces.get(from_square)

    score = 0

    # Adding score for moving our piece (not doing anything temporary)
    if piece:
        score += scores.get(piece, 0)

    # If the destination is occupied by an opponent's piece, add its score to our move score
    if to_square in pieces:
        opponent_piece = pieces[to_square]
        if (to_play == 'white' and opponent_piece[0] == 'b') or (to_play == 'black' and opponent_piece[0] == 'w'):
            score += scores.get(opponent_piece, 0)

    return score

def policy(pieces: dict[str, str], to_play: str) -> str:
    legal_moves = []
    best_move = ""
    best_score = float('-inf')

    # Gather legal moves (replace this block with the actual logic to get legal moves in practice)
    for move in legal_moves:
        score = evaluate_move(pieces, move, to_play)

        # If we find a checkmate move, prioritize it immediately
        if score == float('inf'):
            return move

        if score > best_score:
            best_score = score
            best_move = move

    return best_move

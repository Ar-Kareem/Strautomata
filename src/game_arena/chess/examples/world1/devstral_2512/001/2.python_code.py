
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    # Priority 1: Checkmate
    for move in legal_moves:
        if move.endswith('#'):
            return move

    # Priority 2: Captures (material gain)
    captures = [move for move in legal_moves if 'x' in move]
    if captures:
        return captures[0]

    # Priority 3: Promotions (prefer Queen)
    promotions = [move for move in legal_moves if '=' in move]
    if promotions:
        for move in promotions:
            if move.endswith('=Q'):
                return move
        return promotions[0]

    # Priority 4: Castling (king safety)
    castling_moves = [move for move in legal_moves if move in ['O-O', 'O-O-O']]
    if castling_moves:
        return castling_moves[0]

    # Default: Return the first legal move
    return legal_moves[0]

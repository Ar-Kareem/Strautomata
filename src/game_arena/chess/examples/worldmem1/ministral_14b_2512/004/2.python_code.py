
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    color = 'w' if to_play == 'white' else 'b'
    opponent_color = 'b' if color == 'w' else 'w'

    # Piece values (material)
    piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}

    # Precompute piece positions for faster access
    piece_positions = {}
    for square, piece in pieces.items():
        if piece[0] == color:
            if piece[1] not in piece_positions:
                piece_positions[piece[1]] = []
            piece_positions[piece[1]].append(square)

    # Get king position
    king_pos = piece_positions.get('K', [''])[0] if 'K' in piece_positions else ''

    # Helper function to parse move and get captured piece
    def parse_move(move):
        if move.startswith('O-O') or move.startswith('O-O-O'):
            return move, None
        if '=' in move:  # Promotion
            return move, None
        if 'x' in move:  # Capture
            capture_square = move.split('x')[1].split('+')[0].split('=')[0]
            captured_piece = pieces.get(capture_square, None)
            return move, captured_piece
        return move, None

    # Helper function to evaluate a move (higher score is better)
    def evaluate_move(move):
        move, captured_piece = parse_move(move)
        score = 0

        # Check if move is a capture
        if captured_piece:
            score += piece_values[captured_piece[1]] * 10  # High weight for captures

        # Check if move is a checkmate (simplified: assume if move is in legal_moves and opponent has no moves)
        # Note: In practice, we can't simulate opponent's moves here, so we rely on the legal_moves list
        # being correct and assume that if a move is in legal_moves, it's valid.

        # Check if move improves king safety (simplified: avoid moving king into check)
        if move.startswith(color + 'K'):
            # Simplified: avoid moving king into squares attacked by opponent
            # This is a placeholder; a full implementation would require checking attacks
            pass

        # Prefer castling if king is safe
        if move in ['O-O', 'O-O-O']:
            score += 5  # Small bonus for castling

        # Prefer promotions to queen
        if '=' in move and move[-1] == 'Q':
            score += 2  # Small bonus for promoting to queen

        # Prefer developing pieces (e.g., pawn moves, knight/bishop outposts)
        if move[0] == 'P' and len(move) == 2:  # Pawn move (not capture)
            score += 1
        elif move[0] in ['N', 'B'] and len(move) == 3 and move[1] not in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']:  # Knight/Bishop move
            score += 1

        return score

    # Evaluate all legal moves and pick the best one
    best_move = None
    best_score = -float('inf')

    for move in legal_moves:
        score = evaluate_move(move)
        if score > best_score:
            best_score = score
            best_move = move

    # Fallback: if no clear best move, pick the first one (shouldn't happen as legal_moves is non-empty)
    if best_move is None:
        best_move = legal_moves[0]

    return (best_move, {})

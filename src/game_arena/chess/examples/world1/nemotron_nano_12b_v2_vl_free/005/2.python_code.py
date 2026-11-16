
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    # Helper function to determine the value of a piece type
    def piece_value(pc: str) -> int:
        if pc == 'Q' or pc == 'q':
            return 9
        elif pc == 'R' or pc == 'r':
            return 5
        elif pc == 'B' or pc == 'b' or pc == 'N' or pc == 'n':
            return 3
        elif pc == 'P' or pc == 'p':
            return 1
        return 0

    # Step 1: Check for pawn promotions first (prefer queen)
    promotions = [m for m in legal_moves if m.endswith('=Q')]
    if promotions:
        return promotions[0]

    # Step 2: Evaluate captures
    best_move = None
    max_captured_value = -1

    for move in legal_moves:
        if 'x' in move:
            # Extract the square being captured
            captured_square = move.split('x')[-1]
            captured_piece = pieces.get(captured_square, '')
            if not captured_piece:
                continue  # Not a valid capture (though impossible in legal moves)

            # Determine the value of the captured piece
            pc_type = captured_piece[1]
            move_value = piece_value(pc_type)

            # Update the best move if this capture is better
            if move_value > max_captured_value:
                max_captured_value = move_value
                best_move = move

    if best_move is not None:
        return best_move

    # Step 3: Prioritize castling for king safety
    if 'O-O' in legal_moves:
        return 'O-O'
    elif 'O-O-O' in legal_moves:
        return 'O-O-O'

    # Step 4: Return the first legal move if nothing else applies
    return legal_moves[0] if legal_moves else None

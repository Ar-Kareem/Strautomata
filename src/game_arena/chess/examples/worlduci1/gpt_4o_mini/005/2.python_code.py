
def policy(pieces: dict[str, str], to_play: str) -> str:
    from collections import defaultdict
    
    def is_attacked(square, opponent_pieces):
        # Very simplified attack detection for the sake of example
        # This should ideally contain logic for all pieces' movements
        attacked_squares = set()
        for position, piece in opponent_pieces.items():
            file, rank = position
            file_idx = ord(file) - ord('a')
            rank_idx = int(rank) - 1
            
            if piece[1] == 'K':
                for df in [-1, 0, 1]:
                    for dr in [-1, 0, 1]:
                        attacked_squares.add(chr(file_idx + df + ord('a')) + str(rank_idx + dr + 1))
            # Note: Expand this logic for other piece types.

        return square in attacked_squares
    
    moves = []
    opponent_color = 'b' if to_play == 'white' else 'w'
    opponent_pieces = {pos: piece for pos, piece in pieces.items() if piece[0] == opponent_color}
    
    # Generate legal moves (mocked up for the sake of this example)
    legal_moves = ['e2e4', 'd2d4']  # Replace it with real legal moves from an external library
    
    # Check for immediate threats and capture opportunities
    best_move = None
    for move in legal_moves:
        start, end = move[:2], move[2:]
        if end in pieces:
            # Capture opportunities
            captured_piece = pieces[end]
            if best_move is None or captured_piece[1] > pieces[best_move[2:]][1]:
                best_move = move
        elif not is_attacked(end, opponent_pieces):
            # Position enhancing moves
            if best_move is None:
                best_move = move
            
    if best_move:
        return best_move

    # Fallback in case no move is found
    return legal_moves[0] if legal_moves else ''  # Ensure to return a legal move

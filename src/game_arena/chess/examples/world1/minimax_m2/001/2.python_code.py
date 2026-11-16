
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
    best_move = None
    best_gain = -float('inf')
    
    for move in legal_moves:
        gain = 0
        
        # Check for promotion
        if '=' in move:
            # Get the promoted piece type (Q, R, B, N)
            index = move.index('=')
            promoted_piece_type = move[index+1]
            gain += piece_values[promoted_piece_type] - 1  # Gain is value of promoted piece minus pawn value
        
        # Check for capture (look for 'x' in move string)
        if 'x' in move:
            # The destination square is the last two characters
            dest_square = move[-2:]
            captured_piece = pieces.get(dest_square)
            if captured_piece is not None:
                # captured_piece[1] is the piece type (P, N, B, R, Q, K)
                gain += piece_values[captured_piece[1]]
        
        # If no promotion/capture gains, check for king move penalty (non-castling)
        if gain == 0:
            # Check if it's a king move (starts with 'K') and not castling
            if move[0] == 'K' and move not in ['O-O', 'O-O-O']:
                gain = -1  # Penalty for moving king non-castling
        
        # Update best move if current move has higher gain
        if gain > best_gain:
            best_gain = gain
            best_move = move
    
    return best_move

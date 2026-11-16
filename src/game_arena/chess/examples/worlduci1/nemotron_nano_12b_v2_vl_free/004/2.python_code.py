
def policy(pieces: dict[str, str], to_play: str) -> str:
    import chess

    # Initialize the board and reset all pieces
    board = chess.Board()
    for i in range(64):
        board.clear(i)
    
    # Populate the board with given pieces
    for square, piece in pieces.items():
        # Parse square and piece components
        file_char = square[0]
        rank_char = square[1]
        file_idx = ord(file_char) - ord('a')
        rank_idx = int(rank_char) - 1
        square_int = rank_idx * 8 + file_idx
        
        color = chess.WHITE if piece[0] == 'w' else chess.BLACK
        piece_type = piece[1]
        board.set_piece_at(square_int, chess.Piece(piece_type, color))
    
    # Get all legal moves for the current player
    legal_moves = list(board.moves())
    
    # Check for checkmate moves first
    for move in legal_moves:
        new_board = chess.Board(board)
        new_board.push(move)
        if new_board.is_checkmate():
            return move.uci()
    
    # Evaluate each move's impact
    evaluations = []
    for move in legal_moves:
        temp_board = board.copy()
        temp_board.push(move)
        # Evaluate from white's perspective, adjust for current player
        score = temp_board.evaluate()
        if to_play == 'black':
            score = -score  # Minimize white's advantage
        evaluations.append((move.uci(), score))
    
    # Sort by descending score, then lexicographical order
    evaluations.sort(key=lambda x: (-x[1], x[0]))
    return evaluations[0][0]

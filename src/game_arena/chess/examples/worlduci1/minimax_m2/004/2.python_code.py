
def policy(pieces: dict[str, str], to_play: str) -> str:
    try:
        import chess
    except ImportError:
        return "e2e4"

    board = chess.Board()
    board.clear()
    color_map = {'w': chess.WHITE, 'b': chess.BLACK}
    piece_map = {
        'P': chess.PAWN,
        'N': chess.KNIGHT,
        'B': chess.BISHOP,
        'R': chess.ROOK,
        'Q': chess.QUEEN,
        'K': chess.KING
    }
    
    for square_str, piece_code in pieces.items():
        sq = chess.parse_square(square_str)
        color = color_map[piece_code[0]]
        piece_type = piece_map[piece_code[1]]
        piece_obj = chess.Piece(piece_type, color)
        board.set_piece_at(sq, piece_obj)
    
    board.turn = color_map[to_play[0]]
    
    legal_moves = [move.uci() for move in board.legal_moves]
    
    if not legal_moves:
        return "e2e4"
    
    for move in legal_moves:
        board_copy = board.copy()
        board_copy.push_uci(move)
        if board_copy.is_checkmate():
            return move
    
    def material_evaluation(board_state):
        total = 0
        piece_values = {
            chess.PAWN: 100,
            chess.KNIGHT: 300,
            chess.BISHOP: 300,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 0
        }
        for square in chess.SQUARES:
            piece = board_state.piece_at(square)
            if piece is None:
                continue
            value = piece_values[piece.piece_type]
            if piece.color == board_state.turn:
                total += value
            else:
                total -= value
        return total
    
    def minimax(board_state, depth, is_maximizing):
        if depth == 0:
            return material_evaluation(board_state)
        moves = list(board_state.legal_moves)
        if not moves:
            if board_state.is_checkmate():
                return -10000
            else:
                return 0
        if is_maximizing:
            max_eval = -float('inf')
            for move in moves:
                board_state.push(move)
                eval_score = minimax(board_state, depth-1, False)
                board_state.pop()
                if eval_score > max_eval:
                    max_eval = eval_score
            return max_eval
        else:
            min_eval = float('inf')
            for move in moves:
                board_state.push(move)
                eval_score = minimax(board_state, depth-1, True)
                board_state.pop()
                if eval_score < min_eval:
                    min_eval = eval_score
            return min_eval
    
    if len(legal_moves) <= 10:
        best_move = None
        best_score = -float('inf')
        for move in legal_moves:
            board_copy = board.copy()
            board_copy.push_uci(move)
            score = minimax(board_copy, 1, False)
            if score > best_score:
                best_score = score
                best_move = move
        return best_move
    else:
        best_move = None
        best_score = -float('inf')
        for move in legal_moves:
            board_copy = board.copy()
            board_copy.push_uci(move)
            score = material_evaluation(board_copy)
            if score > best_score:
                best_score = score
                best_move = move
        return best_move

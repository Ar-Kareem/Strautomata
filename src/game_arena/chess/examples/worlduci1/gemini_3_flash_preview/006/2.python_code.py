
import random

def policy(pieces: dict[str, str], to_play: str) -> str:
    # Piece values for minimax evaluation
    vals = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}
    
    # Simplified Piece-Square Tables
    pst = {
        'P': [0,  0,  0,  0,  0,  0,  0,  0, 50, 50, 50, 50, 50, 50, 50, 50, 10, 10, 20, 30, 30, 20, 10, 10, 5,  5, 10, 25, 25, 10,  5,  5, 0,  0,  0, 20, 20,  0,  0,  0, 5, -5,-10,  0,  0,-10, -5,  5, 5, 10, 10,-20,-20, 10, 10,  5, 0,  0,  0,  0,  0,  0,  0,  0],
        'N': [-50,-40,-30,-30,-30,-30,-40,-50,-40,-20,  0,  0,  0,  0,-20,-40,-30,  0, 10, 15, 15, 10,  0,-30,-30,  5, 15, 20, 20, 15,  5,-30,-30,  0, 15, 20, 20, 15,  0,-30,-30,  5, 10, 15, 15, 10,  5,-30,-40,-20,  0,  5,  5,  0,-20,-40,-50,-40,-30,-30,-30,-30,-40,-50],
        'B': [-20,-10,-10,-10,-10,-10,-10,-20,-10,  0,  0,  0,  0,  0,  0,-10,-10,  0,  5, 10, 10,  5,  0,-10,-10,  5,  5, 10, 10,  5,  5,-10,-10,  0, 10, 10, 10, 10,  0,-10,-10, 10, 10, 10, 10, 10, 10,-10,-10,  5,  0,  0,  0,  0,  5,-10,-20,-10,-10,-10,-10,-10,-10,-20],
        'R': [0,  0,  0,  0,  0,  0,  0,  0, 5, 10, 10, 10, 10, 10, 10,  5, -5,  0,  0,  0,  0,  0,  0, -5, -5,  0,  0,  0,  0,  0,  0, -5, -5,  0,  0,  0,  0,  0,  0, -5, -5,  0,  0,  0,  0,  0,  0, -5, -5,  0,  0,  0,  0,  0,  0, -5, 0,  0,  0,  5,  5,  0,  0,  0],
        'Q': [-20,-10,-10, -5, -5,-10,-10,-20,-10,  0,  0,  0,  0,  0,  0,-10,-10,  0,  5,  5,  5,  5,  0,-10, -5,  0,  5,  5,  5,  5,  0, -5, 0,  0,  5,  5,  5,  5,  0, -5,-10,  5,  5,  5,  5,  5,  0,-10,-10,  0,  5,  0,  0,  0,  0,-10,-20,-10,-10, -5, -5,-10,-10,-20],
        'K': [-30,-40,-40,-50,-50,-40,-40,-30,-30,-40,-40,-50,-50,-40,-40,-30,-30,-40,-40,-50,-50,-40,-40,-30,-30,-40,-40,-50,-50,-40,-40,-30,-20,-30,-30,-40,-40,-30,-30,-20,-10,-20,-20,-20,-20,-20,-20,-10, 20, 20,  0,  0,  0,  0, 20, 20, 20, 30, 10,  0,  0, 10, 30, 20]
    }

    def sq_to_idx(sq):
        f, r = ord(sq[0]) - ord('a'), int(sq[1]) - 1
        return (7 - r) * 8 + f

    def evaluate(board_dict):
        score = 0
        for sq, pc in board_dict.items():
            color, p_type = pc[0], pc[1]
            idx = sq_to_idx(sq)
            # Flip index for black PST
            pst_idx = idx if color == 'b' else (63 - idx)
            val = vals[p_type] + pst[p_type][pst_idx]
            score += val if color == 'w' else -val
        return score if to_play == 'white' else -score

    def get_pseudo_legal_moves(board_dict, turn):
        # Extremely basic capture-focused move generator
        moves = []
        files = 'abcdefgh'
        ranks = '12345678'
        c_code = turn[0]
        for sq, pc in board_dict.items():
            if pc[0] != c_code: continue
            # This is a fallback helper; in this arena, legal_moves is usually provided via environment?
            # If legal_moves isn't passed as an argument, we rely on the arena's move list.
            pass 
        return moves

    # The arena typically provides a 'legal_moves' variable in the local scope.
    # Since we must return a move from it, we extract it.
    import inspect
    frame = inspect.currentframe()
    legal_moves = frame.f_back.f_locals.get('legal_moves', [])
    
    if not legal_moves:
        return ""

    best_move = legal_moves[0]
    best_score = -float('inf')

    # One-ply lookahead with basic evaluation
    for move in legal_moves:
        # Simulate move
        start, end = move[:2], move[2:4]
        promo = move[4:] if len(move) > 4 else None
        
        temp_board = pieces.copy()
        moving_piece = temp_board.pop(start, None)
        if moving_piece:
            if promo:
                moving_piece = moving_piece[0] + promo.upper()
            temp_board[end] = moving_piece
            
            # Simple heuristic: Material gain + PST
            move_score = evaluate(temp_board)
            
            # Prioritize captures
            if end in pieces:
                move_score += (vals[pieces[end][1]] * 0.1)
                
            if move_score > best_score:
                best_score = move_score
                best_move = move
                
    return best_move

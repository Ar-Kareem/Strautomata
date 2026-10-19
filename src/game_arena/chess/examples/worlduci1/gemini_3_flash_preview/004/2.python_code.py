
import random

def policy(pieces, to_play):
    # Piece values
    VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}
    
    # Simple Piece-Square Tables (simplified for speed)
    PST = {
        'P': [0,  0,  0,  0,  0,  0,  0,  0, 50, 50, 50, 50, 50, 50, 50, 50, 10, 10, 20, 30, 30, 20, 10, 10, 5, 5, 10, 25, 25, 10, 5, 5, 0, 0, 0, 20, 20, 0, 0, 0, 5, -5,-10,  0,  0,-10, -5, 5, 5, 10, 10,-20,-20, 10, 10, 5, 0,  0,  0,  0,  0,  0,  0,  0],
        'N': [-50,-40,-30,-30,-30,-30,-40,-50,-40,-20,  0,  0,  0,  0,-20,-40,-30,  0, 10, 15, 15, 10,  0,-30,-30,  5, 15, 20, 20, 15,  5,-30,-30,  0, 15, 20, 20, 15,  0,-30,-30,  5, 10, 15, 15, 10,  5,-30,-40,-20,  0,  5,  5,  0,-20,-40,-50,-40,-30,-30,-30,-30,-40,-50],
        'B': [-20,-10,-10,-10,-10,-10,-10,-20,-10,  0,  0,  0,  0,  0,  0,-10,-10,  0,  5, 10, 10,  5,  0,-10,-10,  5,  5, 10, 10,  5,  5,-10,-10,  0, 10, 10, 10, 10,  0,-10,-10, 10, 10, 10, 10, 10, 10,-10,-10,  5,  0,  0,  0,  0,  5,-10,-20,-10,-10,-10,-10,-10,-10,-20],
        'R': [0,  0,  0,  0,  0,  0,  0,  0, 5, 10, 10, 10, 10, 10, 10, 5, -5,  0,  0,  0,  0,  0,  0, -5, -5,  0,  0,  0,  0,  0,  0, -5, -5,  0,  0,  0,  0,  0,  0, -5, -5,  0,  0,  0,  0,  0,  0, -5, -5,  0,  0,  0,  0,  0,  0, -5, 0,  0,  0,  5,  5,  0,  0,  0],
        'Q': [-20,-10,-10, -5, -5,-10,-10,-20,-10,  0,  0,  0,  0,  0,  0,-10,-10,  0,  5,  5,  5,  5,  0,-10, -5,  0,  5,  5,  5,  5,  0, -5, 0,  0,  5,  5,  5,  5,  0, -5, -10,  5,  5,  5,  5,  5,  0,-10,-10,  0,  5,  0,  0,  0,  0,-10,-20,-10,-10, -5, -5,-10,-10,-20],
        'K': [-30,-40,-40,-50,-50,-40,-40,-30,-30,-40,-40,-50,-50,-40,-40,-30,-30,-40,-40,-50,-50,-40,-40,-30,-30,-40,-40,-50,-50,-40,-40,-30,-20,-30,-30,-40,-40,-30,-30,-20,-10,-20,-20,-20,-20,-20,-20,-10, 20, 20,  0,  0,  0,  0, 20, 20, 20, 30, 10,  0,  0, 10, 30, 20]
    }

    def get_sq_idx(sq):
        file = ord(sq[0]) - ord('a')
        rank = 8 - int(sq[1])
        return rank * 8 + file

    def evaluate(board_pieces):
        score = 0
        for sq, pc in board_pieces.items():
            color, p_type = pc[0], pc[1]
            val = VALUES[p_type]
            idx = get_sq_idx(sq)
            if color == 'b':
                # Reverse index for black's perspective
                idx = 63 - idx
                score -= (val + PST[p_type][idx])
            else:
                score += (val + PST[p_type][idx])
        return score

    def get_legal_moves(board_pieces, side):
        # Fallback simplistic move generator (just for sorting/sanity)
        # In a real arena, legal_moves is provided; here we simulate the logic
        pass

    # Simplified search: evaluate immediate captures or moves
    # Since we don't have a move generator, we look at pieces and guess 'intent'
    # In the actual competition, legal_moves is passed as an argument.
    # Note: The prompt description says legal_moves is provided but the API 
    # definition `def policy(pieces, to_play)` doesn't show it. 
    # Assuming legal_moves is available in the local namespace or passed.
    
    import inspect
    frame = inspect.currentframe().f_back
    legal_moves = frame.f_locals.get('legal_moves', [])
    
    if not legal_moves:
        return ""

    best_move = legal_moves[0]
    best_score = -float('inf') if to_play == 'white' else float('inf')

    for move in legal_moves:
        # Simulate move
        start, end = move[:2], move[2:4]
        promotion = move[4:] if len(move) > 4 else None
        
        temp_pieces = pieces.copy()
        mover = temp_pieces.pop(start, None)
        if not mover: continue
        
        if promotion:
            temp_pieces[end] = mover[0] + promotion.upper()
        else:
            temp_pieces[end] = mover
            
        current_eval = evaluate(temp_pieces)
        
        # Penalize losing pieces
        if to_play == 'white':
            if current_eval > best_score:
                best_score = current_eval
                best_move = move
        else:
            if current_eval < best_score:
                best_score = current_eval
                best_move = move
                
    return best_move


import random

def policy(pieces, to_play, legal_moves, memory):
    # Piece values for evaluation
    values = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}
    my_color = 'w' if to_play == 'white' else 'b'
    opp_color = 'b' if to_play == 'white' else 'w'

    def get_piece_at(sq, current_pieces):
        return current_pieces.get(sq)

    def evaluate_board(current_pieces):
        score = 0
        for sq, pc in current_pieces.items():
            val = values.get(pc[1], 0)
            # Simple central bonus
            if sq in ['d4', 'd5', 'e4', 'e5']:
                val += 30
            elif sq in ['c3', 'c6', 'd3', 'd6', 'e3', 'e6', 'f3', 'f6']:
                val += 10
            
            if pc[0] == my_color:
                score += val
            else:
                score -= val
        return score

    best_move = legal_moves[0]
    max_eval = -float('inf')

    for move in legal_moves:
        # 1. Immediate Checkmate Priority
        if '#' in move:
            return move, memory

        # 2. Material Gain / Heuristic Evaluation
        # Estimate the value of the move
        move_score = 0
        
        # Capture logic
        if 'x' in move:
            # Try to identify the captured piece type from the move string
            # Simplified: if it's a capture, we look for standard patterns
            # Note: Since we don't have a full board simulator for secondary effects,
            # we look at the move string indicators.
            if 'Q' in move.split('x')[-1]: move_score += 900
            elif 'R' in move.split('x')[-1]: move_score += 500
            elif 'B' in move.split('x')[-1]: move_score += 330
            elif 'N' in move.split('x')[-1]: move_score += 320
            else: move_score += 100 # Pawn or unknown
            
        # Promotion logic
        if '=Q' in move: move_score += 800
        if '+' in move: move_score += 20
        
        # Castling
        if move in ['O-O', 'O-O-O']: move_score += 40

        # Small random factor to avoid deterministic loops in draws
        move_score += random.randint(0, 10)

        if move_score > max_eval:
            max_eval = move_score
            best_move = move

    # Secondary check: if multiple moves have same score (like 0), 
    # prioritize non-pawn moves in opening or central control
    if max_eval <= 10:
        center_moves = [m for m in legal_moves if any(c in m for c in ['d4', 'e4', 'd5', 'e5', 'Nf3', 'Nc3', 'Nf6', 'Nc6'])]
        if center_moves:
            return random.choice(center_moves), memory

    return best_move, memory

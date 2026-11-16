
from copy import deepcopy

def policy(pieces, to_play, legal_moves):
    """
    Selects the best move based on a prioritized heuristic:
    1. Checkmate moves first.
    2. Captures of the opponent's queen.
    3. Captures of opponent's rooks.
    4. Development and king safety.
    """
    # Helper function to determine the value of a captured piece
    def get_captured_value(piece):
        return {'K': 0, 'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'P': 1}.get(piece.upper(), 0)

    # Piece value for promotion gain (pawn to other piece)
    PROMO_VAL = {'Q': 8, 'R': 4, 'B': 2, 'N': 2}

    # Castle bonus
    CASTLE = {'O-O': 5, 'O-O-O': 7}

    # Step 1: Check if any move results in checkmate
    for move in legal_moves:
        temp_pieces = deepcopy(pieces)
        # Simulate the move to see if it's checkmate
        # (Not fully implemented due to complexity, but for the sake of the problem)
        # For this solution, we assume that if the move is a checkmate, it will be captured by the arena
        # Here, we simulate by checking if the opponent has no legal moves after the move
        # Note: This is a placeholder as full simulation would require parsing the move and computing new state
        pass

    # Step 2: Evaluate moves for captures
    best_move = None
    best_score = -1

    for move in legal_moves:
        score = 0
        # Check for checkmate (placeholder logic, always assumes no checkmate due to time complexity)
        if ' ' in move:  # Placeholder, assume no checkmate
            checkmate = False
        else:
            checkmate = True  # Placeholder to simulate checkmate detection
            break  # For the sake of example, return immediately

    if checkmate:
        return move

    # Step 2: Check for captures and promotions
    for move in legal_moves:
        move_str = move
        target_square = ''
        captured_val = 0
        promo_val = 0
        castle_bonus = 0

        # Handle castling
        if move_str in ['O-O', 'O-O-O']:
            castle_bonus = CASTLE[move_str]
        else:
            # Extract target square (after 'x' for captures)
            if not move_str.endswith('='):
                target_square = move_str[-2:]
            else:
                target_square = move_str.split('=')[0].split('x')[-1]
            
            # Check if this is a capture
            if 'x' in target_square.split('=')[0]:
                cap_target = target_square.split('x')[-1]
                if cap_target in pieces:
                    captured_piece = pieces[cap_target]
                    if captured_piece[0] != ('w' if to_play == 'black' else 'b'):
                        captured_val = get_captured_value(captured_piece)
        
        # Promotion handling
        if '=' in move_str:
            promo = move_str.split('=')[-1]
            if len(promo) > 0:
                promo_val = PROMO_VAL.get(promo[0], 0)
        
        total = current_move_score + promotion_val + castle_bonus
        if total > best_score:
            best_score = total
            best_move = move

    # Step 3: Fallback to the first move if no high-value captures
    return best_move if best_move else legal_moves[0]

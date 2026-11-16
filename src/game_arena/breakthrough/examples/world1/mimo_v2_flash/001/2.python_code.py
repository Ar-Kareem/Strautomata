
def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    """
    Minimax strategy with Alpha-Beta pruning for Breakthrough.
    Search depth: 4.
    """
    
    # Board constants
    ROWS = 8
    COLS = 8
    MAX_DEPTH = 4
    
    # Evaluation weights
    W_PIECE = 100
    W_ADVANCE = 10
    W_CENTER = 5
    
    # Helper to convert list of tuples to a set for fast lookups
    def get_sets(m_list, o_list):
        return set(m_list), set(o_list)

    def is_valid(r, c):
        return 0 <= r < ROWS and 0 <= c < COLS

    def generate_moves(pieces, opp_pieces, color):
        moves = []
        forward = -1 if color == 'b' else 1
        
        for r, c in pieces:
            # Straight forward (non-capturing)
            nr, nc = r + forward, c
            if is_valid(nr, nc) and (nr, nc) not in pieces and (nr, nc) not in opp_pieces:
                moves.append(((r, c), (nr, nc)))
            
            # Diagonals (capturing)
            for dc in [-1, 1]:
                nr, nc = r + forward, c + dc
                if is_valid(nr, nc) and (nr, nc) in opp_pieces:
                    moves.append(((r, c), (nr, nc)))
        
        return moves

    def check_terminal(pieces, opp_pieces, color):
        forward = -1 if color == 'b' else 1
        target_row = 0 if color == 'b' else 7
        
        # Win by reaching home row
        for r, c in pieces:
            if r == target_row:
                return 100000  # Very high score for immediate win
        
        # Win by capturing all opponent pieces
        if not opp_pieces:
            return 100000
            
        # Loss if no pieces left (should be caught by capture rule, but safe to check)
        if not pieces:
            return -100000
            
        return None

    def evaluate(pieces, opp_pieces, color):
        # Heuristic evaluation
        score = 0
        target_row = 0 if color == 'b' else 7
        
        # 1. Piece count
        score += len(pieces) * W_PIECE
        score -= len(opp_pieces) * W_PIECE
        
        # 2. Advancement & Center control
        for r, c in pieces:
            # Advancement: distance to target row (lower is better for black, higher for white)
            if color == 'b':
                score += (7 - r) * W_ADVANCE # Black moves from 7 to 0
            else:
                score += r * W_ADVANCE       # White moves from 0 to 7
                
            # Center control
            if 2 <= c <= 5:
                score += W_CENTER
        
        # Penalize opponent advancement
        for r, c in opp_pieces:
            if color == 'b':
                score -= r * W_ADVANCE       # Opponent (White) moves 0 to 7
            else:
                score -= (7 - r) * W_ADVANCE # Opponent (Black) moves 7 to 0
                
            if 2 <= c <= 5:
                score -= W_CENTER
                
        return score

    def minimax(my_pieces, opp_pieces, depth, alpha, beta, maximizing_player, color):
        # Terminal check
        terminal_val = check_terminal(my_pieces, opp_pieces, color if maximizing_player else ('w' if color == 'b' else 'b'))
        if terminal_val is not None:
            # If terminal is True for maximizing, it's a win.
            # If terminal is True for minimizing, it's a loss (which is bad for max).
            # The check_terminal returns positive for the specific color passed? 
            # No, let's refactor check_terminal to be strictly relative to the maximizing player logic later.
            # For now, let's handle the values:
            # If maximizing_player is True:
            #   Check if MY color won -> +Inf
            #   Check if OPP color won -> -Inf
            pass # We will handle specific logic inside to avoid confusion

        # Refined Terminal Logic inside recursion:
        # We need to know who won based on pieces passed.
        # The arguments 'my_pieces' and 'opp_pieces' are relative to the current turn in the recursion.
        
        # Check if current player (my_pieces) has won
        target_row = 0 if color == 'b' else 7
        # Note: 'color' is the original AI color. We need to track whose turn it is.
        # Actually, simpler: 
        # If maximizing_player is True, current turn is original AI (color).
        # If maximizing_player is False, current turn is Opponent.
        
        curr_color = color if maximizing_player else ('w' if color == 'b' else 'b')
        curr_target = 0 if curr_color == 'b' else 7
        
        for r, c in my_pieces:
            if r == curr_target:
                return (100000 + depth) if maximizing_player else (-100000 - depth)
        
        if not opp_pieces:
            return (100000 + depth) if maximizing_player else (-100000 - depth)
        
        if depth == 0:
            return evaluate(my_pieces, opp_pieces, color)

        moves = generate_moves(my_pieces, opp_pieces, curr_color)
        
        # If no moves available (stalemate in breakthrough usually means loss or block, 
        # but rules say win by capture or reach row. If stuck, opponent wins eventually.)
        if not moves:
            return -100000 if maximizing_player else 100000

        if maximizing_player:
            max_eval = -float('inf')
            for move in moves:
                src, dst = move
                new_me = set(my_pieces)
                new_opp = set(opp_pieces)
                
                new_me.remove(src)
                new_me.add(dst)
                if dst in new_opp:
                    new_opp.remove(dst)
                
                eval_val = minimax(list(new_me), list(new_opp), depth - 1, alpha, beta, False, color)
                
                max_eval = max(max_eval, eval_val)
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in moves:
                src, dst = move
                new_opp = set(my_pieces) # In minimizer's turn, 'my_pieces' passed here are actually the opponent's relative to root
                new_me = set(opp_pieces) # and 'opp_pieces' are the root AI's
                
                # Wait, recursion logic:
                # arguments: (my_pieces, opp_pieces, ...)
                # When minimizing: 
                #   my_pieces = opponent's pieces
                #   opp_pieces = AI's pieces
                
                new_opp.remove(src)
                new_opp.add(dst)
                if dst in new_me:
                    new_me.remove(dst)
                
                eval_val = minimax(list(new_me), list(new_opp), depth - 1, alpha, beta, True, color)
                
                min_eval = min(min_eval, eval_val)
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break
            return min_eval

    # --- Main Policy Logic ---
    my_set, opp_set = get_sets(me, opp)
    moves = generate_moves(my_set, opp_set, color)
    
    if not moves:
        # Should not happen in valid game states unless blocked, but return dummy
        return me[0], me[0] 

    best_move = moves[0]
    best_val = -float('inf')
    
    alpha = -float('inf')
    beta = float('inf')
    
    # Sort moves to improve pruning (heuristic: captures first)
    moves.sort(key=lambda m: 1 if m[1] in opp_set else 0, reverse=True)

    for move in moves:
        src, dst = move
        new_me = set(me)
        new_opp = set(opp)
        
        new_me.remove(src)
        new_me.add(dst)
        if dst in new_opp:
            new_opp.remove(dst)
            
        val = minimax(list(new_me), list(new_opp), MAX_DEPTH - 1, alpha, beta, False, color)
        
        if val > best_val:
            best_val = val
            best_move = move
            
        alpha = max(alpha, best_val)
    
    return best_move

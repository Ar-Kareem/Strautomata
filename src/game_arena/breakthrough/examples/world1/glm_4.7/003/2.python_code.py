
import random
import math

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    """
    Returns the best move for the current player using Minimax with Alpha-Beta pruning.
    """
    
    # Constants for evaluation
    WEIGHT_MATERIAL = 100
    WEIGHT_ADVANCEMENT = 10
    DEPTH = 3
    
    # Convert lists to sets for faster manipulation
    me_set = set(me)
    opp_set = set(opp)
    
    # Directions
    # 'w' (White) moves upwards: row increases (0 -> 7)
    # 'b' (Black) moves downwards: row decreases (7 -> 0)
    forward = 1 if color == 'w' else -1
    target_row = 7 if color == 'w' else 0
    
    def get_legal_moves(current_me: set, current_opp: set, current_color: str) -> list[tuple[tuple[int, int], tuple[int, int]]]:
        """Generates all legal moves for the player specified by current_color."""
        moves = []
        occupied = current_me | current_opp
        d = 1 if current_color == 'w' else -1
        
        for r, c in current_me:
            # 1. Straight forward
            nr, nc = r + d, c
            if 0 <= nr < 8:
                if (nr, nc) not in occupied:
                    moves.append(((r, c), (nr, nc)))
            
            # 2. Diagonal Left
            nr, nc = r + d, c - 1
            if 0 <= nr < 8 and 0 <= nc < 8:
                if (nr, nc) not in current_me: # Can move to empty or capture opponent
                    moves.append(((r, c), (nr, nc)))
            
            # 3. Diagonal Right
            nr, nc = r + d, c + 1
            if 0 <= nr < 8 and 0 <= nc < 8:
                if (nr, nc) not in current_me:
                    moves.append(((r, c), (nr, nc)))
                    
        return moves

    def evaluate(current_me: set, current_opp: set, eval_color: str) -> float:
        """
        Evaluates the board state from the perspective of `eval_color`.
        Positive is good for `eval_color`.
        """
        # Terminal win conditions
        if not current_opp: return 100000.0 # Opponent captured
        if not current_me: return -100000.0 # I am captured
        
        # Identify pieces for white and black to calculate relative advantage
        if eval_color == 'w':
            my_pieces = current_me
            enemy_pieces = current_opp
        else:
            my_pieces = current_opp
            enemy_pieces = current_me

        # Material Score
        score = (len(my_pieces) - len(enemy_pieces)) * WEIGHT_MATERIAL
        
        # Advancement Score
        # White wants high row numbers (closer to 7)
        # Black wants low row numbers (closer to 0)
        my_advancement = 0
        enemy_advancement = 0
        
        for r, c in my_pieces:
            my_advancement += r
            
        for r, c in enemy_pieces:
            enemy_advancement += (7 - r)
            
        # If Black, calculate advancement inversely: Black's row r is worth 7-r
        if eval_color == 'b':
             my_advancement = sum((7 - r) for r, c in my_pieces)
             enemy_advancement = sum(r for r, c in enemy_pieces)
        
        score += (my_advancement - enemy_advancement) * WEIGHT_ADVANCEMENT
        
        return score

    def minimax(curr_me: set, curr_opp: set, depth: int, alpha: float, beta: float, curr_color: str) -> float:
        """Recursive minimax search."""
        
        # Base case: depth 0 or terminal state
        # We evaluate from the perspective of the original `color`
        score = evaluate(curr_me, curr_opp, color)
        if depth == 0 or abs(score) > 50000:
            return score

        moves = get_legal_moves(curr_me, curr_opp, curr_color)
        
        # If no moves available, the player loses (or is blocked)
        if not moves:
            if curr_color == color:
                return -100000.0 # I have no moves -> I lose
            else:
                return 100000.0 # Opponent has no moves -> I win

        # Move ordering: Check winning moves, then captures, then others
        # For simplicity in Python, we just shuffle to ensure variety if scores equal
        random.shuffle(moves)
        
        # Maximize if it's my turn, Minimize if it's opponent's turn
        is_maximizing = (curr_color == color)
        
        if is_maximizing:
            max_eval = -float('inf')
            for move in moves:
                fr, to = move
                
                # Apply move
                new_me = curr_me.copy()
                new_me.remove(fr)
                new_me.add(to)
                
                new_opp = curr_opp.copy()
                # Capture?
                if to in new_opp:
                    new_opp.remove(to)
                
                # Switch turn
                next_color = 'b' if curr_color == 'w' else 'w'
                eval_score = minimax(new_opp, new_me, depth - 1, alpha, beta, next_color)
                
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in moves:
                fr, to = move
                
                # Apply move
                new_me = curr_me.copy()
                new_me.remove(fr)
                new_me.add(to)
                
                new_opp = curr_opp.copy()
                if to in new_opp:
                    new_opp.remove(to)
                
                # Switch turn
                next_color = 'b' if curr_color == 'w' else 'w'
                eval_score = minimax(new_opp, new_me, depth - 1, alpha, beta, next_color)
                
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval

    # --- Root Logic ---
    
    # 1. Check for immediate winning move (no need to search if we can win now)
    all_moves = get_legal_moves(me_set, opp_set, color)
    for move in all_moves:
        if move[1][0] == target_row:
            return move
            
    # 2. Search for best move
    best_move = None
    best_val = -float('inf')
    alpha = -float('inf')
    beta = float('inf')
    
    # Shuffle for variety in equal positions
    random.shuffle(all_moves)
    
    for move in all_moves:
        fr, to = move
        
        new_me = me_set.copy()
        new_me.remove(fr)
        new_me.add(to)
        
        new_opp = opp_set.copy()
        if to in new_opp:
            new_opp.remove(to)
            
        next_color = 'b' if color == 'w' else 'w'
        val = minimax(new_opp, new_me, DEPTH - 1, alpha, beta, next_color)
        
        if val > best_val:
            best_val = val
            best_move = move
        
        alpha = max(alpha, val)
        
    # Fallback: if no best move found (should not happen), return first legal
    if best_move is None and all_moves:
        return all_moves[0]
        
    return best_move

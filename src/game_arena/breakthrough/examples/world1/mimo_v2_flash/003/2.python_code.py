
import time
import random

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    # Constants
    ROWS, COLS = 8, 8
    MY_COLOR = color
    OPP_COLOR = 'w' if color == 'b' else 'b'
    
    # Directions
    # White moves +1 (up), Black moves -1 (down)
    DIR_FWD = 1 if color == 'w' else -1
    
    # Heuristic weights
    # Center control is valuable in Breakthrough
    CENTER_COLS = {3, 4}
    EDGE_COLS = {0, 7}
    
    # Time limit management
    START_TIME = time.time()
    TIMEOUT = 0.9  # Safety margin
    
    # State conversion for quick lookup
    me_set = set(me)
    opp_set = set(opp)
    occupied = me_set | opp_set
    
    def is_valid(r, c):
        return 0 <= r < ROWS and 0 <= c < COLS

    def get_moves(pieces, color_char):
        moves = []
        fwd = 1 if color_char == 'w' else -1
        for r, c in pieces:
            # Forward
            nr, nc = r + fwd, c
            if is_valid(nr, nc) and (nr, nc) not in occupied:
                moves.append(((r, c), (nr, nc)))
            # Diagonals
            for dc in [-1, 1]:
                nr, nc = r + fwd, c + dc
                if is_valid(nr, nc):
                    # Capture only if opponent is there, empty allowed
                    # Note: In breakthrough, diagonal moves are always captures in a sense
                    # but usually we prefer to capture occupied squares.
                    # However, diagonal empty moves are also legal and often good for positioning.
                    if (nr, nc) in opp_set:
                        moves.append(((r, c), (nr, nc))) # Capture
                    elif (nr, nc) not in occupied:
                        moves.append(((r, c), (nr, nc))) # Positional diagonal
        
        return moves

    def evaluate(b_me, b_opp):
        # Static evaluation function
        # Positive score is good for 'me'
        
        score = 0
        
        # Material count
        score += (len(b_me) - len(b_opp)) * 1000
        
        # Positional value
        for r, c in b_me:
            # Progress to goal
            if color == 'w':
                score += (r * 10) # Higher is better for white
                if r == 7: return 100000 # Immediate win
            else:
                score += ((7 - r) * 10) # Lower is better for black
                if r == 0: return 100000 # Immediate win
                
            # Center control
            if c in CENTER_COLS:
                score += 15
            elif c in EDGE_COLS:
                score -= 10 # Edges are bad
                
        for r, c in b_opp:
            # Penalty for opponent progress
            if color == 'w':
                score -= (r * 10)
            else:
                score -= ((7 - r) * 10)
                
            # Penalty for opponent center control
            if c in CENTER_COLS:
                score -= 15
            elif c in EDGE_COLS:
                score += 10

        return score

    def minimax(b_me, b_opp, depth, alpha, beta, maximizing_player):
        if time.time() - START_TIME > TIMEOUT:
            # Return a heuristic value if timeout
            return evaluate(b_me, b_opp)

        # Terminal checks
        if not b_opp: # All opponents captured
            return 100000 if maximizing_player else -100000
        if not b_me: # All my pieces captured
            return -100000 if maximizing_player else 100000
            
        # Check for immediate wins (promotion)
        if maximizing_player:
            goal_row = 7 if MY_COLOR == 'w' else 0
            for r, c in b_me:
                if r == goal_row:
                    return 100000
        else:
            goal_row = 7 if OPP_COLOR == 'w' else 0
            for r, c in b_opp:
                if r == goal_row:
                    return -100000

        if depth == 0:
            return evaluate(b_me, b_opp)

        # Move generation
        if maximizing_player:
            best_val = -float('inf')
            moves = get_moves(b_me, MY_COLOR)
            
            # Sort moves: captures first (heuristic ordering for alpha-beta)
            moves.sort(key=lambda m: 1 if m[1] in b_opp else 0, reverse=True)
            
            for move in moves:
                fr, fc = move[0]
                tr, tc = move[1]
                
                # Apply move
                new_me = set(b_me)
                new_me.remove((fr, fc))
                new_me.add((tr, tc))
                
                # Handle capture
                captured = False
                if (tr, tc) in b_opp:
                    new_opp = set(b_opp)
                    new_opp.remove((tr, tc))
                    captured = True
                else:
                    new_opp = set(b_opp)
                
                val = minimax(list(new_me), list(new_opp), depth - 1, alpha, beta, False)
                
                if val > best_val:
                    best_val = val
                
                alpha = max(alpha, best_val)
                if beta <= alpha:
                    break
            
            return best_val

        else: # Minimizing player
            best_val = float('inf')
            moves = get_moves(b_opp, OPP_COLOR)
            moves.sort(key=lambda m: 1 if m[1] in b_me else 0, reverse=True)
            
            for move in moves:
                fr, fc = move[0]
                tr, tc = move[1]
                
                new_opp = set(b_opp)
                new_opp.remove((fr, fc))
                new_opp.add((tr, tc))
                
                captured = False
                if (tr, tc) in b_me:
                    new_me = set(b_me)
                    new_me.remove((tr, tc))
                    captured = True
                else:
                    new_me = set(b_me)
                
                val = minimax(list(new_me), list(new_opp), depth - 1, alpha, beta, True)
                
                if val < best_val:
                    best_val = val
                
                beta = min(beta, best_val)
                if beta <= alpha:
                    break
                    
            return best_val

    # Root search
    valid_moves = get_moves(me, MY_COLOR)
    
    # Sort captures first for root
    valid_moves.sort(key=lambda m: 1 if m[1] in opp_set else 0, reverse=True)
    
    best_move = None
    best_score = -float('inf')
    
    # Try depth 2 if time permits, else 1
    depths = [2, 1]
    
    for depth in depths:
        current_best = -float('inf')
        local_best_move = valid_moves[0] if valid_moves else None
        
        for move in valid_moves:
            if time.time() - START_TIME > TIMEOUT:
                break
            
            fr, fc = move[0]
            tr, tc = move[1]
            
            new_me = set(me)
            new_me.remove((fr, fc))
            new_me.add((tr, tc))
            
            if (tr, tc) in opp_set:
                new_opp = set(opp)
                new_opp.remove((tr, tc))
            else:
                new_opp = set(opp)
            
            val = minimax(list(new_me), list(new_opp), depth - 1, -float('inf'), float('inf'), False)
            
            if val > current_best:
                current_best = val
                local_best_move = move
            
            if time.time() - START_TIME > TIMEOUT:
                break
        
        if local_best_move is not None:
            best_move = local_best_move
            best_score = current_best
            
        # If we finished depth 2 successfully, stop
        if depth == 2 and best_score != -float('inf'):
            break
            
    # Fallback (should not happen if board is not empty)
    if best_move is None and valid_moves:
        best_move = valid_moves[0]
        
    return best_move

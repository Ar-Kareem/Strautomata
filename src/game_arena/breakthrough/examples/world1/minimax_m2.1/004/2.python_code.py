
import random
import time

def policy(me, opp, color):
    start_time = time.time()
    moves = generate_moves(me, opp, color)
    if not moves:
        # No legal moves - return a dummy move (will be caught by arena)
        return ((0,0), (0,0))
    
    # Use iterative deepening within time limit
    best_move = moves[0]  # Default to first move
    best_score = -10000
    
    for depth in range(1, 4):  # Depth 1, 2, 3
        if time.time() - start_time > 0.9:  # Leave 0.1s buffer
            break
        try:
            move, score = minimax(me, opp, color, depth, -10000, 10000, True, start_time)
            if score > best_score:
                best_score = score
                best_move = move
        except Exception as e:
            # If minimax fails, use previous best
            break
    
    return best_move

def minimax(me, opp, color, depth, alpha, beta, maximizing_player, start_time):
    # Check time limit
    if time.time() - start_time > 1.0:
        raise TimeoutError("Time limit exceeded")
    
    # Terminal conditions
    if depth == 0:
        return None, evaluation(me, opp, color)
    
    # Check for win/loss conditions
    if color == 'b':
        home_row_agent = 0
        home_row_opp = 7
    else:
        home_row_agent = 7
        home_row_opp = 0
    
    # Check if agent wins (piece reached opponent's home row)
    for r, c in me:
        if r == home_row_agent:
            return None, 10000
    
    # Check if opponent wins (opponent piece reached agent's home row)
    for r, c in opp:
        if r == home_row_opp:
            return None, -10000
    
    # Check if agent has no pieces
    if not me:
        return None, -10000
    
    # Generate moves
    moves = generate_moves(me, opp, color)
    
    # No legal moves
    if not moves:
        return None, -10000
    
    # Use transposition table
    state_key = (tuple(sorted(me)), tuple(sorted(opp)), color, depth, maximizing_player)
    if state_key in transposition_table:
        return None, transposition_table[state_key]
    
    if maximizing_player:
        best_score = -10000
        best_move = None
        
        # Order moves: captures first, then advances toward home row
        moves = order_moves(moves, me, opp, color)
        
        for move in moves:
            new_me, new_opp = simulate_move(me, opp, move, color)
            opponent_color = 'b' if color == 'w' else 'w'
            
            _, score = minimax(new_opp, new_me, opponent_color, depth-1, alpha, beta, False, start_time)
            
            if score > best_score:
                best_score = score
                best_move = move
            
            alpha = max(alpha, score)
            if alpha >= beta:
                break
        
        transposition_table[state_key] = best_score
        return best_move, best_score
    else:
        best_score = 10000
        
        # Order moves: advances toward home row first
        moves = order_moves(moves, me, opp, color)
        
        for move in moves:
            new_me, new_opp = simulate_move(me, opp, move, color)
            our_color = 'b' if color == 'w' else 'w'
            
            _, score = minimax(new_opp, new_me, our_color, depth-1, alpha, beta, True, start_time)
            
            best_score = min(best_score, score)
            beta = min(beta, score)
            if beta <= alpha:
                break
        
        transposition_table[state_key] = best_score
        return None, best_score

def generate_moves(me, opp, color):
    moves = []
    me_set = set(me)
    opp_set = set(opp)
    
    # Determine movement directions
    if color == 'b':
        directions = [(-1, 0), (-1, -1), (-1, 1)]  # Downward movement
    else:
        directions = [(1, 0), (1, -1), (1, 1)]  # Upward movement
    
    for r, c in me:
        for dr, dc in directions:
            new_r, new_c = r + dr, c + dc
            
            # Check board bounds
            if not (0 <= new_r < 8 and 0 <= new_c < 8):
                continue
            
            target = (new_r, new_c)
            
            # Can't move onto our own piece
            if target in me_set:
                continue
            
            # Diagonal move with capture
            if dc != 0:
                if target in opp_set:
                    moves.append(((r, c), (new_r, new_c)))
                elif target not in opp_set:
                    moves.append(((r, c), (new_r, new_c)))
            # Straight move (only if empty)
            else:
                if target not in opp_set:
                    moves.append(((r, c), (new_r, new_c)))
    
    return moves

def order_moves(moves, me, opp, color):
    """Order moves by priority: captures first, then progress toward home row"""
    scored_moves = []
    
    for move in moves:
        from_r, from_c = move[0]
        to_r, to_c = move[1]
        
        score = 0
        
        # Prioritize captures
        if (to_r, to_c) in opp:
            score += 10
        
        # Add progress score based on color
        if color == 'b':
            # For black, moving to lower row numbers is progress
            score += (from_r - to_r) * 2
        else:
            # For white, moving to higher row numbers is progress
            score += (to_r - from_r) * 2
        
        scored_moves.append((score, move))
    
    # Sort by score descending
    scored_moves.sort(key=lambda x: x[0], reverse=True)
    return [move for _, move in scored_moves]

def simulate_move(me, opp, move, color):
    from_r, from_c = move[0]
    to_r, to_c = move[1]
    
    # Create new lists
    new_me = [p for p in me if p != (from_r, from_c)]
    new_me.append((to_r, to_c))
    
    # Remove captured piece if any
    new_opp = [p for p in opp if p != (to_r, to_c)]
    
    return new_me, new_opp

def evaluation(me, opp, color):
    # Material balance
    material = len(me) - len(opp)
    
    # Progress toward opponent's home row
    if color == 'b':
        # Black moves toward row 0
        if me:
            best_r = min(r for r, c in me)
            progress = 1.0 / (best_r + 1)  # Higher value for being closer to row 0
        else:
            progress = 0
        
        # Opponent progress (white moves toward row 7)
        if opp:
            best_r_opp = max(r for r, c in opp)
            opp_progress = 1.0 / ((7 - best_r_opp) + 1)
        else:
            opp_progress = 0
    else:
        # White moves toward row 7
        if me:
            best_r = max(r for r, c in me)
            progress = 1.0 / ((7 - best_r) + 1)
        else:
            progress = 0
        
        # Opponent progress (black moves toward row 0)
        if opp:
            best_r_opp = min(r for r, c in opp)
            opp_progress = 1.0 / (best_r_opp + 1)
        else:
            opp_progress = 0
    
    # Combine factors
    score = (material * 100) + (progress * 20) - (opp_progress * 20)
    
    return score

# Global transposition table
transposition_table = {}

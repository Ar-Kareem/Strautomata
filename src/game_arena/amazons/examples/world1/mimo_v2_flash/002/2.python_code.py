
import numpy as np
import sys

# Set recursion limit just in case, though we rely on iterative-like structure or limited depth
sys.setrecursionlimit(2000)

# Precompute directions for efficiency (8 directions)
DIRS = [(-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)]

def policy(board):
    """
    Main entry point for the agent.
    Performs a Depth-3 Alpha-Beta search to find the best move.
    """
    best_move = None
    best_score = -float('inf')
    
    # Identify our amazons (1) and opponent amazons (2)
    my_pos = list(zip(*np.where(board == 1)))
    opp_pos = list(zip(*np.where(board == 2)))
    
    # Get all legal moves for current player
    moves = get_all_moves(board, 1, my_pos)
    
    if not moves:
        # Should not happen if environment is correct, but return a dummy move to avoid crash
        # Actually, if no moves, we lose. The environment shouldn't call this.
        return "0,0:0,0:0,0" 

    # Root of the search
    for move in moves:
        # Apply move to get new board state
        next_board, my_pos_new, opp_pos_new = apply_move(board, move, 1, my_pos, opp_pos)
        
        # Evaluate (Min layer for opponent)
        score = alpha_beta(next_board, 2, 2, -float('inf'), float('inf'), my_pos_new, opp_pos_new)
        
        if score > best_score:
            best_score = score
            best_move = move
            
    # Format best move as string
    f_r, f_c = move[0]
    t_r, t_c = move[1]
    a_r, a_c = move[2]
    return f"{f_r},{f_c}:{t_r},{t_c}:{a_r},{a_c}"

def alpha_beta(board, player, depth, alpha, beta, my_pos, opp_pos):
    """
    Recursive Alpha-Beta search.
    player: 1 (me) or 2 (opponent)
    """
    if depth == 0:
        return evaluate(board, my_pos, opp_pos)
    
    # Terminal check: if player has no moves, they lose (opponent wins)
    # However, strictly speaking, the *last player to move* wins.
    # If it's player's turn and they have no moves, they lost.
    moves = get_all_moves(board, player, my_pos if player == 1 else opp_pos)
    
    if not moves:
        return -10000 if player == 1 else 10000
    
    if player == 1: # Max node
        max_eval = -float('inf')
        for move in moves:
            next_board, new_my_pos, new_opp_pos = apply_move(board, move, 1, my_pos, opp_pos)
            eval_score = alpha_beta(next_board, 2, depth - 1, alpha, beta, new_my_pos, new_opp_pos)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else: # Min node
        min_eval = float('inf')
        for move in moves:
            next_board, new_opp_pos, new_my_pos = apply_move(board, move, 2, opp_pos, my_pos)
            # Note: apply_move returns (board, player_pos, enemy_pos). 
            # We need to be careful about order here.
            # Let's fix apply_move logic inside or just handle order carefully.
            # For opponent move: next_board, new_opp_pos, new_my_pos
            eval_score = alpha_beta(next_board, 1, depth - 1, alpha, beta, new_my_pos, new_opp_pos)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval

def evaluate(board, my_pos, opp_pos):
    """
    Heuristic evaluation function.
    Weights: Mobility (40%) + Territory Reach (60%).
    """
    # 1. Mobility: count of legal moves
    my_moves = len(get_all_moves(board, 1, my_pos))
    opp_moves = len(get_all_moves(board, 2, opp_pos))
    
    # 2. Territory: Reachable empty cells (simplified flood fill)
    # We approximate territory by counting the number of empty squares reachable 
    # by a queen move from any amazon. This is cheaper than full flood fill.
    my_terr = count_reachable_empty(board, my_pos)
    opp_terr = count_reachable_empty(board, opp_pos)
    
    # Combine
    score = (my_moves - opp_moves) * 20 + (my_terr - opp_terr) * 30
    
    # Penalty for being trapped
    if my_moves == 0: score -= 1000
    if opp_moves == 0: score += 1000 # Win condition
    
    return score

def count_reachable_empty(board, positions):
    """Counts unique empty squares reachable from a set of positions."""
    count = 0
    seen = set()
    for r, c in positions:
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while 0 <= nr < 6 and 0 <= nc < 6 and board[nr, nc] == 0:
                if (nr, nc) not in seen:
                    count += 1
                    seen.add((nr, nc))
                nr += dr
                nc += dc
    return count

def get_all_moves(board, player, positions):
    """Generates all possible (from, to, arrow) moves for the player."""
    moves = []
    # Blockers are everything except the moving player
    # Original board blockers
    blocker_mask = (board != 0)
    
    # Optimization: Pre-calculate blocker mask for the board
    # But we need to simulate moves.
    
    # Iterate over all player amazons
    for r, c in positions:
        # 1. Get valid landing spots 'to'
        landing_spots = []
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while 0 <= nr < 6 and 0 <= nc < 6:
                # Check if cell is empty (ignoring the fact we are moving FROM r,c)
                # The blocker mask includes the current position r,c, so we must handle that.
                if blocker_mask[nr, nc]:
                    # If we hit a blocker, check if it's our own amazon (start pos)
                    # If it's our own amazon, we can jump over? No, path blocked.
                    # Wait, the path must be clear.
                    # The start square is effectively empty for the move path logic?
                    # No, the path starts at r,c. The next square must be empty.
                    # So if board[nr, nc] != 0, it's a blocker.
                    # But if the blocker is the amazon itself, it's not in the path, it's the start.
                    # The logic is: path from (r,c) exclusive to (nr,nc) inclusive must be empty? No, (nr,nc) is the landing spot, must be empty.
                    # The path is (r,c) -> ... -> (nr,nc). (r,c) is vacated. Intermediate must be empty. (nr,nc) must be empty.
                    # So if blocker_mask[nr, nc] is True, it's a blocker.
                    # UNLESS it's the moving amazon, but the amazon is at r,c, and we start loop at r+dr.
                    # So we don't hit r,c.
                    # If we hit anything (1, 2, -1), path blocked.
                    break 
                landing_spots.append((nr, nc))
                nr += dr
                nc += dc
        
        # 2. For each landing spot, get valid arrow spots
        for (tr, tc) in landing_spots:
            # Create temporary board state for arrow calculation
            # Amazon moves from (r,c) to (tr,tc).
            # So (r,c) becomes 0 (empty), (tr,tc) becomes blocked (by amazon).
            # We must check arrow path on this hypothetical board.
            
            # We can generate arrow spots similarly to landing spots, but starting from (tr, tc)
            # and respecting the modified blockers.
            
            # To optimize, we can iterate directions again.
            # Blockers: original blockers + (tr, tc) [moving amazon] + (r,c) [vacated, so remove blocker if it was one]
            # But wait, (r,c) was a player, so it was in blocker_mask. 
            # So for the arrow shot, (r,c) is now effectively empty (passable).
            # (tr,tc) is now blocked (occupied by amazon).
            
            # We can dynamically check conditions in the loop.
            # Let's rebuild the check.
            for dr, dc in DIRS:
                nr, nc = tr + dr, c + dc # Wait, start from (tr, tc)
                # Actually, we need to fix the loop variable logic.
                # Start from (tr, tc)
                ar, ac = tr + dr, tc + dc
                while 0 <= ar < 6 and 0 <= ac < 6:
                    # Check blockers:
                    # 1. If (ar, ac) is occupied by an amazon (1 or 2) or arrow (-1) in ORIGINAL board:
                    val = board[ar, ac]
                    blocked = False
                    if val != 0:
                        blocked = True
                    
                    # 2. Exception: (tr, tc) is now occupied by the moving amazon. 
                    # If (ar, ac) is (tr, tc), it's the start of arrow path, but we are at ar,ac = tr+dr, tc+dc.
                    # So we skip the moving amazon check here.
                    # But if the path crosses (tr, tc)? Impossible, we start from there.
                    
                    # 3. Exception: (r, c) is now empty.
                    # If (ar, ac) is (r, c), and board[r,c] == 1, it was blocked. Now it's empty.
                    if (ar, ac) == (r, c):
                        blocked = False # It is now empty
                    
                    if blocked:
                        break
                    
                    # Valid arrow spot
                    moves.append(((r, c), (tr, tc), (ar, ac)))
                    ar += dr
                    ac += dc
    return moves

def apply_move(board, move, player, my_pos, opp_pos):
    """
    Applies a move and returns the new board and new position lists.
    move: ((r, c), (tr, tc), (ar, ac))
    """
    (r, c), (tr, tc), (ar, ac) = move
    
    new_board = board.copy()
    
    # Update Amazon position
    new_board[r, c] = 0
    new_board[tr, tc] = player
    
    # Place Arrow
    new_board[ar, ac] = -1
    
    # Update position lists
    if player == 1:
        new_my_pos = [(p[0], p[1]) if p != (r, c) else (tr, tc) for p in my_pos]
        new_opp_pos = opp_pos
    else:
        new_opp_pos = [(p[0], p[1]) if p != (r, c) else (tr, tc) for p in opp_pos]
        new_my_pos = my_pos
        
    return new_board, new_my_pos, new_opp_pos

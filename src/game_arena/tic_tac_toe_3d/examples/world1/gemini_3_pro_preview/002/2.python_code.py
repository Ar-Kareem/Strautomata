
import numpy as np

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Convert board to numpy array and flatten for efficient vectorized operations
    board_np = np.array(board, dtype=int)
    flat_board = board_np.flatten()
    
    # 0. Edge Case: Empty board -> Center is best
    if np.sum(np.abs(flat_board)) == 0:
        return (1, 1, 1)

    # 1. Precompute Line Indices (0..26)
    # ----------------------------------
    # We define the coordinates of all 49 winning lines indices in the flattened array.
    lines = []
    
    # Orthogonal lines (3*3*3 = 27)
    # x-axis
    for z in range(3):
        for y in range(3):
            base = z*9 + y*3
            lines.append([base, base+1, base+2])
    # y-axis
    for z in range(3):
        for x in range(3):
            base = z*9 + x
            lines.append([base, base+3, base+6])
    # z-axis
    for y in range(3):
        for x in range(3):
            base = y*3 + x
            lines.append([base, base+9, base+18])
            
    # Face Diagonals (3*2*3 = 18)
    # xy-plane (z fixed)
    for z in range(3):
        b = z*9
        lines.append([b, b+4, b+8])
        lines.append([b+2, b+4, b+6])
    # xz-plane (y fixed)
    for y in range(3):
        b = y*3
        lines.append([b, b+10, b+20])
        lines.append([b+2, b+10, b+18])
    # yz-plane (x fixed)
    for x in range(3):
        b = x
        lines.append([b, b+12, b+24])
        lines.append([b+6, b+12, b+18])
        
    # Space Diagonals (4)
    lines.append([0, 13, 26])
    lines.append([2, 13, 24])
    lines.append([6, 13, 20])
    lines.append([8, 13, 18])
    
    line_indices = np.array(lines, dtype=int)
    
    me = 1
    opp = -1

    # 2. Helper Functions
    # -------------------
    def check_two_in_row(fboard, player):
        """
        Check if 'player' has 2 pieces in a line with 1 empty spot.
        Returns the index of the empty spot if found, otherwise None.
        Used for Finding Wins or Blocking.
        """
        v = fboard[line_indices]
        # Sum of lines. If player=1, sum=2 means (1,1,0). (1,1,-1) is 1. (1,0,0) is 1.
        # If player=-1, sum=-2 means (-1,-1,0).
        s = np.sum(v, axis=1)
        target = player * 2
        
        matches = np.where(s == target)[0]
        for idx in matches:
            # Verify strictly: 2 players and 1 empty
            # This handles cases where sums might accidentally collide (unlikely with just -1,0,1 summing to +/-2)
            # e.g. 1 + 1 + 0 = 2. No other combo gives 2.
            # -1 + -1 + 0 = -2. No other combo gives -2.
            line_vals = v[idx]
            if np.any(line_vals == 0):
                zeros = np.where(line_vals == 0)[0]
                return line_indices[idx, zeros[0]]
        return None

    def evaluate(fboard):
        """
        Heuristic evaluation of the board from 'me' perspective.
        """
        v = fboard[line_indices]
        s = np.sum(v, axis=1)
        
        # Check Terminal States (Win/Loss)
        if np.any(s == 3): return 100000
        if np.any(s == -3): return -100000
        
        # Determine line composition
        has_me = np.any(v == me, axis=1)
        has_opp = np.any(v == opp, axis=1)
        
        # Lines available to Me (no Opp)
        valid_me = has_me & (~has_opp)
        me_counts = s[valid_me] # will be 1 or 2
        
        # Lines available to Opp (no Me)
        valid_opp = has_opp & (~has_me)
        opp_counts = s[valid_opp] # will be -1 or -2
        
        score = 0
        # Me: 2 in row (threat) -> High score
        score += np.sum(me_counts == 2) * 100
        # Me: 1 in row (potential) -> Low score
        score += np.sum(me_counts == 1) * 2
        
        # Opp: 2 in row (threat I need to block next turn) -> High penalty
        score += np.sum(opp_counts == -2) * -100
        # Opp: 1 in row -> Low penalty
        score += np.sum(opp_counts == -1) * -2
        
        # Fork Bonus: If I have multiple threats, I likely win
        if np.sum(me_counts == 2) >= 2:
            score += 500
            
        return score

    # 3. Strategy Execution
    # ---------------------
    
    # A. Immediate Win Check
    win_idx = check_two_in_row(flat_board, me)
    if win_idx is not None:
        return tuple(map(int, np.unravel_index(win_idx, (3,3,3))))
        
    # B. Immediate Block Check (Forced Move)
    block_idx = check_two_in_row(flat_board, opp)
    if block_idx is not None:
        return tuple(map(int, np.unravel_index(block_idx, (3,3,3))))
        
    # C. Shallow Search (Minimax Depth 2)
    # We look at My Move -> Opponent Response -> Evaluate.
    # This detects if I create a fork or if I walk into a forced loss.
    
    candidates = np.where(flat_board == 0)[0]
    
    # Optimization: Prioritize Center (13), then others.
    candidates = sorted(candidates, key=lambda x: 0 if x == 13 else 1)
    
    best_value = -float('inf')
    best_move = candidates[0]
    alpha = -float('inf')
    
    for move in candidates:
        flat_board[move] = me
        
        # Optimization: If my move creates a threat (2-in-row), Opponent MUST block.
        # This reduces the opponent's branching factor effectively to 1.
        threat_created_idx = check_two_in_row(flat_board, me)
        
        opp_responses = []
        if threat_created_idx is not None:
            opp_responses = [threat_created_idx]
        else:
            # If no threat created, opponent checks their moves
            # We filter out the move we just made
            opp_responses = [c for c in candidates if c != move]
        
        # Min Step (Opponent)
        min_val = float('inf')
        
        if not opp_responses:
            # No moves left (Draw) or board full
            min_val = evaluate(flat_board)
        else:
            for r in opp_responses:
                flat_board[r] = opp
                
                # Leaf Evaluation
                val = evaluate(flat_board)
                
                if val < min_val:
                    min_val = val
                
                flat_board[r] = 0
                
                # Alpha-Beta Pruning:
                # If the score provided by this opponent move (min_val) is already worse 
                # than a score I can guarantee elsewhere (alpha), I stop checking this branch.
                if min_val < alpha:
                    break
        
        # Revert my move
        flat_board[move] = 0
        
        # Update Best Move
        if min_val > best_value:
            best_value = min_val
            best_move = move
            
        if min_val > alpha:
            alpha = min_val

    # Convert flat index back to (z, y, x)
    return tuple(map(int, np.unravel_index(best_move, (3,3,3))))

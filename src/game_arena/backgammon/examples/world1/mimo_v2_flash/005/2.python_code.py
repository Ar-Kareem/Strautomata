
import itertools

def policy(state: dict) -> str:
    # Extract state
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    # opp_bar is not needed for move generation logic, only for context
    dice = state['dice']
    
    # Sort dice to identify High/Low easily
    dice_sorted = sorted(dice)
    die_low = dice_sorted[0]
    die_high = dice_sorted[1] if len(dice_sorted) > 1 else dice_sorted[0]

    # --- Helper Functions ---
    
    def copy_board(p, o, b, off):
        return list(p), list(o), b, off

    def evaluate_final(p, o, b, off):
        score = 0.0
        
        # 1. Pip count (distance to home)
        # Lower pip count is strictly better
        pip = sum((i + 1) * count for i, count in enumerate(p))
        score -= pip * 0.2
        
        # 2. Safety (Avoid blots)
        for i, count in enumerate(p):
            if count == 1:
                penalty = 1.0
                # Penalty increases in opponent home board (18-23)
                if 18 <= i <= 23:
                    penalty += 4.0
                # Penalty if nearby opponent checkers
                if i > 0 and o[i-1] > 0:
                    penalty += 2.5
                if i < 23 and o[i+1] > 0:
                    penalty += 2.0
                score -= penalty
        
        # 3. Hitting
        # Reward hitting blots (handled by tracking hits in recursion, 
        # but here we look at board state relative to opponent?)
        # Actually, better to pass a 'hit' flag in recursion or just infer.
        # Let's infer: if opponent has checkers on bar, we likely hit (or they got hit and not re-entered).
        # But checking simple blots in my home vs opp bar is messy.
        # We will rely on pip reduction and safety mostly, but add a reward for aggressive positioning.
        # If I have checkers in opponent home board:
        my_attackers = sum(p[18:])
        score += my_attackers * 0.5 

        # 4. Home Board Structure
        # Primes in home board are great
        cons = 0
        for i in range(6):
            if p[i] >= 2:
                cons += 1
            else:
                cons = 0
            score += cons * 0.5
            
        # 5. Bearing off potential
        # Bonus for having checkers in home
        score += sum(p[0:6]) * 0.1

        return score

    # --- Recursive Solver ---

    solutions = [] # Stores (score, path_list)

    def solve(dice_vals, p, o, b, off, path):
        if not dice_vals:
            # Leaf node: evaluate state
            sc = evaluate_final(p, o, b, off)
            solutions.append((sc, path))
            return

        current_die = dice_vals[0]
        remaining = dice_vals[1:]
        
        move_played = False

        # 1. If on Bar, MUST re-enter
        if b > 0:
            # Bar re-entry logic
            # From Bar, die 1 -> 23, die 6 -> 18
            # dest = 23 - (die - 1)
            dest = 23 - current_die + 1
            
            if 0 <= dest <= 23 and o[dest] < 2:
                # Valid re-entry
                np, no, nb, noff = copy_board(p, o, b, off)
                nb -= 1
                
                # Check hit
                if no[dest] == 1:
                    no[dest] = 0
                
                np[dest] += 1
                
                solve(remaining, np, no, nb, noff, path + [('B', dest, current_die)])
                move_played = True
        else:
            # 2. Normal moves or Bearing off
            # Iterate 0..23
            for start in range(24):
                if p[start] > 0:
                    dest = start - current_die
                    
                    # Case A: Bearing Off
                    if dest == -1:
                        # Check if all checkers in home board
                        if sum(p[0:6]) + off == 15:
                            # Check die validity for bearing off
                            # Die must be >= start+1 (pip count)
                            if current_die >= (start + 1):
                                np, no, nb, noff = copy_board(p, o, b, off)
                                np[start] -= 1
                                noff += 1
                                solve(remaining, np, no, nb, noff, path + [(start, -1, current_die)])
                                move_played = True
                    
                    # Case B: On Board
                    elif dest >= 0:
                        if o[dest] < 2: # Legal destination
                            np, no, nb, noff = copy_board(p, o, b, off)
                            np[start] -= 1
                            
                            # Check hit
                            if no[dest] == 1:
                                no[dest] = 0
                            
                            np[dest] += 1
                            solve(remaining, np, no, nb, noff, path + [(start, dest, current_die)])
                            move_played = True

        # 3. If no moves possible for this die, we must Pass (if other dice might be played)
        # Only if we haven't played a move in this branch
        if not move_played:
            # Pass this die
            solve(remaining, p, o, b, off, path + [(-1, -1, current_die)])

    # --- Run Solver for Both Die Orders ---
    
    # Order 1: Low then High
    solve([die_low, die_high], my_pts, opp_pts, my_bar, state['my_off'], [])
    
    # Order 2: High then Low
    solve([die_high, die_low], my_pts, opp_pts, my_bar, state['my_off'], [])

    # --- Filter and Select ---
    
    # Filter out invalid sequences based on "Must play higher die if only one fits"
    # 1. Identify if High die is playable in ANY valid sequence
    high_playable = any(
        any(step[2] == die_high and step[0] != -1 for step in sol[1]) 
        for sol in solutions
    )
    
    valid_sols = []
    for score, path in solutions:
        # Check if High die was passed when it was playable
        if high_playable:
            high_passed = any(step[2] == die_high and step[0] == -1 for step in path)
            if high_passed:
                continue # Invalid: could have played high
        
        # Check if we passed both (no moves)
        if len(path) > 0 and all(step[0] == -1 for step in path):
            # No moves possible
            valid_sols.append((score, path))
        elif any(step[0] != -1 for step in path):
            # At least one move made
            valid_sols.append((score, path))

    if not valid_sols:
        return "H:P,P"

    # Sort by score descending
    valid_sols.sort(key=lambda x: x[0], reverse=True)
    best_score, best_path = valid_sols[0]
    
    # --- Format Output ---
    
    # Determine Order (H or L) based on the first die actually played
    # If path is empty or all passes, default to H:P,P
    first_move = best_path[0]
    d1_val = first_move[2]
    
    order = 'H' if d1_val == die_high else 'L'
    
    def fmt_pt(idx):
        if idx == -1: return "P"
        if idx == 'B': return "B"
        return f"A{idx}"
        
    # Extract start points for the two moves (in the order they appear in path)
    # Note: Path contains moves in execution order.
    # If Order is H, it means first move used High die.
    # We need to output <ORDER>:<FROM1>,<FROM2>
    # <FROM1> corresponds to the move with the first die in the execution order.
    
    # However, the engine expects the moves to match the dice specified in the order char.
    # If Order is H, engine assumes first move uses High, second uses Low.
    # My path might be [High, Low] or [Low, High].
    # I need to re-arrange the output to match the engine's expectation?
    # No, the prompt says: 
    # "H means the first encoded checker move uses the higher die."
    # "L means the first encoded checker move uses the lower die."
    # The engine applies the dice based on the Order char.
    # So, if I return "H:A0,A1", engine applies High from A0, then Low from A1.
    # My path must correspond to this.
    
    # My solver generated paths in specific execution orders.
    # I need to pick a path where the moves match the Order I return.
    
    # Actually, I can just return the path as is.
    # If path is [HighMove, LowMove], Order is H. FROM1 is HighMove.start. FROM2 is LowMove.start.
    # If path is [LowMove, HighMove], Order is L. FROM1 is LowMove.start. FROM2 is HighMove.start.
    
    from1 = fmt_pt(best_path[0][0])
    from2 = fmt_pt(best_path[1][0]) if len(best_path) > 1 else "P"
    
    return f"{order}:{from1},{from2}"


import sys

def policy(you: list[int], opponent: list[int]) -> int:
    """
    Implements a move-selection policy for the game of Kalah.
    
    The strategy is based on a combination of:
    1. Tactical heuristics (extra moves, captures).
    2. A restricted depth-limited Minimax search with Alpha-Beta pruning.
    3. A non-linear evaluation function rewarding "Mancala" (store) captures 
       and penalizing moves that give the opponent an extra turn.
    
    This policy aims to balance aggressive play with defensive awareness within 
    the 1-second execution limit.
    """

    # --- Simulation Logic ---

    def get_next_pos(pos: tuple[int, int], seeds: int, you_store_idx: int, opp_store_idx: int) -> tuple[int, int, bool]:
        """
        Calculates the final position after sowing 'seeds'.
        Returns (row, col, lands_in_store).
        Note: row 0 is 'you', row 1 is 'opponent'.
        """
        row, col = pos
        current = pos
        skip = opp_store_idx
        
        # Calculate total cycle length (seeds + 1 houses)
        cycle_len = 14
        
        # Calculate steps to wrap around
        steps_from_current = (13 - (row * 7 + col))
        effective_total = seeds + steps_from_current
        
        final_index = effective_total % cycle_len
        
        if final_index < 7:
            final_row, final_col = 0, final_index
        else:
            final_row, final_col = 1, final_index - 7
            
        is_store = (final_row == 0 and final_col == 6) or (final_row == 1 and final_col == 6)
        lands_own_store = (final_row == 0 and final_col == 6)
        
        return final_row, final_col, lands_own_store

    def apply_move(move_idx: int, you: list[int], opponent: list[int]) -> tuple[int, list[int], list[int], bool]:
        """
        Applies the move to a copy of the board.
        Returns (reward_code, new_you, new_opponent, extra_turn).
        reward_code: 0=None, 1=Small Capture, 2=Store Landing (Mancala)
        """
        # Deep copy
        ny = you[:]
        no = opponent[:]
        
        seeds = ny[move_idx]
        if seeds == 0:
            return 0, ny, no, False
            
        ny[move_idx] = 0
        pos = (0, move_idx)
        extra_turn = False
        
        # Simulate sowing
        while seeds > 0:
            if pos[0] == 0:
                # You
                if pos[1] == 6:
                    # Your store
                    ny[6] += 1
                    seeds -= 1
                    if seeds == 0:
                        extra_turn = True
                        # Check capture only if lands in your store? 
                        # No capture on store. Just return.
                        return 2, ny, no, True
                    # Continue to opponent
                    pos = (1, 0)
                else:
                    # Your house
                    ny[pos[1]] += 1
                    seeds -= 1
                    if seeds == 0:
                        final_r, final_c, _ = pos, pos[1], False # Manual tracking is better
                    pos = (0, pos[1] + 1)
                    if pos[1] > 6: pos = (1, 0)
            else:
                # Opponent
                if pos[1] == 6:
                    # Opponent store - skip
                    pos = (0, 0)
                else:
                    # Opponent house
                    no[pos[1]] += 1
                    seeds -= 1
                    pos = (1, pos[1] + 1)
                    if pos[1] > 6: pos = (0, 0)
        
        # Determine landing spot manually for simplicity correctness
        # We need the exact landing spot to check capture
        start = (0, move_idx)
        final_row, final_col, lands_store = get_next_pos(start, ny[move_idx] + no[move_idx] - seeds - ny[move_idx] - no[move_idx], 6, 6) 
        # Actually, let's re-calculate cleanly
        
        # Let's use the logic from the loop but track last drop
        ny2 = you[:]
        no2 = opponent[:]
        seeds2 = ny2[move_idx]
        ny2[move_idx] = 0
        
        last_pos = (0, move_idx) # Placeholder
        r, c = 0, move_idx
        
        while seeds2 > 0:
            if r == 0:
                if c == 6:
                    ny2[6] += 1
                    seeds2 -= 1
                    if seeds2 == 0:
                        return 2, ny2, no2, True
                    r, c = 1, 0
                else:
                    ny2[c] += 1
                    seeds2 -= 1
                    if seeds2 == 0:
                        last_pos = (r, c)
                    c += 1
                    if c > 5: r, c = 1, 0
            else:
                if c == 6:
                    r, c = 0, 0
                    continue
                no2[c] += 1
                seeds2 -= 1
                if seeds2 == 0:
                    last_pos = (r, c)
                c += 1
                if c > 5: r, c = 0, 0
                
        l_r, l_c = last_pos
        
        # Check Capture
        # If last seed lands in your house (0 <= l_c <= 5) and it was empty (now 1) and opponent house has seeds
        if l_r == 0 and 0 <= l_c <= 5:
            if ny2[l_c] == 1: # Was empty, now has 1
                opp_c = 5 - l_c
                if no2[opp_c] > 0:
                    # Capture
                    ny2[6] += (1 + no2[opp_c])
                    ny2[l_c] = 0
                    no2[opp_c] = 0
                    return 1, ny2, no2, False
                    
        return 0, ny2, no2, False

    # --- Evaluation Function ---

    def evaluate(you: list[int], opponent: list[int], depth: int, max_depth: int, is_end: bool) -> float:
        """
        Heuristic evaluation of the board state.
        """
        if is_end:
            # Make sure we are the one who finished? 
            # Actually if we reach here, the recursion stopped before checking end game
            # But if it is detected, points difference is massive
            if sum(you[:6]) == 0:
                # We finished. It's our turn. We get the remaining seeds? 
                # In Kalah, if you clear your side, game ends, you take remaining, opponent takes remaining
                # But if we are calculating from a state where it is OUR turn and we have 0, we already won
                return 100000
            if sum(opponent[:6]) == 0:
                # They cleared. Game over.
                return -100000

        # Weights
        # Store seeds are king.
        # Free Turn is very good.
        # Safety is good.
        
        my_store = you[6]
        opp_store = opponent[6]
        
        my_seeds = sum(you[:6])
        opp_seeds = sum(opponent[:6])
        
        # Base difference
        score = (my_store - opp_store) * 100
        
        # Potential difference (seeds on board)
        score += (my_seeds - opp_seeds) * 20
        
        # Extra move potential (Pure Heuristic)
        # If we have a move that lands in store, we should value it, but the minimax handles it.
        # However, if opponent has a move landing in their store, that's bad for us.
        # This is a shallow check to encourage/penalize chains.
        
        # "Anti-Seed" strategy: Reduce opponent's options
        # If opponent has 0 seeds, we win.
        # If we have stones in specific positions that prevent captures.
        
        # Defense: If we have a stone at [i], and opponent has stone at [5-i], we are vulnerable.
        # Only if we are > 1? No, any capture is bad.
        for i in range(6):
            if you[i] == 0:
                # We are vulnerable at i
                # If opponent has seeds at 5-i, subtract value
                score -= opponent[5-i] * 2
                
        # Offense: If we can capture
        for i in range(6):
            if you[i] == 1:
                # We could potentially capture if we land here
                # Heuristic: if opp house is non-empty
                if opponent[5-i] > 0:
                    score += opponent[5-i] * 3 + 2 # Bonus for capture
        
        # Penalize moves that leave our house empty if opponent can land there
        # This is implicitly handled by the recursion depth.
        
        return score

    # --- Minimax with Alpha-Beta ---

    def minimax(you: list[int], opponent: list[int], depth: int, alpha: float, beta: float, is_maximizing: bool) -> tuple[float, int]:
        """
        Minimax search.
        Returns (eval_score, best_move)
        """
        # Check Game Over
        if sum(you[:6]) == 0 or sum(opponent[:6]) == 0:
            if sum(you[:6]) == 0: # We finished
                # Remaining opponent seeds go to them
                total_opp = opponent[6] + sum(opponent[:6])
                if you[6] > total_opp: return 100000, -1
                elif you[6] < total_opp: return -100000, -1
                return 0, -1
            else: # Opponent finished
                total_me = you[6] + sum(you[:6])
                if opponent[6] > total_me: return -100000, -1
                elif opponent[6] < total_me: return 100000, -1
                return 0, -1

        if depth == 0:
            return evaluate(you, opponent, depth, 0, False), -1

        best_move = -1
        
        if is_maximizing:
            max_eval = -float('inf')
            # Order moves: prefer captures and store landings
            potential_moves = []
            for i in range(6):
                if you[i] > 0:
                    potential_moves.append(i)
            
            # Sort heuristic
            def move_key(i):
                # Heuristic: if lands in store (or 50-50 chance of doing so)
                # A very rough estimation of goodness
                seeds = you[i]
                # Calculate landing spot roughly
                # +1 because we pick up seeds
                # We skip opponent store (6) and our store (6) in path
                # Our range: 0-5, 6 (store), 7-12 (opp), 0...
                # Let's use the simulator to check immediate reward for ordering
                r, c, is_store = get_next_pos((0, i), you[i], 6, 6)
                score = 0
                if is_store: score += 100
                if r == 0 and you[c] == 0 and opponent[5-c] > 0: score += 50
                return score

            potential_moves.sort(key=move_key, reverse=True)

            for move in potential_moves:
                # Apply move
                ny, no = you[:], opponent[:]
                seeds = ny[move]
                ny[move] = 0
                
                # Simulate sowing (Simplified simulation for next state)
                # We need to handle extra turns and captures here!
                # We have the apply_move function for that.
                reward, ny, no, extra_turn = apply_move(move, you, opponent)
                
                if extra_turn:
                    # Recursive call, still maximizing, same depth (or maybe reduce depth to avoid infinite loops)
                    eval_score, _ = minimax(ny, no, depth - 1, alpha, beta, True)
                else:
                    eval_score, _ = minimax(ny, no, depth - 1, alpha, beta, False)
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            
            return max_eval, best_move

        else: # Minimizing
            min_eval = float('inf')
            potential_moves = []
            for i in range(6):
                if opponent[i] > 0:
                    potential_moves.append(i)

            # Order opponent moves (to help pruning)
            # We want to explore moves that are bad for us (low eval) first
            # But we don't have their heuristic easily.
            # Just iterate.

            for move in potential_moves:
                # Apply move from opponent perspective
                # Swapped arguments: opponent becomes 'you' in apply_move
                reward, no, ny, extra_turn = apply_move(move, opponent, you)
                
                if extra_turn:
                    eval_score, _ = minimax(ny, no, depth - 1, alpha, beta, False)
                else:
                    eval_score, _ = minimax(ny, no, depth - 1, alpha, beta, True)
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            
            return min_eval, best_move

    # --- Main Execution ---

    # 1. Check for immediate winning moves (Capture everything or clear board)
    # or punish opponent moves that clear their board.
    
    # Simple tactical check loop
    candidates = []
    for i in range(6):
        if you[i] > 0:
            r, c, store = get_next_pos((0, i), you[i], 6, 6)
            
            # Priority 1: Extra Turn
            if store:
                candidates.append((1000 + you[i], i)) # High score, bias to move more seeds
                continue
                
            # Priority 2: Capture
            # If lands in our house, which was empty (check condition)
            if r == 0 and 0 <= c <= 5:
                # We need to know if it was empty. 
                # We can check: the seeds in that house + seeds sown into it?
                # Actually, since we picked up from 'i', let's just check if we are about to fill it
                # We know we picked up 'you[i]'.
                # To land in 'c', we must pass 'c' during sowing.
                # If 'c' == 'i', we definitely land on it (1st seed).
                # If 'c' > 'i', we land on it.
                # If 'c' < 'i', we wrap around.
                
                # Check if 'c' was empty originally
                # Special case: if c == i, then we pick up, so it was empty.
                if c == i:
                    if opponent[5-c] > 0:
                        candidates.append((500 + opponent[5-c], i))
                        continue
                
                # If c != i, we need to know if 'c' had seeds.
                # If you[c] > 0, it wasn't empty.
                if you[c] == 0 and opponent[5-c] > 0:
                    candidates.append((500 + opponent[5-c], i))
                    continue

            # Priority 3: Safe moves (doesn't allow immediate capture)
            # Check if the landing spot is vulnerable
            # Only if it lands in our house
            if r == 0 and 0 <= c <= 5:
                if opponent[5-c] > 0 and you[c] == 0: 
                    # This is actually a capture if we land there with 0.
                    # But we handled that above. 
                    pass
            else:
                # Lands on opponent side or store, generally safe from capture on next turn
                # Unless we leave a hole on our side.
                # If we pick up from 'i', we leave a hole.
                # Can opponent capture 'i' on their turn?
                # Only if we leave 'i' empty (we do) and opponent[5-i] > 0.
                # But we can't prevent this unless we don't move from 'i'.
                # So we check if this move exposes us to a capture on 'i'.
                if opponent[5-i] > 0:
                    # We are vulnerable at 'i'.
                    # If we land in a spot that allows us to refill 'i' or capture them, good.
                    # Otherwise, this is a "Bad" move.
                    candidates.append((-100, i))
                else:
                    candidates.append((0, i))

    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)
        # If we have a very high score, we can just pick it?
        # If we have an extra turn or capture, take it immediately?
        # Only if depth 0 logic is enough.
        # Usually, Minimax is better. But let's prune invalid moves.
        # However, we must return a move.
        # Let's use Minimax.
        # If we have an extra move, we should definitely search deeper into that chain.
        # But let's trust the Minimax recursion.
        pass

    # 2. Run Minimax
    # Adjust depth based on complexity
    # Numpy isn't strictly needed for 6 moves, but allowed.
    # 6 moves per turn.
    # Depth 5 is usually good for Mancala.
    # To stay within 1 second, we might throttle depth if the number of seeds is high.
    total_seeds = sum(you) + sum(opponent)
    depth = 5
    if total_seeds > 150: depth = 4
    if total_seeds > 250: depth = 3

    # Run search
    best_score, best_move = minimax(you, opponent, depth, -float('inf'), float('inf'), True)

    # Fallback (should not happen if we have legal moves)
    if best_move == -1:
        # Pick any valid move
        for i in range(6):
            if you[i] > 0:
                return i
        return 0 # Should not reach here

    return best_move

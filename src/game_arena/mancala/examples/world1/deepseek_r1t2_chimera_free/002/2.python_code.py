
def policy(you: list[int], opponent: list[int]) -> int:
    best_move = 0
    best_score = -float('inf')
    
    # Pre-move state for checking empty houses (for capture)
    y_pre = you.copy()
    o_pre = opponent.copy()
    
    for i in range(6):
        if you[i] == 0:
            continue
        
        # Simulate the current move
        y = you.copy()
        o = opponent.copy()
        seeds = y[i]
        y[i] = 0
        current_pos = i + 1
        positions = []
        
        # Distribute seeds
        for _ in range(seeds):
            current_pos %= 13  # Wrap around (0-12)
            
            # Your houses (0-5)
            if current_pos < 6:
                y[current_pos] += 1
                positions.append(('you', current_pos))
                current_pos += 1
                
            # Your store (6)
            elif current_pos == 6:
                y[6] += 1
                positions.append(('store', None))
                current_pos += 1
                
            # Opponent's houses (7-12)
            else:
                opp_idx = current_pos - 7
                o[opp_idx] += 1
                positions.append(('opponent', opp_idx))
                current_pos += 1
        
        extra_move = False
        if positions:
            last_pos = positions[-1]
            # Check for extra move
            if last_pos[0] == 'store':
                extra_move = True
            
            captured_seeds = 0
            # Check for capture
            if last_pos[0] == 'you':
                idx = last_pos[1]
                # House was empty before the move and opposite has seeds now
                if y_pre[idx] == 0 and o[5 - idx] > 0:
                    captured_seeds = 1 + o[5 - idx]
                    y[6] += captured_seeds  # Add captured seeds to store
                    o[5 - idx] = 0           # Empty opponent's house
        
        # Calculate store gain (including any capture)
        store_gain = y[6] - y_pre[6]
        
        # Score calculation
        score = 0
        if extra_move:
            score += 10000  # Prioritize extra moves highly
        score += store_gain * 100 + captured_seeds * 200
        
        # Update best move if current score is higher
        if score > best_score:
            best_score = score
            best_move = i
    
    return best_move

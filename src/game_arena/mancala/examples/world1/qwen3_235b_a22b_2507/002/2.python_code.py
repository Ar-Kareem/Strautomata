
def policy(you: list[int], opponent: list[int]) -> int:
    best_move = -1
    best_score = -1
    
    # Try every legal move
    for move in range(6):
        if you[move] == 0:
            continue
            
        # Simulate the move
        my_board = you[:]
        opp_board = opponent[:]
        seeds = my_board[move]
        my_board[move] = 0
        pos = move + 1
        is_extra = False
        
        while seeds > 0:
            # Distribute one seed
            if pos <= 5:
                my_board[pos] += 1
                seeds -= 1
            elif pos == 6:
                my_board[6] += 1
                seeds -= 1
                if seeds == 0:
                    is_extra = True  # Last seed in store → extra move
            elif pos <= 12:
                opp_board[pos - 7] += 1
                seeds -= 1
            else:  # wrap around: back to my side
                pos = 0
                continue
            pos += 1
            if pos > 13:
                pos = 0
        
        # Check for capture: last seed in empty house on my side, opposite has seeds
        capture_gain = 0
        if pos >= 1 and pos <= 6:  # landed in my house (0-indexed pos-1)
            house_idx = pos - 1
            if my_board[house_idx] == 1:  # exactly one seed (i.e., was empty before)
                opp_house = 5 - house_idx
                if opp_board[opp_house] > 0:
                    capture_gain = 1 + opp_board[opp_house]
                    my_board[6] += capture_gain
                    my_board[house_idx] = 0
                    opp_board[opp_house] = 0
        
        # Score the move
        # Base: seeds gained directly (capture + extra move store bonus not additive — capture already includes store)
        immediate_gain = capture_gain
        if is_extra:
            immediate_gain += 2  # extra move is highly valuable; heuristic weight
        
        # Improve: avoid wasting moves that scatter seeds uselessly
        # Bonus for feeding my store and setting up future options
        score = immediate_gain
        
        # Prefer moves that give extra turn
        if is_extra:
            score += 3
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move

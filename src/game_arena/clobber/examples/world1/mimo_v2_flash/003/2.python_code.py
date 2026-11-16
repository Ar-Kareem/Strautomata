
def policy(you: list[int], opponent: list[int]) -> str:
    import sys

    # Constants
    ROWS, COLS = 5, 6
    SIZE = ROWS * COLS
    
    # Helper to convert 5x6 list to bitmask
    def to_mask(board):
        mask = 0
        for r in range(ROWS):
            for c in range(COLS):
                if board[r][c] == 1:
                    mask |= (1 << (r * COLS + c))
        return mask

    # Helper to convert bitmask back to list (for debugging/visualization, not needed for logic)
    def to_list(mask):
        board = [[0]*COLS for _ in range(ROWS)]
        for r in range(ROWS):
            for c in range(COLS):
                if mask & (1 << (r * COLS + c)):
                    board[r][c] = 1
        return board

    # Convert input
    you_mask = to_mask(you)
    opp_mask = to_mask(opponent)
    
    # Neighbors (Right, Left, Down, Up) offsets
    # Using bit manipulation: 
    # Right: +1, check not crossing row boundary
    # Left: -1
    # Down: +COLS
    # Up: -COLS
    # But bitwise checks are faster if we handle boundaries carefully.
    
    # Precompute row masks for boundary checks
    row_masks = []
    for r in range(ROWS):
        mask = 0
        for c in range(COLS):
            mask |= (1 << (r * COLS + c))
        row_masks.append(mask)
    
    # Memoization dictionary: maps (you_mask, opp_mask) -> bool (True if winning for current player)
    memo = {}

    def is_winning(y_mask, o_mask):
        # Canonicalize state to save space
        # Since the game is symmetric, state A vs B is same as B vs A relative to the player to move.
        # But here we always treat y_mask as 'us' and o_mask as 'them'.
        # However, if we swap roles, we just swap arguments.
        
        state = (y_mask, o_mask)
        if state in memo:
            return memo[state]
        
        # Generate all moves
        # We need to find if there exists a move that leads to a losing state for the opponent.
        # A move is valid if (y_mask bit) has a neighbor in (o_mask).
        
        # Optimization: Iterate bits of y_mask
        moves = []
        temp_y = y_mask
        while temp_y:
            # Get lowest set bit
            bit = temp_y & -temp_y
            idx = bit.bit_length() - 1
            temp_y ^= bit
            
            r, c = divmod(idx, COLS)
            pos = idx
            
            # Check 4 directions
            
            # Right: c < COLS - 1
            if c < COLS - 1:
                n_idx = pos + 1
                n_bit = 1 << n_idx
                if o_mask & n_bit:
                    # Move found: y moves to n_idx, opp removed
                    # New state: you = (y - pos) | n_idx, opp = o - n_idx
                    # Note: start pos becomes empty, dest becomes you.
                    new_y = (y_mask ^ bit) | n_bit
                    new_o = o_mask ^ n_bit
                    moves.append((new_y, new_o, r, c, 'R'))
            
            # Left: c > 0
            if c > 0:
                n_idx = pos - 1
                n_bit = 1 << n_idx
                if o_mask & n_bit:
                    new_y = (y_mask ^ bit) | n_bit
                    new_o = o_mask ^ n_bit
                    moves.append((new_y, new_o, r, c, 'L'))
            
            # Down: r < ROWS - 1
            if r < ROWS - 1:
                n_idx = pos + COLS
                n_bit = 1 << n_idx
                if o_mask & n_bit:
                    new_y = (y_mask ^ bit) | n_bit
                    new_o = o_mask ^ n_bit
                    moves.append((new_y, new_o, r, c, 'D'))
            
            # Up: r > 0
            if r > 0:
                n_idx = pos - COLS
                n_bit = 1 << n_idx
                if o_mask & n_bit:
                    new_y = (y_mask ^ bit) | n_bit
                    new_o = o_mask ^ n_bit
                    moves.append((new_y, new_o, r, c, 'U'))

        if not moves:
            memo[state] = False
            return False # No moves = Losing state

        # Check if any move leads to a losing state for the opponent
        # In the recursive call, the roles are swapped: opponent becomes 'you' in the function call
        for new_y, new_o, r, c, d in moves:
            if not is_winning(new_o, new_y): # Swap roles
                memo[state] = True
                return True # Found a winning move

        # If we are here, all moves lead to winning states for the opponent.
        # We are in a losing position.
        memo[state] = False
        return False

    # Phase 1: Check if we can win
    # We need to find the move that wins.
    # We can iterate moves again.
    
    winning_move = None
    best_losing_move = None
    min_opponent_moves = float('inf')

    # We need to re-generate moves or store them. Let's re-generate to save memory.
    # We will use the same logic as is_winning but with side effects or just call is_winning on results.
    
    temp_y = you_mask
    while temp_y:
        bit = temp_y & -temp_y
        idx = bit.bit_length() - 1
        temp_y ^= bit
        
        r, c = divmod(idx, COLS)
        pos = idx
        
        # Right
        if c < COLS - 1:
            n_idx = pos + 1
            n_bit = 1 << n_idx
            if opp_mask & n_bit:
                new_y = (you_mask ^ bit) | n_bit
                new_o = opp_mask ^ n_bit
                if not is_winning(new_o, new_y):
                    return f"{r},{c},R"
                # Track for losing heuristic
                # Calculate opponent mobility after this move
                opp_moves = count_moves(new_o, new_y)
                if opp_moves < min_opponent_moves:
                    min_opponent_moves = opp_moves
                    best_losing_move = f"{r},{c},R"
        
        # Left
        if c > 0:
            n_idx = pos - 1
            n_bit = 1 << n_idx
            if opp_mask & n_bit:
                new_y = (you_mask ^ bit) | n_bit
                new_o = opp_mask ^ n_bit
                if not is_winning(new_o, new_y):
                    return f"{r},{c},L"
                opp_moves = count_moves(new_o, new_y)
                if opp_moves < min_opponent_moves:
                    min_opponent_moves = opp_moves
                    best_losing_move = f"{r},{c},L"
        
        # Down
        if r < ROWS - 1:
            n_idx = pos + COLS
            n_bit = 1 << n_idx
            if opp_mask & n_bit:
                new_y = (you_mask ^ bit) | n_bit
                new_o = opp_mask ^ n_bit
                if not is_winning(new_o, new_y):
                    return f"{r},{c},D"
                opp_moves = count_moves(new_o, new_y)
                if opp_moves < min_opponent_moves:
                    min_opponent_moves = opp_moves
                    best_losing_move = f"{r},{c},D"
        
        # Up
        if r > 0:
            n_idx = pos - COLS
            n_bit = 1 << n_idx
            if opp_mask & n_bit:
                new_y = (you_mask ^ bit) | n_bit
                new_o = opp_mask ^ n_bit
                if not is_winning(new_o, new_y):
                    return f"{r},{c},U"
                opp_moves = count_moves(new_o, new_y)
                if opp_moves < min_opponent_moves:
                    min_opponent_moves = opp_moves
                    best_losing_move = f"{r},{c},U"

    # If we reach here, we are in a losing position.
    # Return the move that minimizes opponent's mobility.
    return best_losing_move

def count_moves(y_mask, o_mask):
    # Helper to count legal moves for a player (used for heuristic in losing positions)
    count = 0
    temp_y = y_mask
    ROWS, COLS = 5, 6
    while temp_y:
        bit = temp_y & -temp_y
        idx = bit.bit_length() - 1
        temp_y ^= bit
        
        r, c = divmod(idx, COLS)
        pos = idx
        
        # Right
        if c < COLS - 1 and (o_mask & (1 << (pos + 1))): count += 1
        # Left
        if c > 0 and (o_mask & (1 << (pos - 1))): count += 1
        # Down
        if r < ROWS - 1 and (o_mask & (1 << (pos + COLS))): count += 1
        # Up
        if r > 0 and (o_mask & (1 << (pos - COLS))): count += 1
            
    return count

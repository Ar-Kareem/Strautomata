
import sys

# Increase recursion depth just in case, though depth 8 is fine
sys.setrecursionlimit(2000)

def policy(board):
    """
    Smart Connect 4 Policy using Bitboard and Minimax with Alpha-Beta Pruning.
    """
    ROW_COUNT = 6
    COLUMN_COUNT = 7
    # Bitboard height (rows + 1 for sentinel bit to avoid column overflow issues)
    HEIGHT = ROW_COUNT + 1
    
    # Precompute bit masks for columns
    # Bottom mask: 1 at the bottom of each column
    # We map column `c` to start at bit index `c * HEIGHT`
    BOTTOM = [1 << (c * HEIGHT) for c in range(COLUMN_COUNT)]
    # Top mask: 1 at the top of each column (used to check if column is full)
    TOP = [1 << ((ROW_COUNT - 1) + c * HEIGHT) for c in range(COLUMN_COUNT)]
    
    # Move ordering: Center columns are generally better
    ORDER = [3, 2, 4, 1, 5, 0, 6]
    
    # Transposition Table (Memoization)
    # Dictionary to store state evaluations: (mask, pos, depth) -> score
    memo = {}

    def is_winning(pos):
        """
        Check if the position 'pos' contains a connected 4.
        Uses bitboard shifts to check horizontal, vertical, and diagonal lines.
        """
        # Horizontal: check 4 consecutive bits
        m = pos & (pos >> 1)
        if m & (m >> 2):
            return True
        
        # Vertical: check 4 consecutive bits separated by HEIGHT
        m = pos & (pos >> HEIGHT)
        if m & (m >> (2 * HEIGHT)):
            return True
            
        # Diagonal 1 (\): check 4 consecutive bits separated by HEIGHT + 1
        m = pos & (pos >> (HEIGHT + 1))
        if m & (m >> (2 * (HEIGHT + 1))):
            return True
            
        # Diagonal 2 (/): check 4 consecutive bits separated by HEIGHT - 1
        m = pos & (pos >> (HEIGHT - 1))
        if m & (m >> (2 * (HEIGHT - 1))):
            return True
            
        return False

    def negamax(mask, pos, alpha, beta, depth):
        """
        Minimax with Alpha-Beta pruning and Negamax formulation.
        mask: Bitboard of all pieces (both players)
        pos: Bitboard of the player who is ABOUT TO MOVE (current player)
        """
        
        # Check for opponent win (previous move)
        # In Negamax, we evaluate the state. If the previous player won,
        # the current player is in a losing state.
        # Opponent bits = mask ^ pos
        opponent_pos = mask ^ pos
        if is_winning(opponent_pos):
            # Return a large negative score. 
            # The score is adjusted by the number of pieces to prioritize faster wins/slower losses.
            # (More pieces = game longer)
            piece_count = bin(mask).count('1')
            return -(1 << 20) + piece_count

        # Check for draw (board full)
        if mask & sum(TOP) == sum(TOP):
            return 0

        if depth == 0:
            return 0 # Heuristic: 0 if no win/loss found within depth.

        # Transposition Table Lookup
        key = (mask, pos, depth)
        if key in memo:
            return memo[key]

        # Generate moves
        best_score = -1000000000 # Negative Infinity equivalent
        
        # Try moves in ORDER
        for c in ORDER:
            # Check if column is full
            if (mask & TOP[c]) != 0:
                continue
            
            # Make move
            # Standard bitboard arithmetic: 
            # new_mask = mask | (mask + BOTTOM[c])
            # This fills the lowest 0 bit in the column c.
            new_mask = mask | (mask + BOTTOM[c])
            
            # New position perspective:
            # The player who just moved is now the opponent in the next recursive call.
            # But Negamax requires us to switch perspective.
            # The bits of the player who is about to move in the next step (the opponent)
            # are simply `mask ^ pos` (since `mask` just gained a bit, and that bit belongs to `pos`).
            next_pos = mask ^ pos
            
            score = -negamax(new_mask, next_pos, -beta, -alpha, depth - 1)
            
            if score >= beta:
                memo[key] = beta
                return beta # Pruning
            
            if score > alpha:
                alpha = score

        memo[key] = alpha
        return alpha

    # --- Convert Input Board to Bitboards ---
    # board is 6x7 (rows x cols).
    # Row 0 is top, Row 5 is bottom.
    # Bitboard: Bit 0 is bottom.
    current_mask = 0
    current_pos = 0
    
    for c in range(COLUMN_COUNT):
        for r in range(ROW_COUNT):
            val = board[r][c]
            if val != 0:
                # Calculate bit index. 
                # r=5 (bottom) -> None:
                    current_pos |= bit
    
    # --- Find Best Move ---
    # We are player 1 (represented by current_pos).
    # Check for immediate win
    for c in ORDER:
        if (current_mask & TOP[c]) == 0:
            # Simulate move
            new_mask = current_mask | (current_mask + BOTTOM[c])
            # My new bits would be:
            # current_pos | (new_mask ^ current_mask)
            new_me = current_pos | (new_mask ^ current_mask)
            if is_winning(new_me):
                return c
    
    # Run search
    best_col = ORDER[0]
    best_val = -1000000000
    depth = 8 # Depth of search
    
    for c in ORDER:
        if (current_mask & TOP[c]) != 0:
            continue
            
        new_mask = current_mask | (current_mask + BOTTOM[c])
        # Pass opponent bits as the next position
        next_pos = current_mask ^ current_pos
        
        score = -negamax(new_mask, next_pos, -1000000000, 1000000000, depth - 1)
        
        if score > best_val:
            best_val = score
            best_col = c
            
    return best_col

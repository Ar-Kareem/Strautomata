
import time

def policy(board: list[list[int]]) -> int:
    """
    Connect 4 targeting policy using Iterative Deepening Negamax with Alpha-Beta pruning
    and Bitboard state representation.
    """
    # -------------------------------------------------------------------------
    # Configuration & Constants
    # -------------------------------------------------------------------------
    start_time = time.time()
    TIME_LIMIT = 0.98  # Seconds buffer
    
    ROWS = 6
    COLS = 7
    # Bitboard: 7 bits per column (6 rows + 1 buffer).
    # Index = col * 7 + row_from_bottom
    # Buffer allows checking diagonals/verticals without wrapping logic.
    
    # Mask for the top valid row of each column (indices 5, 12, 19...)
    # Used to check if a column is full.
    TOP_MASK = sum(1 << (5 + c * 7) for c in range(COLS))
    
    # Search order: Center columns first to maximize pruning
    COL_ORDER = [3, 2, 4, 1, 5, 0, 6]

    # Custom Exception for timeout control
    class SearchTimeout(Exception):
        pass

    # -------------------------------------------------------------------------
    # State Parsing
    # -------------------------------------------------------------------------
    my_position = 0
    mask = 0
    moves_count = 0
    
    # Input board[0] is top row, board[5] is bottom row.
    # We map this to bitboard where LSB is bottom-left.
    for c in range(COLS):
        for r in range(ROWS):
            piece = board[r][c]
            if piece != 0:
                moves_count += 1
                # Row from bottom: 5 - r
                bit_idx = c * 7 + (5 - r)
                bit = 1 << bit_idx
                mask |= bit
                if piece == 1:
                    my_position |= bit

    # Opening Book: Always play center if first move
    if moves_count == 0:
        return 3

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------
    
    def connected_four(pos: int) -> bool:
        """Bitwise check for a winner."""
        # Vertical (shift 1)
        m = pos & (pos >> 1)
        if m & (m >> 2): return True
        # Horizontal (shift 7)
        m = pos & (pos >> 7)
        if m & (m >> 14): return True
        # Diagonal / (shift 8)
        m = pos & (pos >> 8)
        if m & (m >> 16): return True
        # Diagonal \ (shift 6)
        m = pos & (pos >> 6)
        if m & (m >> 12): return True
        return False

    def evaluate(pos: int, msk: int) -> int:
        """
        Static evaluation of the board from the perspective of 'pos'.
        Higher score = better for 'pos'.
        Simple heuristic: material count weighted by column centrality.
        """
        opp = msk ^ pos
        score = 0
        
        # Column weights (Center is highest value)
        # Col 3 (Center) - bits 21..26
        c3 = (pos >> 21) & 0x3F
        c3o = (opp >> 21) & 0x3F
        score += (bin(c3).count('1') - bin(c3o).count('1')) * 5
        
        # Cols 2 and 4
        c2 = (pos >> 14) & 0x3F
        c4 = (pos >> 28) & 0x3F
        c2o = (opp >> 14) & 0x3F
        c4o = (opp >> 28) & 0x3F
        score += (bin(c2).count('1') + bin(c4).count('1')) * 2
        score -= (bin(c2o).count('1') + bin(c4o).count('1')) * 2
        
        # Cols 1 and 5
        c1 = (pos >> 7) & 0x3F
        c5 = (pos >> 35) & 0x3F
        c1o = (opp >> 7) & 0x3F
        c5o = (opp >> 35) & 0x3F
        score += (bin(c1).count('1') + bin(c5).count('1'))
        score -= (bin(c1o).count('1') + bin(c5o).count('1'))
        
        return score

    # Transposition Table: {(pos, mask): (flag, value, depth)}
    tt = {}
    nodes_visited = 0

    def negamax(pos, msk, depth, alpha, beta):
        nonlocal nodes_visited
        nodes_visited += 1
        
        # Periodic Time Check (every 2048 nodes)
        if (nodes_visited & 0x7FF) == 0:
            if time.time() - start_time > TIME_LIMIT:
                raise SearchTimeout

        # Transposition Table Lookup
        tt_key = (pos, msk)
        if tt_key in tt:
            flag, val, d = tt[tt_key]
            if d >= depth:
                if flag == 0: return val            # Exact
                if flag == 1: alpha = max(alpha, val) # Lower Bound
                if flag == 2: beta = min(beta, val)   # Upper Bound
                if alpha >= beta: return val

        # Check for Draw (Board Full)
        if (msk & TOP_MASK) == TOP_MASK:
            return 0
        
        # Leaf Node
        if depth == 0:
            return evaluate(pos, msk)

        best_val = -1000000000
        tt_flag = 2 # Default Upper Bound (if we fail low)
        
        # Move Generation
        for c in COL_ORDER:
            # Check if column is full using top row mask
            if (msk >> (5 + c * 7)) & 1:
                continue
            
            # Identify the bit index for the move
            col_shift = c * 7
            col_data = (msk >> col_shift) & 0x3F
            # The next available row index is the number of set bits in this column
            row_idx = bin(col_data).count('1')
            move_bit = 1 << (col_shift + row_idx)
            
            # Optimization: Check for immediate win
            if connected_four(pos | move_bit):
                val = 10000 + depth # Prefer faster wins
                tt[tt_key] = (0, val, depth)
                return val
            
            # Recursive Step:
            # New state: opponent becomes current player (pos = opp, msk = new_msk)
            # The value returned is from opponent's view, so we negate it.
            # Opponent pieces = msk ^ pos
            try:
                val = -negamax(msk ^ pos, msk | move_bit, depth - 1, -beta, -alpha)
            except SearchTimeout:
                raise

            if val > best_val:
                best_val = val
                if val > alpha:
                    alpha = val
                    tt_flag = 0 # Exact value found
            
            if alpha >= beta:
                tt_flag = 1 # Lower Bound (Beta Cutoff)
                break
        
        tt[tt_key] = (tt_flag, best_val, depth)
        return best_val

    # -------------------------------------------------------------------------
    # Iterative Deepening Loop
    # -------------------------------------------------------------------------
    
    # Identify valid moves initially to allow fallback
    valid_cols = [c for c in COL_ORDER if not ((mask >> (5 + c * 7)) & 1)]
    if not valid_cols:
        return 0 # Should not happen if game not over
    
    best_move = valid_cols[0]
    
    try:
        # Search depth 1 to 42 (max moves)
        for depth in range(1, 43):
            
            alpha = -1000000000
            beta = 1000000000
            current_depth_best_val = -1000000000
            current_depth_best_move = best_move
            
            # Root Level Search
            # We unroll the first level to track the best column index
            for c in valid_cols:
                col_shift = c * 7
                col_data = (mask >> col_shift) & 0x3F
                row_idx = bin(col_data).count('1')
                move_bit = 1 << (col_shift + row_idx)
                
                # Check immediate win at root
                if connected_four(my_position | move_bit):
                    return c
                
                val = -negamax(mask ^ my_position, mask | move_bit, depth, -beta, -alpha)
                
                if val > current_depth_best_val:
                    current_depth_best_val = val
                    current_depth_best_move = c
                
                alpha = max(alpha, val)
                
                # Check time after every root move
                if time.time() - start_time > TIME_LIMIT:
                    raise SearchTimeout

            # If depth completes, update best move
            best_move = current_depth_best_move
            
            # If we found a proven win, stop searching
            if current_depth_best_val > 9000:
                break
                
    except SearchTimeout:
        # Time runs out: return the best move found in the last fully completed depth
        pass
        
    return best_move

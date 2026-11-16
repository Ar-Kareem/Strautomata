
import time

# Bitboard constants
ROWS = 6
COLS = 7
H = 7  # Height of each column including padding bit
FULL_MASK = (1 << (COLS * H)) - 1

# Move ordering: center columns first for better alpha-beta pruning
COLUMN_ORDER = [3, 2, 4, 1, 5, 0, 6]

def policy(board: list[list[int]]) -> int:
    start_time = time.time()
    
    # Convert list-of-lists to bitboards
    # player: bits for current player (1), opponent: bits for opponent (-1)
    player = 0
    opponent = 0
    mask = 0
    
    for r in range(ROWS):
        for c in range(COLS):
            val = board[r][c]
            if val != 0:
                # Map row r (0=top, 5=bottom) to bit position (5-r) within column
                bit_pos = c * H + (ROWS - 1 - r)
                mask |= (1 << bit_pos)
                if val == 1:
                    player |= (1 << bit_pos)
                else:
                    opponent |= (1 << bit_pos)
    
    # 1. Check for immediate winning move
    for c in range(COLS):
        if _is_playable(mask, c):
            h = _get_height(mask, c)
            move_bit = 1 << (c * H + h)
            if _is_win(player | move_bit):
                return c
    
    # 2. Check for opponent immediate win (must block)
    block_cols = []
    for c in range(COLS):
        if _is_playable(mask, c):
            h = _get_height(mask, c)
            move_bit = 1 << (c * H + h)
            if _is_win(opponent | move_bit):
                block_cols.append(c)
    
    if len(block_cols) == 1:
        return block_cols[0]
    elif len(block_cols) > 1:
        # Double threat - game is lost, but return a legal move
        return block_cols[0]
    
    # 3. Iterative Deepening Search
    best_move = 3  # Default to center
    for depth in range(1, 20):
        try:
            score, move = _search(player, opponent, mask, depth, -float('inf'), float('inf'), start_time)
            if move is not None:
                best_move = move
            # If we found a forced win or loss, we could break early, but we continue deepening
        except TimeoutError:
            break
        if time.time() - start_time > 0.9:
            break
    
    return best_move

def _is_playable(mask, col):
    """Check if column has space (top bit is not set)"""
    top_bit = 1 << (col * H + (ROWS - 1))
    return (mask & top_bit) == 0

def _get_height(mask, col):
    """Return the number of pieces in a column (0-6), which equals the row index for next piece"""
    col_mask = (mask >> (col * H)) & ((1 << ROWS) - 1)
    return col_mask.bit_count()

def _is_win(bits):
    """Check if bits has 4 in a row using bitwise operations"""
    # Vertical (down): shift by 1
    if bits & (bits >> 1) & (bits >> 2) & (bits >> 3):
        return True
    # Horizontal (left): shift by 7 (1 column)
    if bits & (bits >> 7) & (bits >> 14) & (bits >> 21):
        return True
    # Diagonal \ (down-left): shift by 8 (1 column + 1 row down)
    if bits & (bits >> 8) & (bits >> 16) & (bits >> 24):
        return True
    # Diagonal / (down-right): shift by 6 (1 column - 1 row down)
    if bits & (bits >> 6) & (bits >> 12) & (bits >> 18):
        return True
    return False

def _evaluate(player, opponent):
    """Simple heuristic: count 2-in-a-rows and favor center control"""
    # Center column control (column 3)
    center_mask = (player >> (3 * H)) & ((1 << ROWS) - 1)
    score = center_mask.bit_count() * 10
    
    # Count 2-in-a-rows for player (potential threats)
    p = player
    # Horizontal pairs
    score += (p & (p >> 7)).bit_count() * 2
    # Vertical pairs
    score += (p & (p >> 1)).bit_count() * 2
    # Diagonal \
    score += (p & (p >> 8)).bit_count() * 2
    # Diagonal /
    score += (p & (p >> 6)).bit_count() * 2
    
    # Subtract opponent threats
    o = opponent
    score -= (o & (o >> 7)).bit_count() * 2
    score -= (o & (o >> 1)).bit_count() * 2
    score -= (o & (o >> 8)).bit_count() * 2
    score -= (o & (o >> 6)).bit_count() * 2
    
    return score

def _search(player, opponent, mask, depth, alpha, beta, start_time):
    """Negamax search with alpha-beta pruning"""
    if time.time() - start_time > 0.95:
        raise TimeoutError()
    
    # If opponent already won (previous move), this is a terminal node
    if _is_win(opponent):
        return -(1000000 - (20 - depth)), None  # Penalize longer losses
    
    if depth == 0:
        return _evaluate(player, opponent), None
    
    # Check for draw (all columns full)
    if all(not _is_playable(mask, c) for c in range(COLS)):
        return 0, None
    
    best_move = None
    
    for c in COLUMN_ORDER:
        if not _is_playable(mask, c):
            continue
        
        h = _get_height(mask, c)
        move_bit = 1 << (c * H + h)
        new_mask = mask | move_bit
        new_opponent = opponent  # Next turn, current player becomes opponent
        new_player = player | move_bit  # We become the "opponent" in next call
        
        # Recurse (negamax: switch sign and swap alpha/beta)
        score, _ = _search(new_opponent, new_player, new_mask, depth - 1, -beta, -alpha, start_time)
        score = -score
        
        if score > alpha:
            alpha = score
            best_move = c
            if alpha >= beta:
                break
    
    return alpha, best_move

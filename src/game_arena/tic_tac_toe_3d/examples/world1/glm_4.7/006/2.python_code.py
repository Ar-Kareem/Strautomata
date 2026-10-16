
import sys
import functools
import random

# -----------------------------------------------------------------------------
# Constants and Precomputation
# -----------------------------------------------------------------------------

# Board dimensions
SIZE = 3
TOTAL_CELLS = SIZE ** 3

# Bit masks for 27 cells (0..26)
# We use 32-bit integers to represent the board state.
# 1 represents a move by the AI, -1 (opponent) is tracked in a separate mask.
ALL_CELLS_MASK = (1 << TOTAL_CELLS) - 1

# Precompute all 49 winning lines in 3x3x3 Tic Tac Toe
# Lines are stored as bitmasks where bits corresponding to the cells in the line are set.
WINNING_LINES = []

# Helper to get bit index from coordinates (i, j, k)
def get_idx(i, j, k):
    return i * 9 + j * 3 + k

# 1. Orthogonal lines
# Along k-axis (rows in a layer)
for i in range(3):
    for j in range(3):
        mask = (1 << get_idx(i, j, 0)) | (1 << get_idx(i, j, 1)) | (1 << get_idx(i, j, 2))
        WINNING_LINES.append(mask)

# Along j-axis (columns in a layer)
for i in range(3):
    for k in range(3):
        mask = (1 << get_idx(i, 0, k)) | (1 << get_idx(i, 1, k)) | (1 << get_idx(i, 2, k))
        WINNING_LINES.append(mask)

# Along i-axis (pillars)
for j in range(3):
    for k in range(3):
        mask = (1 << get_idx(0, j, k)) | (1 << get_idx(1, j, k)) | (1 << get_idx(2, j, k))
        WINNING_LINES.append(mask)

# 2. Face Diagonals (2D diagonals on the planes)
# On XY planes (fixed i)
for i in range(3):
    mask1 = (1 << get_idx(i, 0, 0)) | (1 << get_idx(i, 1, 1)) | (1 << get_idx(i, 2, 2))
    mask2 = (1 << get_idx(i, 0, 2)) | (1 << get_idx(i, 1, 1)) | (1 << get_idx(i, 2, 0))
    WINNING_LINES.append(mask1)
    WINNING_LINES.append(mask2)

# On XZ planes (fixed j)
for j in range(3):
    mask1 = (1 << get_idx(0, j, 0)) | (1 << get_idx(1, j, 1)) | (1 << get_idx(2, j, 2))
    mask2 = (1 << get_idx(0, j, 2)) | (1 << get_idx(1, j, 1)) | (1 << get_idx(2, j, 0))
    WINNING_LINES.append(mask1)
    WINNING_LINES.append(mask2)

# On YZ planes (fixed k)
for k in range(3):
    mask1 = (1 << get_idx(0, 0, k)) | (1 << get_idx(1, 1, k)) | (1 << get_idx(2, 2, k))
    mask2 = (1 << get_idx(0, 2, k)) | (1 << get_idx(1, 1, k)) | (1 << get_idx(2, 0, k))
    WINNING_LINES.append(mask1)
    WINNING_LINES.append(mask2)

# 3. Space Diagonals (corners through center)
mask1 = (1 << get_idx(0, 0, 0)) | (1 << get_idx(1, 1, 1)) | (1 << get_idx(2, 2, 2))
mask2 = (1 << get_idx(0, 0, 2)) | (1 << get_idx(1, 1, 1)) | (1 << get_idx(2, 2, 0))
mask3 = (1 << get_idx(0, 2, 0)) | (1 << get_idx(1, 1, 1)) | (1 << get_idx(2, 0, 2))
mask4 = (1 << get_idx(0, 2, 2)) | (1 << get_idx(1, 1, 1)) | (1 << get_idx(2, 0, 0))
WINNING_LINES.append(mask1)
WINNING_LINES.append(mask2)
WINNING_LINES.append(mask3)
WINNING_LINES.append(mask4)

# Heuristic weights
SCORE_WIN = 10000
SCORE_LOSE = -10000
WEIGHT_2 = 100
WEIGHT_1 = 10

# Move ordering to optimize Alpha-Beta pruning
# Priority: Center (13) -> Face Centers -> Edges -> Corners
# Center
ORDERED_INDICES = [13]
# Face Centers (1,1,0), (1,0,1), etc. (indices where 2 coords are 0/2 and 1 is 1)
ORDERED_INDICES.extend([4, 10, 12, 14, 16, 22])
# Edges (indices where 1 coord is 0/2 and 2 are 0/2... actually indices of edges)
# Edges are the remaining 12 non-corner, non-center, non-face-center cells
ORDERED_INDICES.extend([1, 3, 5, 7, 9, 11, 15, 17, 19, 21, 23, 25])
# Corners
ORDERED_INDICES.extend([0, 2, 6, 8, 18, 20, 24, 26])

# -----------------------------------------------------------------------------
# Logic
# -----------------------------------------------------------------------------

def board_to_masks(board):
    """Converts the 3D list board to two bitmasks: player and opponent."""
    me_mask = 0
    opp_mask = 0
    for i in range(3):
        for j in range(3):
            for k in range(3):
                idx = get_idx(i, j, k)
                val = board[i][j][k]
                if val == 1:
                    me_mask |= (1 << idx)
                elif val == -1:
                    opp_mask |= (1 << idx)
    return me_mask, opp_mask

def idx_to_coord(idx):
    """Converts bit index 0-26 to (i, j, k)."""
    i = idx // 9
    j = (idx % 9) // 3
    k = idx % 3
    return (i, j, k)

def check_win(mask):
    """Returns True if the given mask contains a winning line."""
    for line in WINNING_LINES:
        if (mask & line) == line:
            return True
    return False

def evaluate_state(me_mask, opp_mask):
    """
    Heuristic evaluation of the board state.
    Returns a score from the perspective of 'me_mask'.
    """
    score = 0
    for line in WINNING_LINES:
        # Check if line is blocked by both players
        m_line = line & me_mask
        o_line = line & opp_mask
        
        if m_line and o_line:
            continue # Blocked line, no potential
        
        c1 = m_line.bit_count()
        c2 = o_line.bit_count()
        
        if c1 == 3:
            return SCORE_WIN
        if c2 == 3:
            return SCORE_LOSE
            
        # Potential lines
        if c1 == 2:
            score += WEIGHT_2
        elif c1 == 1:
            score += WEIGHT_1
            
        if c2 == 2:
            score -= WEIGHT_2
        elif c2 == 1:
            score -= WEIGHT_1
            
    return score

def find_immediate_move(me_mask, opp_mask):
    """
    Checks for a win or a block.
    Returns (bit_index, is_win) or (None, None).
    """
    # Check for win
    for i in range(TOTAL_CELLS):
        bit = 1 << i
        if (me_mask | opp_mask) & bit: continue # occupied
        
        if check_win(me_mask | bit):
            return i, True
            
    # Check for block
    for i in range(TOTAL_CELLS):
        bit = 1 << i
        if (me_mask | opp_mask) & bit: continue # occupied
        
        if check_win(opp_mask | bit):
            return i, False
            
    return None, None

@functools.lru_cache(maxsize=None)
def minimax(me_mask, opp_mask, depth, alpha, beta, is_maximizing):
    """
    Minimax with Alpha-Beta Pruning.
    Evaluates from the perspective of 'me_mask'.
    """
    
    # Terminal checks
    if check_win(me_mask):
        return SCORE_WIN
    if check_win(opp_mask):
        return SCORE_LOSE
    
    # Depth limit or draw
    empty_mask = ~(me_mask | opp_mask) & ALL_CELLS_MASK
    if empty_mask == 0 or depth == 0:
        return evaluate_state(me_mask, opp_mask)
    
    # Generate moves based on priority ordering
    if is_maximizing:
        max_eval = -float('inf')
        for idx in ORDERED_INDICES:
            bit = 1 << idx
            if bit & empty_mask:
                eval_val = minimax(me_mask | bit, opp_mask, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval_val)
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break
        return max_eval
    else:
        min_eval = float('inf')
        for idx in ORDERED_INDICES:
            bit = 1 << idx
            if bit & empty_mask:
                eval_val = minimax(me_mask, opp_mask | bit, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval_val)
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break
        return min_eval

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    Determines the next move for the 3x3x3 Tic Tac Toe game.
    """
    me_mask, opp_mask = board_to_masks(board)
    
    # 1. Check for immediate win
    move_idx, _ = find_immediate_move(me_mask, opp_mask)
    if move_idx is not None:
        return idx_to_coord(move_idx)
    
    # 2. Strategic Search (Minimax)
    # Determine search depth. 
    # Higher depth in mid-game, lower if full to avoid timeout, though 
    # endgame is faster due to fewer branches.
    # Depth 5 is usually sufficient for 3x3x3 tactical depth.
    # We can go deeper if few pieces are left.
    
    pieces_on_board = (me_mask | opp_mask).bit_count()
    if pieces_on_board < 10:
        search_depth = 5
    elif pieces_on_board < 20:
        search_depth = 7
    else:
        search_depth = 10 # Endgame solve

    best_score = -float('inf')
    best_move = -1
    alpha = -float('inf')
    beta = float('inf')
    
    empty_mask = ~(me_mask | opp_mask) & ALL_CELLS_MASK
    
    # Iterate through moves to find the best one
    for idx in ORDERED_INDICES:
        bit = 1 << idx
        if bit & empty_mask:
            # Call minimax for the resulting state
            # Next player is minimizing (opponent)
            score = minimax(me_mask | bit, opp_mask, search_depth - 1, alpha, beta, False)
            
            if score > best_score:
                best_score = score
                best_move = idx
            
            alpha = max(alpha, score)
            if beta <= alpha:
                break # Prune
    
    # Fallback (should rarely happen if empty_mask is not 0)
    if best_move == -1:
        # Pick first available from ordered list
        for idx in ORDERED_INDICES:
            bit = 1 << idx
            if bit & empty_mask:
                best_move = idx
                break
                
    return idx_to_coord(best_move)

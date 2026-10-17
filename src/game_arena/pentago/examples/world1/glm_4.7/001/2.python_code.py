
import numpy as np
import time
import sys

# --- Precomputed Constants ---

# Indices for all possible winning lines of length 5 on a 6x6 board
# A line is a list of (row, col) tuples
def generate_lines():
    lines = []
    # Rows
    for r in range(6):
        lines.append([(r, c) for c in range(5)])
        lines.append([(r, c+1) for c in range(5)])
    # Columns
    for c in range(6):
        lines.append([(r, c) for r in range(5)])
        lines.append([(r+1, c) for r in range(5)])
    # Diagonals (Top-Left to Bottom-Right)
    # Main diagonal (0,0)-(5,5) splits into two: (0,0)-(4,4) and (1,1)-(5,5)
    lines.append([(i, i) for i in range(5)])
    lines.append([(i+1, i+1) for i in range(5)])
    # Offset diagonal (0,1)-(4,5)
    lines.append([(i, i+1) for i in range(5)])
    # Offset diagonal (1,0)-(5,4)
    lines.append([(i+1, i) for i in range(5)])
    
    # Diagonals (Top-Right to Bottom-Left)
    # Main anti-diagonal (0,5)-(5,0) splits into (0,5)-(4,1) and (1,5)-(5,1)
    lines.append([(i, 5-i) for i in range(5)])
    lines.append([(i+1, 4-i) for i in range(5)])
    # Offset (0,4)-(4,0)
    lines.append([(i, 4-i) for i in range(5)])
    # Offset (1,5)-(5,1)
    lines.append([(i+1, 5-i) for i in range(5)])
    
    return lines

_LINES = generate_lines()
_LINES_ARR = np.array(_LINES) # Shape (32, 5, 2) for fast indexing

# Scoring weights for [0, 1, 2, 3, 4, 5] marbles in a line
_WEIGHTS = np.array([0, 1, 10, 100, 10000, 100000])

# Rotation mappings for 3x3 quadrants
_QUADRANTS = [0, 1, 2, 3]
_DIRECTIONS = ['L', 'R']

# --- Helper Functions ---

def check_win(board_you, board_opp):
    """
    Returns (you_win, opp_win) boolean tuple.
    Uses vectorized operations for speed.
    """
    # Extract values at line coordinates
    # LINES_ARR is (32, 5, 2), so LINES_ARR[:,:,0] are rows, LINES_ARR[:,:,1] are cols
    rows = _LINES_ARR[:, :, 0]
    cols = _LINES_ARR[:, :, 1]
    
    you_counts = board_you[rows, cols].sum(axis=1)
    opp_counts = board_opp[rows, cols].sum(axis=1)
    
    you_win = np.any(you_counts == 5)
    opp_win = np.any(opp_counts == 5)
    
    return bool(you_win), bool(opp_win)

def evaluate(board_you, board_opp):
    """
    Heuristic evaluation of the board state.
    Returns a score: positive for you, negative for opponent.
    """
    rows = _LINES_ARR[:, :, 0]
    cols = _LINES_ARR[:, :, 1]
    
    you_counts = board_you[rows, cols].sum(axis=1)
    opp_counts = board_opp[rows, cols].sum(axis=1)
    
    # Base scores from weights
    you_score = _WEIGHTS[you_counts]
    opp_score = _WEIGHTS[opp_counts]
    
    # Zero out blocked lines (where both have > 0 marbles) unless it's a win (5)
    # If I have 3 and opp has 1, that line is effectively useless for winning.
    # Mask: opp_counts > 0 implies my potential is blocked, UNLESS I already won (you_counts == 5)
    # Note: If you_counts == 5, opp_counts must be 0, so mask logic holds naturally.
    
    blocked_mask = (opp_counts > 0)
    you_score = np.where(blocked_mask, 0, you_score)
    
    blocked_mask_opp = (you_counts > 0)
    opp_score = np.where(blocked_mask_opp, 0, opp_score)
    
    total_score = np.sum(you_score) - np.sum(opp_score)
    return total_score

def apply_move(board_you, board_opp, r, c, quad, direction):
    """
    Applies a placement and rotation to the boards.
    Modifies boards in place.
    """
    # 1. Place marble
    board_you[r, c] = 1
    
    # 2. Rotate quadrant
    # Quad indices:
    # 0: TL (r0-2, c0-2), 1: TR (r0-2, c3-5)
    # 2: BL (r3-5, c0-2), 3: BR (r3-5, c3-5)
    r_start = (quad // 2) * 3
    c_start = (quad % 2) * 3
    
    # Extract subgrid
    sub_you = board_you[r_start:r_start+3, c_start:c_start+3]
    sub_opp = board_opp[r_start:r_start+3, c_start:c_start+3]
    
    # Rotate
    # k=1 is 90 deg counter-clockwise (Left), k=-1 is clockwise (Right)
    k = 1 if direction == 'L' else -1
    rot_you = np.rot90(sub_you, k=k)
    rot_opp = np.rot90(sub_opp, k=k)
    
    # Assign back
    board_you[r_start:r_start+3, c_start:c_start+3] = rot_you
    board_opp[r_start:r_start+3, c_start:c_start+3] = rot_opp

def get_legal_moves(board_you):
    """Returns list of (r, c) tuples for empty cells."""
    return np.argwhere(board_you == 0).tolist()

# --- Policy ---

def policy(you, opponent):
    start_time = time.time()
    
    # Convert to numpy arrays if not already
    you_board = np.array(you, dtype=int)
    opp_board = np.array(opponent, dtype=int)
    
    empty_cells = get_legal_moves(you_board)
    if not empty_cells:
        return "1,1,0,L" # Should not happen per rules, but safe fallback
        
    best_move = None
    best_score = -np.inf
    alpha = -np.inf
    beta = np.inf
    
    # We will perform a depth-2 search (My move -> Opponent move)
    # With pruning and early win checks.
    
    # 1. Loop through all possible moves
    # To optimize search, we might want to try center moves first, 
    # but for simplicity in Python, we iterate linearly and rely on pruning.
    
    for r, c in empty_cells:
        # Time check: reserve 0.1s for finalization
        if time.time() - start_time > 0.9:
            break
            
        for quad in _QUADRANTS:
            for dir in _DIRECTIONS:
                # Create copies for simulation
                sim_you = you_board.copy()
                sim_opp = opp_board.copy()
                
                # Apply move
                apply_move(sim_you, sim_opp, r, c, quad, dir)
                
                # Check immediate win for me
                me_win, opp_win = check_win(sim_you, sim_opp)
                
                if me_win:
                    # If I win and opponent doesn't also win (draw), this is best.
                    if not opp_win:
                        # Found a winning move, return immediately
                        return f"{r+1},{c+1},{quad},{dir}"
                    # If draw, it's a good score but not necessarily instant return 
                    # unless we prefer draws over losses.
                
                # Depth 1 (My move) Evaluation: 
                # Instead of just static eval, we simulate Opponent's best response.
                
                val = -np.inf # Worst case for opponent is best for me
                
                # If I already won (or drew), score is high.
                # We define win score as large positive.
                if me_win and not opp_win:
                    val = 1000000
                elif me_win and opp_win:
                    val = 0
                else:
                    # 2. Opponent's Turn (Depth 1)
                    # Iterate opponent's possible moves to find their best outcome (min for me)
                    opp_empty = get_legal_moves(sim_you)
                    
                    # Optimization: If opponent has many moves, we can't check all.
                    # However, depth 2 is usually feasible for full 288*288 in 1s in C++, 
                    # but Python is slow. We need to prune opponent's search too.
                    
                    # We assume opponent plays optimally to maximize their score.
                    min_opp_score = np.inf # This is the score opponent achieves. 
                                          # Since our eval is (Me - Opp), opponent wants to minimize this.
                    
                    # We limit opponent moves to check to keep time.
                    # If we check all 288 moves inside a 288 loop, it's ~80k nodes.
                    # This is on the edge. Let's try to be smart or just iterate all and hope.
                    # Given the constraint, we iterate all but break if beta cuts.
                    
                    opp_nodes_checked = 0
                    for o_r, o_c in opp_empty:
                        if time.time() - start_time > 0.9:
                            break
                            
                        for o_q in _QUADRANTS:
                            for o_d in _DIRECTIONS:
                                # Simulate opponent move
                                sim_you2 = sim_you.copy()
                                sim_opp2 = sim_opp.copy()
                                apply_move(sim_you2, sim_opp2, o_r, o_c, o_q, o_d)
                                
                                # Check win state for opponent
                                m_win, o_win = check_win(sim_you2, sim_opp2)
                                curr_score = 0
                                
                                if o_win:
                                    curr_score = -1000000 # Opponent won
                                elif m_win:
                                    curr_score = 1000000 # I won somehow
                                else:
                                    curr_score = evaluate(sim_you2, sim_opp2)
                                
                                if curr_score < min_opp_score:
                                    min_opp_score = curr_score
                                    if min_opp_score <= alpha: # Alpha-Beta Cutoff
                                        break
                        if min_opp_score <= alpha:
                            break
                            
                    val = min_opp_score
                    if val == -1000000: # Opponent can force a win from here
                         # This move is terrible, we can skip other rotations for this placement if alpha is low?
                         # Actually, if val is -inf (loss), we don't want to pick it.
                         pass

                # Update best move (Maximize val)
                if val > best_score:
                    best_score = val
                    best_move = (r, c, quad, dir)
                    
                # Alpha update
                if best_score > alpha:
                    alpha = best_score

    # Fallback: If loop finished or time ran out without finding a great move,
    # ensure we have a valid move.
    if best_move is None:
        # Should not happen unless board is full, but pick first available just in case
        r, c = empty_cells[0]
        return f"{r+1},{c+1},0,L"
        
    r, c, q, d = best_move
    return f"{r+1},{c+1},{q},{d}"

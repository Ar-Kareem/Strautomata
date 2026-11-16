
import sys

# --- Constants & Configuration ---
WIN_SCORE = 100000
STREAK_2 = 100
STREAK_1 = 1

# --- Precompute Winning Lines ---
# Flattened indices for all 49 winning lines
_LINES = []

# Axial lines (Rows, Columns, Pillars)
# x-axis (vary x)
for y in range(3):
    for z in range(3):
        _LINES.append([9 * x + 3 * y + z for x in range(3)])
# y-axis (vary y)
for x in range(3):
    for z in range(3):
        _LINES.append([9 * x + 3 * y + z for y in range(3)])
# z-axis (vary z)
for x in range(3):
    for y in range(3):
        _LINES.append([9 * x + 3 * y + z for z in range(3)])

# Face Diagonals (18 lines)
# Lines on constant x planes
for x in range(3):
    base = 9 * x
    _LINES.append([base + 0, base + 4, base + 8]) # 0,0 - 2,2
    _LINES.append([base + 2, base + 4, base + 6]) # 0,2 - 2,0
# Lines on constant y planes
for y in range(3):
    base = 3 * y
    _LINES.append([base + 0, base + 10, base + 20]) # (0,0,0)-(2,0,2) mapped
    _LINES.append([base + 2, base + 10, base + 18]) 
# Lines on constant z planes
for z in range(3):
    base = z
    _LINES.append([base + 0, base + 12, base + 24]) # (0,0,0)-(2,2,0) mapped
    _LINES.append([base + 6, base + 12, base + 18])

# Space Diagonals (4 lines)
_LINES.append([0, 13, 26]) # (0,0,0)-(2,2,2)
_LINES.append([2, 13, 24]) # (0,0,2)-(2,2,0)
_LINES.append([6, 13, 20]) # (0,2,0)-(2,0,2)
_LINES.append([8, 13, 18]) # (0,2,2)-(2,0,0)

# Strategic Positions
_CENTER = 13
_CORNERS = {0, 2, 6, 8, 18, 20, 24, 26}

def _check_win(flat_board, player):
    """Returns True if player has won."""
    for line in _LINES:
        if flat_board[line[0]] == player and flat_board[line[1]] == player and flat_board[line[2]] == player:
            return True
    return False

def _evaluate(flat_board):
    """Heuristic evaluation of the board state."""
    score = 0
    for line in _LINES:
        v0 = flat_board[line[0]]
        v1 = flat_board[line[1]]
        v2 = flat_board[line[2]]
        
        s = v0 + v1 + v2
        
        if s == 3: return WIN_SCORE
        if s == -3: return -WIN_SCORE
        
        # Analyze partial lines
        has_p1 = (v0 == 1) or (v1 == 1) or (v2 == 1)
        has_p2 = (v0 == -1) or (v1 == -1) or (v2 == -1)
        
        # If both have played in this line, it's dead (0 value)
        if has_p1 and has_p2:
            continue
            
        if has_p1:
            if s == 2: score += STREAK_2
            elif s == 1: score += STREAK_1
        elif has_p2:
            # s is negative here
            if s == -2: score -= STREAK_2
            elif s == -1: score -= STREAK_1
            
    return score

def _minimax(flat_board, depth, alpha, beta, is_max):
    # Determine static eval
    current_val = _evaluate(flat_board)
    
    # Terminal check
    if abs(current_val) >= WIN_SCORE:
        return current_val
    if depth == 0:
        return current_val

    # Find empty spots
    moves = [i for i, x in enumerate(flat_board) if x == 0]
    
    # Terminal: Draw
    if not moves:
        return 0

    # Move ordering: Center > Corners > Others to improve pruning
    moves.sort(key=lambda m: 0 if m == _CENTER else (1 if m in _CORNERS else 2))

    if is_max:
        max_eval = -float('inf')
        for m in moves:
            flat_board[m] = 1
            eval_val = _minimax(flat_board, depth - 1, alpha, beta, False)
            flat_board[m] = 0
            
            if eval_val > max_eval:
                max_eval = eval_val
            alpha = max(alpha, eval_val)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for m in moves:
            flat_board[m] = -1
            eval_val = _minimax(flat_board, depth - 1, alpha, beta, True)
            flat_board[m] = 0
            
            if eval_val < min_eval:
                min_eval = eval_val
            beta = min(beta, eval_val)
            if beta <= alpha:
                break
        return min_eval

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    Determines the next move for the 3x3x3 Tic Tac Toe game.
    """
    # 1. Conversion: Flatten board to 1D list for performance
    flat = [0] * 27
    empty = []
    
    idx = 0
    for x in range(3):
        for y in range(3):
            for z in range(3):
                val = board[x][y][z]
                flat[idx] = val
                if val == 0:
                    empty.append(idx)
                idx += 1

    if not empty:
        return (0, 0, 0) # Should not happen in valid game flow

    # 2. Optimal Opening: Always take center if available
    if flat[_CENTER] == 0:
        return (1, 1, 1)

    # 3. Quick Checks: Immediate Win or Forced Block
    # Look for immediate Win
    for m in empty:
        flat[m] = 1
        if _check_win(flat, 1):
            return (m // 9, (m % 9) // 3, m % 3)
        flat[m] = 0
    
    # Look for immediate Block
    for m in empty:
        flat[m] = -1
        if _check_win(flat, -1):
            return (m // 9, (m % 9) // 3, m % 3)
        flat[m] = 0

    # 4. Search: Alpha-Beta Minimax
    # Depth 3 allows looking ahead: Me -> Opp -> Me.
    # This detects if a move allows me to set up a fork (win in 2 turns).
    depth = 3
    # If late game, extend depth slightly as branching factor is low
    if len(empty) < 12:
        depth = 4

    alpha = -float('inf')
    beta = float('inf')
    best_score = -float('inf')
    best_move = empty[0]
    
    # Sort root moves
    empty.sort(key=lambda m: 1 if m in _CORNERS else 2) 

    for m in empty:
        flat[m] = 1
        score = _minimax(flat, depth - 1, alpha, beta, False)
        flat[m] = 0
        
        if score > best_score:
            best_score = score
            best_move = m
        
        alpha = max(alpha, score)
        if beta <= alpha:
            break
            
    # Convert flat index back to tuple
    return (best_move // 9, (best_move % 9) // 3, best_move % 3)

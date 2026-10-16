
import sys

# --- Precomputed Geometry and Constants ---

def _generate_winning_lines():
    """Generates the 49 winning lines for a 3x3x3 board (indices 0-26)."""
    lines = []
    
    # 1. Orthogonal Lines (Axial)
    # x-axis variation (y, z fixed)
    for y in range(3):
        for z in range(3):
            lines.append(tuple(x * 9 + y * 3 + z for x in range(3)))
            
    # y-axis variation (x, z fixed)
    for x in range(3):
        for z in range(3):
            lines.append(tuple(x * 9 + y * 3 + z for y in range(3)))
            
    # z-axis variation (x, y fixed)
    for x in range(3):
        for y in range(3):
            lines.append(tuple(x * 9 + y * 3 + z for z in range(3)))
            
    # 2. Planar Diagonals
    # x-planes (3 planes)
    for x in range(3):
        lines.append(tuple(x * 9 + k * 3 + k for k in range(3)))         # y=z diagonal
        lines.append(tuple(x * 9 + k * 3 + (2 - k) for k in range(3)))   # y=-z diagonal
    
    # y-planes (3 planes)
    for y in range(3):
        lines.append(tuple(k * 9 + y * 3 + k for k in range(3)))         # x=z diagonal
        lines.append(tuple(k * 9 + y * 3 + (2 - k) for k in range(3)))   # x=-z diagonal
        
    # z-planes (3 planes)
    for z in range(3):
        lines.append(tuple(k * 9 + k * 3 + z for k in range(3)))         # x=y diagonal
        lines.append(tuple(k * 9 + (2 - k) * 3 + z for k in range(3)))   # x=-y diagonal

    # 3. Space Diagonals (4 lines)
    lines.append(tuple(k * 9 + k * 3 + k for k in range(3)))             # 0,0,0 to 2,2,2
    lines.append(tuple(k * 9 + k * 3 + (2 - k) for k in range(3)))       # 0,0,2 to 2,2,0
    lines.append(tuple(k * 9 + (2 - k) * 3 + k for k in range(3)))       # 0,2,0 to 2,0,2
    lines.append(tuple(k * 9 + (2 - k) * 3 + (2 - k) for k in range(3))) # 0,2,2 to 2,0,0
    
    return lines

# Global constant for lines (list of tuples of indices)
WINNING_LINES = _generate_winning_lines()

# Lookup table: Which lines pass through a specific cell?
# Used to quickly check win conditions for a specific move.
CELL_TO_LINES = [[] for _ in range(27)]
for _line in WINNING_LINES:
    for _cell in _line:
        CELL_TO_LINES[_cell].append(_line)

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    Returns the next move for a 3x3x3 Tic Tac Toe game.
    AI is Player 1 (value 1), Opponent is Player -1 (value -1).
    """
    # Flatten board for efficient linear indexing
    # board[x][y][z] -> flat[x*9 + y*3 + z]
    flat_board = [cell for plane in board for row in plane for cell in row]
    
    # Identify empty cells
    empty_indices = [i for i, x in enumerate(flat_board) if x == 0]
    
    # 0. Edge case: Full board (should not happen in game loop usually)
    if not empty_indices:
        return (0, 0, 0)
    
    # 1. Check for Immediate Win (Priority 1)
    # Check if there is any line with sum 2 (score 2 means two 1s and one 0)
    for line in WINNING_LINES:
        s = flat_board[line[0]] + flat_board[line[1]] + flat_board[line[2]]
        if s == 2:
            # Find the empty spot to take the win
            for idx in line:
                if flat_board[idx] == 0:
                    return _to_coords(idx)
                    
    # 2. Check for Immediate Block (Priority 2)
    # Check if opponent has any line with sum -2 (two -1s and one 0)
    block_candidate = None
    for line in WINNING_LINES:
        s = flat_board[line[0]] + flat_board[line[1]] + flat_board[line[2]]
        if s == -2:
            for idx in line:
                if flat_board[idx] == 0:
                    block_candidate = idx
                    # We store this but don't return immediately, 
                    # theoretically we might prefer blocking a fork 
                    # but usually blocking a win is the only option.
                    # Since we checked our win first, we must block now.
                    return _to_coords(block_candidate)

    # 3. Strategic Opening: Take Center if available
    # The center (index 13) is statistically the strongest position.
    CENTER_IDX = 13
    if flat_board[CENTER_IDX] == 0:
        return _to_coords(CENTER_IDX)

    # 4. Minimax Search (Depth Limited)
    # Search depth 2: My Move -> Opponent Reply -> Evaluate State.
    # This prevents moving into a state where opponent can force a win (fork).
    best_move = empty_indices[0]
    best_score = -float('inf')
    
    # Optimization: Sort candidates to check Corners first (after center), then others.
    # Corners: 0, 2, 6, 8, 18, 20, 24, 26
    corners = {0, 2, 6, 8, 18, 20, 24, 26}
    candidates = sorted(empty_indices, key=lambda x: 1 if x in corners else 0, reverse=True)
    
    alpha = -float('inf')
    beta = float('inf')
    
    for move in candidates:
        # Execute Move
        flat_board[move] = 1
        
        # Evaluate using Minimax (Next turn is Opponent (Min))
        score = _minimax(flat_board, depth=1, alpha=alpha, beta=beta, is_max=False)
        
        # Undo Move
        flat_board[move] = 0
        
        if score > best_score:
            best_score = score
            best_move = move
            
        alpha = max(alpha, best_score)
        # Beta cutoff is not applicable at root
        
    return _to_coords(best_move)

def _minimax(board, depth, alpha, beta, is_max):
    """
    Minimax with Alpha-Beta pruning.
    """
    # Leaf evaluation
    if depth == 0:
        return _evaluate_state(board)

    # Note: We assumed immediate win/loss checked at root, 
    # but inside the tree we need to detect terminal states.
    # Or, we can rely on the heuristic to return huge numbers for won lines.
    
    empty_indices = [i for i, x in enumerate(board) if x == 0]
    if not empty_indices:
        return 0

    if is_max:
        max_eval = -float('inf')
        for move in empty_indices:
            board[move] = 1
            # Check immediate win optimization
            if _check_win_at(board, move, 1):
                board[move] = 0
                return 10000 + depth  # Prefer faster wins
            
            eval_val = _minimax(board, depth - 1, alpha, beta, False)
            board[move] = 0
            
            max_eval = max(max_eval, eval_val)
            alpha = max(alpha, eval_val)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for move in empty_indices:
            board[move] = -1
            # Check immediate win optimization for opponent
            if _check_win_at(board, move, -1):
                board[move] = 0
                return -10000 - depth # Prefer slower losses (or avoid completely)
            
            eval_val = _minimax(board, depth - 1, alpha, beta, True)
            board[move] = 0
            
            min_eval = min(min_eval, eval_val)
            beta = min(beta, eval_val)
            if beta <= alpha:
                break
        return min_eval

def _evaluate_state(board):
    """
    Heuristic evaluation of the board.
    High score -> Good for Player 1.
    Low score -> Good for Player -1.
    """
    score = 0
    
    for line in WINNING_LINES:
        # Sum of the line: a quick way to identify content composition
        # Values: 1 (me), -1 (opp), 0 (empty)
        # 3 -> Win Me (Handling in Search typically, but good for safety)
        # 2 -> 2 Me, 0 Opp (Threat) -> +100
        # 1 -> 1 Me, 0 Opp -> +10
        # 0 -> Empty or Balanced (1 Me, 1 Opp)
        # -1 -> 1 Opp, 0 Me -> -10
        # -2 -> 2 Opp, 0 Me (Threat) -> -100
        # -3 -> Win Opp
        
        v0 = board[line[0]]
        v1 = board[line[1]]
        v2 = board[line[2]]
        
        # Check composition distinct from sum to avoid cancellations (e.g. 1, 1, -1 = 1)
        # We only care about lines that are NOT blocked by the opponent for positive score
        # and lines NOT blocked by us for negative score.
        
        has_me = (v0 == 1 or v1 == 1 or v2 == 1)
        has_opp = (v0 == -1 or v1 == -1 or v2 == -1)
        
        if has_me and not has_opp:
            # Potential line for me
            count = v0 + v1 + v2
            if count == 3: score += 10000
            elif count == 2: score += 100
            elif count == 1: score += 10
        elif has_opp and not has_me:
            # Potential line for opponent
            count = -(v0 + v1 + v2) # Positive count of opp
            if count == 3: score -= 10000
            elif count == 2: score -= 100
            elif count == 1: score -= 10
            
    return score

def _check_win_at(board, move_idx, player):
    """Checks if placing 'player' at 'move_idx' completes a line."""
    target = 3 * player
    for line in CELL_TO_LINES[move_idx]:
        if board[line[0]] + board[line[1]] + board[line[2]] == target:
            return True
    return False

def _to_coords(idx):
    """Converts linear index 0-26 to (x, y, z)."""
    # idx = x*9 + y*3 + z
    z = idx % 3
    y = (idx // 3) % 3
    x = idx // 9
    return (x, y, z)

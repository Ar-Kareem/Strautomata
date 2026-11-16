
import sys

# Global cache for winning lines indices
# 49 lines in 3x3x3 Tic Tac Toe
WIN_LINES = []

def _initialize_lines():
    if WIN_LINES:
        return
    # 1. 1D Lines (Axial)
    for i in range(3):
        for j in range(3):
            # i,j fixed, vary k (x, y, z axes)
            WIN_LINES.append([(k, i, j) for k in range(3)]) 
            WIN_LINES.append([(i, k, j) for k in range(3)])
            WIN_LINES.append([(i, j, k) for k in range(3)])

    # 2. 2D Diagonals (Face Diagonals) on planes
    for k in range(3):
        # constant dim 0 (x-planes) -> diagonals in yz
        WIN_LINES.append([(k, 0, 0), (k, 1, 1), (k, 2, 2)])
        WIN_LINES.append([(k, 2, 0), (k, 1, 1), (k, 0, 2)])
        # constant dim 1 (y-planes) -> diagonals in xz
        WIN_LINES.append([(0, k, 0), (1, k, 1), (2, k, 2)])
        WIN_LINES.append([(2, k, 0), (1, k, 1), (0, k, 2)])
        # constant dim 2 (z-planes) -> diagonals in xy
        WIN_LINES.append([(0, 0, k), (1, 1, k), (2, 2, k)])
        WIN_LINES.append([(2, 0, k), (1, 1, k), (0, 2, k)])

    # 3. 3D Space Diagonals
    WIN_LINES.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
    WIN_LINES.append([(2, 0, 0), (1, 1, 1), (0, 2, 2)])
    WIN_LINES.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
    WIN_LINES.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])

# Initialize once
_initialize_lines()

def _evaluate_board(board):
    """
    Weighted heuristic for the board state.
    Calculated from the perspective of Player 1 (AI).
    """
    score = 0
    # Values: 1 (Me), -1 (Opp), 0 (Empty)
    
    for line in WIN_LINES:
        v0 = board[line[0][0]][line[0][1]][line[0][2]]
        v1 = board[line[1][0]][line[1][1]][line[1][2]]
        v2 = board[line[2][0]][line[2][1]][line[2][2]]
        
        # Check if line is blocked
        has_me = (v0 == 1 or v1 == 1 or v2 == 1)
        has_opp = (v0 == -1 or v1 == -1 or v2 == -1)
        
        if has_me and has_opp:
            continue # Blocked line, no potential
            
        if has_me:
            # Only my markers and empty cells
            count = (v0 == 1) + (v1 == 1) + (v2 == 1)
            if count == 3:
                return 100000 # Actual Win
            elif count == 2:
                # 2 markers + 1 empty = Threat
                score += 100
            elif count == 1:
                score += 10
        elif has_opp:
            # Only opponent markers and empty cells
            count = (v0 == -1) + (v1 == -1) + (v2 == -1)
            if count == 3:
                return -100000 # Actual Loss
            elif count == 2:
                score -= 100
            elif count == 1:
                score -= 10
                
    return score

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    Determines the next move for a 3x3x3 Tic Tac Toe game.
    Uses immediate win/block checks followed by a depth-2 Minimax search.
    """
    # Find all legal moves
    empty_cells = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    empty_cells.append((i, j, k))
    
    if not empty_cells:
        return (0, 0, 0)
        
    # --- PHASE 1: Immediate Critical Moves ---
    
    # Check for Winning Move
    for line in WIN_LINES:
        vals = [board[c[0]][c[1]][c[2]] for c in line]
        if sum(vals) == 2 and 0 in vals: # Two 1s and one 0
            return line[vals.index(0)]
            
    # Check for Forced Block
    for line in WIN_LINES:
        vals = [board[c[0]][c[1]][c[2]] for c in line]
        if sum(vals) == -2 and 0 in vals: # Two -1s and one 0
            return line[vals.index(0)]

    # --- PHASE 2: Alpha-Beta Search (Depth 2) ---
    
    # Optimization: If board is empty, take center
    if len(empty_cells) == 27:
        return (1, 1, 1)

    # Heuristic limit: if too many empty cells, depth 2 is fast enough (27*26 approx 700 checks).
    
    # Move Ordering: Evaluate Center -> Corners -> Edges/Faces
    # This maximizes pruning
    def sort_key(move):
        x, y, z = move
        # Center
        if (x, y, z) == (1, 1, 1): return 3
        # Corners (0 or 2 in all dims)
        is_corner = (x != 1) + (y != 1) + (z != 1)
        if is_corner == 3: return 2
        return 1
        
    empty_cells.sort(key=sort_key, reverse=True)
    
    best_value = -float('inf')
    best_move = empty_cells[0]
    
    alpha = -float('inf')
    beta = float('inf')
    
    for move in empty_cells:
        # Apply My Move
        mx, my, mz = move
        board[mx][my][mz] = 1
        
        # Minimax Step: Opponent's Turn (Minimize)
        min_opp_val = float('inf')
        
        # Check if this move was a win (already handled in Phase 1, but safe to keep logic consistent)
        # Assuming we didn't win, Opponent will try to win or minimize my score.
        
        # We perform a 1-ply search for opponent (Total Depth = 2)
        # Opponent moves: All currently empty cells (excluding the one I just filled)
        
        # If no moves left after mine?
        if len(empty_cells) == 1:
            val = _evaluate_board(board)
            min_opp_val = val
        else:
            can_prune_inner = False
            for omove in empty_cells:
                if omove == move: continue
                
                ox, oy, oz = omove
                board[ox][oy][oz] = -1
                
                # Leaf Evaluation
                val = _evaluate_board(board)
                
                # Backtrack Opponent
                board[ox][oy][oz] = 0
                
                if val < min_opp_val:
                    min_opp_val = val
                
                # Alpha-Beta Pruning (Min Node)
                if min_opp_val <= alpha:
                    can_prune_inner = True
                    break
            
        # Backtrack My Move
        board[mx][my][mz] = 0
        
        if min_opp_val > best_value:
            best_value = min_opp_val
            best_move = move
            
        if best_value >= beta:
            break
            
        alpha = max(alpha, best_value)
        
    return best_move


import numpy as np
from collections import deque

def policy(you: list[int], opponent: list[int]) -> str:
    # Convert to numpy arrays for easier manipulation
    you = np.array(you, dtype=int)
    opponent = np.array(opponent, dtype=int)
    
    rows, cols = 5, 6
    moves = []  # List of tuples: (row, col, dir, group_size, mobility)
    
    # Directions: up, right, down, left
    directions = [(-1, 0, 'U'), (0, 1, 'R'), (1, 0, 'D'), (0, -1, 'L')]
    
    # For each cell where you have a piece
    for r in range(rows):
        for c in range(cols):
            if you[r, c] == 1:
                # Check each direction
                for dr, dc, dir_name in directions:
                    nr, nc = r + dr, c + dc
                    # Check bounds and if opponent piece is present
                    if 0 <= nr < rows and 0 <= nc < cols and opponent[nr, nc] == 1:
                        # Found a legal move
                        # Compute size of opponent connected component that includes (nr, nc)
                        group_size = get_opponent_component_size(opponent, nr, nc)
                        
                        # Compute mobility after move: from new position (nr, nc), how many adjacent opponent pieces or empty spaces?
                        # But note: after move, your piece moves to (nr,nc), and (r,c) becomes empty.
                        # So we evaluate potential future moves FROM (nr, nc)
                        mobility = 0
                        for ddr, ddc, _ in directions:
                            nnr, nnc = nr + ddr, nc + ddc
                            if 0 <= nnr < rows and 0 <= nnc < cols:
                                # After move, our piece is at (nr, nc)
                                # Adjacent cells can be: empty (0,0) or opponent (still there, unless captured, but we're simulating)
                                # We care about: opponent pieces (potential future captures) OR empty spaces (potential for future expansion)
                                # We count both as mobility: because empty spaces give flexibility, opponent pieces give capture potential.
                                if you[nnr, nnc] == 0 and opponent[nnr, nnc] == 0:
                                    # empty space
                                    mobility += 1
                                elif opponent[nnr, nnc] == 1:
                                    # opponent piece (future capture)
                                    mobility += 1
                        moves.append((r, c, dir_name, group_size, mobility))
    
    # If no moves found (shouldn't happen per problem statement, but safety)
    if not moves:
        # Fallback: try any legal move by scanning again (should not occur)
        for r in range(rows):
            for c in range(cols):
                if you[r, c] == 1:
                    for dr, dc, dir_name in directions:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < rows and 0 <= nc < cols and opponent[nr, nc] == 1:
                            return f"{r},{c},{dir_name}"
        # If still nothing, raise error (per problem, won't happen)
        raise RuntimeError("No legal move found")
    
    # Sort by: 1) group_size descending (destroy big groups first) 
    #          2) mobility descending (more options next turn)
    #          3) then by row, col, and direction for deterministic behavior
    moves.sort(key=lambda x: (-x[3], -x[4], x[0], x[1], {'U':0, 'R':1, 'D':2, 'L':3}[x[2]]))
    
    best_move = moves[0]
    return f"{best_move[0]},{best_move[1]},{best_move[2]}"

def get_opponent_component_size(opponent: np.ndarray, start_row: int, start_col: int) -> int:
    """Compute size of connected component (4-directional) of opponent pieces starting at (start_row, start_col)"""
    if opponent[start_row, start_col] == 0:
        return 0
    
    rows, cols = opponent.shape
    visited = np.zeros_like(opponent, dtype=bool)
    queue = deque([(start_row, start_col)])
    visited[start_row, start_col] = True
    size = 0
    
    directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
    
    while queue:
        r, c = queue.popleft()
        size += 1
        
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if (0 <= nr < rows and 0 <= nc < cols and 
                opponent[nr, nc] == 1 and not visited[nr, nc]):
                visited[nr, nc] = True
                queue.append((nr, nc))
    
    return size

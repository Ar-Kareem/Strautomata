
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # Collect all legal moves
    legal_moves = []
    # Horizontal edges
    for row in range(5):
        for col in range(5):
            if horizontal[row, col] == 0:
                legal_moves.append((row, col, 'H'))
    # Vertical edges
    for row in range(5):
        for col in range(5):
            if vertical[row, col] == 0:
                legal_moves.append((row, col, 'V'))
                
    if not legal_moves:
        return "0,0,H"  # Should not happen in a valid game state
    
    capturing_moves = []
    non_capturing_moves = []
    
    for move in legal_moves:
        row, col, orientation = move
        capture_count = 0
        dangerous_count = 0
        sum_edges = 0  # Sum of existing edges in adjacent boxes
        
        if orientation == 'H':
            # Check upper box if exists
            if row > 0:
                top = horizontal[row-1, col] != 0
                left = vertical[row-1, col] != 0
                right = vertical[row-1, col+1] != 0
                edge_sum = top + left + right
                if edge_sum == 3:
                    capture_count += 1
                elif edge_sum == 2:
                    dangerous_count += 1
                sum_edges += edge_sum
            
            # Check lower box if exists
            if row < 4:
                bottom = horizontal[row+1, col] != 0
                left_box = vertical[row, col] != 0
                right_box = vertical[row, col+1] != 0
                edge_sum = bottom + left_box + right_box
                if edge_sum == 3:
                    capture_count += 1
                elif edge_sum == 2:
                    dangerous_count += 1
                sum_edges += edge_sum
        
        else:  # Vertical edge
            # Check left box if exists
            if col > 0:
                top = horizontal[row, col-1] != 0
                bottom = horizontal[row+1, col-1] != 0
                left = vertical[row, col-1] != 0
                edge_sum = top + bottom + left
                if edge_sum == 3:
                    capture_count += 1
                elif edge_sum == 2:
                    dangerous_count += 1
                sum_edges += edge_sum
            
            # Check right box if exists
            if col < 4:
                top = horizontal[row, col] != 0
                bottom = horizontal[row+1, col] != 0
                right = vertical[row, col+1] != 0
                edge_sum = top + bottom + right
                if edge_sum == 3:
                    capture_count += 1
                elif edge_sum == 2:
                    dangerous_count += 1
                sum_edges += edge_sum
        
        if capture_count > 0:
            capturing_moves.append((capture_count, dangerous_count, sum_edges, move))
        else:
            non_capturing_moves.append((dangerous_count, sum_edges, move))
    
    # Prioritize capturing moves
    if capturing_moves:
        # Sort by capture count (highest first), then dangerous count (lowest first), then sum edges
        capturing_moves.sort(key=lambda x: (-x[0], x[1], x[2]))
        best_move = capturing_moves[0][3]
        return f"{best_move[0]},{best_move[1]},{best_move[2]}"
    
    # Select safe moves (no dangerous boxes created)
    safe_moves = [m for m in non_capturing_moves if m[0] == 0]
    if safe_moves:
        # Sort by sum of existing edges (lower sum is better)
        safe_moves.sort(key=lambda x: x[1])
        best_move = safe_moves[0][2]
        return f"{best_move[0]},{best_move[1]},{best_move[2]}"
    
    # Only dangerous moves remain; choose least harmful option
    non_capturing_moves.sort(key=lambda x: (x[0], x[1]))  # Minimize dangerous count and edge sum
    best_move = non_capturing_moves[0][2]
    return f"{best_move[0]},{best_move[1]},{best_move[2]}"

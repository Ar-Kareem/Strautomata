
import numpy as np
from collections import deque

def policy(you: list[list[int]], opponent: list[list[int]]) -> str:
    you_arr = np.array(you)
    opp_arr = np.array(opponent)
    rows, cols = 5, 6
    
    best_move = None
    best_score = -1
    
    # Directions in order: Up, Right, Down, Left
    directions = [('U', -1, 0), ('R', 0, 1), ('D', 1, 0), ('L', 0, -1)]
    
    # Evaluate all possible moves
    for row in range(rows):
        for col in range(cols):
            if you_arr[row, col] != 1:
                continue
                
            for dir_code, dr, dc in directions:
                new_row, new_col = row + dr, col + dc
                
                # Check if move is valid
                if (0 <= new_row < rows and 0 <= new_col < cols and 
                    opp_arr[new_row, new_col] == 1):
                    
                    # Calculate score for this move
                    # 1. Count possible follow-up moves from new position
                    temp_you = you_arr.copy()
                    temp_opp = opp_arr.copy()
                    
                    # Execute the move
                    temp_you[row, col] = 0
                    temp_you[new_row, new_col] = 1
                    temp_opp[new_row, new_col] = 0
                    
                    # Count how many moves would be available from new position
                    follow_ups = 0
                    for (_, ndr, ndc) in directions:
                        nr, nc = new_row + ndr, new_col + ndc
                        if (0 <= nr < rows and 0 <= nc < cols and 
                            temp_opp[nr, nc] == 1 and temp_you[nr, nc] == 0):
                            follow_ups += 1
                    
                    # 2. Prefer moves closer to center (weighted by distance)
                    center_row, center_col = rows // 2, cols // 2
                    centrality = 1 / (1 + abs(new_row - center_row) + abs(new_col - center_col))
                    
                    # 3. Count opponent pieces adjacent to the captured piece (potential to open new moves)
                    adjacent_opp = 0
                    for (_, ndr, ndc) in directions:
                        nr, nc = new_row + ndr, new_col + ndc
                        if 0 <= nr < rows and 0 <= nc < cols and temp_opp[nr, nc] == 1:
                            adjacent_opp += 1
                    
                    # Combined score
                    score = follow_ups + centrality + adjacent_opp
                    
                    if score > best_score:
                        best_score = score
                        best_move = f"{row},{col},{dir_code}"
    
    # This should always return a move since policy is only called when moves exist
    return best_move

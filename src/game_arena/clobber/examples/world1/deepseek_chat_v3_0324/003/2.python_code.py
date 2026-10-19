
import numpy as np
import random

def policy(you: list[int], opponent: list[int]) -> str:
    you_arr = np.array(you)
    opponent_arr = np.array(opponent)
    rows, cols = 5, 6
    best_moves = []
    best_score = -1
    
    # Directions: U, R, D, L
    directions = [(-1, 0, 'U'), (0, 1, 'R'), (1, 0, 'D'), (0, -1, 'L')]
    
    for row in range(rows):
        for col in range(cols):
            if you_arr[row, col] == 1:
                for dr, dc, dir in directions:
                    new_row, new_col = row + dr, col + dc
                    if 0 <= new_row < rows and 0 <= new_col < cols:
                        if opponent_arr[new_row, new_col] == 1:
                            # Calculate move score based on opponent neighbors
                            score = 0
                            # Base score for capturing this piece
                            score += 1
                            
                            # Bonus if this capture isolates opponent pieces
                            for ndr, ndc, _ in directions:
                                nr, nc = new_row + ndr, new_col + ndc
                                if 0 <= nr < rows and 0 <= nc < cols:
                                    if opponent_arr[nr, nc] == 1:
                                        score += 0.1
                            
                            # Penalize moves that isolate our own pieces
                            our_neighbors = 0
                            for ndr, ndc, _ in directions:
                                nr, nc = row + ndr, col + dc
                                if 0 <= nr < rows and 0 <= nc < cols:
                                    if you_arr[nr, nc] == 1:
                                        our_neighbors += 1
                            if our_neighbors > 1:
                                score += 0.05 * our_neighbors
                            
                            if score > best_score:
                                best_score = score
                                best_moves = [(row, col, dir)]
                            elif score == best_score:
                                best_moves.append((row, col, dir))
    
    # Randomly select among best moves if there are ties
    selected = random.choice(best_moves)
    return f"{selected[0]},{selected[1]},{selected[2]}"

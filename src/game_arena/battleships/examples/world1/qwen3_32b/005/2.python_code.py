
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Generate all candidate cells (unshot)
    candidates = []
    for i in range(10):
        for j in range(10):
            if board[i][j] == 0:
                candidates.append((i, j))
    
    # Define the ship lengths to consider
    ship_lengths = [5, 4, 3, 3, 2]
    
    # Function to compute score for a candidate cell
    def compute_score(row, col):
        score = 0
        for length in ship_lengths:
            # Check horizontal placements including (row, col)
            start_col_min = max(0, col - length + 1)
            start_col_max = min(col, 10 - length)
            for c_start in range(start_col_min, start_col_max + 1):
                # Check all columns from c_start to c_start + length - 1
                valid = True
                for k in range(c_start, c_start + length):
                    if board[row][k] == -1:
                        valid = False
                        break
                if valid:
                    score += 1
            
            # Check vertical placements including (row, col)
            start_row_min = max(0, row - length + 1)
            start_row_max = min(row, 10 - length)
            for r_start in range(start_row_min, start_row_max + 1):
                # Check all rows from r_start to r_start + length - 1
                valid = True
                for k in range(r_start, r_start + length):
                    if board[k][col] == -1:
                        valid = False
                        break
                if valid:
                    score += 1
        return score
    
    # Evaluate all candidates and find best one
    best_score = -1
    best_move = candidates[0]  # Default to first candidate
    
    for (i, j) in candidates:
        current_score = compute_score(i, j)
        if current_score > best_score:
            best_score = current_score
            best_move = (i, j)
    
    return best_move

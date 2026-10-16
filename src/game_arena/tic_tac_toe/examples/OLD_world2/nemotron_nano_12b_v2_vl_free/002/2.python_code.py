
def policy(board: list[list[int]]) -> tuple[int, int]:
    empty_cells = [(i, j) for i in range(4) for j in range(4) if board[i][j] == 0]
    
    # Step 1: Check for winning moves (my three marks in a line)
    for i, j in empty_cells:
        # Check row i
        if board[i].count(1) == 3:
            return (i, j)
        # Check column j
        if sum(board[x][j] == 1 for x in range(4)) == 3:
            return (i, j)
        # Check main diagonal (i == j)
        if i == j:
            diag = [board[k][k] for k in range(4)]
            if sum(diag) == 3:
                return (i, j)
        # Check other diagonal (i + j == 3)
        if i + j == 3:
            diag = [board[k][3 - k] for k in range(4)]
            if sum(diag) == 3:
                return (i, j)
    
    # Step 2: Check for blocking moves (opponent's three marks)
    for i, j in empty_cells:
        # Check row
        if board[i].count(-1) == 3:
            return (i, j)
        # Check column
        if sum(board[x][j] == -1 for x in range(4)) == 3:
            return (i, j)
        # Check main diagonal
        if i == j:
            diag = [board[k][k] for k in range(4)]
            if sum(diag) == -3:
                return (i, j)
        # Check other diagonal
        if i + j == 3:
            diag = [board[k][3 - k] for k in range(4)]
            if sum(diag) == -3:
                return (i, j)
    
    # Step 3: Heuristic-based selection for strategic moves
    best_score = float('-inf')
    best_cell = None
    
    for cell in empty_cells:
        i, j = cell
        score = 0
        
        # Check row contribution
        row = board[i]
        my_row = row.count(1)
        opp_row = row.count(-1)
        row_diff = my_row - opp_row
        if row_diff > 0:
            score += row_diff * row_diff
        elif row_diff == 0:
            score += 1
        
        # Check column contribution
        col = [board[x][j] for x in range(4)]
        my_col = col.count(1)
        opp_col = col.count(-1)
        col_diff = my_col - opp_col
        if col_diff > 0:
            score += col_diff * col_diff
        elif col_diff == 0:
            score += 1
        
        # Evaluate diagonals
        if i == j:
            diag = [board[k][k] for k in range(4)]
            my_diag = diag.count(1)
            opp_diag = diag.count(-1)
            diag_diff = my_diag - opp_diag
            if diag_diff > 0:
                score += diag_diff * diag_diff
            elif diag_diff == 0:
                score += 1
        if i + j == 3:
            diag = [board[k][3 - k] for k in range(4)]
            my_diag = diag.count(1)
            opp_diag = diag.count(-1)
            diag_diff = my_diag - opp_diag
            if diag_diff > 0:
                score += diag_diff * diag_diff
            elif diag_diff == 0:
                score += 1
        
        # Position bonuses
        if i in {1, 2} and j in {1, 2}:
            score += 2  # Center cells bonus
        if (i, j) in {(0, 0), (0, 3), (3, 0), (3, 3)}:
            score += 1  # Corners bonus
        
        if score > best_score:
            best_score = score
            best_cell = cell
        elif score == best_score and cell < best_cell:
            best_cell = cell
    
    return best_cell

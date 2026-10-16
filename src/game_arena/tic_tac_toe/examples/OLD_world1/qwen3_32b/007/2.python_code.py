
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Helper function to determine if the given player has won
    def has_won(b, player):
        # Check rows
        for row in b:
            if all(cell == player for cell in row):
                return True
        # Check columns
        for col in range(3):
            if all(b[row][col] == player for row in range(3)):
                return True
        # Check diagonals
        if all(b[i][i] == player for i in range(3)):
            return True
        if all(b[i][2-i] == player for i in range(3)):
            return True
        return False
    
    # Find all empty cells
    empty_cells = [(i, j) for i in range(3) for j in range(3) if board[i][j] == 0]
    
    if not empty_cells:
        return (0, 0)  # This should not occur in valid gameplay

    # Step 1: Check for an immediate win
    for i, j in empty_cells:
        board_copy = [row[:] for row in board]
        board_copy[i][j] = 1
        if has_won(board_copy, 1):
            return (i, j)
    
    # Step 2: Block opponent's immediate win
    for i, j in empty_cells:
        board_copy = [row[:] for row in board]
        board_copy[i][j] = -1
        if has_won(board_copy, -1):
            return (i, j)
    
    # Step 3: Check for moves that create a fork (two threats)
    for i, j in empty_cells:
        board_sim = [row[:] for row in board]
        board_sim[i][j] = 1
        threats = 0
        
        # Check row for two 1s and one 0
        row = board_sim[i]
        ones = row.count(1)
        blanks = row.count(0)
        if ones == 2 and blanks == 1:
            threats += 1
        
        # Check column
        col = [board_sim[x][j] for x in range(3)]
        ones = col.count(1)
        blanks = col.count(0)
        if ones == 2 and blanks == 1:
            threats += 1
        
        # Check diagonals if applicable
        if i == j:
            diag = [board_sim[x][x] for x in range(3)]
            ones = diag.count(1)
            blanks = diag.count(0)
            if ones == 2 and blanks == 1:
                threats += 1
        if i + j == 2:
            anti_diag = [board_sim[x][2 - x] for x in range(3)]
            ones = anti_diag.count(1)
            blanks = anti_diag.count(0)
            if ones == 2 and blanks == 1:
                threats += 1
        
        if threats >= 2:
            return (i, j)
    
    # Step 4: Block opponent's potential fork
    fork_block_candidates = []
    for i, j in empty_cells:
        board_sim = [row[:] for row in board]
        board_sim[i][j] = -1
        threats = 0
        
        # Check row for two -1s and one 0
        row = board_sim[i]
        minus_ones = row.count(-1)
        blanks = row.count(0)
        if minus_ones == 2 and blanks == 1:
            threats += 1
        
        # Check column
        col = [board_sim[x][j] for x in range(3)]
        minus_ones = col.count(-1)
        blanks = col.count(0)
        if minus_ones == 2 and blanks == 1:
            threats += 1
        
        # Check diagonals if applicable
        if i == j:
            diag = [board_sim[x][x] for x in range(3)]
            minus_ones = diag.count(-1)
            blanks = diag.count(0)
            if minus_ones == 2 and blanks == 1:
                threats += 1
        if i + j == 2:
            anti_diag = [board_sim[x][2 - x] for x in range(3)]
            minus_ones = anti_diag.count(-1)
            blanks = anti_diag.count(0)
            if minus_ones == 2 and blanks == 1:
                threats += 1
        
        if threats >= 2:
            fork_block_candidates.append((i, j))
    
    if fork_block_candidates:
        # Prioritize center, then corners, then edges
        if (1, 1) in fork_block_candidates:
            return (1, 1)
        for x, y in [(0,0), (0,2), (2,0), (2,2)]:
            if (x, y) in fork_block_candidates:
                return (x, y)
        return fork_block_candidates[0]
    
    # Step 5: Default strategy - center, corners, edges
    if (1, 1) in empty_cells:
        return (1, 1)
    
    # Try corners
    for i, j in [(0,0), (0,2), (2,0), (2,2)]:
        if (i, j) in empty_cells:
            return (i, j)
    
    # Finally, choose an edge
    for i, j in [(0,1), (1,0), (1,2), (2,1)]:
        if (i, j) in empty_cells:
            return (i, j)
    
    # Fallback (shouldn't reach here in valid game)
    return empty_cells[0]

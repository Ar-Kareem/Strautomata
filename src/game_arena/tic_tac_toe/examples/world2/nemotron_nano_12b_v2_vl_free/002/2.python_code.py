def policy(board: list[list[int]]) -> tuple[int, int]:
    def is_win_move(r: int, c: int, player: int) -> bool:
        # Check if placing player at (r,c) would result in a win.
        # Check row r
        row_win = True
        for i in range(4):
            if i != c and board[r][i] != player:
                row_win = False
                break
        if row_win:
            return True
        
        # Check column c
        col_win = True
        for i in range(4):
            cell = board[i][c]
            if i != r and cell != player:
                col_win = False
                break
        if col_win:
            return True
        
        # Check main diagonal (if cell is on it)
        if r == c:
            diag_win = True
            for i in range(4):
                cell = board[i][i]
                if i != r and cell != player:
                    diag_win = False
                    break
            if diag_win:
                return True
        
        # Check anti-diagonal (if cell is on it)
        if r + c == 3:
            anti_diag_win = True
            for i in range(4):
                cell = board[i][3 - i]
                if i != r and cell != player:
                    anti_diag_win = False
                    break
            if anti_diag_win:
                return True
        
        return False

    # Step 1: Check for AI's winning move
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                if is_win_move(r, c, 1):
                    return (r, c)
    
    # Step 2: Check for opponent's winning move to block
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                if is_win_move(r, c, -1):
                    return (r, c)
    
    # Step 3: Heuristic-based move selection
    empty_cells = []
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                line_count = 2  # All cells have row and column
                # Check if part of main diagonal
                if r == c:
                    line_count += 1
                # Check if part of anti-diagonal
                if r + c == 3:
                    line_count += 1
                # Assign group based on cell position
                if r in {1, 2} and c in {1, 2}:
                    group = 0  # Center cells have higher priority
                elif r in {0, 3} and c in {0, 3}:
                    group = 1  # Corners next
                else:
                    group = 2  # Edges last
                # Append with negative line_count for descending sort
                empty_cells.append((-line_count, group, r, c))
    
    # Sort by line_count (desc), group (asc), then row and column
    empty_cells.sort()
    best_move = empty_cells[0]
    return (best_move[2], best_move[3])


def policy(board: list[list[int]]) -> int:
    def check_win(r: int, c: int, player: int) -> bool:
        """Check if placing player's disc at (r, c) creates a four-in-a-row."""
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]  # Horizontal, vertical, diagonal
        for dr, dc in directions:
            count = 1  # Current cell
            # Check positive direction
            for step in range(1, 4):
                nr, nc = r + dr * step, c + dc * step
                if 0 <= nr < 6 and 0 <= nc < 7 and board[nr][nc] == player:
                    count += 1
                else:
                    break
            # Check negative direction
            for step in range(1, 4):
                nr, nc = r - dr * step, c - dc * step
                if 0 <= nr < 6 and 0 <= nc < 7 and board[nr][nc] == player:
                    count += 1
                else:
                    break
            if count >= 4:
                return True
        return False

    # Step 1: Check for immediate win
    for col in range(7):
        if board[5][col] != 0:  # Skip full columns
            continue
        for row in range(5, -1, -1):
            if board[row][col] == 0:
                if check_win(row, col, 1):
                    return col

    # Step 2: Block opponent's win
    for col in range(7):
        if board[5][col] != 0:
            continue
        for row in range(5, -1, -1):
            if board[row][col] == 0:
                if check_win(row, col, -1):
                    return col

    # Step 3: Fork detection (create two winning threats)
    for col in range(7):
        if board[5][col] != 0:
            continue
        for row in range(5, -1, -1):
            if board[row][col] == 0:
                # Simulate placing disc
                board[row][col] = 1
                threats = 0
                for c_opp in range(7):
                    if board[5][c_opp] != 0:
                        continue
                    for r_opp in range(5, -1, -1):
                        if board[r_opp][c_opp] == 0:
                            if check_win(r_opp, c_opp, -1):
                                threats += 1
                board[row][col] = 0  # Reset
                if threats >= 2:
                    return col

    # Step 4: Create at least one winning threat
    for col in range(7):
        if board[5][col] != 0:
            continue
        for row in range(5, -1, -1):
            if board[row][col] == 0:
                board[row][col] = 1
                threats = 0
                for c_opp in range(7):
                    if board[5][c_opp] != 0:
                        continue
                    for r_opp in range(5, -1, -1):
                        if board[r_opp][c_opp] == 0:
                            if check_win(r_opp, c_opp, -1):
                                threats += 1
                board[row][col] = 0
                if threats >= 1:
                    return col

    # Step 5: Build strong position (center columns first)
    best_col = 0
    best_count = -1
    for col in range(7):
        if board[5][col] != 0:
            continue
        count = 0
        for row in range(5, -1, -1):
            if board[row][col] == 1:
                count += 1
        if count > best_count:
            best_count = count
            best_col = col
    return best_col

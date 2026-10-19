
def policy(board):
    def check_win(b, player):
        # Check rows
        for row in b:
            if all(cell == player for cell in row):
                return True
        # Check columns
        for col in range(4):
            if all(b[row][col] == player for row in range(4)):
                return True
        # Check main diagonal (0,0 to 3,3)
        if all(b[i][i] == player for i in range(4)):
            return True
        # Check anti-diagonal (0,3 to 3,0)
        if all(b[i][3 - i] == player for i in range(4)):
            return True
        return False

    # Step 1: Check for winning move
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                new_board = [row.copy() for row in board]
                new_board[i][j] = 1
                if check_win(new_board, 1):
                    return (i, j)
    
    # Step 2: Check for opponent's winning move and block
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                new_board = [row.copy() for row in board]
                new_board[i][j] = -1
                if check_win(new_board, -1):
                    return (i, j)
    
    # Step 3: Heuristic evaluation
    best_score = -1
    best_move = None
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                temp_board = [row.copy() for row in board]
                temp_board[i][j] = 1
                lines = []
                # Add the row i
                lines.append(temp_board[i])
                # Add column j
                col = [temp_board[k][j] for k in range(4)]
                lines.append(col)
                # Check if on main diagonal (i == j)
                if i == j:
                    diag = [temp_board[k][k] for k in range(4)]
                    lines.append(diag)
                # Check if on anti-diagonal (i + j == 3)
                if i + j == 3:
                    diag = [temp_board[k][3 - k] for k in range(4)]
                    lines.append(diag)
                # Calculate the maximum number of 1s in any of these lines
                max_count = 0
                for line in lines:
                    cnt = sum(1 for x in line if x == 1)
                    if cnt > max_count:
                        max_count = cnt
                current_score = max_count
                # Update best_move if current is better
                if current_score > best_score:
                    best_score = current_score
                    best_move = (i, j)
                elif current_score == best_score:
                    # Prefer moves closer to the center
                    current_dist = abs(i - 1.5) + abs(j - 1.5)
                    best_dist = abs(best_move[0] - 1.5) + abs(best_move[1] - 1.5)
                    if current_dist < best_dist:
                        best_move = (i, j)
    
    # Fallback if no move found (shouldn't happen if there are empty cells)
    if best_move is None:
        for i in range(4):
            for j in range(4):
                if board[i][j] == 0:
                    return (i, j)
        return (0, 0)  # Default in case of no moves (unlikely)
    
    return best_move

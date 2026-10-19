
def policy(board: list[list[int]]) -> int:
    # Helper function to check if a player has won
    def check_win(b, player):
        # Check horizontal
        for r in range(6):
            for c in range(4):
                if all(b[r][c + i] == player for i in range(4)):
                    return True
        # Check vertical
        for c in range(7):
            for r in range(3):
                if all(b[r + i][c] == player for i in range(4)):
                    return True
        # Check positive slope diagonals
        for r in range(3):
            for c in range(4):
                if all(b[r + i][c + i] == player for i in range(4)):
                    return True
        # Check negative slope diagonals
        for r in range(3, 6):
            for c in range(4):
                if all(b[r - i][c + i] == player for i in range(4)):
                    return True
        return False

    # Helper function to score a new disc's contribution to potential wins
    def score_position(b, row, col, player):
        score = 0
        
        # Horizontal
        count = 1
        c = col - 1
        while c >= 0 and b[row][c] == player:
            count += 1
            c -= 1
        c = col + 1
        while c < 7 and b[row][c] == player:
            count += 1
            c += 1
        if count == 4:
            score += 100
        elif count == 3:
            score += 5
        elif count == 2:
            score += 2
            
        # Vertical
        count = 1
        r = row - 1
        while r >= 0 and b[r][col] == player:
            count += 1
            r -= 1
        if count == 4:
            score += 100
        elif count == 3:
            score += 5
        elif count == 2:
            score += 2
            
        # Positive diagonal
        count = 1
        r, c = row - 1, col + 1
        while r >= 0 and c < 7 and b[r][c] == player:
            count += 1
            r -= 1
            c += 1
        r, c = row + 1, col - 1
        while r < 6 and c >= 0 and b[r][c] == player:
            count += 1
            r += 1
            c -= 1
        if count == 4:
            score += 100
        elif count == 3:
            score += 5
        elif count == 2:
            score += 2
            
        # Negative diagonal
        count = 1
        r, c = row + 1, col + 1
        while r < 6 and c < 7 and b[r][c] == player:
            count += 1
            r += 1
            c += 1
        r, c = row - 1, col - 1
        while r >= 0 and c >= 0 and b[r][c] == player:
            count += 1
            r -= 1
            c -= 1
        if count == 4:
            score += 100
        elif count == 3:
            score += 5
        elif count == 2:
            score += 2
            
        return score

    valid_cols = [col for col in range(7) if board[0][col] == 0]
    
    # Step 1: Check for immediate win
    for col in valid_cols:
        for row in range(6):
            if board[row][col] == 0:
                break
        new_board = [list(row) for row in board]
        new_board[row][col] = 1
        if check_win(new_board, 1):
            return col
    
    # Step 2: Block opponent's immediate win
    for col in valid_cols:
        for row in range(6):
            if board[row][col] == 0:
                break
        new_board = [list(row) for row in board]
        new_board[row][col] = -1
        if check_win(new_board, -1):
            return col
    
    # Step 3: Select best move based on scoring and center preference
    best_score = -1
    best_col = valid_cols[0]
    
    for col in valid_cols:
        for row in range(6):
            if board[row][col] == 0:
                break
        new_board = [list(row) for row in board]
        new_board[row][col] = 1
        current_score = score_position(new_board, row, col, 1)
        
        if current_score > best_score:
            best_score = current_score
            best_col = col
        elif current_score == best_score:
            current_dist = abs(col - 3)
            best_dist = abs(best_col - 3)
            if current_dist < best_dist:
                best_col = col
    
    return best_col

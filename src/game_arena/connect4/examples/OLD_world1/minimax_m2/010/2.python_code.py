
def policy(board: list[list[int]]) -> int:
    """
    Implements a Connect 4 targeting policy for a 6x7 grid.
    Returns the column index where to drop the disc.
    """
    rows, cols = len(board), len(board[0])
    
    def check_win_from_piece(r, c, player):
        """Check if placing at (r,c) forms a win for player"""
        directions = [(0,1), (1,0), (1,1), (1,-1)]
        for dr, dc in directions:
            count = 1
            # Check positive direction
            rr, cc = r+dr, c+dc
            while 0 <= rr < rows and 0 <= cc < cols and board[rr][cc] == player:
                count += 1
                rr += dr
                cc += dc
            # Check negative direction
            rr, cc = r-dr, c-dc
            while 0 <= rr < rows and 0 <= cc < cols and board[rr][cc] == player:
                count += 1
                rr -= dr
                cc -= dc
            if count >= 4:
                return True
        return False

    def evaluate_board():
        """Evaluate board position from current player's perspective"""
        score = 0
        center = cols // 2
        center_range = range(center-2, center+3) if cols >= 5 else range(cols)
        
        # Check horizontal
        for r in range(rows):
            for c in range(cols-3):
                window = [board[r][c+i] for i in range(4)]
                score += evaluate_window(window)
        
        # Check vertical
        for r in range(rows-3):
            for c in range(cols):
                window = [board[r+i][c] for i in range(4)]
                score += evaluate_window(window)
        
        # Check diagonal (down-right)
        for r in range(rows-3):
            for c in range(cols-3):
                window = [board[r+i][c+i] for i in range(4)]
                score += evaluate_window(window)
        
        # Check diagonal (down-left)
        for r in range(rows-3):
            for c in range(3, cols):
                window = [board[r+i][c-i] for i in range(4)]
                score += evaluate_window(window)
        
        # Center column preference
        for r in range(rows):
            if board[r][center] == 1:
                score += 3
            elif board[r][center] == -1:
                score -= 3
        
        return score

    def evaluate_window(window):
        """Evaluate a 4-cell window and return score"""
        count_self = window.count(1)
        count_opp = window.count(-1)
        count_empty = window.count(0)
        
        if count_self == 4:
            return 100000
        elif count_opp == 4:
            return -100000
        elif count_self == 3 and count_opp == 0:
            return 120 + count_empty * 10
        elif count_self == 2 and count_opp == 0:
            return 20 + count_empty * 5
        elif count_self == 1 and count_opp == 0:
            return 2 + count_empty * 2
        elif count_opp == 3 and count_self == 0:
            return -120 - count_empty * 10
        elif count_opp == 2 and count_self == 0:
            return -20 - count_empty * 5
        elif count_opp == 1 and count_self == 0:
            return -2 - count_empty * 2
        else:
            return 0

    # Step 1: Check for immediate winning move
    for col in range(cols):
        if board[0][col] == 0:  # Column not full
            # Find the lowest available row
            for row in range(rows-1, -1, -1):
                if board[row][col] == 0:
                    board[row][col] = 1
                    if check_win_from_piece(row, col, 1):
                        board[row][col] = 0
                        return col
                    board[row][col] = 0
                    break

    # Step 2: Check for opponent's winning move and block it
    for col in range(cols):
        if board[0][col] == 0:
            for row in range(rows-1, -1, -1):
                if board[row][col] == 0:
                    board[row][col] = -1
                    if check_win_from_piece(row, col, -1):
                        board[row][col] = 0
                        return col
                    board[row][col] = 0
                    break

    # Step 3: Use heuristic evaluation for remaining moves
    best_col = 0
    best_score = float('-inf')
    
    for col in range(cols):
        if board[0][col] == 0:
            for row in range(rows-1, -1, -1):
                if board[row][col] == 0:
                    board[row][col] = 1
                    score = evaluate_board()
                    
                    # Add small bonus for center column
                    if col == cols // 2:
                        score += 10
                    elif abs(col - cols // 2) == 1:
                        score += 5
                    
                    if score > best_score:
                        best_score = score
                        best_col = col
                    
                    board[row][col] = 0
                    break
    
    return best_col

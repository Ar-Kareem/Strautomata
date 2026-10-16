
def policy(board: list[list[int]]) -> int:
    # Check for immediate win
    for col in range(7):
        if board[0][col] != 0:  # Skip full columns
            continue
        # Simulate placing my disc
        row = 0
        while row < 6 and board[row][col] == 0:
            row += 1
        row -= 1
        board[row][col] = 1
        
        # Check if I won
        if check_win(board, row, col, 1):
            board[row][col] = 0  # Revert move
            return col
        
        # Check if opponent can win next
        opponent_win = False
        for opp_col in range(7):
            if board[0][opp_col] != 0:
                continue
            opp_row = 0
            while opp_row < 6 and board[opp_row][opp_col] == 0:
                opp_row += 1
            opp_row -= 1
            board[opp_row][opp_col] = -1
            
            if check_win(board, opp_row, opp_col, -1):
                opponent_win = True
                board[opp_row][opp_col] = 0  # Revert move
                break
            
            board[opp_row][opp_col] = 0  # Revert move
        
        # Revert my move
        board[row][col] = 0
        
        # Return column if safe
        if not opponent_win:
            return col
    
    # Choose center columns if no immediate threats
    for col in [3, 4, 2, 5, 1, 0, 6]:
        if board[0][col] == 0:
            return col
    
    # Fallback: return any available column
    for col in range(7):
        if board[0][col] == 0:
            return col

def check_win(board: list[list[int]], row: int, col: int, player: int) -> bool:
    # Check horizontal
    count = 0
    for i in range(4):
        if col - i >= 0 and board[row][col - i] == player:
            count += 1
        else:
            break
    if count == 4:
        return True
    count = 0
    for i in range(4):
        if col + i < 7 and board[row][col + i] == player:
            count += 1
        else:
            break
    if count == 4:
        return True
    
    # Check vertical
    count = 0
    for i in range(4):
        if row - i >= 0 and board[row - i][col] == player:
            count += 1
        else:
            break
    if count == 4:
        return True
    count = 0
    for i in range(4):
        if row + i < 6 and board[row + i][col] == player:
            count += 1
        else:
            break
    if count == 4:
        return True
    
    # Check diagonals
    count = 0
    for i in range(4):
        if row - i >= 0 and col - i >= 0 and board[row - i][col - i] == player:
            count += 1
        else:
            break
    if count == 4:
        return True
    count = 0
    for i in range(4):
        if row - i >= 0 and col + i < 7 and board[row - i][col + i] == player:
            count += 1
        else:
            break
    if count == 4:
        return True
    count = 0
    for i in range(4):
        if row + i < 6 and col - i >= 0 and board[row + i][col - i] == player:
            count += 1
        else:
            break
    if count == 4:
        return True
    count = 0
    for i in range(4):
        if row + i < 6 and col + i < 7 and board[row + i][col + i] == player:
            count += 1
        else:
            break
    if count == 4:
        return True
    
    return False

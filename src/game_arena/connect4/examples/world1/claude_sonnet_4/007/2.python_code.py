
def policy(board: list[list[int]]) -> int:
    def get_valid_moves():
        return [col for col in range(7) if board[0][col] == 0]
    
    def get_drop_row(col):
        for row in range(5, -1, -1):
            if board[row][col] == 0:
                return row
        return -1
    
    def check_win_at_position(board, row, col, player):
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        
        for dr, dc in directions:
            count = 1
            
            # Check positive direction
            r, c = row + dr, col + dc
            while 0 <= r < 6 and 0 <= c < 7 and board[r][c] == player:
                count += 1
                r += dr
                c += dc
            
            # Check negative direction
            r, c = row - dr, col - dc
            while 0 <= r < 6 and 0 <= c < 7 and board[r][c] == player:
                count += 1
                r -= dr
                c -= dc
            
            if count >= 4:
                return True
        return False
    
    def is_winning_move(col, player):
        row = get_drop_row(col)
        if row == -1:
            return False
        
        # Simulate the move
        board[row][col] = player
        is_win = check_win_at_position(board, row, col, player)
        board[row][col] = 0  # Undo
        return is_win
    
    valid_moves = get_valid_moves()
    
    # Priority 1: Win if possible
    for col in valid_moves:
        if is_winning_move(col, 1):
            return col
    
    # Priority 2: Block opponent's winning move
    for col in valid_moves:
        if is_winning_move(col, -1):
            return col
    
    # Priority 3: Choose center columns (better strategic positioning)
    center_order = [3, 2, 4, 1, 5, 0, 6]
    for col in center_order:
        if col in valid_moves:
            return col
    
    return valid_moves[0]

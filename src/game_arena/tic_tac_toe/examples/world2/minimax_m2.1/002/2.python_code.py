
def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Smart policy for 4x4 Tic Tac Toe
    Returns (row, col) for the next move
    """
    
    def check_win(bd, player):
        """Check if player has won"""
        # Check rows
        for i in range(4):
            if all(bd[i][j] == player for j in range(4)):
                return True
        # Check columns
        for j in range(4):
            if all(bd[i][j] == player for i in range(4)):
                return True
        # Check diagonals
        if all(bd[i][i] == player for i in range(4)):
            return True
        if all(bd[i][3-i] == player for i in range(4)):
            return True
        return False
    
    def count_line_potential(bd, player):
        """Count potential winning lines for player"""
        count = 0
        # Rows
        for i in range(4):
            player_count = sum(1 for j in range(4) if bd[i][j] == player)
            empty_count = sum(1 for j in range(4) if bd[i][j] == 0)
            if player_count == 3 and empty_count == 1:
                count += 1
        # Columns
        for j in range(4):
            player_count = sum(1 for i in range(4) if bd[i][j] == player)
            empty_count = sum(1 for i in range(4) if bd[i][j] == 0)
            if player_count == 3 and empty_count == 1:
                count += 1
        # Diagonals
        player_count = sum(1 for i in range(4) if bd[i][i] == player)
        empty_count = sum(1 for i in range(4) if bd[i][i] == 0)
        if player_count == 3 and empty_count == 1:
            count += 1
        player_count = sum(1 for i in range(4) if bd[i][3-i] == player)
        empty_count = sum(1 for i in range(4) if bd[i][3-i] == 0)
        if player_count == 3 and empty_count == 1:
            count += 1
        return count
    
    def count_threats(bd, player):
        """Count how many winning opportunities player has"""
        count = 0
        # Rows
        for i in range(4):
            player_count = sum(1 for j in range(4) if bd[i][j] == player)
            empty_count = sum(1 for j in range(4) if bd[i][j] == 0)
            if player_count >= 2 and empty_count >= 2:
                count += 1
        # Columns
        for j in range(4):
            player_count = sum(1 for i in range(4) if bd[i][j] == player)
            empty_count = sum(1 for i in range(4) if bd[i][j] == 0)
            if player_count >= 2 and empty_count >= 2:
                count += 1
        # Diagonals
        player_count = sum(1 for i in range(4) if bd[i][i] == player)
        empty_count = sum(1 for i in range(4) if bd[i][i] == 0)
        if player_count >= 2 and empty_count >= 2:
            count += 1
        player_count = sum(1 for i in range(4) if bd[i][3-i] == player)
        empty_count = sum(1 for i in range(4) if bd[i][3-i] == 0)
        if player_count >= 2 and empty_count >= 2:
            count += 1
        return count
    
    def get_position_value(row, col):
        """Strategic position values"""
        # Center squares are most valuable
        if row in [1, 2] and col in [1, 2]:
            return 3
        # Corners are next most valuable
        if (row == 0 or row == 3) and (col == 0 or col == 3):
            return 2
        # Edge centers
        return 1
    
    # Get all empty cells
    empty_cells = []
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                empty_cells.append((i, j))
    
    if not empty_cells:
        return (0, 0)  # Should not happen
    
    # 1. Check if we can win immediately
    for move in empty_cells:
        row, col = move
        board[row][col] = 1
        if check_win(board, 1):
            board[row][col] = 0
            return move
        board[row][col] = 0
    
    # 2. Check if opponent can win next and block them
    for move in empty_cells:
        row, col = move
        board[row][col] = -1
        if check_win(board, -1):
            board[row][col] = 0
            return move
        board[row][col] = 0
    
    # 3. Evaluate moves by strategic value
    best_moves = []
    best_score = -float('inf')
    
    for move in empty_cells:
        row, col = move
        board[row][col] = 1
        
        # Calculate score
        score = 0
        
        # Base position value
        score += get_position_value(row, col) * 10
        
        # Count threats we create
        threats = count_threats(board, 1)
        score += threats * 50
        
        # Count how many opponent threats we block
        board[row][col] = 0
        board[row][col] = -1
        opponent_threats_blocked = count_threats(board, -1)
        board[row][col] = 0
        
        score += opponent_threats_blocked * 30
        
        # Restore board
        board[row][col] = 0
        
        if score > best_score:
            best_score = score
            best_moves = [move]
        elif score == best_score:
            best_moves.append(move)
    
    # Return best move with some randomness to avoid predictability
    if best_moves:
        return best_moves[0]
    
    return empty_cells[0]


def policy(board: list[list[int]]) -> tuple[int, int]:
    def check_line_win(line, player):
        """Check if a line (4 positions) has a winning opportunity for player"""
        count_player = line.count(player)
        count_empty = line.count(0)
        count_opponent = line.count(-player)
        
        # Can win if 3 of player's pieces and 1 empty
        if count_player == 3 and count_empty == 1:
            return True
        return False
    
    def find_win_position(board, player):
        """Find position where player can win immediately"""
        for row in range(4):
            for col in range(4):
                if board[row][col] == 0:
                    # Try this position
                    board[row][col] = player
                    if is_winner(board, player):
                        board[row][col] = 0  # Reset
                        return (row, col)
                    board[row][col] = 0  # Reset
        return None
    
    def is_winner(board, player):
        """Check if player has won"""
        # Check rows
        for row in range(4):
            if all(board[row][col] == player for col in range(4)):
                return True
        
        # Check columns
        for col in range(4):
            if all(board[row][col] == player for row in range(4)):
                return True
        
        # Check main diagonal
        if all(board[i][i] == player for i in range(4)):
            return True
        
        # Check anti-diagonal
        if all(board[i][3-i] == player for i in range(4)):
            return True
        
        return False
    
    def evaluate_position(board, row, col):
        """Evaluate how good a position is strategically"""
        if board[row][col] != 0:
            return -1000  # Invalid move
        
        score = 0
        
        # Center positions are valuable
        if (row, col) in [(1,1), (1,2), (2,1), (2,2)]:
            score += 10
        
        # Corners are somewhat valuable
        elif (row, col) in [(0,0), (0,3), (3,0), (3,3)]:
            score += 5
        
        # Check how many lines this position participates in
        lines = []
        
        # Row
        lines.append([board[row][c] for c in range(4)])
        # Column  
        lines.append([board[r][col] for r in range(4)])
        # Main diagonal
        if row == col:
            lines.append([board[i][i] for i in range(4)])
        # Anti-diagonal
        if row + col == 3:
            lines.append([board[i][3-i] for i in range(4)])
        
        # Evaluate each line this position participates in
        for line in lines:
            my_count = line.count(1)
            opp_count = line.count(-1)
            empty_count = line.count(0)
            
            # Good if we can build on this line
            if opp_count == 0:  # No opponent pieces blocking
                score += my_count * 3
            
            # Bad if opponent can build on this line
            if my_count == 0:  # No our pieces blocking opponent
                score -= opp_count * 2
        
        return score
    
    # Strategy:
    # 1. Check if we can win immediately
    win_pos = find_win_position(board, 1)
    if win_pos:
        return win_pos
    
    # 2. Check if we need to block opponent from winning
    block_pos = find_win_position(board, -1)
    if block_pos:
        return block_pos
    
    # 3. Find best strategic position
    best_score = -1000
    best_move = None
    
    for row in range(4):
        for col in range(4):
            if board[row][col] == 0:
                score = evaluate_position(board, row, col)
                if score > best_score:
                    best_score = score
                    best_move = (row, col)
    
    return best_move if best_move else (0, 0)

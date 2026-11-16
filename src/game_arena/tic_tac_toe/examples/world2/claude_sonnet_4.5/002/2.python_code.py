
def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    4x4 Tic Tac Toe policy
    Returns (row, col) for next move
    """
    
    def check_line(line, player):
        """Check if a line has 3 of player and 1 empty (winning opportunity)"""
        count_player = sum(1 for x in line if x == player)
        count_empty = sum(1 for x in line if x == 0)
        if count_player == 3 and count_empty == 1:
            return True
        return False
    
    def get_empty_in_line(line, indices):
        """Get the empty position in a line"""
        for i, (val, idx) in enumerate(zip(line, indices)):
            if val == 0:
                return idx
        return None
    
    def get_all_lines():
        """Get all possible winning lines with their board positions"""
        lines = []
        
        # Rows
        for r in range(4):
            line = [board[r][c] for c in range(4)]
            indices = [(r, c) for c in range(4)]
            lines.append((line, indices))
        
        # Columns
        for c in range(4):
            line = [board[r][c] for r in range(4)]
            indices = [(r, c) for r in range(4)]
            lines.append((line, indices))
        
        # Diagonals
        line = [board[i][i] for i in range(4)]
        indices = [(i, i) for i in range(4)]
        lines.append((line, indices))
        
        line = [board[i][3-i] for i in range(4)]
        indices = [(i, 3-i) for i in range(4)]
        lines.append((line, indices))
        
        return lines
    
    def find_winning_move(player):
        """Find if player can win in one move"""
        lines = get_all_lines()
        for line, indices in lines:
            if check_line(line, player):
                return get_empty_in_line(line, indices)
        return None
    
    def score_position(r, c):
        """Score a position based on potential"""
        if board[r][c] != 0:
            return -1000
        
        score = 0
        
        # Prefer center positions
        center_distance = abs(r - 1.5) + abs(c - 1.5)
        score += (6 - center_distance) * 2
        
        # Count how many lines this position is part of
        lines = get_all_lines()
        for line, indices in lines:
            if (r, c) in indices:
                # Check if this line is promising
                idx = indices.index((r, c))
                temp_line = line.copy()
                temp_line[idx] = 1  # Simulate placing our piece
                
                count_mine = sum(1 for x in temp_line if x == 1)
                count_opp = sum(1 for x in temp_line if x == -1)
                
                # Line is good if no opponent pieces
                if count_opp == 0:
                    score += count_mine * 3
                
                # Bonus for creating threats
                if count_mine == 3 and count_opp == 0:
                    score += 20
        
        return score
    
    # 1. Check if we can win
    win_move = find_winning_move(1)
    if win_move:
        return win_move
    
    # 2. Check if we need to block opponent
    block_move = find_winning_move(-1)
    if block_move:
        return block_move
    
    # 3. Find best move by scoring all positions
    best_score = -float('inf')
    best_move = None
    
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                score = score_position(r, c)
                if score > best_score:
                    best_score = score
                    best_move = (r, c)
    
    # Fallback: return any empty position
    if best_move is None:
        for r in range(4):
            for c in range(4):
                if board[r][c] == 0:
                    return (r, c)
    
    return best_move

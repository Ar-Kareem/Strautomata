
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    Smart 3D Tic Tac Toe policy that evaluates positions and chooses optimal moves.
    
    Strategy:
    1. Take immediate winning moves
    2. Block opponent's winning moves
    3. Create multiple threats (2 in a row with empty third)
    4. Prioritize strategically important positions
    
    Args:
        board: 3x3x3 array where 0=empty, 1=your move, -1=opponent's move
        
    Returns:
        Tuple (i, j, k) representing the next move
    """
    
    def get_empty_cells(board):
        """Get all empty cell coordinates"""
        empty = []
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    if board[i][j][k] == 0:
                        empty.append((i, j, k))
        return empty
    
    def count_line(line):
        """Count my marks, opponent marks, and empty cells in a line"""
        my_count = 0
        opp_count = 0
        empty_count = 0
        for cell in line:
            val = board[cell[0]][cell[1]][cell[2]]
            if val == 1:
                my_count += 1
            elif val == -1:
                opp_count += 1
            else:
                empty_count += 1
        return my_count, opp_count, empty_count
    
    def get_winning_lines():
        """Generate all 49 winning lines in 3x3x3 Tic Tac Toe"""
        lines = []
        
        # Lines along each axis
        for i in range(3):
            for j in range(3):
                lines.append([(i, j, k) for k in range(3)])  # z-axis
                lines.append([(i, k, j) for k in range(3)])  # y-axis  
                lines.append([(k, i, j) for k in range(3)])  # x-axis
        
        # 2D diagonals in each plane
        for i in range(3):
            # xy plane diagonals
            lines.append([(i, j, j) for j in range(3)])
            lines.append([(i, j, 2-j) for j in range(3)])
            # xz plane diagonals
            lines.append([(j, i, j) for j in range(3)])
            lines.append([(j, i, 2-j) for j in range(3)])
            # yz plane diagonals
            lines.append([(i, j, j) for j in range(3)])
            lines.append([(i, j, 2-j) for j in range(3)])
        
        # Space diagonals (corner to corner through center)
        lines.append([(0,0,0), (1,1,1), (2,2,2)])
        lines.append([(0,0,2), (1,1,1), (2,2,0)])
        lines.append([(0,2,0), (1,1,1), (2,0,2)])
        lines.append([(0,2,2), (1,1,1), (2,0,0)])
        
        return lines
    
    def would_win(move):
        """Check if placing a mark at move would win the game"""
        i, j, k = move
        temp_board = [[[board[x][y][z] for z in range(3)] for y in range(3)] for x in range(3)]
        temp_board[i][j][k] = 1
        
        lines = get_winning_lines()
        for line in lines:
            my_count = 0
            for (x, y, z) in line:
                if temp_board[x][y][z] == 1:
                    my_count += 1
            if my_count == 3:
                return True
        return False
    
    def would_lose(move):
        """Check if opponent would win if we don't block this move"""
        i, j, k = move
        temp_board = [[[board[x][y][z] for z in range(3)] for y in range(3)] for x in range(3)]
        temp_board[i][j][k] = -1  # Simulate opponent's move
        
        lines = get_winning_lines()
        for line in lines:
            opp_count = 0
            for (x, y, z) in line:
                if temp_board[x][y][z] == -1:
                    opp_count += 1
            if opp_count == 3:
                return True
        return False
    
    def evaluate_move(move):
        """Heuristic evaluation of a move's quality"""
        i, j, k = move
        
        # Base positional value
        if (i, j, k) == (1, 1, 1):  # Center
            base_value = 100
        elif (i, j, k) in [(0,0,0), (0,0,2), (0,2,0), (0,2,2), 
                           (2,0,0), (2,0,2), (2,2,0), (2,2,2)]:  # Corners
            base_value = 50
        elif (i == 1 and j == 1) or (i == 1 and k == 1) or (j == 1 and k == 1):  # Face centers
            base_value = 30
        else:  # Edge centers
            base_value = 10
        
        # Count how many lines this move would complete for me
        threat_bonus = 0
        lines = get_winning_lines()
        for line in lines:
            if move in line:
                my_count, opp_count, empty_count = count_line(line)
                # Bonus for creating threats (2 in a row with empty third)
                if my_count == 2 and empty_count == 1:
                    threat_bonus += 20
                elif my_count == 1 and empty_count == 2:
                    threat_bonus += 5
                # Penalty for helping opponent
                if opp_count == 2 and empty_count == 1:
                    threat_bonus -= 40
        
        return base_value + threat_bonus
    
    # Main strategy logic
    empty_cells = get_empty_cells(board)
    
    if not empty_cells:
        return (0, 0, 0)  # Should not happen, but return valid move
    
    # Priority 1: Take winning move if available
    for move in empty_cells:
        if would_win(move):
            return move
    
    # Priority 2: Block opponent's winning move
    for move in empty_cells:
        if would_lose(move):
            return move
    
    # Priority 3: Choose best move based on evaluation
    best_move = empty_cells[0]
    best_score = evaluate_move(empty_cells[0])
    
    for move in empty_cells[1:]:
        score = evaluate_move(move)
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move

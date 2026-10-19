
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    import random
    
    def get_all_lines():
        """Get all possible winning lines in 3x3x3 board"""
        lines = []
        
        # Rows (9 lines)
        for z in range(3):
            for y in range(3):
                lines.append([(z, y, 0), (z, y, 1), (z, y, 2)])
        
        # Columns (9 lines) 
        for z in range(3):
            for x in range(3):
                lines.append([(z, 0, x), (z, 1, x), (z, 2, x)])
        
        # Verticals (9 lines)
        for y in range(3):
            for x in range(3):
                lines.append([(0, y, x), (1, y, x), (2, y, x)])
        
        # Face diagonals (12 lines)
        # XY plane diagonals
        for z in range(3):
            lines.append([(z, 0, 0), (z, 1, 1), (z, 2, 2)])
            lines.append([(z, 0, 2), (z, 1, 1), (z, 2, 0)])
        
        # XZ plane diagonals  
        for y in range(3):
            lines.append([(0, y, 0), (1, y, 1), (2, y, 2)])
            lines.append([(0, y, 2), (1, y, 1), (2, y, 0)])
        
        # YZ plane diagonals
        for x in range(3):
            lines.append([(0, 0, x), (1, 1, x), (2, 2, x)])
            lines.append([(0, 2, x), (1, 1, x), (2, 0, x)])
        
        # Space diagonals (4 lines)
        lines.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
        lines.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
        lines.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
        lines.append([(0, 2, 2), (1, 1, 1), (2, 0, 0)])
        
        return lines
    
    def get_line_values(line):
        """Get values for positions in a line"""
        return [board[z][y][x] for z, y, x in line]
    
    def is_empty(pos):
        """Check if position is empty"""
        z, y, x = pos
        return board[z][y][x] == 0
    
    def get_empty_positions():
        """Get all empty positions"""
        empty = []
        for z in range(3):
            for y in range(3):
                for x in range(3):
                    if board[z][y][x] == 0:
                        empty.append((z, y, x))
        return empty
    
    def evaluate_move(pos):
        """Evaluate a move by checking all lines it participates in"""
        score = 0
        z, y, x = pos
        
        for line in get_all_lines():
            if (z, y, x) not in line:
                continue
                
            values = get_line_values(line)
            my_count = values.count(1)
            opp_count = values.count(-1)
            empty_count = values.count(0)
            
            # If opponent can win next turn, this is critical
            if opp_count == 2 and empty_count == 1:
                score += 1000
            # If we can win, this is best
            elif my_count == 2 and empty_count == 1:
                score += 2000
            # If we can create a threat
            elif my_count == 1 and empty_count == 2:
                score += 10
            # If this prevents opponent threat
            elif opp_count == 1 and empty_count == 2:
                score += 5
            # Empty line is still valuable
            elif empty_count == 3:
                score += 1
        
        # Prefer center positions
        if (z, y, x) == (1, 1, 1):
            score += 50
        # Prefer corners and edges
        elif sum([coord in [0, 2] for coord in [z, y, x]]) >= 2:
            score += 20
        
        return score
    
    # Get all possible moves
    empty_positions = get_empty_positions()
    
    if not empty_positions:
        return (0, 0, 0)  # Should not happen in valid game
    
    # Check for immediate win or block
    lines = get_all_lines()
    
    # First priority: win if possible
    for line in lines:
        values = get_line_values(line)
        if values.count(1) == 2 and values.count(0) == 1:
            for pos in line:
                if is_empty(pos):
                    return pos
    
    # Second priority: block opponent win
    for line in lines:
        values = get_line_values(line)
        if values.count(-1) == 2 and values.count(0) == 1:
            for pos in line:
                if is_empty(pos):
                    return pos
    
    # Otherwise, choose best strategic move
    best_moves = []
    best_score = -1
    
    for pos in empty_positions:
        score = evaluate_move(pos)
        if score > best_score:
            best_score = score
            best_moves = [pos]
        elif score == best_score:
            best_moves.append(pos)
    
    # If multiple best moves, choose randomly among them
    return random.choice(best_moves)

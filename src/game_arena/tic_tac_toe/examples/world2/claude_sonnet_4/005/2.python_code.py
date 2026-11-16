
def policy(board: list[list[int]]) -> tuple[int, int]:
    def check_line(line):
        """Check a line of 4 positions and return (my_count, opp_count, empty_positions)"""
        my_count = sum(1 for x in line if x == 1)
        opp_count = sum(1 for x in line if x == -1)
        empty_pos = [i for i, x in enumerate(line) if x == 0]
        return my_count, opp_count, empty_pos
    
    def get_all_lines():
        """Get all possible winning lines (rows, columns, diagonals)"""
        lines = []
        
        # Rows
        for r in range(4):
            lines.append([(r, c) for c in range(4)])
        
        # Columns
        for c in range(4):
            lines.append([(r, c) for r in range(4)])
        
        # Main diagonal
        lines.append([(i, i) for i in range(4)])
        
        # Anti-diagonal
        lines.append([(i, 3-i) for i in range(4)])
        
        return lines
    
    def evaluate_position(r, c):
        """Evaluate how good a position is"""
        if board[r][c] != 0:
            return -1000  # Invalid move
        
        # Try the move
        board[r][c] = 1
        score = 0
        
        # Check all lines that include this position
        for line_pos in get_all_lines():
            if (r, c) in line_pos:
                line_values = [board[pos[0]][pos[1]] for pos in line_pos]
                my_count, opp_count, empty_pos = check_line(line_values)
                
                # Winning move
                if my_count == 4:
                    board[r][c] = 0  # Undo move
                    return 10000
                
                # Creating threats
                if my_count == 3 and opp_count == 0:
                    score += 500
                elif my_count == 2 and opp_count == 0:
                    score += 50
                elif my_count == 1 and opp_count == 0:
                    score += 5
        
        # Undo move
        board[r][c] = 0
        return score
    
    def find_immediate_win():
        """Find immediate winning move"""
        for line_pos in get_all_lines():
            line_values = [board[pos[0]][pos[1]] for pos in line_pos]
            my_count, opp_count, empty_pos = check_line(line_values)
            
            if my_count == 3 and opp_count == 0 and len(empty_pos) == 1:
                empty_idx = empty_pos[0]
                return line_pos[empty_idx]
        return None
    
    def find_immediate_block():
        """Find move to block opponent's immediate win"""
        for line_pos in get_all_lines():
            line_values = [board[pos[0]][pos[1]] for pos in line_pos]
            my_count, opp_count, empty_pos = check_line(line_values)
            
            if opp_count == 3 and my_count == 0 and len(empty_pos) == 1:
                empty_idx = empty_pos[0]
                return line_pos[empty_idx]
        return None
    
    # First, check for immediate win
    win_move = find_immediate_win()
    if win_move:
        return win_move
    
    # Second, check if we need to block opponent
    block_move = find_immediate_block()
    if block_move:
        return block_move
    
    # Otherwise, find the best move using evaluation
    best_score = -10000
    best_moves = []
    
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                score = evaluate_position(r, c)
                
                # Add positional bonus (prefer center)
                center_bonus = 0
                if (r, c) in [(1, 1), (1, 2), (2, 1), (2, 2)]:
                    center_bonus = 10
                elif (r, c) in [(0, 1), (0, 2), (1, 0), (1, 3), (2, 0), (2, 3), (3, 1), (3, 2)]:
                    center_bonus = 5
                
                score += center_bonus
                
                if score > best_score:
                    best_score = score
                    best_moves = [(r, c)]
                elif score == best_score:
                    best_moves.append((r, c))
    
    # Return the first best move (or any best move if multiple)
    return best_moves[0] if best_moves else (0, 0)

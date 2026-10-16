
def policy(board: list[list[int]]) -> tuple[int, int]:
    def get_all_lines():
        """Get all possible winning lines (rows, columns, diagonals)"""
        lines = []
        
        # Rows
        for i in range(4):
            lines.append([(i, j) for j in range(4)])
        
        # Columns
        for j in range(4):
            lines.append([(i, j) for i in range(4)])
        
        # Diagonals
        lines.append([(i, i) for i in range(4)])  # Main diagonal
        lines.append([(i, 3-i) for i in range(4)])  # Anti-diagonal
        
        return lines
    
    def evaluate_line(line):
        """Evaluate a line and return (my_count, opp_count, empty_positions)"""
        my_count = 0
        opp_count = 0
        empty_positions = []
        
        for r, c in line:
            if board[r][c] == 1:
                my_count += 1
            elif board[r][c] == -1:
                opp_count += 1
            else:
                empty_positions.append((r, c))
        
        return my_count, opp_count, empty_positions
    
    def find_winning_move():
        """Find immediate winning move"""
        for line in get_all_lines():
            my_count, opp_count, empty_positions = evaluate_line(line)
            if my_count == 3 and opp_count == 0 and len(empty_positions) == 1:
                return empty_positions[0]
        return None
    
    def find_blocking_move():
        """Find move to block opponent's win"""
        for line in get_all_lines():
            my_count, opp_count, empty_positions = evaluate_line(line)
            if opp_count == 3 and my_count == 0 and len(empty_positions) == 1:
                return empty_positions[0]
        return None
    
    def get_strategic_move():
        """Get best strategic move using heuristics"""
        move_scores = {}
        
        # Evaluate all empty positions
        for i in range(4):
            for j in range(4):
                if board[i][j] == 0:
                    score = 0
                    
                    # Check all lines this position is part of
                    for line in get_all_lines():
                        if (i, j) in line:
                            my_count, opp_count, empty_positions = evaluate_line(line)
                            
                            # If line is not blocked by opponent
                            if opp_count == 0:
                                # Prefer lines where I already have pieces
                                if my_count == 2:
                                    score += 10  # Create a threat
                                elif my_count == 1:
                                    score += 3   # Extend existing line
                                else:
                                    score += 1   # Start new line
                            
                            # If line is not blocked by me (defensive consideration)
                            if my_count == 0 and opp_count == 2:
                                score += 5  # Prevent opponent threat
                    
                    # Position-based bonuses
                    # Center squares are valuable
                    if (i, j) in [(1, 1), (1, 2), (2, 1), (2, 2)]:
                        score += 2
                    
                    # Corner squares have some value
                    if (i, j) in [(0, 0), (0, 3), (3, 0), (3, 3)]:
                        score += 1
                    
                    move_scores[(i, j)] = score
        
        # Return the move with highest score
        if move_scores:
            return max(move_scores.items(), key=lambda x: x[1])[0]
        
        # Fallback: return first available position
        for i in range(4):
            for j in range(4):
                if board[i][j] == 0:
                    return (i, j)
        
        return (0, 0)  # Should never reach here in a valid game
    
    # Strategy: Win > Block > Strategic move
    
    # 1. Check if I can win immediately
    winning_move = find_winning_move()
    if winning_move:
        return winning_move
    
    # 2. Check if I need to block opponent's win
    blocking_move = find_blocking_move()
    if blocking_move:
        return blocking_move
    
    # 3. Make strategic move
    return get_strategic_move()

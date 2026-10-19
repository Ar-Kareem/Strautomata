
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    import numpy as np
    
    b = np.array(board)
    
    # Generate all winning lines (49 total)
    lines = []
    
    # Straight lines along each axis (27 lines)
    for i in range(3):
        for j in range(3):
            lines.append([(i, j, k) for k in range(3)])  # Along z
            lines.append([(i, k, j) for k in range(3)])  # Along y
            lines.append([(k, i, j) for k in range(3)])  # Along x
    
    # 2D diagonals on each slice (18 lines)
    for i in range(3):
        # xy plane diagonals (fixed z)
        lines.append([(j, j, i) for j in range(3)])
        lines.append([(j, 2-j, i) for j in range(3)])
        # xz plane diagonals (fixed y)
        lines.append([(j, i, j) for j in range(3)])
        lines.append([(j, i, 2-j) for j in range(3)])
        # yz plane diagonals (fixed x)
        lines.append([(i, j, j) for j in range(3)])
        lines.append([(i, j, 2-j) for j in range(3)])
    
    # 4 space diagonals
    lines.append([(i, i, i) for i in range(3)])
    lines.append([(i, i, 2-i) for i in range(3)])
    lines.append([(i, 2-i, i) for i in range(3)])
    lines.append([(2-i, i, i) for i in range(3)])
    
    def get_line_state(line):
        """Return (my_count, opp_count, empty_positions) for a line."""
        my_count = sum(1 for pos in line if b[pos] == 1)
        opp_count = sum(1 for pos in line if b[pos] == -1)
        empty = [pos for pos in line if b[pos] == 0]
        return my_count, opp_count, empty
    
    def find_winning_move(player):
        """Find a move that completes 3-in-a-row for player."""
        for line in lines:
            values = [b[pos] for pos in line]
            if values.count(player) == 2 and values.count(0) == 1:
                return line[values.index(0)]
        return None
    
    # 1. Win if possible
    move = find_winning_move(1)
    if move:
        return move
    
    # 2. Block opponent's win
    move = find_winning_move(-1)
    if move:
        return move
    
    # 3. Look for fork (create two winning threats)
    empty_cells = [(i, j, k) for i in range(3) for j in range(3) for k in range(3) if b[i,j,k] == 0]
    
    def count_threats_after_move(cell, player):
        """Count winning threats created if player plays at cell."""
        threats = 0
        for line in lines:
            if cell in line:
                my_count, opp_count, empty = get_line_state(line)
                if player == 1 and my_count == 1 and opp_count == 0 and len(empty) == 2:
                    threats += 1
                elif player == -1 and opp_count == 1 and my_count == 0 and len(empty) == 2:
                    threats += 1
        return threats
    
    # Try to create a fork
    best_fork = None
    best_fork_score = 1
    for cell in empty_cells:
        threats = count_threats_after_move(cell, 1)
        if threats > best_fork_score:
            best_fork_score = threats
            best_fork = cell
    
    if best_fork:
        return best_fork
    
    # 4. Block opponent's fork attempts
    for cell in empty_cells:
        opp_threats = count_threats_after_move(cell, -1)
        if opp_threats >= 2:
            return cell
    
    # 5. Strategic scoring for remaining moves
    def score_cell(cell):
        score = 0
        for line in lines:
            if cell in line:
                my_count, opp_count, empty = get_line_state(line)
                if opp_count == 0:  # Line still winnable
                    score += (my_count + 1) ** 2
                elif my_count == 0:  # Could block opponent
                    score += opp_count * 0.5
        
        # Position bonuses
        if cell == (1, 1, 1):  # Center - part of 13 lines
            score += 15
        elif all(c in [0, 2] for c in cell):  # Corners - part of 7 lines
            score += 5
        elif list(cell).count(1) == 1:  # Edge centers
            score += 2
        
        return score
    
    if empty_cells:
        return max(empty_cells, key=score_cell)
    
    return (0, 0, 0)

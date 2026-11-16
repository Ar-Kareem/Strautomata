
def policy(board):
    """
    3D Tic Tac Toe Policy for 3x3x3 board.
    Prioritizes: 1) Wins, 2) Blocks, 3) Forks, 4) Heuristic scoring
    """
    # Generate all 49 winning lines (27 axis-aligned + 18 face diagonals + 4 space diagonals)
    lines = []
    
    # Axis-aligned lines (27)
    for a in range(3):
        for b in range(3):
            lines.append([(0, a, b), (1, a, b), (2, a, b)])  # i-direction
            lines.append([(a, 0, b), (a, 1, b), (a, 2, b)])  # j-direction
            lines.append([(a, b, 0), (a, b, 1), (a, b, 2)])  # k-direction
    
    # Face diagonals (18)
    for c in range(3):
        lines.append([(0, 0, c), (1, 1, c), (2, 2, c)])  # XY main
        lines.append([(0, 2, c), (1, 1, c), (2, 0, c)])  # XY anti
        lines.append([(0, c, 0), (1, c, 1), (2, c, 2)])  # XZ main
        lines.append([(0, c, 2), (1, c, 1), (2, c, 0)])  # XZ anti
        lines.append([(c, 0, 0), (c, 1, 1), (c, 2, 2)])  # YZ main
        lines.append([(c, 0, 2), (c, 1, 1), (c, 2, 0)])  # YZ anti
    
    # Space diagonals (4)
    lines.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
    lines.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
    lines.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
    lines.append([(2, 0, 0), (1, 1, 1), (0, 2, 2)])
    
    # Find all empty cells
    empty_cells = [(i, j, k) for i in range(3) for j in range(3) for k in range(3) if board[i][j][k] == 0]
    
    if not empty_cells:
        return (0, 0, 0)
    
    # Opening: take center if first move
    if len(empty_cells) == 27:
        return (1, 1, 1)
    
    # 1. Check for immediate win
    for line in lines:
        values = [board[i][j][k] for (i, j, k) in line]
        if values.count(1) == 2 and values.count(0) == 1:
            return line[values.index(0)]
    
    # 2. Check for opponent win (block)
    for line in lines:
        values = [board[i][j][k] for (i, j, k) in line]
        if values.count(-1) == 2 and values.count(0) == 1:
            return line[values.index(0)]
    
    # 3. Check for fork (create two threats)
    position_value = {
        (1, 1, 1): 100,
        (0, 0, 0): 40, (0, 0, 2): 40, (0, 2, 0): 40, (0, 2, 2): 40,
        (2, 0, 0): 40, (2, 0, 2): 40, (2, 2, 0): 40, (2, 2, 2): 40,
        (0, 1, 1): 30, (2, 1, 1): 30, (1, 0, 1): 30, (1, 2, 1): 30,
        (1, 1, 0): 30, (1, 1, 2): 30,
    }
    
    for cell in empty_cells:
        threat_count = 0
        for line in lines:
            if cell in line:
                values = [board[i][j][k] for (i, j, k) in line]
                if values.count(1) == 1 and values.count(0) == 2 and -1 not in values:
                    threat_count += 1
        if threat_count >= 2:
            return cell
    
    # 4. Heuristic scoring
    best_move = empty_cells[0]
    best_score = -1
    
    for cell in empty_cells:
        score = position_value.get(cell, 20)
        
        # Bonus for creating threats
        for line in lines:
            if cell in line:
                values = [board[i][j][k] for (i, j, k) in line]
                if values.count(1) == 1 and -1 not in values:
                    score += 5
        
        if score > best_score:
            best_score = score
            best_move = cell
    
    return best_move

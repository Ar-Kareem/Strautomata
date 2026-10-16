
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    import numpy as np
    
    b = np.array(board)
    
    # Generate all 49 winning lines
    lines = []
    
    # Straight lines along each axis (27 total)
    for i in range(3):
        for j in range(3):
            lines.append([(i, j, k) for k in range(3)])  # along z
            lines.append([(i, k, j) for k in range(3)])  # along y
            lines.append([(k, i, j) for k in range(3)])  # along x
    
    # Face diagonals (18 total)
    for i in range(3):
        lines.append([(i, k, k) for k in range(3)])
        lines.append([(i, k, 2-k) for k in range(3)])
        lines.append([(k, i, k) for k in range(3)])
        lines.append([(k, i, 2-k) for k in range(3)])
        lines.append([(k, k, i) for k in range(3)])
        lines.append([(k, 2-k, i) for k in range(3)])
    
    # Space diagonals (4 total)
    lines.append([(k, k, k) for k in range(3)])
    lines.append([(k, k, 2-k) for k in range(3)])
    lines.append([(k, 2-k, k) for k in range(3)])
    lines.append([(2-k, k, k) for k in range(3)])
    
    def get_empty():
        return [(i, j, k) for i in range(3) for j in range(3) for k in range(3) if b[i,j,k] == 0]
    
    def check_win(player):
        for line in lines:
            if all(b[p] == player for p in line):
                return True
        return False
    
    def find_winning_move(player):
        for line in lines:
            vals = [b[p] for p in line]
            if vals.count(player) == 2 and vals.count(0) == 1:
                for p in line:
                    if b[p] == 0:
                        return p
        return None
    
    # Immediate win
    win = find_winning_move(1)
    if win:
        return win
    
    # Block opponent win
    block = find_winning_move(-1)
    if block:
        return block
    
    # Check for fork (two ways to win)
    def count_threats(player):
        threats = 0
        for line in lines:
            vals = [b[p] for p in line]
            if vals.count(player) == 2 and vals.count(0) == 1:
                threats += 1
        return threats
    
    empty = get_empty()
    
    # Try to create a fork or block opponent's fork
    best_move = None
    best_score = -float('inf')
    
    for cell in empty:
        b[cell] = 1
        my_threats = count_threats(1)
        b[cell] = -1
        opp_threats = count_threats(-1)
        b[cell] = 0
        
        # Prioritize creating multiple threats, then blocking
        score = my_threats * 100 + opp_threats * 50
        
        # Add positional value
        # Center is most valuable
        if cell == (1, 1, 1):
            score += 30
        # Corners are valuable
        elif all(c in [0, 2] for c in cell):
            score += 20
        # Edge centers
        elif sum(c == 1 for c in cell) == 1:
            score += 10
        
        # Count lines this cell participates in
        for line in lines:
            if cell in line:
                vals = [b[p] for p in line]
                if vals.count(-1) == 0:  # Line still available for us
                    score += 3 + vals.count(1) * 5
                if vals.count(1) == 0:  # Line available for opponent
                    score += 2 + vals.count(-1) * 4
        
        if score > best_score:
            best_score = score
            best_move = cell
    
    return best_move

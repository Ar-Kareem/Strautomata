
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    3D Tic-Tac-Toe strategy:
    1. Win if possible
    2. Block opponent's win
    3. Create forks (multiple threats)
    4. Take strategic positions (center, corners)
    """
    
    # Generate all 49 winning lines
    lines = []
    
    # 27 axis-parallel lines
    for j in range(3):
        for k in range(3):
            lines.append([(i, j, k) for i in range(3)])
    for i in range(3):
        for k in range(3):
            lines.append([(i, j, k) for j in range(3)])
    for i in range(3):
        for j in range(3):
            lines.append([(i, j, k) for k in range(3)])
    
    # 18 plane diagonal lines
    for k in range(3):
        lines.append([(i, i, k) for i in range(3)])
        lines.append([(i, 2-i, k) for i in range(3)])
    for j in range(3):
        lines.append([(i, j, i) for i in range(3)])
        lines.append([(i, j, 2-i) for i in range(3)])
    for i in range(3):
        lines.append([(i, j, j) for j in range(3)])
        lines.append([(i, j, 2-j) for j in range(3)])
    
    # 4 space diagonal lines
    lines.append([(i, i, i) for i in range(3)])
    lines.append([(i, i, 2-i) for i in range(3)])
    lines.append([(i, 2-i, i) for i in range(3)])
    lines.append([(2-i, i, i) for i in range(3)])
    
    # Priority 1: Win immediately
    for line in lines:
        my_count = sum(1 for p in line if board[p[0]][p[1]][p[2]] == 1)
        if my_count == 2:
            for p in line:
                if board[p[0]][p[1]][p[2]] == 0:
                    return p
    
    # Priority 2: Block opponent's win
    for line in lines:
        opp_count = sum(1 for p in line if board[p[0]][p[1]][p[2]] == -1)
        if opp_count == 2:
            for p in line:
                if board[p[0]][p[1]][p[2]] == 0:
                    return p
    
    # Priority 3: Strategic move
    best_move = None
    best_score = -1
    
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] != 0:
                    continue
                
                pos = (i, j, k)
                score = 0
                threats = 0
                
                # Evaluate lines through this position
                for line in lines:
                    if pos in line:
                        my = sum(1 for p in line if board[p[0]][p[1]][p[2]] == 1)
                        opp = sum(1 for p in line if board[p[0]][p[1]][p[2]] == -1)
                        
                        if opp == 0:
                            if my == 1:
                                threats += 1
                                score += 10
                            else:
                                score += 1
                        elif my == 0 and opp == 1:
                            score += 5
                
                # Bonus for fork creation
                if threats >= 2:
                    score += 100
                
                # Position value
                if pos == (1, 1, 1):
                    score += 40
                elif pos in [(0,0,0), (0,0,2), (0,2,0), (0,2,2),
                             (2,0,0), (2,0,2), (2,2,0), (2,2,2)]:
                    score += 10
                
                if score > best_score:
                    best_score = score
                    best_move = pos
    
    return best_move if best_move else (1, 1, 1)

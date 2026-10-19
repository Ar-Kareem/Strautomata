
def policy(you, opponent) -> str:
    def rotate_quadrant(you, opponent, quad, dir):
        new_you = [row.copy() for row in you]
        new_opp = [row.copy() for row in opponent]
        if quad == 0:
            rows, cols = range(0,3), range(0,3)
        elif quad == 1:
            rows, cols = range(0,3), range(3,6)
        elif quad == 2:
            rows, cols = range(3,6), range(0,3)
        else:
            rows, cols = range(3,6), range(3,6)
        
        you_sub = [[new_you[r][c] for c in cols] for r in rows]
        opp_sub = [[new_opp[r][c] for c in cols] for r in rows]
        
        if dir == 'L':
            rotated_you = [list(row) for row in zip(*you_sub)][::-1]
            rotated_opp = [list(row) for row in zip(*opp_sub)][::-1]
        else:
            rotated_you = [list(row) for row in zip(*you_sub[::-1])]
            rotated_opp = [list(row) for row in zip(*opp_sub[::-1])]
        
        for i, r in enumerate(rows):
            for j, c in enumerate(cols):
                new_you[r][c] = rotated_you[i][j]
                new_opp[r][c] = rotated_opp[i][j]
        return new_you, new_opp
    
    def has_won(board):
        lines = []
        for r in range(6):
            for c in range(2):
                lines.append([(r, c + i) for i in range(5)])
        for c in range(6):
            for r in range(2):
                lines.append([(r + i, c) for i in range(5)])
        for r in range(2):
            for c in range(2):
                lines.append([(r + i, c + i) for i in range(5)])
        for r in range(2):
            for c in range(4, 6):
                lines.append([(r + i, c - i) for i in range(5)])
        
        for line in lines:
            total = sum(board[r][c] for (r,c) in line)
            if total >= 5:
                return True
        return False
    
    you = [list(row) for row in you]
    opponent = [list(row) for row in opponent]
    best_score = -float('inf')
    best_move = None
    empty_cells = [(r,c) for r in range(6) for c in range(6) if you[r][c] == 0 and opponent[r][c] == 0]
    weight = [
        [1, 1, 1, 1, 1, 1],
        [1, 2, 2, 2, 2, 1],
        [1, 2, 3, 3, 2, 1],
        [1, 2, 3, 3, 2, 1],
        [1, 2, 2, 2, 2, 1],
        [1, 1, 1, 1, 1, 1],
    ]
    
    lines = []
    for r in range(6):
        for c in range(2):
            lines.append([(r, c+i) for i in range(5)])
    for c in range(6):
        for r in range(2):
            lines.append([(r+i, c) for i in range(5)])
    for r in range(2):
        for c in range(2):
            lines.append([(r+i, c+i) for i in range(5)])
    for r in range(2):
        for c in range(4,6):
            lines.append([(r+i, c-i) for i in range(5)])
    
    for (r, c) in empty_cells:
        new_you = [row.copy() for row in you]
        new_opp = [row.copy() for row in opponent]
        new_you[r][c] = 1
        for quad in range(4):
            for dir in ['L', 'R']:
                rotated_you, rotated_opp = rotate_quadrant(new_you, new_opp, quad, dir)
                if has_won(rotated_you):
                    return f"{r+1},{c+1},{quad},{dir}"
                
                score = weight[r][c]
                my_lines = sum(rotated_you[rl][cl] for line in lines for (rl, cl) in line)
                opp_lines = sum(rotated_opp[rl][cl] for line in lines for (rl, cl) in line)
                current_score = score + (my_lines - opp_lines)
                
                if current_score > best_score:
                    best_score = current_score
                    best_move = f"{r+1},{c+1},{quad},{dir}"
    
    return best_move if best_move else "1,1,0,L"  # fallback

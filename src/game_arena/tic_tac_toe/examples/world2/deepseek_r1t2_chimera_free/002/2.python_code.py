
def policy(board: list[list[int]]) -> tuple[int, int]:
    def has_won(b, player):
        # Check rows
        for i in range(4):
            if all(cell == player for cell in b[i]):
                return True
        # Check columns
        for j in range(4):
            if all(b[i][j] == player for i in range(4)):
                return True
        # Check diagonals
        if all(b[i][i] == player for i in range(4)):
            return True
        if all(b[i][3-i] == player for i in range(4)):
            return True
        return False

    # Collect empty cells
    empty_cells = []
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                empty_cells.append((i, j))
                
    # 1. Check immediate win for AI
    for i, j in empty_cells:
        temp = [row[:] for row in board]
        temp[i][j] = 1
        if has_won(temp, 1):
            return (i, j)
    
    # 2. Block opponent's immediate win
    for i, j in empty_cells:
        temp = [row[:] for row in board]
        temp[i][j] = -1
        if has_won(temp, -1):
            return (i, j)
    
    # 3. Heuristic scoring of remaining moves
    scores = {}
    center_cells = [(1,1), (1,2), (2,1), (2,2)]
    for (i, j) in empty_cells:
        score = 0
        
        # Center bonus
        if (i, j) in center_cells:
            score += 3
        
        # Evaluate row
        row = board[i]
        count_me = sum(1 for x in row if x == 1)
        count_opp = sum(1 for x in row if x == -1)
        if count_opp == 0:  # No opponent interference
            if count_me == 2:
                score += 5
            elif count_me == 1:
                score += 2
        
        # Evaluate column
        col = [board[k][j] for k in range(4)]
        count_me = sum(1 for x in col if x == 1)
        count_opp = sum(1 for x in col if x == -1)
        if count_opp == 0:
            if count_me == 2:
                score += 5
            elif count_me == 1:
                score += 2
        
        # Evaluate main diagonal (if applicable)
        if i == j:
            diag = [board[k][k] for k in range(4)]
            count_me = sum(1 for x in diag if x == 1)
            count_opp = sum(1 for x in diag if x == -1)
            if count_opp == 0:
                if count_me == 2:
                    score += 5
                elif count_me == 1:
                    score += 2
        
        # Evaluate anti-diagonal (if applicable)
        if i + j == 3:
            anti_diag = [board[k][3-k] for k in range(4)]
            count_me = sum(1 for x in anti_diag if x == 1)
            count_opp = sum(1 for x in anti_diag if x == -1)
            if count_opp == 0:
                if count_me == 2:
                    score += 5
                elif count_me == 1:
                    score += 2
        
        scores[(i, j)] = score
    
    # Choose best scoring move
    return max(scores, key=scores.get)

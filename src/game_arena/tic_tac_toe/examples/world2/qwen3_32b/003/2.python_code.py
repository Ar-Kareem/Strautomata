
def policy(board: list[list[int]]) -> tuple[int, int]:
    possible_moves = [(i, j) for i in range(4) for j in range(4) if board[i][j] == 0]
    
    def is_winning(player):
        # Check rows
        for row in board:
            if all(x == player for x in row):
                return True
        # Check columns
        for col in range(4):
            if all(board[row][col] == player for row in range(4)):
                return True
        # Check main diagonal
        if all(board[i][i] == player for i in range(4)):
            return True
        # Check anti-diagonal
        if all(board[i][3 - i] == player for i in range(4)):
            return True
        return False
    
    # Check for own winning move
    for move in possible_moves:
        r, c = move
        board[r][c] = 1
        if is_winning(1):
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0  # revert
    
    # Check for opponent's winning move
    for move in possible_moves:
        r, c = move
        board[r][c] = -1
        if is_winning(-1):
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0  # revert
    
    # Evaluate moves based on heuristic
    def evaluate_move(r, c):
        score = 0
        
        # Check row
        my_count = 0
        opp_count = 0
        for j in range(4):
            cell = board[r][j]
            if cell == 1:
                my_count += 1
            elif cell == -1:
                opp_count += 1
        if opp_count == 0:
            score += (my_count + 1)  # Adding current cell (which is empty now)
        
        # Check column
        my_count = 0
        opp_count = 0
        for i in range(4):
            cell = board[i][c]
            if cell == 1:
                my_count += 1
            elif cell == -1:
                opp_count += 1
        if opp_count == 0:
            score += (my_count + 1)
        
        # Check main diagonal (if applicable)
        my_count = 0
        opp_count = 0
        if r == c:
            for i in range(4):
                cell = board[i][i]
                if cell == 1:
                    my_count += 1
                elif cell == -1:
                    opp_count += 1
            if opp_count == 0:
                score += (my_count + 1)
        
        # Check anti-diagonal (if applicable)
        my_count = 0
        opp_count = 0
        if r + c == 3:
            for i in range(4):
                cell = board[i][3 - i]
                if cell == 1:
                    my_count += 1
                elif cell == -1:
                    opp_count += 1
            if opp_count == 0:
                score += (my_count + 1)
        
        return score
    
    best_score = -1
    best_move = possible_moves[0]
    for move in possible_moves:
        r, c = move
        current_score = evaluate_move(r, c)
        if current_score > best_score:
            best_score = current_score
            best_move = move
    return best_move

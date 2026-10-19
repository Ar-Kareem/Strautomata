
def policy(board):
    def check_win(b, p):
        # Check all rows
        for row in b:
            if all(cell == p for cell in row):
                return True
        # Check all columns
        for col in range(3):
            if all(b[i][col] == p for i in range(3)):
                return True
        # Check main diagonals
        if all(b[i][i] == p for i in range(3)):
            return True
        if all(b[i][2 - i] == p for i in range(3)):
            return True
        return False

    possible_moves = [(i, j) for i in range(3) for j in range(3) if board[i][j] == 0]
    
    # Check if any move results in a win
    for move in possible_moves:
        x, y = move
        new_board = [row.copy() for row in board]
        new_board[x][y] = 1
        if check_win(new_board, 1):
            return move
    
    # Assign priorities based on Tic Tac Toe strategy
    priority = {'center': 2, 'corner': 1, 'other': 0}
    candidates = []
    for move in possible_moves:
        x, y = move
        if move == (1, 1):
            score = 2
        elif (x in [0, 2] and y in [0, 2]):
            score = 1
        else:
            score = 0
        candidates.append((score, move))
    
    # Sort by score, maintaining original order for ties
    candidates.sort(key=lambda x: (-x[0], x[1]))
    return candidates[0][1]

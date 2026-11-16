
def policy(you, opponent) -> str:
    # Create a full board matrix: 0 for empty, 1 for me, 2 for opponent
    board = [[0 for _ in range(6)] for _ in range(6)]
    for r in range(6):
        for c in range(6):
            if you[r][c] == 1:
                board[r][c] = 1
            elif opponent[r][c] == 1:
                board[r][c] = 2
    
    # List of all possible winning lines (each line is a list of 5 (r, c) tuples with 0-based indices)
    lines = []
    # Horizontal lines
    for r in range(6):
        for start in range(2):
            line = []
            for i in range(5):
                line.append((r, start + i))
            lines.append(line)
    # Vertical lines
    for c in range(6):
        for start in range(2):
            line = []
            for i in range(5):
                line.append((start + i, c))
            lines.append(line)
    # Main diagonal lines (i-j constant)
    line1 = [(i, i + 1) for i in range(5)]  # i-j = -1
    lines.append(line1)
    line2 = [(i, i) for i in range(5)]      # i-j = 0, first line
    lines.append(line2)
    line3 = [(i, i) for i in range(1, 6)]   # i-j = 0, second line
    lines.append(line3)
    line4 = [(i, i - 1) for i in range(1, 6)]  # i-j = 1
    lines.append(line4)
    # Anti-diagonal lines (i+j constant)
    line5 = [(i, 4 - i) for i in range(5)]     # i+j = 4
    lines.append(line5)
    line6 = [(i, 5 - i) for i in range(5)]     # i+j = 5, first line
    lines.append(line6)
    line7 = [(i, 5 - i) for i in range(1, 6)]  # i+j = 5, second line
    lines.append(line7)
    line8 = [(i, 6 - i) for i in range(1, 6)]  # i+j = 6
    lines.append(line8)

    # Function to check if player has 5-in-a-row
    def check_win(board, player):
        for line in lines:
            count = 0
            for (r, c) in line:
                if board[r][c] == player:
                    count += 1
                else:
                    count = 0
                if count >= 5:
                    return True
        return False

    # Function to get score for a sequence on a line
    def get_sequence_score(L, O):
        if L == 4:
            if O == 2:
                return 100
            elif O == 1:
                return 50
            else:
                return 0
        elif L == 3:
            if O == 2:
                return 20
            elif O == 1:
                return 10
            else:
                return 0
        elif L == 2:
            if O == 2:
                return 5
            elif O == 1:
                return 2
            else:
                return 0
        elif L == 1:
            if O == 2:
                return 1
            elif O == 1:
                return 0.5
            else:
                return 0
        else:
            return 0

    # Function to score a line for a player
    def score_line(values, player):
        best_score = 0
        i = 0
        while i < 5:
            if values[i] == player:
                start = i
                while i < 5 and values[i] == player:
                    i += 1
                end = i - 1
                L = end - start + 1
                O = 0
                if start > 0:
                    if values[start - 1] == 0:
                        O += 1
                if end < 4:
                    if values[end + 1] == 0:
                        O += 1
                score = get_sequence_score(L, O)
                if score > best_score:
                    best_score = score
            else:
                i += 1
        return best_score

    # Function to evaluate the board
    def evaluate(board):
        my_score = 0
        opp_score = 0
        for line in lines:
            values = [board[r][c] for (r, c) in line]
            my_score += score_line(values, 1)
            opp_score += score_line(values, 2)
        return my_score - opp_score

    # Function to rotate a quadrant
    def rotate_quadrant(board, quad, direction):
        new_board = [row[:] for row in board]
        if quad == 0:
            rows = [0, 1, 2]
            cols = [0, 1, 2]
        elif quad == 1:
            rows = [0, 1, 2]
            cols = [3, 4, 5]
        elif quad == 2:
            rows = [3, 4, 5]
            cols = [0, 1, 2]
        else:  # quad == 3
            rows = [3, 4, 5]
            cols = [3, 4, 5]
        
        # Extract the 3x3 quadrant
        submatrix = []
        for r in rows:
            sub_row = []
            for c in cols:
                sub_row.append(new_board[r][c])
            submatrix.append(sub_row)
        
        # Rotate the submatrix
        rotated = [[0]*3 for _ in range(3)]
        if direction == 'R':  # clockwise
            for i in range(3):
                for j in range(3):
                    rotated[i][j] = submatrix[2-j][i]
        else:  # direction == 'L', anticlockwise
            for i in range(3):
                for j in range(3):
                    rotated[i][j] = submatrix[j][2-i]
        
        # Put the rotated matrix back
        for i, r in enumerate(rows):
            for j, c in enumerate(cols):
                new_board[r][c] = rotated[i][j]
        
        return new_board

    # Find all empty cells
    empty_cells = []
    for r in range(6):
        for c in range(6):
            if board[r][c] == 0:
                empty_cells.append((r, c))

    best_move = None
    best_score = -float('inf')

    for r, c in empty_cells:
        for quad in range(4):
            for direction in ['L', 'R']:
                # Simulate the move
                new_board = [row[:] for row in board]
                new_board[r][c] = 1  # place my marble
                new_board = rotate_quadrant(new_board, quad, direction)
                
                # Check if I win
                if check_win(new_board, 1):
                    return f"{r+1},{c+1},{quad},{direction}"
                
                # Check if opponent wins
                if check_win(new_board, 2):
                    score = -1000  # very low score for losing move
                else:
                    score = evaluate(new_board)
                
                # Update best move
                if score > best_score:
                    best_score = score
                    best_move = (r, c, quad, direction)

    return f"{best_move[0]+1},{best_move[1]+1},{best_move[2]},{best_move[3]}"

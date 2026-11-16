
def has_five(player_array):
    """Check if the player has 5-in-a-row on the board."""
    n = 6
    # Horizontal sequences
    for r in range(n):
        for c in range(n-4):
            if all(player_array[r][c+i] == 1 for i in range(5)):
                return True
    # Vertical sequences
    for c in range(n):
        for r in range(n-4):
            if all(player_array[r+i][c] == 1 for i in range(5)):
                return True
    # Diagonal down-right sequences
    for r in range(n-4):
        for c in range(n-4):
            if all(player_array[r+i][c+i] == 1 for i in range(5)):
                return True
    # Diagonal down-left sequences
    for r in range(n-4):
        for c in range(4, n):
            if all(player_array[r+i][c-i] == 1 for i in range(5)):
                return True
    return False

def rotate_quadrant(board, quad, dir):
    """Rotate a 3x3 quadrant of the board."""
    # Define quadrant boundaries
    if quad == 0:
        rows = [0, 1, 2]
        cols = [0, 1, 2]
    elif quad == 1:
        rows = [0, 1, 2]
        cols = [3, 4, 5]
    elif quad == 2:
        rows = [3, 4, 5]
        cols = [0, 1, 2]
    elif quad == 3:
        rows = [3, 4, 5]
        cols = [3, 4, 5]
    else:
        return board
    
    # Extract the 3x3 sub-board
    sub_board = []
    for r in rows:
        sub_row = []
        for c in cols:
            sub_row.append(board[r][c])
        sub_board.append(sub_row)
    
    # Rotate the 3x3 sub-board
    rotated = [[0]*3 for _ in range(3)]
    if dir == 'R':  # 90 degrees clockwise
        for i in range(3):
            for j in range(3):
                rotated[i][j] = sub_board[2-j][i]
    elif dir == 'L':  # 90 degrees anticlockwise
        for i in range(3):
            for j in range(3):
                rotated[i][j] = sub_board[j][2-i]
    
    # Write back to the board
    for i in range(3):
        for j in range(3):
            board[rows[i]][cols[j]] = rotated[i][j]
    
    return board

def evaluate_board(you_array, opponent_array):
    """Evaluate the board state from the perspective of the 'you' player."""
    # Check for win conditions
    if has_five(you_array) and has_five(opponent_array):
        return 0  # Draw
    if has_five(you_array):
        return 10000  # Win
    if has_five(opponent_array):
        return -10000  # Loss
    
    # Heuristic score based on sequences
    score = 0
    n = 6
    sequences = []
    # Horizontal sequences
    for r in range(n):
        for c in range(n-4):
            seq = [(r, c+i) for i in range(5)]
            sequences.append(seq)
    # Vertical sequences
    for c in range(n):
        for r in range(n-4):
            seq = [(r+i, c) for i in range(5)]
            sequences.append(seq)
    # Diagonal down-right sequences
    for r in range(n-4):
        for c in range(n-4):
            seq = [(r+i, c+i) for i in range(5)]
            sequences.append(seq)
    # Diagonal down-left sequences
    for r in range(n-4):
        for c in range(4, n):
            seq = [(r+i, c-i) for i in range(5)]
            sequences.append(seq)
    
    # Score each sequence
    for seq in sequences:
        count_you = 0
        count_op = 0
        for (r, c) in seq:
            if you_array[r][c] == 1:
                count_you += 1
            if opponent_array[r][c] == 1:
                count_op += 1
        if count_op == 0:
            if count_you > 0:
                score += 3 ** count_you
        else:
            if count_you > 0:
                score += 0  # Contested sequence
            else:
                score -= 3 ** count_op
    
    return score

def policy(you, opponent):
    """Determine the next move for Pentago."""
    n = 6
    empty_cells = []
    for r in range(n):
        for c in range(n):
            if you[r][c] == 0 and opponent[r][c] == 0:
                empty_cells.append((r, c))
    
    best_score = -10**9
    best_move = None
    
    for r, c in empty_cells:
        for quad in range(4):
            for dir in ['L', 'R']:
                # Simulate the move
                new_you = [row[:] for row in you]  # Deep copy
                new_opponent = [row[:] for row in opponent]
                new_you[r][c] = 1  # Place marble
                new_you = rotate_quadrant(new_you, quad, dir)
                new_opponent = rotate_quadrant(new_opponent, quad, dir)
                score = evaluate_board(new_you, new_opponent)
                
                if score > best_score:
                    best_score = score
                    best_move = (r, c, quad, dir)
    
    r, c, quad, dir = best_move
    return f"{r+1},{c+1},{quad},{dir}"

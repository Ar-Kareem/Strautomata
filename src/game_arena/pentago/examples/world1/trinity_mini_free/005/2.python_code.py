
def policy(you, opponent):
    # Helper function to check if a player has 5-in-a-row
    def check_win(board, player):
        for r in range(6):
            for c in range(6):
                if board[r][c] == player:
                    # Check horizontal
                    if c <= 2 and board[r][c+1] == player and board[r][c+2] == player and board[r][c+3] == player and board[r][c+4] == player:
                        return True
                    # Check vertical
                    if r <= 2 and board[r+1][c] == player and board[r+2][c] == player and board[r+3][c] == player and board[r+4][c] == player:
                        return True
                    # Check diagonal (top-left to bottom-right)
                    if r <= 2 and c <= 2 and board[r+1][c+1] == player and board[r+2][c+2] == player and board[r+3][c+3] == player and board[r+4][c+4] == player:
                        return True
                    # Check diagonal (top-right to bottom-left)
                    if r <= 2 and c >= 4 and board[r+1][c-1] == player and board[r+2][c-2] == player and board[r+3][c-3] == player and board[r+4][c-4] == player:
                        return True
        return False

    # Helper function to evaluate board position
    def evaluate(board):
        score = 0
        # Check for immediate threats
        for r in range(6):
            for c in range(6):
                if board[r][c] == 0:
                    # Check horizontal threats
                    if c <= 2 and board[r][c+1] == 0 and board[r][c+2] == 0 and board[r][c+3] == 0 and board[r][c+4] == 0:
                        score += 10
                    # Check vertical threats
                    if r <= 2 and board[r+1][c] == 0 and board[r+2][c] == 0 and board[r+3][c] == 0 and board[r+4][c] == 0:
                        score += 10
                    # Check diagonal threats
                    if r <= 2 and c <= 2 and board[r+1][c+1] == 0 and board[r+2][c+2] == 0 and board[r+3][c+3] == 0 and board[r+4][c+4] == 0:
                        score += 10
                    if r <= 2 and c >= 4 and board[r+1][c-1] == 0 and board[r+2][c-2] == 0 and board[r+3][c-3] == 0 and board[r+4][c-4] == 0:
                        score += 10
        return score

    # Generate all possible moves
    moves = []
    for r in range(6):
        for c in range(6):
            if you[r][c] == 0 and opponent[r][c] == 0:
                for quad in range(4):
                    for direction in ['L', 'R']:
                        # Create move string
                        move_str = f"{r+1},{c+1},{quad},{direction}"
                        moves.append((move_str, quad, direction))

    # Evaluate each move
    best_move = None
    best_score = -float('inf')
    for move_str, quad, direction in moves:
        # Create board copy
        board = [row[:] for row in you]
        # Place marble
        r, c = int(move_str.split(',')[0]) - 1, int(move_str.split(',')[1]) - 1
        board[r][c] = 1
        # Rotate quadrant
        if direction == 'L':
            # Rotate quadrant 90° counterclockwise
            quad_board = [board[i][j] for i in range(quad*3, quad*3+3) for j in range(quad*3, quad*3+3)]
            rotated = [quad_board[2], quad_board[5], quad_board[8], quad_board[1], quad_board[4], quad_board[7], quad_board[0], quad_board[3], quad_board[6]]
            for i in range(3):
                for j in range(3):
                    board[quad*3+i][quad*3+j] = rotated[i*3+j]
        else:
            # Rotate quadrant 90° clockwise
            quad_board = [board[i][j] for i in range(quad*3, quad*3+3) for j in range(quad*3, quad*3+3)]
            rotated = [quad_board[6], quad_board[3], quad_board[0], quad_board[7], quad_board[4], quad_board[1], quad_board[8], quad_board[5], quad_board[2]]
            for i in range(3):
                for j in range(3):
                    board[quad*3+i][quad*3+j] = rotated[i*3+j]
        
        # Check for immediate win
        if check_win(board, 1):
            return move_str
        
        # Evaluate position
        score = evaluate(board)
        # Prioritize moves that create threats
        if score > best_score:
            best_score = score
            best_move = move_str
    
    # Return best move found
    return best_move

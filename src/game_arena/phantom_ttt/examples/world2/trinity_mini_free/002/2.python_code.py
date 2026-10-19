
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Check for winning moves
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                # Check row
                if board[r][c] == 0 and board[r][0] == 1 and board[r][1] == 1:
                    return (r, c)
                # Check column
                if board[r][c] == 0 and board[0][c] == 1 and board[1][c] == 1:
                    return (r, c)
                # Check main diagonal
                if board[r][c] == 0 and r == c and board[0][0] == 1 and board[1][1] == 1:
                    return (r, c)
                # Check anti-diagonal
                if board[r][c] == 0 and r + c == 2 and board[0][2] == 1 and board[1][1] == 1:
                    return (r, c)
    
    # Evaluate available cells
    best_score = -1
    best_cell = None
    best_line_count = -1
    
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                # Calculate score based on your marks in row, column, and diagonals
                score = 0
                # Row
                score += board[r][0] + board[r][1] + board[r][2]
                # Column
                score += board[0][c] + board[1][c] + board[2][c]
                # Main diagonal
                if r == c:
                    score += board[0][0] + board[1][1] + board[2][2]
                # Anti-diagonal
                if r + c == 2:
                    score += board[0][2] + board[1][1] + board[2][0]
                
                # Determine line count for positional value
                line_count = 0
                if r == c:  # Main diagonal
                    line_count += 1
                if r + c == 2:  # Anti-diagonal
                    line_count += 1
                if r == 1:  # Center row
                    line_count += 1
                if c == 1:  # Center column
                    line_count += 1
                
                # Select best cell based on score and positional value
                if score > best_score or (score == best_score and line_count > best_line_count):
                    best_score = score
                    best_cell = (r, c)
                    best_line_count = line_count
    
    return best_cell

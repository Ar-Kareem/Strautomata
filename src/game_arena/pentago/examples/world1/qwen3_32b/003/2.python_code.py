
def policy(you, opponent) -> str:
    def get_quad_offsets(quad):
        if quad == 0:
            return 0, 3, 0, 3
        elif quad == 1:
            return 0, 3, 3, 6
        elif quad == 2:
            return 3, 6, 0, 3
        else:  # quad == 3
            return 3, 6, 3, 6

    def rotate_clockwise(quad_data):
        return [[quad_data[2 - j][i] for j in range(3)] for i in range(3)]

    def rotate_counter_clockwise(quad_data):
        # Rotate 3 times clockwise is equivalent to 1 counter-clockwise rotation
        temp = rotate_clockwise(quad_data)
        temp = rotate_clockwise(temp)
        return rotate_clockwise(temp)

    def rotate_board(board, quad, direction):
        rs, re, cs, ce = get_quad_offsets(quad)
        # Extract the 3x3 quadrant
        quad_data = [
            board[rs][cs:cs + 3],
            board[rs + 1][cs:cs + 3],
            board[rs + 2][cs:cs + 3]
        ]
        # Rotate the quadrant
        if direction == 'R':
            rotated = rotate_clockwise(quad_data)
        else:
            rotated = rotate_counter_clockwise(quad_data)
        # Create a new board with the rotated quadrant
        new_board = [list(row) for row in board]  # Deep copy
        for i in range(3):
            for j in range(3):
                new_board[rs + i][cs + j] = rotated[i][j]
        return new_board

    def is_win(board):
        # Check for any 5-in-a-line in all directions
        # Horizontal
        for r in range(6):
            for c in range(2):
                if sum(board[r][c + i] for i in range(5)) == 5:
                    return True
        # Vertical
        for c in range(6):
            for r in range(2):
                if sum(board[r + i][c] for i in range(5)) == 5:
                    return True
        # Diagonal top-left to bottom-right
        for r in range(2):
            for c in range(2):
                if sum(board[r + i][c + i] for i in range(5)) == 5:
                    return True
        # Diagonal top-right to bottom-left
        for r in range(2):
            for c in range(4, 6):
                if sum(board[r + i][c - i] for i in range(5)) == 5:
                    return True
        return False

    def count_threats(board):
        def line_score(line_cells):
            total = sum(line_cells)
            if total == 5:
                return 1000
            elif total == 4:
                return 10
            elif total == 3:
                return 1
            else:
                return 0

        score = 0
        # Horizontal lines
        for r in range(6):
            for c in range(2):
                line = board[r][c:c + 5]
                score += line_score(line)
        # Vertical lines
        for c in range(6):
            for r in range(2):
                line = [board[r + i][c] for i in range(5)]
                score += line_score(line)
        # Diagonal top-left to bottom-right
        for r in range(2):
            for c in range(2):
                line = [board[r + i][c + i] for i in range(5)]
                score += line_score(line)
        # Diagonal top-right to bottom-left
        for r in range(2):
            for c in range(4, 6):
                line = [board[r + i][c - i] for i in range(5)]
                score += line_score(line)
        return score

    # Try all possible moves for a win
    for r in range(6):
        for c in range(6):
            if you[r][c] != 0 or opponent[r][c] != 0:
                continue
            new_you_placed = [list(row) for row in you]
            new_you_placed[r][c] = 1
            for quad in range(4):
                for direction in ['L', 'R']:
                    new_you_rotated = rotate_board(new_you_placed, quad, direction)
                    new_opponent_rotated = rotate_board(opponent, quad, direction)
                    
                    if is_win(new_you_rotated) and not is_win(new_opponent_rotated):
                        return f"{r + 1},{c + 1},{quad},{direction}"
    
    # Check for draw move (both players win)
    for r in range(6):
        for c in range(6):
            if you[r][c] != 0 or opponent[r][c] != 0:
                continue
            new_you_placed = [list(row) for row in you]
            new_you_placed[r][c] = 1
            for quad in range(4):
                for direction in ['L', 'R']:
                    new_you_rotated = rotate_board(new_you_placed, quad, direction)
                    new_opponent_rotated = rotate_board(opponent, quad, direction)
                    
                    if is_win(new_you_rotated) and is_win(new_opponent_rotated):
                        return f"{r + 1},{c + 1},{quad},{direction}"

    # Best move that doesn't cause a loss
    best_score = -1
    best_move = None
    for r in range(6):
        for c in range(6):
            if you[r][c] != 0 or opponent[r][c] != 0:
                continue
            new_you_placed = [list(row) for row in you]
            new_you_placed[r][c] = 1
            for quad in range(4):
                for direction in ['L', 'R']:
                    new_you = rotate_board(new_you_placed, quad, direction)
                    new_opponent = rotate_board(opponent, quad, direction)
                    
                    if is_win(new_opponent):  # Opponent wins after this
                        continue
                        
                    my_score = count_threats(new_you)
                    opp_score = count_threats(new_opponent)
                    move_score = my_score - 1.5 * opp_score  # Weigh opponent's threats more
                    
                    if move_score > best_score:
                        best_score = move_score
                        best_move = (r, c, quad, direction)

    if best_move:
        r, c, quad, direction = best_move
        return f"{r + 1},{c + 1},{quad},{direction}"

    # Fallback to a default move (should never happen as per problem constraints)
    for r in range(6):
        for c in range(6):
            if you[r][c] == 0 and opponent[r][c] == 0:
                return f"{r + 1},{c + 1},0,R"  # Top-left, rotate right

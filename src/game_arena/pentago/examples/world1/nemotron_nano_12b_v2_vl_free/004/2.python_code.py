
def policy(you, opponent):

    # Helper function to rotate a 3x3 quadrant
    def rotate_quad(quad, dir):
        new_quad = [[0]*3 for _ in range(3)]
        for i in range(3):
            for j in range(3):
                if dir == 'R':
                    new_quad[j][2 - i] = quad[i][j]
                else:
                    new_quad[2 - j][i] = quad[i][j]
        return new_quad

    # Helper function to check for 5-in-a-row for the current player
    def has_5_in_row(board):
        # Horizontal
        for r in range(6):
            for c in range(2):
                if all(board[r][c + i] == 1 for i in range(5)):
                    return True
        # Vertical
        for c in range(6):
            for r in range(2):
                if all(board[r + i][c] == 1 for i in range(5)):
                    return True
        # Diagonal TL-BR
        for r in range(2):
            for c in range(2):
                if all(board[r + i][c + i] == 1 for i in range(5)):
                    return True
        # Diagonal TR-BL
        for r in range(2):
            for c in range(4, 6):
                if all(board[r + i][c - i] == 1 for i in range(5)):
                    return True
        return False

    # Precompute quadrant starting positions
    quad_start_row = [0, 0, 3, 3]
    quad_start_col = [0, 3, 0, 3]

    # Find all empty cells
    empty_cells = [(r, c) for r in range(6) for c in range(6) if you[r][c] == 0 and opponent[r][c] == 0]

    # Step 1: Check for immediate win
    for r, c in empty_cells:
        new_you = [[cell for cell in row] for row in you]
        new_you[r][c] = 1  # Place the marble

        for quad in range(4):
            quad_r = quad_start_row[quad]
            quad_c = quad_start_col[quad]
            quad_you = [row[quad_c:quad_c+3] for row in new_you[quad_r:quad_r+3]]
            quad_opp = [row[quad_c:quad_c+3] for row in opponent[quad_r:quad_r+3]]

            for dir in ['L', 'R']:
                rotated_you = rotate_quad(quad_you, dir)

                new_you_sim = [row.copy() for row in new_you]
                for i in range(3):
                    for j in range(3):
                        new_you_sim[quad_r + i][quad_c + j] = rotated_you[i][j]

                if has_5_in_row(new_you_sim):
                    return f"{r+1},{c+1},{quad},{dir}"

    # Step 2: Find the best move using a heuristic
    best_cell = None
    best_score = -1

    for r, c in empty_cells:
        new_you_placed = [row.copy() for row in you]
        new_you_placed[r][c] = 1

        max_score = -1
        best_quad = None
        best_dir = None

        for quad in range(4):
            quad_r = quad_start_row[quad]
            quad_c = quad_start_col[quad]
            quad_you = [row[quad_c:quad_c+3] for row in new_you_placed[quad_r:quad_r+3]]
            quad_opp = [row[quad_c:quad_c+3] for row in opponent[quad_r:quad_r+3]]

            for dir in ['L', 'R']:
                rotated_you = rotate_quad(quad_you, dir)

                new_you_sim = [row.copy() for row in new_you_placed]
                for i in range(3):
                    for j in range(3):
                        new_you_sim[quad_r + i][quad_c + j] = rotated_you[i][j]

                score = has_5_in_row(new_you_sim)
                if score > max_score:
                    max_score = score
                    best_quad = quad
                    best_dir = dir

        if max_score > best_score:
            best_score = max_score
            best_move = (r, c, best_quad, best_dir)

    if best_move:
        r, c, quad, dir = best_move
        return f"{r+1},{c+1},{quad},{dir}"
    else:
        r, c = empty_cells[0]
        return f"{r+1},{c+1},0,L"

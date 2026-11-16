
def policy(you, opponent):
    """
    Policy that returns a legal move for the game of Pentago.
    The move is represented by a string in the format "row,col,quad,dir"
    where 'row' and 'col' are 1-based indices, 'quad' is the quadrant number (0-3), 
    and 'dir' is either 'L' (anti-clockwise 90°) or 'R' (clockwise 90°).
    """
    import copy

    def rotate_quadrant(quad, direction):
        """
        Rotate a 3x3 quadrant matrix 90 degrees clockwise or anticlockwise.
        """
        if direction == 'L':
            return [[quad[j][2 - i] for j in range(3)] for i in range(3)]
        else:  # 'R'
            return [[quad[2 - j][i] for j in range(3)] for i in range(3)]

    def get_quadrant_matrix(matrix, q):
        """
        Extract the 3x3 quadrant from the main board matrix.
        """
        if q == 0:
            return [row[:3] for row in matrix[:3]]
        elif q == 1:
            return [row[3:6] for row in matrix[:3]]
        elif q == 2:
            return [row[:3] for row in matrix[3:6]]
        else:  # q == 3
            return [row[3:6] for row in matrix[3:6]]

    def apply_quadrant_rotation(board, q, dir):
        """
        Apply a rotation to the specified quadrant in the board matrix.
        """
        rows, cols = get_quadrant_rows_cols(q)
        quad_data = get_quadrant_matrix(board, q)

        # Rotate the quadrant and update the board
        rotated_quad = rotate_quadrant(quad_data, dir)

        if q == 0:
            for i in range(3):
                board[i][0:3] = rotated_quad[i]
        elif q == 1:
            for i in range(3):
                board[i] = matrix[i][:3] + rotated_quad[i] + matrix[i][6:]
        elif q == 2:
            for i in range(3):
                board[i + 3][0:3] = rotated_quad[i]
        else:  # q == 3
            for i in range(3):
                board[i + 3] = matrix[i + 3][:3] + rotated_quad[i]

    def check_win(board):
        """
        Check if the current player has 5 or more consecutive marbles in a row.
        """
        for i in range(6):
            for j in range(6):
                # Check all four directions for consecutive marbles
                for dx, dy in [(0, 1), (1, 0), (1, 1), (1, -1)]:
                    count = 0
                    ni, nj = i, j
                    while count < 5 and 0 <= ni < 6 and 0 <= nj < 6:
                        if board[ni][nj] == 1:
                            count += 1
                        else:
                            count = 0  # Reset if interrupted
                        ni += dx
                        nj += dy
                    if count >= 5:
                        return True
        return False

    def get_quadrant_rows_cols(q):
        """
        Returns the list of rows and columns that belong to a given quadrant.
        """
        if q == 0:
            return list(range(3)), list(range(3))
        elif q == 1:
            return list(range(3)), list(range(3, 6))
        elif q == 2:
            return list(range(3, 6)), list(range(3))
        else:  # q == 3
            return list(range(3, 6)), list(range(3, 6))

    def apply_move(you_copy, opponent_copy, move):
        """
        Apply a move to the board: place a marble and rotate a quadrant.
        """
        r, c, q, d = move
        r, c = r - 1, c - 1  # convert to 0-based
        quad, direction = q, d

        # Make copies to avoid modifying original matrices
        new_you = [row.copy() for row in you]
        new_opp = [row.copy() for row in opponent]

        # Place the marble
        new_you[r][c] = 1

        # Apply rotation to both players' marbles in the quadrant
        apply_quadrant_rotation(new_you, q, direction)
        apply_quadrant_rotation(new_opp, q, direction)

        return new_you, new_opp

    # Step 1: Generate all possible moves
    moves = []
    for r in range(6):
        for c in range(6):
            if you[r][c] == 0 and opponent[r][c] == 0:
                for q in range(4):
                    for d in ['L', 'R']:
                        moves.append((r + 1, c + 1, q, d))

    # Step 2: Check for winning moves
    for move in moves:
        new_you, new_opp = apply_move(you, opponent, move)
        if check_win(new_you):
            return f"{move[0]},{move[1]},{move[2]},{move[3]}"

    # Step 3: If no winning move, return the first legally possible move
    if moves:
        return f"{moves[0][0]},{moves[0][1]},{moves[0][2]},{moves[0][3]}"

    # Fallback move if no legal move exists (should not happen)
    return "1,1,0,R"


def policy(you, opponent):
    def rotate_board(board, quad, direction):
        new_board = [row[:] for row in board]
        if quad == 0:
            rows, cols = [0, 1, 2], [0, 1, 2]
        elif quad == 1:
            rows, cols = [0, 1, 2], [3, 4, 5]
        elif quad == 2:
            rows, cols = [3, 4, 5], [0, 1, 2]
        else:
            rows, cols = [3, 4, 5], [3, 4, 5]
        original_quad = [[new_board[r][c] for c in cols] for r in rows]
        if direction == 'R':
            rotated_quad = [[original_quad[2 - j][i] for j in range(3)] for i in range(3)]
        else:
            rotated_quad = [[original_quad[j][2 - i] for j in range(3)] for i in range(3)]
        for r_idx, r in enumerate(rows):
            for c_idx, c in enumerate(cols):
                new_board[r][c] = rotated_quad[r_idx][c_idx]
        return new_board

    def has_five_in_row(board):
        directions = [(0,1), (1,0), (1,1), (1,-1)]
        for r in range(6):
            for c in range(6):
                for dr, dc in directions:
                    end_r, end_c = r + 4*dr, c + 4*dc
                    if 0 <= end_r < 6 and 0 <= end_c < 6:
                        if all(board[r+i*dr][c+i*dc] for i in range(5)):
                            return True
        return False

    def opponent_can_win(new_you, new_opponent):
        for r in range(6):
            for c in range(6):
                if new_you[r][c] or new_opponent[r][c]:
                    continue
                for quad in range(4):
                    for direction in ['L', 'R']:
                        copy_opponent = [row[:] for row in new_opponent]
                        copy_opponent[r][c] = 1
                        copy_you = [row[:] for row in new_you]
                        ry = rotate_board(copy_you, quad, direction)
                        ro = rotate_board(copy_opponent, quad, direction)
                        if has_five_in_row(ro):
                            return True
        return False

    for row in range(1, 7):
        for col in range(1, 7):
            r, c = row - 1, col - 1
            if you[r][c] or opponent[r][c]:
                continue
            for quad in range(4):
                for direction in ['L', 'R']:
                    cy = [row[:] for row in you]
                    cy[r][c] = 1
                    ny = rotate_board(cy, quad, direction)
                    no = rotate_board([row[:] for row in opponent], quad, direction)
                    if has_five_in_row(ny):
                        return f"{row},{col},{quad},{direction}"

    for row in range(1, 7):
        for col in range(1, 7):
            r, c = row - 1, col - 1
            if you[r][c] or opponent[r][c]:
                continue
            for quad in range(4):
                for direction in ['L', 'R']:
                    cy = [row[:] for row in you]
                    cy[r][c] = 1
                    ny = rotate_board(cy, quad, direction)
                    no = rotate_board([row[:] for row in opponent], quad, direction)
                    if not opponent_can_win(ny, no):
                        return f"{row},{col},{quad},{direction}"

    for row in range(1, 7):
        for col in range(1, 7):
            r, c = row - 1, col - 1
            if you[r][c] or opponent[r][c]:
                continue
            for quad in range(4):
                for direction in ['L', 'R']:
                    return f"{row},{col},{quad},{direction}"
    return ""


import copy

def has_five(board):
    """Check if there's a sequence of five 1's in a row on the board."""
    rows, cols = 6, 6
    # Check rows
    for r in range(rows):
        for c_start in range(cols - 4):
            if all(board[r][c_start + i] == 1 for i in range(5)):
                return True
    # Check columns
    for c in range(cols):
        for r_start in range(rows - 4):
            if all(board[r_start + i][c] == 1 for i in range(5)):
                return True
    # Check top-left to bottom-right diagonals
    for r_start in range(rows - 4):
        for c_start in range(cols - 4):
            if all(board[r_start + i][c_start + i] == 1 for i in range(5)):
                return True
    # Check top-right to bottom-left diagonals
    for r_start in range(rows - 4):
        for c_start in range(4, cols):
            if all(board[r_start + i][c_start - i] == 1 for i in range(5)):
                return True
    return False

def rotate_3x3(mat, dir):
    """Rotate a 3x3 matrix clockwise (R) or anticlockwise (L)."""
    if dir == 'R':
        return [
            [mat[2][0], mat[1][0], mat[0][0]],
            [mat[2][1], mat[1][1], mat[0][1]],
            [mat[2][2], mat[1][2], mat[0][2]],
        ]
    else:  # 'L'
        return [
            [mat[0][2], mat[1][2], mat[2][2]],
            [mat[0][1], mat[1][1], mat[2][1]],
            [mat[0][0], mat[1][0], mat[2][0]],
        ]

def rotate_board_quadrant(board, quad, dir):
    """Rotate the specified quadrant of the board in-place."""
    r0, c0 = (0, 0) if quad == 0 else (0, 3) if quad == 1 else (3, 0) if quad == 2 else (3, 3)
    mat = [[board[r0 + i][c0 + j] for j in range(3)] for i in range(3)]
    rotated = rotate_3x3(mat, dir)
    for i in range(3):
        for j in range(3):
            board[r0 + i][c0 + j] = rotated[i][j]

def simulate_move(you, opponent, r, c, quad, dir):
    """Simulate placing a marble and rotating the quadrant, returning new boards."""
    new_you = [row.copy() for row in you]
    new_opponent = [row.copy() for row in opponent]
    new_you[r][c] = 1
    rotate_board_quadrant(new_you, quad, dir)
    rotate_board_quadrant(new_opponent, quad, dir)
    return new_you, new_opponent

def compute_score(board):
    """Heuristic score favoring boards with longer contiguous lines."""
    score = 0
    for r in range(6):
        for c in range(6):
            if board[r][c] == 1:
                # Horizontal
                h_left = 0
                cc = c - 1
                while cc >= 0 and board[r][cc] == 1:
                    h_left += 1
                    cc -= 1
                h_right = 0
                cc = c + 1
                while cc < 6 and board[r][cc] == 1:
                    h_right += 1
                    cc += 1
                h_total = 1 + h_left + h_right

                # Vertical
                v_up = 0
                rr = r - 1
                while rr >= 0 and board[rr][c] == 1:
                    v_up += 1
                    rr -= 1
                v_down = 0
                rr = r + 1
                while rr < 6 and board[rr][c] == 1:
                    v_down += 1
                    rr += 1
                v_total = 1 + v_up + v_down

                # Diagonal top-left to bottom-right
                d1_up = 0
                rr, cc = r - 1, c - 1
                while rr >= 0 and cc >= 0 and board[rr][cc] == 1:
                    d1_up += 1
                    rr -= 1
                    cc -=1
                d1_down = 0
                rr, cc = r + 1, c + 1
                while rr < 6 and cc < 6 and board[rr][cc] == 1:
                    d1_down += 1
                    rr += 1
                    cc += 1
                d1_total = 1 + d1_up + d1_down

                # Diagonal top-right to bottom-left
                d2_up = 0
                rr, cc = r - 1, c + 1
                while rr >= 0 and cc < 6 and board[rr][cc] == 1:
                    d2_up += 1
                    rr -= 1
                    cc += 1
                d2_down = 0
                rr, cc = r + 1, c - 1
                while rr < 6 and cc >= 0 and board[rr][cc] == 1:
                    d2_down += 1
                    rr += 1
                    cc -=1
                d2_total = 1 + d2_up + d2_down

                max_line = max(h_total, v_total, d1_total, d2_total)
                score += max_line * max_line  # Favor longer lines quadratically
    return score

def policy(you, opponent):
    empty_cells = [(r, c) for r in range(6) for c in range(6) if you[r][c] == 0 and opponent[r][c] == 0]
    
    win_moves = []
    draw_moves = []
    safe_moves = []  # [(score, move_str)]
    losing_moves = []

    # Evaluate all possible moves
    for r, c in empty_cells:
        for quad in range(4):
            for dir in ['L', 'R']:
                new_you, new_opponent = simulate_move(you, opponent, r, c, quad, dir)
                you_win = has_five(new_you)
                opp_win = has_five(new_opponent)
                move_str = f"{r+1},{c+1},{quad},{dir}"

                if you_win and not opp_win:
                    win_moves.append(move_str)
                elif you_win and opp_win:
                    draw_moves.append(move_str)
                elif opp_win:
                    losing_moves.append(move_str)
                else:
                    score = compute_score(new_you)
                    safe_moves.append( (score, move_str) )
    
    # Return the best move possible
    if win_moves:
        return win_moves[0]
    if safe_moves:
        safe_moves.sort(reverse=True, key=lambda x: x[0])
        return safe_moves[0][1]
    if draw_moves:
        return draw_moves[0]
    return losing_moves[0] if losing_moves else f"{empty_cells[0][0]+1},{empty_cells[0][1]+1},0,R"  # Fallback

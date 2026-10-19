
import copy

def has_five(board):
    """Check if the given board has five in a row."""
    # Check rows
    for r in range(6):
        for c in range(2):
            if all(board[r][c+i] for i in range(5)):
                return True
    # Check columns
    for c in range(6):
        for r in range(2):
            if all(board[r+i][c] for i in range(5)):
                return True
    # Check main diagonals (top-left to bottom-right)
    for r in range(2):
        for c in range(2):
            if all(board[r+i][c+i] for i in range(5)):
                return True
    # Check anti-diagonals (top-right to bottom-left)
    for r in range(2):
        for c in range(4,6):
            if all(board[r+i][c-i] for i in range(5)):
                return True
    return False

def apply_rotation(board, quad, direction):
    """Rotate the specified quadrant of the board in-place."""
    if quad == 0:
        rows = slice(0,3)
        cols = slice(0,3)
    elif quad == 1:
        rows = slice(0,3)
        cols = slice(3,6)
    elif quad == 2:
        rows = slice(3,6)
        cols = slice(0,3)
    elif quad == 3:
        rows = slice(3,6)
        cols = slice(3,6)
    else:
        return

    quadrant = [board[r][cols] for r in range(rows.start, rows.stop)]
    if direction == 'R':
        rotated = list(zip(*reversed(quadrant)))
    elif direction == 'L':
        rotated = list(zip(*quadrant))[::-1]
    rotated = [list(row) for row in rotated]

    for i, r in enumerate(range(rows.start, rows.stop)):
        for j, c in enumerate(range(cols.start, cols.stop)):
            board[r][c] = rotated[i][j]

def policy(you, opponent):
    """Select the best move according to the policy."""
    you = [list(row) for row in you]
    opponent = [list(row) for row in opponent]
    
    empty_cells = []
    for r in range(6):
        for c in range(6):
            if you[r][c] == 0 and opponent[r][c] == 0:
                empty_cells.append((r+1, c+1))

    candidate_moves = []
    for r, c in empty_cells:
        for quad in range(4):
            for dir in ['L', 'R']:
                candidate_moves.append(f"{r},{c},{quad},{dir}")

    winning_moves = []
    losing_moves = []
    neutral_moves = []

    for move_str in candidate_moves:
        r, c, quad, dir = move_str.split(',')
        r_idx = int(r) - 1
        c_idx = int(c) - 1
        quad = int(quad)
        dir = dir

        you_copy = copy.deepcopy(you)
        opponent_copy = copy.deepcopy(opponent)

        if you_copy[r_idx][c_idx] != 0 or opponent_copy[r_idx][c_idx] != 0:
            continue

        you_copy[r_idx][c_idx] = 1

        apply_rotation(you_copy, quad, dir)
        apply_rotation(opponent_copy, quad, dir)

        me_win = has_five(you_copy)
        opp_win = has_five(opponent_copy)

        if me_win:
            winning_moves.append(move_str)
        elif opp_win:
            losing_moves.append(move_str)
        else:
            r_placed = int(r)
            c_placed = int(c)
            dx = (r_placed - 3.5) ** 2
            dy = (c_placed - 3.5) ** 2
            center_score = 1 / (1 + dx + dy)

            quad_marbles = 0
            if quad == 0:
                rows = slice(0,3)
                cols = slice(0,3)
            elif quad == 1:
                rows = slice(0,3)
                cols = slice(3,6)
            elif quad == 2:
                rows = slice(3,6)
                cols = slice(0,3)
            else:
                rows = slice(3,6)
                cols = slice(3,6)

            for i in range(rows.start, rows.stop):
                for j in range(cols.start, cols.stop):
                    quad_marbles += you[i][j] - opponent[i][j]

            total_score = center_score + 0.1 * quad_marbles
            neutral_moves.append((move_str, total_score))

    if winning_moves:
        return winning_moves[0]
    if neutral_moves:
        neutral_moves.sort(key=lambda x: -x[1])
        return neutral_moves[0][0]
    if losing_moves:
        return losing_moves[0]
    return candidate_moves[0]

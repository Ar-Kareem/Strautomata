
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Plays Tic Tac Toe optimally.
    1. Can win immediately.
    2. Must block opponent's immediate win.
    3. Takes the center if available.
    4. Takes a corner if available.
    5. Takes the remaining side.
    """
    me = 1
    opp = -1
    
    def check_line(a, b, c, target):
        return (a == target) + (b == target) + (c == target)

    # 1. Check for immediate win
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                # Temporarily check if this move wins
                # Check Row
                r_count = check_line(board[r][(c+1)%3], board[r][(c+2)%3], 0, 1) # Actually easier to check specific cells
                # Better approach:
                # Check row
                r_cells = [board[r][0], board[r][1], board[r][2]]
                r_cells[c] = 1
                if r_cells.count(1) == 3:
                    return r, c
                
                # Check col
                c_cells = [board[0][c], board[1][c], board[2][c]]
                c_cells[r] = 1
                if c_cells.count(1) == 3:
                    return r, c
                
                # Check diagonal
                if r == c:
                    d_cells = [board[0][0], board[1][1], board[2][2]]
                    d_cells[r] = 1
                    if d_cells.count(1) == 3:
                        return r, c
                if r == 2-c:
                    d_cells = [board[0][2], board[1][1], board[2][0]]
                    d_cells[r] = 1
                    if d_cells.count(1) == 3:
                        return r, c

    # 2. Check for immediate block (opponent can win next)
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                # Check row
                r_cells = [board[r][0], board[r][1], board[r][2]]
                r_cells[c] = -1
                if r_cells.count(-1) == 3:
                    return r, c
                
                # Check col
                c_cells = [board[0][c], board[1][c], board[2][c]]
                c_cells[r] = -1
                if c_cells.count(-1) == 3:
                    return r, c
                
                # Check diagonal
                if r == c:
                    d_cells = [board[0][0], board[1][1], board[2][2]]
                    d_cells[r] = -1
                    if d_cells.count(-1) == 3:
                        return r, c
                if r == 2-c:
                    d_cells = [board[0][2], board[1][1], board[2][0]]
                    d_cells[r] = -1
                    if d_cells.count(-1) == 3:
                        return r, c

    # 3. Take Center
    if board[1][1] == 0:
        return 1, 1

    # 4. Take a Corner
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    random.shuffle(corners) # Prefer random to avoid patterns, though center is deterministic
    for r, c in corners:
        if board[r][c] == 0:
            return r, c

    # 5. Take Side
    sides = [(0, 1), (1, 0), (1, 2), (2, 1)]
    for r, c in sides:
        if board[r][c] == 0:
            return r, c

    # Board is full (should not happen in a valid game call)
    return 0, 0

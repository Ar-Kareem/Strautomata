
import copy

def policy(you, opponent) -> str:
    # Convert input to 2D lists for easier manipulation
    me = [list(row) for row in you]
    them = [list(row) for row in opponent]

    def check_win(board):
        # Checks if a board (6x6 list) has 5 in a row
        # check rows
        for r in range(6):
            for c in range(2):
                if board[r][c] != 0 and all(board[r][c+i] == board[r][c] for i in range(1, 5)):
                    return board[r][c]
        # check cols
        for c in range(6):
            for r in range(2):
                if board[r][c] != 0 and all(board[r+i][c] == board[r][c] for i in range(1, 5)):
                    return board[r][c]
        # check diagonals
        for r in range(2):
            for c in range(2):
                if board[r][c] != 0 and all(board[r+i][c+i] == board[r][c] for i in range(1, 5)):
                    return board[r][c]
            for c in range(4, 6):
                if board[r][c] != 0 and all(board[r+i][c-i] == board[r][c] for i in range(1, 5)):
                    return board[r][c]
        return 0

    def rotate(board, quad, direction):
        new_board = [row[:] for row in board]
        r_start = (quad // 2) * 3
        c_start = (quad % 2) * 3
        sub = [board[r_start+i][c_start:c_start+3] for i in range(3)]
        if direction == 'R': # Clockwise
            rotated = [[sub[2-j][i] for j in range(3)] for i in range(3)]
        else: # Anticlockwise (L)
            rotated = [[sub[j][2-i] for j in range(3)] for i in range(3)]
        
        for i in range(3):
            for j in range(3):
                new_board[r_start+i][c_start+j] = rotated[i][j]
        return new_board

    # Combine boards for internal simulation: 1 for me, -1 for opponent
    sim_board = [[0]*6 for _ in range(6)]
    empty_cells = []
    for r in range(6):
        for c in range(6):
            if me[r][c] == 1: sim_board[r][c] = 1
            elif them[r][c] == 1: sim_board[r][c] = -1
            else: empty_cells.append((r, c))

    # 1. Search for a winning move
    for r, c in empty_cells:
        temp_board = [row[:] for row in sim_board]
        temp_board[r][c] = 1
        for q in range(4):
            for d in ['L', 'R']:
                after_rot = rotate(temp_board, q, d)
                win = check_win(after_rot)
                if win == 1:
                    return f"{r+1},{c+1},{q},{d}"

    # 2. Block immediate opponent wins (Simple heuristic)
    # If opponent can win in 1 move, we must block. 
    # This is complex in Pentago, so we pick a high-value central move if no win.
    
    # Preferred order: Center of quadrants, then others
    centers = [(1,1), (1,4), (4,1), (4,4), (2,2), (2,3), (3,2), (3,3)]
    for r, c in centers:
        if sim_board[r][c] == 0:
            return f"{r+1},{c+1},0,R"

    # Fallback to first available
    r, c = empty_cells[0]
    return f"{r+1},{c+1},0,R"


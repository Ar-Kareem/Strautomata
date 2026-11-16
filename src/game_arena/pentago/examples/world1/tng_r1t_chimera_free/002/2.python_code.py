
def policy(you, opponent) -> str:
    # Helper function to rotate a quadrant in a given direction
    def rotate_quadrant(board, quad, direction):
        if quad == 0:
            rows = slice(0, 3)
            cols = slice(0, 3)
        elif quad == 1:
            rows = slice(0, 3)
            cols = slice(3, 6)
        elif quad == 2:
            rows = slice(3, 6)
            cols = slice(0, 3)
        elif quad == 3:
            rows = slice(3, 6)
            cols = slice(3, 6)
        else:
            raise ValueError("Invalid quadrant")

        q = [[board[r][c] for c in range(cols.start, cols.stop)] for r in range(rows.start, rows.stop)]
        if direction == 'L':
            rotated = list(zip(*q))[::-1]  # Anticlockwise
        elif direction == 'R':
            rotated = list(zip(*q[::-1]))  # Clockwise
        else:
            raise ValueError("Invalid direction")
        
        rotated = [list(row) for row in rotated]
        for i in range(3):
            for j in range(3):
                board[rows.start + i][cols.start + j] = rotated[i][j]

    # Helper function to check for five in a row
    def check_five(board):
        # Check rows
        for r in range(6):
            for c in range(2):
                if sum(board[r][c:c+5]) == 5:
                    return True
        # Check columns
        for c in range(6):
            if sum(board[r][c] for r in range(2, 6)) == 5:
                return False
            for r in range(2):
                total = 0
                for i in range(5):
                    total += board[r + i][c]
                if total == 5:
                    return True
        # Check \ diagonals
        for r in range(2):
            for c in range(2):
                total = 0
                for i in range(5):
                    total += board[r + i][c + i]
                if total == 5:
                    return True
        # Check / diagonals
        for r in range(2):
            for c in range(4, 6):
                total = 0
                for i in range(5):
                    total += board[r + i][c - i]
                if total == 5:
                    return True
        return False

    # Convert input to lists for easier manipulation
    you = [list(row) for row in you]
    opponent = [list(row) for row in opponent]

    # Collect all empty cells, sorted by centrality
    empty_cells = []
    for r in range(6):
        for c in range(6):
            if you[r][c] == 0 and opponent[r][c] == 0:
                empty_cells.append((r, c))
    # Prioritize central cells: Manhattan distance from center (2.5, 2.5)
    empty_cells.sort(key=lambda pos: abs(pos[0] - 2.5) + abs(pos[1] - 2.5))

    # Check for winning moves
    for r, c in empty_cells:
        for quad in range(4):
            for dir in ['L', 'R']:
                # Simulate the move
                you_copy = [row.copy() for row in you]
                opp_copy = [row.copy() for row in opponent]
                you_copy[r][c] = 1
                rotate_quadrant(you_copy, quad, dir)
                rotate_quadrant(opp_copy, quad, dir)
                if check_five(you_copy):
                    return f"{r+1},{c+1},{quad},{dir}"

    # If no winning move, return the first legal move
    r, c = empty_cells[0]
    return f"{r+1},{c+1},0,L"

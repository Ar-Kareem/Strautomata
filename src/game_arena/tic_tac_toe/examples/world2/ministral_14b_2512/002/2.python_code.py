import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Precompute all possible lines (rows, columns, diagonals)
    lines = get_all_lines(board)

    # Check all empty spots to see if placing 1 would win or block
    empty_spots = [(row, col) for row in range(4) for col in range(4) if board[row][col] == 0]
    for (row, col) in empty_spots:
        temp_board = [row[:] for row in board]
        temp_board[row][col] = 1
        if would_win_or_block(temp_board, lines):
            return (row, col)

    # If no winning or blocking move found, pick a random empty spot
    if empty_spots:
        return random.choice(empty_spots)
    else:
        return (0, 0)

def get_all_lines(board: list[list[int]]) -> list[list[tuple[int, int]]]:
    # Get all rows
    rows = [[(row, col) for col in range(4)] for row in range(4)]
    # Get all columns
    columns = [[(row, col) for row in range(4)] for col in range(4)]
    # Get main diagonals (top-left to bottom-right and top-right to bottom-left)
    diagonal1 = [(i, i) for i in range(4)]
    diagonal2 = [(i, 3-i) for i in range(4)]
    # Get diagonals of length 3
    diagonals_length3 = [
        [(0,1), (1,2), (2,3)],  # top-left to bottom-right
        [(1,0), (2,1), (3,2)],  # top-left to bottom-right
        [(0,2), (1,1), (2,0)],  # top-right to bottom-left
        [(1,3), (2,2), (3,1)]   # top-right to bottom-left
    ]
    # Also, diagonals of length 4 are already included as main diagonals
    all_lines = rows + columns + [diagonal1, diagonal2] + diagonals_length3
    return all_lines

def would_win_or_block(board: list[list[int]], lines: list[list[tuple[int, int]]]) -> bool:
    # Check if placing 1 would complete a line of four or block opponent's line of four
    for line in lines:
        count_1 = sum(1 for (row, col) in line if board[row][col] == 1)
        count_neg1 = sum(1 for (row, col) in line if board[row][col] == -1)
        count_0 = sum(1 for (row, col) in line if board[row][col] == 0)
        if count_0 == 1 and count_1 == 3:
            return True  # would win
        if count_0 == 1 and count_neg1 == 3:
            return True  # would block
    return False

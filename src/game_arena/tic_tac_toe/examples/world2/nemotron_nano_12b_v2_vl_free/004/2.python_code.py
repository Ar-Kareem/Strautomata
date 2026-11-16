
import copy

def check_win(board, player):
    for row in board:
        if all(cell == player for cell in row):
            return True
    for c in range(4):
        if all(board[r][c] == player for r in range(4)):
            return True
    if all(board[i][i] == player for i in range(4)):
        return True
    if all(board[i][3 - i] == player for i in range(4)):
        return True
    return False

def policy(board):
    for row in range(4):
        for col in range(4):
            if board[row][col] == 0:
                temp = [row.copy() for row in board]
                temp[row][col] = 1
                if check_win(temp, 1):
                    return (row, col)
                temp[row][col] = 0

    for row in range(4):
        for col in range(4):
            if board[row][col] == 0:
                temp = [row.copy() for row in board]
                temp[row][col] = -1
                if check_win(temp, -1):
                    return (row, col)
                temp[row][col] = 0

    best_cell = None
    best_score = float('-inf')
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                new_board = [row.copy() for row in board]
                new_board[r][c] = 1
                line_count = 2
                if r == c or r + c == 3:
                    line_count += 1
                distance = (r - 1.5) ** 2 + (c - 1.5) ** 2
                score = line_count * 1000 + distance * 10
                if score > best_score:
                    best_score = score
                    best_cell = (r, c)
    return best_cell

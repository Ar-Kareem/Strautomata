
import copy

def check_winner(board):
    # Check rows
    for row in board:
        if abs(sum(row)) == 3:
            return 1 if sum(row) > 0 else -1
    # Check columns
    for col in range(3):
        col_sum = board[0][col] + board[1][col] + board[2][col]
        if abs(col_sum) == 3:
            return 1 if col_sum > 0 else -1
    # Check diagonals
    diag1 = board[0][0] + board[1][1] + board[2][2]
    diag2 = board[0][2] + board[1][1] + board[2][0]
    if abs(diag1) == 3:
        return 1 if diag1 > 0 else -1
    if abs(diag2) == 3:
        return 1 if diag2 > 0 else -1
    return 0

def get_possible_moves(board):
    moves = []
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                moves.append((i, j))
    return moves

def policy(board: list[list[int]]) -> int:
    possible_moves = get_possible_moves(board)
    
    # Check if we can win in this move
    for i, j in possible_moves:
        temp_board = copy.deepcopy(board)
        temp_board[i][j] = 1
        if check_winner(temp_board) == 1:
            return i * 3 + j + 1
    
    # Check if we need to block opponent's winning move
    for i, j in possible_moves:
        temp_board = copy.deepcopy(board)
        temp_board[i][j] = -1
        if check_winner(temp_board) == -1:
            return i * 3 + j + 1
    
    # Try to take the center
    if board[1][1] == 0:
        return 5
    
    # Try to take a corner
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    for i, j in corners:
        if board[i][j] == 0:
            return i * 3 + j + 1
    
    # Take any edge
    edges = [(0, 1), (1, 0), (1, 2), (2, 1)]
    for i, j in edges:
        if board[i][j] == 0:
            return i * 3 + j + 1
    
    # This should not happen if the board is valid
    return -1
